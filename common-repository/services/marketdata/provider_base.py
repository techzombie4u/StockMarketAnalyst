
"""
Abstract Base Class for Market Data Providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MarketDataProvider(ABC):
    """Abstract base class for all market data providers"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_connected = False
        self.last_error = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection to data source"""
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, days: int = 365) -> Optional[Dict]:
        """Get historical data for a symbol"""
        pass
    
    @abstractmethod
    def get_fundamental_data(self, symbol: str) -> Optional[Dict]:
        """Get fundamental data for a symbol"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            'name': self.name,
            'connected': self.is_connected,
            'available': self.is_available(),
            'last_error': self.last_error
        }
    
    def handle_error(self, error: Exception, operation: str) -> None:
        """Handle and log errors"""
        self.last_error = str(error)
        logger.error(f"{self.name} error in {operation}: {str(error)}")
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic validation - symbol should be alphanumeric
        return symbol.strip().isalnum() and len(symbol.strip()) > 0

class MarketDataManager:
    """Manager class to handle multiple market data providers"""
    
    def __init__(self):
        self.providers = {}
        self.primary_provider = None
        self.fallback_providers = []
    
    def register_provider(self, provider: MarketDataProvider, 
                         is_primary: bool = False) -> None:
        """Register a market data provider"""
        self.providers[provider.name] = provider
        
        if is_primary:
            self.primary_provider = provider.name
        else:
            self.fallback_providers.append(provider.name)
    
    def get_provider(self, name: str) -> Optional[MarketDataProvider]:
        """Get provider by name"""
        return self.providers.get(name)
    
    def get_data_with_fallback(self, operation: str, symbol: str, **kwargs) -> Optional[Any]:
        """Get data using primary provider with fallback support"""
        providers_to_try = []
        
        # Try primary provider first
        if self.primary_provider and self.primary_provider in self.providers:
            providers_to_try.append(self.primary_provider)
        
        # Add fallback providers
        providers_to_try.extend(self.fallback_providers)
        
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider or not provider.is_available():
                continue
            
            try:
                # Execute operation based on method name
                if operation == 'get_current_price':
                    result = provider.get_current_price(symbol)
                elif operation == 'get_historical_data':
                    result = provider.get_historical_data(symbol, kwargs.get('days', 365))
                elif operation == 'get_fundamental_data':
                    result = provider.get_fundamental_data(symbol)
                else:
                    logger.error(f"Unknown operation: {operation}")
                    continue
                
                if result is not None:
                    logger.debug(f"Successfully got {operation} for {symbol} from {provider_name}")
                    return result
                    
            except Exception as e:
                provider.handle_error(e, operation)
                logger.warning(f"Provider {provider_name} failed for {operation}: {str(e)}")
                continue
        
        logger.error(f"All providers failed for {operation} on {symbol}")
        return None
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            'primary_provider': self.primary_provider,
            'fallback_providers': self.fallback_providers,
            'providers': {}
        }
        
        for name, provider in self.providers.items():
            status['providers'][name] = provider.get_provider_info()
        
        return status
