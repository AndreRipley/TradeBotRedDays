"""
Main entry point for the trading bot.
"""
import logging
import sys
from config import Config
from scheduler import TradingScheduler


def setup_logging():
    """Configure logging for the application."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def main():
    """Main function to start the trading bot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🚀 Trading Bot Starting")
    logger.info("=" * 60)
    
    # Validate configuration
    if not Config.STOCKS:
        logger.error("No stocks configured. Please set STOCKS in .env or config.py")
        sys.exit(1)
    
    # Start scheduler
    scheduler = TradingScheduler()
    
    try:
        scheduler.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

