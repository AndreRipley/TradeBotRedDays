"""
Scheduler module to execute trades at noon daily.
"""
import schedule
import time
import logging
from datetime import datetime
import pytz
from config import Config
from stock_data import StockDataFetcher
from trader import Trader

logger = logging.getLogger(__name__)


class TradingScheduler:
    """Schedules and executes trading logic at noon."""
    
    def __init__(self):
        self.stock_fetcher = StockDataFetcher()
        self.trader = Trader()
        self.stocks = Config.STOCKS
        self.trade_time = Config.TRADE_TIME
        self.timezone = pytz.timezone(Config.TIMEZONE)
        
    def run(self):
        """Start the scheduler and run continuously."""
        logger.info(f"Starting trading bot scheduler")
        logger.info(f"Monitoring stocks: {', '.join(self.stocks)}")
        logger.info(f"Trade time: {self.trade_time} ({Config.TIMEZONE})")
        
        # Schedule the trading function
        schedule.every().day.at(self.trade_time).do(self._execute_trading_logic)
        
        logger.info("Scheduler started. Waiting for trade time...")
        
        # Run scheduler
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
    
    def _execute_trading_logic(self):
        """Execute the main trading logic: buy on red days at noon."""
        logger.info("=" * 60)
        logger.info(f"🕐 Trade execution time: {datetime.now(self.timezone)}")
        logger.info("=" * 60)
        
        for symbol in self.stocks:
            symbol = symbol.strip().upper()
            if not symbol:
                continue
                
            logger.info(f"\n📊 Checking {symbol}...")
            
            # Check if it's a red day
            is_red = self.stock_fetcher.is_red_day(symbol)
            
            if is_red is None:
                logger.warning(f"⚠️  Could not determine red day status for {symbol}. Skipping.")
                continue
            
            if is_red:
                logger.info(f"🔴 RED DAY detected for {symbol}. Executing buy order...")
                success = self.trader.buy_stock(symbol)
                
                if success:
                    logger.info(f"✅ Successfully executed buy order for {symbol}")
                else:
                    logger.error(f"❌ Failed to execute buy order for {symbol}")
            else:
                logger.info(f"🟢 GREEN DAY for {symbol}. No action taken.")
        
        logger.info("=" * 60)
        logger.info("Trading logic execution complete.\n")

