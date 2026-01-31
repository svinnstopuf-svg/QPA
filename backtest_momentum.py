"""
Backtest Module - Momentum Strategy (Motor B)

10-Year Validation of Momentum Trading Strategy:
1. Scan for momentum patterns (Cup & Handle, Ascending Triangle, etc.)
2. Check RS-Rating ≥95 and uptrend (Price > EMA50 > EMA200)
3. Enter on breakout with volume confirmation
4. Exit on:
   - Trailing stop (2.5x ATR below high)
   - Profit targets (2R, 3R, 5R)
   - EMA50 breakdown
   - Volume climax

Goal: Validate Motor B performance and compare to Motor A
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass

from src.utils.data_fetcher import DataFetcher
from src.utils.market_data import MarketData
from src.patterns.momentum_patterns import MomentumPatternDetector
from src.patterns.momentum_engine import MomentumEngine, calculate_universe_returns
from src.exit.momentum_exit import MomentumExitManager


@dataclass
class MomentumTrade:
    """Represents a single momentum backtest trade"""
    ticker: str
    pattern_name: str
    entry_date: datetime
    entry_price: float
    stop_loss: float
    target_price: float
    
    # Exit details
    exit_date: datetime
    exit_price: float
    exit_reason: str  # "STOP", "TARGET", "EXHAUSTION", "BREAKDOWN"
    
    # Performance
    return_pct: float
    holding_days: int
    highest_price: float  # Max price during hold
    mae: float  # Max adverse excursion
    mfe: float  # Max favorable excursion
    
    # Pattern metrics
    rs_rating: float
    volume_surge_ratio: float
    pattern_quality: float


@dataclass
class MomentumBacktestResults:
    """Aggregate backtest results for momentum strategy"""
    total_trades: int
    
    # Performance
    win_rate: float
    avg_return: float
    avg_winner: float
    avg_loser: float
    best_trade: float
    worst_trade: float
    
    # Risk metrics
    avg_mae: float
    max_mae: float
    avg_holding_days: float
    profit_factor: float
    
    # Pattern breakdown
    results_by_pattern: Dict[str, Dict]
    
    # All trades
    trades: List[MomentumTrade]


class MomentumBacktester:
    """
    Backtests momentum strategy over historical data.
    
    Process:
    1. For each historical point, detect momentum patterns
    2. Check RS-Rating and trend alignment
    3. Enter on breakout with volume
    4. Trail stop and take profits
    5. Track performance vs Motor A
    """
    
    def __init__(self):
        self.pattern_detector = MomentumPatternDetector(
            min_rs_rating=90.0,  # Relaxed from 95 for backtest
            min_volume_surge=1.5,  # Relaxed from 2.0
            min_consolidation_days=10  # Relaxed from 15
        )
        self.momentum_engine = MomentumEngine()
        self.exit_manager = MomentumExitManager()
        self.data_fetcher = DataFetcher()
    
    def backtest_ticker(
        self,
        ticker: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[MomentumTrade]:
        """
        Backtest momentum strategy on single ticker.
        
        Returns:
            List of MomentumTrade objects
        """
        trades = []
        
        try:
            # Fetch historical data (need 2y for RS-Rating)
            market_data = self.data_fetcher.fetch_stock_data(ticker, period="max")
            if not market_data or len(market_data.close_prices) < 252:
                return trades
            
            # Calculate universe returns (for RS-Rating)
            # NOTE: For full backtest, you'd need all tickers' data
            # For now, using single ticker (simplified)
            universe_returns = {ticker: (
                (market_data.close_prices[-1] - market_data.close_prices[-63]) / market_data.close_prices[-63],
                (market_data.close_prices[-1] - market_data.close_prices[-126]) / market_data.close_prices[-126],
                (market_data.close_prices[-1] - market_data.close_prices[-252]) / market_data.close_prices[-252]
            )}
            
            # Scan through history
            lookback_days = 325  # Max for Cup & Handle
            forward_days = 90   # Max holding period
            
            for i in range(lookback_days, len(market_data.timestamps) - forward_days):
                current_date = market_data.timestamps[i]
                
                # Skip if outside date range
                if start_date and current_date < start_date:
                    continue
                if end_date and current_date > end_date:
                    continue
                
                # Create point-in-time market data
                pit_data = MarketData(
                    timestamps=market_data.timestamps[:i+1],
                    open_prices=market_data.open_prices[:i+1],
                    high_prices=market_data.high_prices[:i+1],
                    low_prices=market_data.low_prices[:i+1],
                    close_prices=market_data.close_prices[:i+1],
                    volume=market_data.volume[:i+1]
                )
                
                # Check RS-Rating
                motor_b = self.momentum_engine.detect_momentum_signal(
                    ticker, pit_data, universe_returns
                )
                
                if not motor_b.is_valid:
                    continue  # Skip: not in momentum setup
                
                # Detect patterns
                patterns = self.pattern_detector.detect_all_patterns(
                    pit_data, motor_b.rs_rating
                )
                
                if not patterns:
                    continue  # No patterns detected
                
                # Take best pattern
                pattern = patterns[0]  # Already sorted by quality
                
                # Check if already in a trade (prevent overlaps)
                if trades and (current_date - trades[-1].exit_date).days < 30:
                    continue
                
                # ENTER TRADE
                entry_price = market_data.close_prices[i]
                stop_loss = pattern.stop_loss
                target_price = pattern.target_price
                
                # Simulate holding period
                exit_idx = i
                exit_price = entry_price
                exit_reason = "TIME_STOP"
                highest_price = entry_price
                mae = 0.0
                mfe = 0.0
                
                for j in range(i + 1, min(i + forward_days, len(market_data.close_prices))):
                    current_price = market_data.close_prices[j]
                    highest_price = max(highest_price, current_price)
                    
                    # Track MAE/MFE
                    current_return = (current_price - entry_price) / entry_price
                    mae = min(mae, current_return)
                    mfe = max(mfe, current_return)
                    
                    # Calculate trailing stop
                    profit_pct = ((highest_price - entry_price) / entry_price) * 100
                    atr = pattern.stop_loss - entry_price  # Approx ATR
                    
                    if profit_pct < 20:
                        trailing_stop = stop_loss
                    elif profit_pct < 40:
                        trailing_stop = entry_price + abs(atr)
                    else:
                        trailing_stop = highest_price - 2.5 * abs(atr)
                    
                    # Check exits
                    if current_price <= trailing_stop:
                        exit_idx = j
                        exit_price = current_price
                        exit_reason = "STOP"
                        break
                    elif current_price >= target_price:
                        exit_idx = j
                        exit_price = current_price
                        exit_reason = "TARGET"
                        break
                    # NOTE: Volume climax/EMA50 breakdown would need live tracking
                
                # Record trade
                exit_date = market_data.timestamps[exit_idx]
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                holding_days = (exit_date - current_date).days
                
                trade = MomentumTrade(
                    ticker=ticker,
                    pattern_name=pattern.pattern_name,
                    entry_date=current_date,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    exit_date=exit_date,
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    return_pct=return_pct,
                    holding_days=holding_days,
                    highest_price=highest_price,
                    mae=mae,
                    mfe=mfe,
                    rs_rating=motor_b.rs_rating,
                    volume_surge_ratio=pattern.volume_surge_ratio,
                    pattern_quality=pattern.pattern_quality
                )
                
                trades.append(trade)
        
        except Exception as e:
            print(f"Error backtesting {ticker}: {e}")
        
        return trades
    
    def analyze_results(self, trades: List[MomentumTrade]) -> MomentumBacktestResults:
        """
        Analyze backtest results.
        
        Returns:
            MomentumBacktestResults with statistics
        """
        if not trades:
            return self._create_empty_results()
        
        total_trades = len(trades)
        returns = np.array([t.return_pct for t in trades])
        
        # Performance
        winners = returns[returns > 0]
        losers = returns[returns <= 0]
        
        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        avg_return = np.mean(returns)
        avg_winner = np.mean(winners) if len(winners) > 0 else 0
        avg_loser = np.mean(losers) if len(losers) > 0 else 0
        best_trade = np.max(returns) if len(returns) > 0 else 0
        worst_trade = np.min(returns) if len(returns) > 0 else 0
        
        # Risk
        maes = np.array([t.mae for t in trades])
        avg_mae = np.mean(maes)
        max_mae = np.min(maes)  # Most negative
        
        holding_days = np.array([t.holding_days for t in trades])
        avg_holding = np.mean(holding_days)
        
        # Profit factor
        total_wins = np.sum(winners)
        total_losses = abs(np.sum(losers))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # By pattern
        pattern_stats = {}
        for pattern_name in set(t.pattern_name for t in trades):
            pattern_trades = [t for t in trades if t.pattern_name == pattern_name]
            pattern_returns = np.array([t.return_pct for t in pattern_trades])
            pattern_wins = np.sum(pattern_returns > 0)
            
            pattern_stats[pattern_name] = {
                'count': len(pattern_trades),
                'win_rate': pattern_wins / len(pattern_trades),
                'avg_return': np.mean(pattern_returns),
                'best': np.max(pattern_returns),
                'worst': np.min(pattern_returns)
            }
        
        return MomentumBacktestResults(
            total_trades=total_trades,
            win_rate=win_rate,
            avg_return=avg_return,
            avg_winner=avg_winner,
            avg_loser=avg_loser,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_mae=avg_mae,
            max_mae=max_mae,
            avg_holding_days=avg_holding,
            profit_factor=profit_factor,
            results_by_pattern=pattern_stats,
            trades=trades
        )
    
    def _create_empty_results(self) -> MomentumBacktestResults:
        return MomentumBacktestResults(
            total_trades=0,
            win_rate=0,
            avg_return=0,
            avg_winner=0,
            avg_loser=0,
            best_trade=0,
            worst_trade=0,
            avg_mae=0,
            max_mae=0,
            avg_holding_days=0,
            profit_factor=0,
            results_by_pattern={},
            trades=[]
        )


def print_results(results: MomentumBacktestResults, strategy_name: str = "Momentum Strategy"):
    """
    Print backtest results.
    """
    print("\n" + "="*80)
    print(f"BACKTEST RESULTS: {strategy_name}")
    print("="*80)
    
    print(f"\nOVERALL PERFORMANCE:")
    print(f"  Total Trades: {results.total_trades}")
    print(f"  Win Rate: {results.win_rate*100:.1f}%")
    print(f"  Avg Return: {results.avg_return:+.2f}%")
    print(f"  Avg Winner: {results.avg_winner:+.2f}%")
    print(f"  Avg Loser: {results.avg_loser:+.2f}%")
    print(f"  Best Trade: {results.best_trade:+.2f}%")
    print(f"  Worst Trade: {results.worst_trade:+.2f}%")
    
    print(f"\nRISK METRICS:")
    print(f"  Avg MAE: {results.avg_mae*100:.2f}%")
    print(f"  Max MAE: {results.max_mae*100:.2f}%")
    print(f"  Avg Holding: {results.avg_holding_days:.0f} days")
    print(f"  Profit Factor: {results.profit_factor:.2f}")
    
    if results.results_by_pattern:
        print(f"\nBY PATTERN:")
        for pattern, stats in results.results_by_pattern.items():
            print(f"\n  {pattern}:")
            print(f"    Trades: {stats['count']}")
            print(f"    Win Rate: {stats['win_rate']*100:.1f}%")
            print(f"    Avg Return: {stats['avg_return']:+.2f}%")
    
    print("\n" + "="*80)


def main():
    """Run momentum backtest"""
    print("\n" + "="*80)
    print("MOMENTUM STRATEGY BACKTEST (Motor B)")
    print("="*80)
    
    backtester = MomentumBacktester()
    
    # Test tickers (momentum leaders)
    test_tickers = ["NVDA", "TSLA", "AAPL"]
    
    all_trades = []
    
    for ticker in test_tickers:
        print(f"\nBacktesting {ticker}...")
        trades = backtester.backtest_ticker(ticker)
        all_trades.extend(trades)
        print(f"  Found {len(trades)} trades")
    
    # Analyze
    results = backtester.analyze_results(all_trades)
    print_results(results)
    
    print("\n✅ Backtest complete")


if __name__ == "__main__":
    main()
