"""
Paper Trade API - Real-time Trading Simulation
"""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify
import yfinance as yf
import pandas as pd
from src.utils.file_utils import load_json_safe, save_json_safe
from src.core.cache import get_cached_data, cache_data
from src.analyzers.market_sentiment_analyzer import MarketSentimentAnalyzer
from src.data.fetch_historical_data import get_stock_data
from src.data.realtime_data_fetcher import get_realtime_price, get_multiple_realtime_prices

logger = logging.getLogger(__name__)

papertrade_bp = Blueprint('papertrade', __name__)

class PaperTradeEngine:
    def __init__(self):
        self.orders_file = "data/persistent/papertrade_orders.json"
        self.positions_file = "data/persistent/papertrade_positions.json"
        self.portfolio_file = "data/persistent/papertrade_portfolio.json"
        self.sentiment_analyzer = MarketSentimentAnalyzer()

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.orders_file), exist_ok=True)

        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize persistent files if they don't exist"""
        if not os.path.exists(self.orders_file):
            save_json_safe(self.orders_file, [])
        if not os.path.exists(self.positions_file):
            save_json_safe(self.positions_file, [])
        if not os.path.exists(self.portfolio_file):
            save_json_safe(self.portfolio_file, {
                "initial_capital": 1000000.0,  # 10 Lakh INR
                "current_capital": 1000000.0,
                "total_pnl": 0.0,
                "realized_pnl": 0.0,
                "unrealized_pnl": 0.0,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            })

    def get_live_price(self, symbol: str) -> Optional[float]:
        """Get real-time price for symbol"""
        try:
            # Check cache first (30 second TTL for paper trading)
            cache_key = f"live_price_{symbol}"
            cached_data = get_cached_data(cache_key)
            if cached_data is not None:
                return cached_data.get('price') if isinstance(cached_data, dict) else cached_data

            # Use the real-time data fetcher
            realtime_data = get_realtime_price(symbol)
            
            if realtime_data and realtime_data.get('current_price', 0) > 0:
                live_price = float(realtime_data['current_price'])
                # Cache the full data for 30 seconds
                cache_data(cache_key, {
                    'price': live_price,
                    'change': realtime_data.get('change', 0),
                    'change_percent': realtime_data.get('change_percent', 0)
                }, ttl=30)
                logger.info(f"✅ Live price for {symbol}: ₹{live_price}")
                return live_price

            # Fallback to historical data
            try:
                stock_data = get_stock_data(symbol)
                if stock_data and len(stock_data) > 0:
                    live_price = float(stock_data.iloc[-1]['Close'])
                    cache_data(cache_key, {'price': live_price}, ttl=30)
                    logger.info(f"✅ Historical price for {symbol}: ₹{live_price}")
                    return live_price
            except Exception as e:
                logger.warning(f"Historical data fallback failed for {symbol}: {e}")

            logger.error(f"Could not fetch any price data for {symbol}")
            return None

        except Exception as e:
            logger.error(f"Error getting live price for {symbol}: {e}")
            return None

    def execute_order(self, symbol: str, side: str, quantity: int, order_type: str = "MARKET") -> Dict:
        """Execute a paper trade order at live market price"""
        try:
            # Get current price using real-time data
            realtime_data = get_realtime_price(symbol)

            if realtime_data.get('is_realtime') and realtime_data.get('current_price', 0) > 0:
                live_price = float(realtime_data['current_price'])
                price_source = 'real-time'
            else:
                # Fallback to historical data
                stock_data = get_stock_data(symbol)
                if not stock_data or len(stock_data) == 0:
                    return {
                        "success": False,
                        "error": f"Unable to fetch price data for {symbol}",
                        "symbol": symbol
                    }
                live_price = float(stock_data.iloc[-1]['Close'])
                price_source = 'historical'

            if live_price is None:
                return {
                    "success": False,
                    "error": f"Unable to fetch live price for {symbol}",
                    "symbol": symbol
                }

            # Generate order ID
            order_id = f"PT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}_{side}"

            # Create order record
            order = {
                "order_id": order_id,
                "symbol": symbol,
                "side": side.upper(),  # BUY or SELL
                "quantity": quantity,
                "order_type": order_type,
                "exec_price": live_price,
                "exec_value": live_price * quantity,
                "timestamp": datetime.now().isoformat(),
                "status": "EXECUTED",
                "price_source": price_source
            }

            # Save order
            orders = load_json_safe(self.orders_file, [])
            orders.append(order)
            save_json_safe(self.orders_file, orders)

            # Update positions
            self._update_positions(order)

            # Update portfolio
            self._update_portfolio()

            logger.info(f"✅ Paper trade executed: {side} {quantity} {symbol} @ ₹{live_price} (Source: {price_source})")

            return {
                "success": True,
                "order": order,
                "live_price": live_price,
                "exec_value": live_price * quantity,
                "price_source": price_source
            }

        except Exception as e:
            logger.error(f"Error executing paper trade: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol
            }

    def _update_positions(self, order: Dict):
        """Update positions based on executed order"""
        try:
            positions = load_json_safe(self.positions_file, [])
            symbol = order["symbol"]
            side = order["side"]
            quantity = order["quantity"]
            price = order["exec_price"]

            # Find existing position
            position_idx = None
            for i, pos in enumerate(positions):
                if pos["symbol"] == symbol:
                    position_idx = i
                    break

            if side == "BUY":
                if position_idx is not None:
                    # Add to existing position
                    pos = positions[position_idx]
                    total_value = (pos["quantity"] * pos["avg_price"]) + (quantity * price)
                    total_quantity = pos["quantity"] + quantity
                    avg_price = total_value / total_quantity

                    positions[position_idx].update({
                        "quantity": total_quantity,
                        "avg_price": avg_price,
                        "last_updated": datetime.now().isoformat()
                    })
                else:
                    # Create new position
                    positions.append({
                        "position_id": f"POS_{symbol}_{datetime.now().strftime('%Y%m%d')}",
                        "symbol": symbol,
                        "quantity": quantity,
                        "avg_price": price,
                        "created_at": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat()
                    })

            elif side == "SELL":
                if position_idx is not None:
                    pos = positions[position_idx]
                    if pos["quantity"] >= quantity:
                        pos["quantity"] -= quantity
                        pos["last_updated"] = datetime.now().isoformat()

                        # Remove position if quantity is 0
                        if pos["quantity"] == 0:
                            positions.pop(position_idx)
                    else:
                        logger.warning(f"Insufficient quantity to sell for {symbol}")
                else:
                    logger.warning(f"No position found to sell for {symbol}")

            save_json_safe(self.positions_file, positions)

        except Exception as e:
            logger.error(f"Error updating positions: {e}")

    def _update_portfolio(self):
        """Update portfolio metrics with current positions and live prices"""
        try:
            portfolio = load_json_safe(self.portfolio_file, {})
            positions = load_json_safe(self.positions_file, [])
            orders = load_json_safe(self.orders_file, [])

            # Calculate realized P&L from completed trades
            realized_pnl = 0.0
            for order in orders:
                if order["side"] == "SELL":
                    realized_pnl += order["exec_value"]
                elif order["side"] == "BUY":
                    realized_pnl -= order["exec_value"]

            # Calculate unrealized P&L from current positions
            unrealized_pnl = 0.0
            total_position_value = 0.0

            for position in positions:
                live_price = self.get_live_price(position["symbol"])
                if live_price:
                    position_value = position["quantity"] * live_price
                    cost_basis = position["quantity"] * position["avg_price"]
                    position_pnl = position_value - cost_basis

                    unrealized_pnl += position_pnl
                    total_position_value += position_value

            # Update portfolio
            total_pnl = realized_pnl + unrealized_pnl
            current_capital = portfolio["initial_capital"] + total_pnl

            portfolio.update({
                "current_capital": current_capital,
                "total_pnl": total_pnl,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_position_value": total_position_value,
                "last_updated": datetime.now().isoformat()
            })

            save_json_safe(self.portfolio_file, portfolio)

        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")

    def get_positions(self) -> List[Dict]:
        """Get current positions with live P&L"""
        try:
            positions = load_json_safe(self.positions_file, [])

            # Get current prices for all positions using real-time data
            symbols = list(set(position['symbol'] for position in positions))
            current_prices = {}

            # Try real-time data first
            try:
                realtime_prices = get_multiple_realtime_prices(symbols)
                for symbol in symbols:
                    if symbol in realtime_prices and realtime_prices[symbol].get('is_realtime'):
                        current_prices[symbol] = float(realtime_prices[symbol]['current_price'])
                    else:
                        # Fallback to historical data
                        try:
                            stock_data = get_stock_data(symbol)
                            if stock_data and len(stock_data) > 0:
                                current_prices[symbol] = float(stock_data.iloc[-1]['Close'])
                            else:
                                current_prices[symbol] = 100.0
                        except Exception as e:
                            logger.warning(f"Could not get historical price for {symbol}: {str(e)}")
                            current_prices[symbol] = 100.0
            except Exception as e:
                logger.error(f"Error fetching real-time prices: {str(e)}")
                # Fallback to historical data for all symbols
                for symbol in symbols:
                    try:
                        stock_data = get_stock_data(symbol)
                        if stock_data and len(stock_data) > 0:
                            current_prices[symbol] = float(stock_data.iloc[-1]['Close'])
                        else:
                            current_prices[symbol] = 100.0
                    except Exception as e:
                        logger.warning(f"Could not get price for {symbol}: {str(e)}")
                        current_prices[symbol] = 100.0

            # Enrich with live data
            enriched_positions = []
            for position in positions:
                live_price = current_prices.get(position["symbol"])
                if live_price:
                    position_value = position["quantity"] * live_price
                    cost_basis = position["quantity"] * position["avg_price"]
                    pnl = position_value - cost_basis
                    pnl_percent = (pnl / cost_basis) * 100 if cost_basis > 0 else 0

                    enriched_position = position.copy()
                    enriched_position.update({
                        "current_price": live_price,
                        "position_value": position_value,
                        "cost_basis": cost_basis,
                        "pnl": pnl,
                        "pnl_percent": pnl_percent
                    })
                    enriched_positions.append(enriched_position)

            return enriched_positions

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_orders(self, limit: int = 50) -> List[Dict]:
        """Get order history"""
        try:
            orders = load_json_safe(self.orders_file, [])
            # Return latest orders first
            return sorted(orders, key=lambda x: x["timestamp"], reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []

    def close_position(self, symbol: str) -> Dict:
        """Close an entire position at current market price"""
        try:
            positions = load_json_safe(self.positions_file, [])

            # Find position
            position = None
            for pos in positions:
                if pos["symbol"] == symbol:
                    position = pos
                    break

            if not position:
                return {
                    "success": False,
                    "error": f"No position found for {symbol}"
                }

            # Execute sell order for entire quantity
            return self.execute_order(symbol, "SELL", position["quantity"])

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary with live data"""
        try:
            self._update_portfolio()  # Refresh with live prices
            portfolio = load_json_safe(self.portfolio_file, {})
            positions = self.get_positions()
            orders = load_json_safe(self.orders_file, [])

            # Calculate additional metrics
            total_trades = len(orders)
            open_positions = len(positions)
            
            # Calculate win/loss statistics
            buy_orders = [o for o in orders if o['side'] == 'BUY']
            sell_orders = [o for o in orders if o['side'] == 'SELL']
            
            # Calculate performance metrics
            total_invested = sum(o['exec_value'] for o in buy_orders)
            total_realized = sum(o['exec_value'] for o in sell_orders)

            return {
                "portfolio": portfolio,
                "positions_count": open_positions,
                "total_trades": total_trades,
                "positions": positions,
                "metrics": {
                    "total_invested": total_invested,
                    "total_realized": total_realized,
                    "buy_orders": len(buy_orders),
                    "sell_orders": len(sell_orders)
                }
            }

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                "portfolio": {
                    "initial_capital": 1000000.0,
                    "current_capital": 1000000.0,
                    "total_pnl": 0.0,
                    "realized_pnl": 0.0,
                    "unrealized_pnl": 0.0,
                    "total_position_value": 0.0,
                    "last_updated": datetime.now().isoformat()
                },
                "positions_count": 0,
                "total_trades": 0,
                "positions": []
            }

# Initialize engine
engine = PaperTradeEngine()

@papertrade_bp.route('/positions', methods=['GET'])
def get_positions():
    """Get current positions with live P&L"""
    try:
        positions = engine.get_positions()
        return jsonify({
            "success": True,
            "positions": positions,
            "count": len(positions),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_positions: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "positions": []
        }), 500

@papertrade_bp.route('/orders', methods=['GET'])
def get_orders():
    """Get order history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        orders = engine.get_orders(limit)
        return jsonify({
            "success": True,
            "orders": orders,
            "count": len(orders),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_orders: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "orders": []
        }), 500

@papertrade_bp.route('/execute', methods=['POST'])
def execute_trade():
    """Execute a paper trade at live market price"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        symbol = data.get('symbol', '').upper()
        side = data.get('side', '').upper()
        quantity = data.get('quantity', 0)

        # Validation
        if not symbol:
            return jsonify({
                "success": False,
                "error": "Symbol is required"
            }), 400

        if side not in ['BUY', 'SELL']:
            return jsonify({
                "success": False,
                "error": "Side must be BUY or SELL"
            }), 400

        if quantity <= 0:
            return jsonify({
                "success": False,
                "error": "Quantity must be positive"
            }), 400

        # Execute order
        result = engine.execute_order(symbol, side, quantity)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error in execute_trade: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@papertrade_bp.route('/close', methods=['POST'])
def close_position():
    """Close a position at current market price"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        symbol = data.get('symbol', '').upper()
        if not symbol:
            return jsonify({
                "success": False,
                "error": "Symbol is required"
            }), 400

        result = engine.close_position(symbol)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error in close_position: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@papertrade_bp.route('/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio summary with live data"""
    try:
        portfolio_data = engine.get_portfolio_summary()
        return jsonify({
            "success": True,
            "data": portfolio_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_portfolio: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {}
        }), 500

@papertrade_bp.route('/live-price/<symbol>', methods=['GET'])
def get_live_price(symbol):
    """Get live price for a symbol"""
    try:
        # Get cached data or fetch fresh
        cache_key = f"live_price_{symbol.upper()}"
        cached_data = get_cached_data(cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            return jsonify({
                "success": True,
                "symbol": symbol.upper(),
                "price": cached_data.get('price'),
                "change": cached_data.get('change', 0),
                "change_percent": cached_data.get('change_percent', 0),
                "timestamp": datetime.now().isoformat()
            })
        
        # Fallback to engine method
        price = engine.get_live_price(symbol.upper())
        if price is not None:
            return jsonify({
                "success": True,
                "symbol": symbol.upper(),
                "price": price,
                "change": 0,
                "change_percent": 0,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Unable to fetch price for {symbol}",
                "symbol": symbol.upper()
            }), 404
    except Exception as e:
        logger.error(f"Error getting live price: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500