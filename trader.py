"""
Trading executor module for executing buy and sell orders.
"""
import logging
from typing import Optional, Dict
from config import Config

logger = logging.getLogger(__name__)


class Trader:
    """Handles execution of buy orders."""
    
    def __init__(self):
        self.api_key = Config.ALPACA_API_KEY
        self.secret_key = Config.ALPACA_SECRET_KEY
        self.base_url = Config.ALPACA_BASE_URL
        self.position_size = Config.POSITION_SIZE
        
        # Initialize Alpaca client if credentials are provided
        self.client = None
        if self.api_key and self.secret_key:
            try:
                from alpaca.trading.client import TradingClient
                from alpaca.trading.requests import MarketOrderRequest
                from alpaca.trading.enums import OrderSide, TimeInForce
                
                self.client = TradingClient(
                    api_key=self.api_key,
                    secret_key=self.secret_key,
                    paper=True if 'paper' in self.base_url.lower() else False
                )
                self.MarketOrderRequest = MarketOrderRequest
                self.OrderSide = OrderSide
                self.TimeInForce = TimeInForce
                logger.info("Alpaca trading client initialized")
            except ImportError:
                logger.warning("alpaca-py not installed. Install with: pip install alpaca-py")
            except Exception as e:
                logger.error(f"Error initializing Alpaca client: {e}")
        else:
            logger.warning("Alpaca API credentials not set. Trading will be simulated.")
    
    def buy_stock(self, symbol: str, dollar_amount: Optional[float] = None) -> bool:
        """
        Execute a buy order for a stock.
        
        Args:
            symbol: Stock symbol to buy
            dollar_amount: Dollar amount to invest (defaults to POSITION_SIZE)
            
        Returns:
            True if order was successful, False otherwise
        """
        if dollar_amount is None:
            dollar_amount = self.position_size
        
        try:
            if self.client:
                return self._execute_alpaca_order(symbol, dollar_amount)
            else:
                return self._simulate_order(symbol, dollar_amount)
                
        except Exception as e:
            logger.error(f"Error executing buy order for {symbol}: {e}")
            return False
    
    def _execute_alpaca_order(self, symbol: str, dollar_amount: float) -> bool:
        """Execute order using Alpaca API."""
        try:
            # Get current price to calculate quantity
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest
            
            data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key
            )
            
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quote = data_client.get_stock_latest_quote(quote_request)
            
            if symbol not in quote:
                logger.error(f"No quote data available for {symbol}")
                return False
            
            current_price = float(quote[symbol].ask_price)
            quantity = int(dollar_amount / current_price)
            
            if quantity < 1:
                logger.warning(
                    f"Position size ${dollar_amount:.2f} too small for {symbol} "
                    f"at ${current_price:.2f}. Minimum 1 share required."
                )
                return False
            
            # Create market order
            market_order_data = self.MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=self.OrderSide.BUY,
                time_in_force=self.TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_data=market_order_data)
            
            logger.info(
                f"✅ BUY ORDER EXECUTED: {quantity} shares of {symbol} "
                f"at ~${current_price:.2f} (${dollar_amount:.2f} total)"
            )
            logger.info(f"Order ID: {order.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing Alpaca order for {symbol}: {e}")
            return False
    
    def sell_stock(self, symbol: str, shares: Optional[float] = None) -> bool:
        """
        Execute a sell order for a stock.
        
        Args:
            symbol: Stock symbol to sell
            shares: Number of shares to sell (defaults to all shares in position)
            
        Returns:
            True if order was successful, False otherwise
        """
        try:
            if self.client:
                return self._execute_alpaca_sell_order(symbol, shares)
            else:
                return self._simulate_sell_order(symbol, shares)
                
        except Exception as e:
            logger.error(f"Error executing sell order for {symbol}: {e}")
            return False
    
    def _execute_alpaca_sell_order(self, symbol: str, shares: Optional[float] = None) -> bool:
        """Execute sell order using Alpaca API."""
        try:
            # Get current position if shares not specified
            if shares is None:
                positions = self.client.get_all_positions()
                position = next((p for p in positions if p.symbol == symbol), None)
                if not position:
                    logger.warning(f"No position found for {symbol}")
                    return False
                shares = float(position.qty)
            
            if shares < 1:
                logger.warning(f"Not enough shares to sell for {symbol}")
                return False
            
            # Get current price
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest
            
            data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key
            )
            
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quote = data_client.get_stock_latest_quote(quote_request)
            
            if symbol not in quote:
                logger.error(f"No quote data available for {symbol}")
                return False
            
            current_price = float(quote[symbol].bid_price)
            quantity = int(shares)
            
            # Create market order
            market_order_data = self.MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=self.OrderSide.SELL,
                time_in_force=self.TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_data=market_order_data)
            
            logger.info(
                f"✅ SELL ORDER EXECUTED: {quantity} shares of {symbol} "
                f"at ~${current_price:.2f} (${quantity * current_price:.2f} total)"
            )
            logger.info(f"Order ID: {order.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing Alpaca sell order for {symbol}: {e}")
            return False
    
    def _simulate_sell_order(self, symbol: str, shares: Optional[float] = None) -> bool:
        """Simulate sell order execution (for testing without API credentials)."""
        shares_str = f"{shares:.2f} shares" if shares else "all shares"
        logger.info(
            f"🔵 SIMULATED SELL ORDER: {symbol} - {shares_str} "
            f"(No API credentials configured)"
        )
        return True
    
    def _simulate_order(self, symbol: str, dollar_amount: float) -> bool:
        """Simulate order execution (for testing without API credentials)."""
        logger.info(
            f"🔵 SIMULATED BUY ORDER: {symbol} for ${dollar_amount:.2f} "
            f"(No API credentials configured)"
        )
        return True
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol."""
        try:
            if self.client:
                positions = self.client.get_all_positions()
                position = next((p for p in positions if p.symbol == symbol), None)
                if position:
                    return {
                        'symbol': position.symbol,
                        'shares': float(position.qty),
                        'avg_entry_price': float(position.avg_entry_price),
                        'market_value': float(position.market_value)
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting position for {symbol}: {e}")
            return None

