
"""
Pinned Symbols Manager
Handles adding/removing/aggregating pinned symbols across products
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .date_utils import get_ist_now
from ..storage.json_store import json_store

logger = logging.getLogger(__name__)

class PinnedManager:
    """Manages pinned symbols and their stats across all products"""
    
    def __init__(self):
        self.pinned_store_key = "pinned_symbols"
        self.max_pinned = 20  # From runtime.py PINNED_ROW_MAX
    
    def get_pinned_symbols(self, product_type: str = None) -> List[str]:
        """Get list of pinned symbols, optionally filtered by product type"""
        try:
            pinned_data = json_store.load(self.pinned_store_key) or {}
            
            if product_type:
                return pinned_data.get(product_type, [])
            
            # Return all pinned symbols across products
            all_pinned = []
            for symbols in pinned_data.values():
                all_pinned.extend(symbols)
            
            return list(set(all_pinned))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting pinned symbols: {e}")
            return []
    
    def add_pinned_symbol(self, symbol: str, product_type: str) -> bool:
        """Add a symbol to pinned list"""
        try:
            pinned_data = json_store.load(self.pinned_store_key) or {}
            
            if product_type not in pinned_data:
                pinned_data[product_type] = []
            
            # Check if already pinned
            if symbol in pinned_data[product_type]:
                return True
            
            # Check max limit
            if len(pinned_data[product_type]) >= self.max_pinned:
                logger.warning(f"Max pinned limit ({self.max_pinned}) reached for {product_type}")
                return False
            
            pinned_data[product_type].append(symbol)
            pinned_data['last_updated'] = get_ist_now().isoformat()
            
            success = json_store.save(self.pinned_store_key, pinned_data)
            if success:
                logger.info(f"Added {symbol} to pinned {product_type} symbols")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding pinned symbol {symbol}: {e}")
            return False
    
    def remove_pinned_symbol(self, symbol: str, product_type: str) -> bool:
        """Remove a symbol from pinned list"""
        try:
            pinned_data = json_store.load(self.pinned_store_key) or {}
            
            if product_type not in pinned_data:
                return True
            
            if symbol in pinned_data[product_type]:
                pinned_data[product_type].remove(symbol)
                pinned_data['last_updated'] = get_ist_now().isoformat()
                
                success = json_store.save(self.pinned_store_key, pinned_data)
                if success:
                    logger.info(f"Removed {symbol} from pinned {product_type} symbols")
                return success
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing pinned symbol {symbol}: {e}")
            return False
    
    def get_pinned_stats(self, product_type: str, product_data: List[Dict]) -> Dict:
        """Calculate aggregated stats for pinned symbols"""
        try:
            pinned_symbols = self.get_pinned_symbols(product_type)
            
            if not pinned_symbols:
                return {
                    "count": 0,
                    "avg_roi": 0.0,
                    "avg_confidence": 0.0,
                    "top_gainer": None,
                    "top_loser": None,
                    "total_pl": 0.0
                }
            
            # Filter product data for pinned symbols
            pinned_data = [item for item in product_data if item.get('symbol') in pinned_symbols]
            
            if not pinned_data:
                return {
                    "count": len(pinned_symbols),
                    "avg_roi": 0.0,
                    "avg_confidence": 0.0,
                    "top_gainer": None,
                    "top_loser": None,
                    "total_pl": 0.0
                }
            
            # Calculate stats
            rois = [float(item.get('roi', 0)) for item in pinned_data if item.get('roi') is not None]
            confidences = [float(item.get('ai_confidence', 0)) for item in pinned_data if item.get('ai_confidence') is not None]
            
            avg_roi = sum(rois) / len(rois) if rois else 0.0
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            total_pl = sum(rois)  # Simplified P/L calculation
            
            # Find top gainer and loser
            top_gainer = max(pinned_data, key=lambda x: float(x.get('roi', 0))) if pinned_data else None
            top_loser = min(pinned_data, key=lambda x: float(x.get('roi', 0))) if pinned_data else None
            
            return {
                "count": len(pinned_symbols),
                "avg_roi": round(avg_roi, 2),
                "avg_confidence": round(avg_confidence, 1),
                "top_gainer": {
                    "symbol": top_gainer.get('symbol'),
                    "roi": round(float(top_gainer.get('roi', 0)), 2)
                } if top_gainer else None,
                "top_loser": {
                    "symbol": top_loser.get('symbol'),
                    "roi": round(float(top_loser.get('roi', 0)), 2)
                } if top_loser else None,
                "total_pl": round(total_pl, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating pinned stats: {e}")
            return {
                "count": 0,
                "avg_roi": 0.0,
                "avg_confidence": 0.0,
                "top_gainer": None,
                "top_loser": None,
                "total_pl": 0.0
            }

# Global instance
pinned_manager = PinnedManager()
