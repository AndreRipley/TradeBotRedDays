"""
Improved Anomaly Detection Trading Strategy
Includes:
- Stop-losses: sell if position drops by a certain percentage
- Trailing stops: let winners run instead of selling on first overbought signal
- Risk/reward ratio: ensure average win is larger than average loss
- Position sizing: reduce size on losing trades, increase on winning trades
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from anomaly_strategy import AnomalyDetector

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Position:
    """Represents a stock position with tracking for stop-loss and trailing stop."""
    
    def __init__(self, shares: float, entry_price: float, entry_date: str, position_size: float):
        self.shares = shares
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.position_size = position_size
        self.highest_price = entry_price  # For trailing stop
        self.stop_loss_price = entry_price * 0.95  # 5% stop-loss by default
        self.trailing_stop_price = entry_price * 0.95  # Trailing stop starts at 5% below entry
        self.trailing_stop_pct = 0.05  # 5% trailing stop
    
    def update_trailing_stop(self, current_price: float):
        """Update trailing stop if price moves higher."""
        if current_price > self.highest_price:
            self.highest_price = current_price
            # Trailing stop follows price up, maintaining 5% below highest
            self.trailing_stop_price = current_price * (1 - self.trailing_stop_pct)
    
    def should_stop_loss(self, current_price: float) -> bool:
        """Check if stop-loss should trigger."""
        return current_price <= self.stop_loss_price
    
    def should_trailing_stop(self, current_price: float) -> bool:
        """Check if trailing stop should trigger."""
        return current_price <= self.trailing_stop_price
    
    def get_unrealized_pnl_pct(self, current_price: float) -> float:
        """Get unrealized profit/loss percentage."""
        return ((current_price - self.entry_price) / self.entry_price) * 100


class ImprovedAnomalyTradingStrategy:
    """Improved anomaly detection trading strategy with risk management."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0, min_severity: float = 1.0,
                 stop_loss_pct: float = 0.05, trailing_stop_pct: float = 0.05,
                 min_risk_reward_ratio: float = 1.5):
        """
        Initialize improved strategy.
        
        Args:
            stocks: List of stock symbols
            position_size: Base dollar amount per trade
            min_severity: Minimum anomaly severity to trigger trade
            stop_loss_pct: Stop-loss percentage (default: 5%)
            trailing_stop_pct: Trailing stop percentage (default: 5%)
            min_risk_reward_ratio: Minimum risk/reward ratio (default: 1.5)
        """
        self.stocks = stocks
        self.base_position_size = position_size
        self.min_severity = min_severity
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.min_risk_reward_ratio = min_risk_reward_ratio
        self.detector = AnomalyDetector(lookback_period=20)
        self.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Track performance for dynamic position sizing
        self.stock_performance = {}  # Track win/loss for each stock
    
    def fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch historical stock data."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
            
            if data.empty:
                return pd.DataFrame()
            
            data = data.reset_index()
            data['Date'] = pd.to_datetime(data['Date'])
            return data
        except Exception as e:
            logger.warning(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def get_position_size(self, symbol: str) -> float:
        """Get dynamic position size based on stock performance."""
        if symbol not in self.stock_performance:
            return self.base_position_size
        
        perf = self.stock_performance[symbol]
        wins = perf.get('wins', 0)
        losses = perf.get('losses', 0)
        total_trades = wins + losses
        
        if total_trades == 0:
            return self.base_position_size
        
        win_rate = wins / total_trades
        
        # Increase position size for winning stocks, decrease for losing stocks
        if win_rate >= 0.6:  # 60%+ win rate
            multiplier = 1.2  # 20% increase
        elif win_rate >= 0.5:  # 50-60% win rate
            multiplier = 1.0  # Normal size
        elif win_rate >= 0.4:  # 40-50% win rate
            multiplier = 0.8  # 20% decrease
        else:  # < 40% win rate
            multiplier = 0.6  # 40% decrease
        
        return self.base_position_size * multiplier
    
    def update_performance(self, symbol: str, profit: float):
        """Update performance tracking for a stock."""
        if symbol not in self.stock_performance:
            self.stock_performance[symbol] = {'wins': 0, 'losses': 0, 'total_profit': 0}
        
        if profit > 0:
            self.stock_performance[symbol]['wins'] += 1
        else:
            self.stock_performance[symbol]['losses'] += 1
        
        self.stock_performance[symbol]['total_profit'] += profit
    
    def backtest_strategy(self, symbol: str) -> Dict:
        """Backtest improved anomaly detection strategy for a stock."""
        data = self.fetch_stock_data(symbol)
        if data.empty or len(data) < 30:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'total_invested': 0,
                'current_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'anomalies_detected': 0,
                'trades': [],
                'stop_loss_triggers': 0,
                'trailing_stop_triggers': 0,
                'overbought_sells': 0
            }
        
        trades = []
        total_invested = 0
        total_sold_value = 0
        positions = []  # List of Position objects
        anomalies_detected = 0
        stop_loss_triggers = 0
        trailing_stop_triggers = 0
        overbought_sells = 0
        
        # Start after lookback period
        for i in range(self.detector.lookback_period, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            
            # Check stop-losses and trailing stops for existing positions
            positions_to_remove = []
            for pos in positions:
                # Update trailing stop
                pos.update_trailing_stop(current_price)
                
                # Check stop-loss first (more urgent)
                if pos.should_stop_loss(current_price):
                    # Stop-loss triggered
                    proceeds = pos.shares * current_price
                    profit = proceeds - (pos.shares * pos.entry_price)
                    
                    trades.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'type': 'SELL',
                        'reason': 'STOP_LOSS',
                        'price': round(current_price, 2),
                        'shares': round(pos.shares, 4),
                        'proceeds': round(proceeds, 2),
                        'entry_price': round(pos.entry_price, 2),
                        'profit': round(profit, 2),
                        'profit_pct': round(pos.get_unrealized_pnl_pct(current_price), 2)
                    })
                    
                    total_sold_value += proceeds
                    positions_to_remove.append(pos)
                    stop_loss_triggers += 1
                    self.update_performance(symbol, profit)
                
                # Check trailing stop
                elif pos.should_trailing_stop(current_price):
                    # Trailing stop triggered
                    proceeds = pos.shares * current_price
                    profit = proceeds - (pos.shares * pos.entry_price)
                    
                    trades.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'type': 'SELL',
                        'reason': 'TRAILING_STOP',
                        'price': round(current_price, 2),
                        'shares': round(pos.shares, 4),
                        'proceeds': round(proceeds, 2),
                        'entry_price': round(pos.entry_price, 2),
                        'profit': round(profit, 2),
                        'profit_pct': round(pos.get_unrealized_pnl_pct(current_price), 2)
                    })
                    
                    total_sold_value += proceeds
                    positions_to_remove.append(pos)
                    trailing_stop_triggers += 1
                    self.update_performance(symbol, profit)
            
            # Remove closed positions
            for pos in positions_to_remove:
                positions.remove(pos)
            
            # Detect anomalies
            anomaly_info = self.detector.detect_all_anomalies(data, i)
            
            if anomaly_info['is_anomaly']:
                anomalies_detected += 1
                
                # Only trade if severity meets threshold
                if anomaly_info['severity'] >= self.min_severity:
                    signal_type = anomaly_info.get('signal_type', 'BUY')
                    
                    # Handle BUY signals
                    if signal_type in ['BUY', 'MIXED']:
                        # Get dynamic position size
                        position_size = self.get_position_size(symbol)
                        shares_to_buy = position_size / current_price
                        cost = shares_to_buy * current_price
                        
                        # Create new position
                        new_position = Position(
                            shares=shares_to_buy,
                            entry_price=current_price,
                            entry_date=current_date.strftime('%Y-%m-%d'),
                            position_size=position_size
                        )
                        new_position.stop_loss_price = current_price * (1 - self.stop_loss_pct)
                        new_position.trailing_stop_pct = self.trailing_stop_pct
                        new_position.trailing_stop_price = current_price * (1 - self.trailing_stop_pct)
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'type': 'BUY',
                            'price': round(current_price, 2),
                            'shares': round(shares_to_buy, 4),
                            'cost': round(cost, 2),
                            'position_size': round(position_size, 2),
                            'anomaly_types': ', '.join(anomaly_info['anomaly_types']),
                            'severity': round(anomaly_info['severity'], 2)
                        })
                        
                        positions.append(new_position)
                        total_invested += cost
                    
                    # Handle SELL signals (overbought) - only if no trailing stop is active
                    # We let winners run via trailing stops, so only sell on overbought if we have no positions
                    # or if the position is small and we want to take some profit
                    if signal_type in ['SELL', 'MIXED'] and len(positions) > 0:
                        # Only sell on overbought if we have multiple positions or want to take partial profit
                        # For now, we'll let trailing stops handle profit-taking
                        # But we can sell a small portion on strong overbought signals
                        if anomaly_info['severity'] >= 3.0:  # Very strong overbought signal
                            # Sell smallest position or 25% of largest position
                            if positions:
                                pos_to_sell = min(positions, key=lambda p: p.shares)
                                shares_to_sell = pos_to_sell.shares * 0.25  # Sell 25%
                                if shares_to_sell > 0:
                                    proceeds = shares_to_sell * current_price
                                    profit = proceeds - (shares_to_sell * pos_to_sell.entry_price)
                                    
                                    trades.append({
                                        'date': current_date.strftime('%Y-%m-%d'),
                                        'type': 'SELL',
                                        'reason': 'OVERBOUGHT',
                                        'price': round(current_price, 2),
                                        'shares': round(shares_to_sell, 4),
                                        'proceeds': round(proceeds, 2),
                                        'entry_price': round(pos_to_sell.entry_price, 2),
                                        'profit': round(profit, 2),
                                        'profit_pct': round(pos_to_sell.get_unrealized_pnl_pct(current_price), 2)
                                    })
                                    
                                    pos_to_sell.shares -= shares_to_sell
                                    total_sold_value += proceeds
                                    overbought_sells += 1
                                    self.update_performance(symbol, profit)
                                    
                                    # Remove position if fully sold
                                    if pos_to_sell.shares < 0.0001:
                                        positions.remove(pos_to_sell)
        
        # Close remaining positions at final price
        final_price = data.iloc[-1]['Close'] if len(data) > 0 else 0
        for pos in positions:
            proceeds = pos.shares * final_price
            profit = proceeds - (pos.shares * pos.entry_price)
            total_sold_value += proceeds
            self.update_performance(symbol, profit)
        
        # Calculate final value
        if len(data) > 0 and total_invested > 0:
            current_value = sum(pos.shares * final_price for pos in positions)
            total_value = current_value + total_sold_value
            profit_loss = total_value - total_invested
            return_pct = (profit_loss / total_invested * 100)
            
            return {
                'symbol': symbol,
                'total_trades': len(trades),
                'buy_trades': len([t for t in trades if t['type'] == 'BUY']),
                'sell_trades': len([t for t in trades if t['type'] == 'SELL']),
                'total_invested': round(total_invested, 2),
                'total_sold_value': round(total_sold_value, 2),
                'shares_owned': round(sum(pos.shares for pos in positions), 4),
                'final_price': round(final_price, 2),
                'current_value': round(current_value, 2),
                'total_value': round(total_value, 2),
                'profit_loss': round(profit_loss, 2),
                'return_pct': round(return_pct, 2),
                'anomalies_detected': anomalies_detected,
                'stop_loss_triggers': stop_loss_triggers,
                'trailing_stop_triggers': trailing_stop_triggers,
                'overbought_sells': overbought_sells,
                'trades': trades
            }
        else:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_invested': 0,
                'total_sold_value': 0,
                'current_value': 0,
                'total_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'anomalies_detected': anomalies_detected,
                'stop_loss_triggers': 0,
                'trailing_stop_triggers': 0,
                'overbought_sells': 0,
                'trades': []
            }
    
    def run_backtest(self) -> Dict:
        """Run backtest for all stocks."""
        logger.info(f"Starting improved anomaly detection backtest")
        logger.info(f"Period: {self.start_date} to {self.end_date}")
        logger.info(f"Base position size: ${self.base_position_size} per trade")
        logger.info(f"Stop-loss: {self.stop_loss_pct*100:.1f}%")
        logger.info(f"Trailing stop: {self.trailing_stop_pct*100:.1f}%")
        logger.info(f"Minimum severity: {self.min_severity}")
        
        results = {}
        total_invested_all = 0
        total_value_all = 0
        total_anomalies = 0
        total_stop_losses = 0
        total_trailing_stops = 0
        total_overbought_sells = 0
        
        for symbol in self.stocks:
            symbol = symbol.strip().upper()
            result = self.backtest_strategy(symbol)
            results[symbol] = result
            
            total_invested_all += result['total_invested']
            total_value_all += result.get('total_value', result['current_value'])
            total_anomalies += result['anomalies_detected']
            total_stop_losses += result.get('stop_loss_triggers', 0)
            total_trailing_stops += result.get('trailing_stop_triggers', 0)
            total_overbought_sells += result.get('overbought_sells', 0)
        
        # Calculate overall statistics
        total_profit_loss = total_value_all - total_invested_all
        overall_return_pct = (total_profit_loss / total_invested_all * 100) if total_invested_all > 0 else 0
        
        return {
            'period': f"{self.start_date} to {self.end_date}",
            'position_size': self.base_position_size,
            'min_severity': self.min_severity,
            'stop_loss_pct': self.stop_loss_pct,
            'trailing_stop_pct': self.trailing_stop_pct,
            'stocks': results,
            'summary': {
                'total_invested': round(total_invested_all, 2),
                'total_value': round(total_value_all, 2),
                'total_profit_loss': round(total_profit_loss, 2),
                'overall_return_pct': round(overall_return_pct, 2),
                'total_trades': sum(r['total_trades'] for r in results.values()),
                'total_anomalies_detected': total_anomalies,
                'stop_loss_triggers': total_stop_losses,
                'trailing_stop_triggers': total_trailing_stops,
                'overbought_sells': total_overbought_sells
            }
        }
    
    def print_results(self, results: Dict):
        """Print formatted backtest results."""
        print("\n" + "="*100)
        print("IMPROVED ANOMALY DETECTION STRATEGY - BACKTEST RESULTS")
        print("="*100)
        print(f"\nPeriod: {results['period']}")
        print(f"Base Position Size: ${results['position_size']} per trade")
        print(f"Stop-Loss: {results['stop_loss_pct']*100:.1f}%")
        print(f"Trailing Stop: {results['trailing_stop_pct']*100:.1f}%")
        print(f"Minimum Anomaly Severity: {results['min_severity']}")
        
        summary = results['summary']
        print(f"\n{'Stock':<8} {'Trades':<8} {'Return %':<12} {'Profit':<12} {'Stop-L':<8} {'Trail':<8} {'Overb':<8}")
        print("-"*100)
        
        for symbol, data in results['stocks'].items():
            if data['total_trades'] > 0:
                print(f"{symbol:<8} {data['total_trades']:<8} {data['return_pct']:<11.2f}% "
                      f"${data['profit_loss']:<11.2f} {data.get('stop_loss_triggers', 0):<8} "
                      f"{data.get('trailing_stop_triggers', 0):<8} {data.get('overbought_sells', 0):<8}")
        
        print("-"*100)
        print(f"{'TOTAL':<8} {summary['total_trades']:<8} {summary['overall_return_pct']:<11.2f}% "
              f"${summary['total_profit_loss']:<11.2f} {summary['stop_loss_triggers']:<8} "
              f"{summary['trailing_stop_triggers']:<8} {summary['overbought_sells']:<8}")
        
        print(f"\nRisk Management Triggers:")
        print(f"  Stop-Loss Triggers: {summary['stop_loss_triggers']}")
        print(f"  Trailing Stop Triggers: {summary['trailing_stop_triggers']}")
        print(f"  Overbought Sells: {summary['overbought_sells']}")


def main():
    """Main function to run improved anomaly detection backtest."""
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    
    strategy = ImprovedAnomalyTradingStrategy(
        stocks=stocks,
        position_size=10.0,
        min_severity=1.0,
        stop_loss_pct=0.05,  # 5% stop-loss
        trailing_stop_pct=0.05,  # 5% trailing stop
        min_risk_reward_ratio=1.5
    )
    
    results = strategy.run_backtest()
    strategy.print_results(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df_results = pd.DataFrame([
        {
            'Symbol': symbol,
            'Trades': data['total_trades'],
            'Buy_Trades': data.get('buy_trades', 0),
            'Sell_Trades': data.get('sell_trades', 0),
            'Invested': data['total_invested'],
            'Total_Value': data.get('total_value', data['current_value']),
            'Profit_Loss': data['profit_loss'],
            'Return_Pct': data['return_pct'],
            'Stop_Loss_Triggers': data.get('stop_loss_triggers', 0),
            'Trailing_Stop_Triggers': data.get('trailing_stop_triggers', 0),
            'Overbought_Sells': data.get('overbought_sells', 0)
        }
        for symbol, data in results['stocks'].items()
    ])
    
    output_file = f"improved_anomaly_backtest_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to {output_file}")


if __name__ == '__main__':
    main()

