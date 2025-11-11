"""
Trading executor module for executing buy orders.
"""
import logging
from typing import Optional
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
    
    def _simulate_order(self, symbol: str, dollar_amount: float) -> bool:
        """Simulate order execution (for testing without API credentials)."""
        logger.info(
            f"🔵 SIMULATED BUY ORDER: {symbol} for ${dollar_amount:.2f} "
            f"(No API credentials configured)"
        )
        return True

