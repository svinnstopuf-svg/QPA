"""
Backtest Module - Phase 5

10-Year Validation of Position Trading Strategy:
1. Scan for valid market context (Vattenpasset)
2. Find structural patterns (Double Bottom, IH&S, etc)
3. Simulate entries on breakout
4. Measure 21/42/63-day returns
5. Track MAE (Max Adverse Excursion)
6. Calculate Profit Factor, Win Rate, etc.

Goal: Validate that bottom-fishing with V4.0 filters actually works.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass

from src.utils.data_fetcher import DataFetcher
from src.utils.market_data import MarketData
from src.filters.market_context_filter import MarketContextFilter
from src.patterns.position_trading_patterns import PositionTradingPatternDetector
import backtest_config as cfg


@dataclass
class Trade:
    """Represents a single backtest trade."""
    ticker: str
    pattern_name: str
    entry_date: datetime
    entry_price: float
    
    # Exits at multiple timeframes
    exit_21d_date: datetime
    exit_21d_price: float
    return_21d: float
    
    exit_42d_date: datetime
    exit_42d_price: float
    return_42d: float
    
    exit_63d_date: datetime
    exit_63d_price: float
    return_63d: float
    
    # Risk metrics
    mae: float  # Max Adverse Excursion (worst drawdown during hold)
    mfe: float  # Max Favorable Excursion (best profit during hold)
    
    # Context
    decline_pct: float
    volume_confirmed: bool


@dataclass
class BacktestResults:
    """Aggregate backtest results."""
    total_trades: int
    
    # Performance by timeframe
    win_rate_21d: float
    avg_return_21d: float
    best_trade_21d: float
    worst_trade_21d: float
    
    win_rate_42d: float
    avg_return_42d: float
    best_trade_42d: float
    worst_trade_42d: float
    
    win_rate_63d: float
    avg_return_63d: float
    best_trade_63d: float
    worst_trade_63d: float
    
    # Risk metrics
    avg_mae: float
    max_mae: float
    avg_mfe: float
    
    # Profit Factor (total wins / total losses)
    profit_factor_21d: float
    profit_factor_42d: float
    profit_factor_63d: float
    
    # All trades
    trades: List[Trade]


class PositionTradingBacktester:
    """
    Backtests position trading strategy over historical data.
    
    Process:
    1. For each historical point, check if market context valid
    2. If valid, check for structural patterns
    3. If pattern detected, simulate entry
    4. Track returns at 21/42/63 days
    5. Calculate MAE during holding period
    
    Note: For backtesting, we relax volume confirmation to get more data points.
    """
    
    def __init__(self):
        """
        Initialize with BACKTEST MODE configuration (relaxed filters).
        """
        # Use backtest config for relaxed thresholds
        self.context_filter = MarketContextFilter(
            min_decline_pct=cfg.BACKTEST_MIN_DECLINE_PCT,  # -10% instead of -15%
            lookback_high=cfg.BACKTEST_LOOKBACK_HIGH,
            ema_period=cfg.BACKTEST_EMA_PERIOD
        )
        self.pattern_detector = PositionTradingPatternDetector(
            min_decline_pct=cfg.BACKTEST_MIN_DECLINE_FOR_PATTERN  # -10%
        )
    
    def calculate_mae_mfe(
        self,
        prices: np.ndarray,
        entry_idx: int,
        exit_idx: int,
        entry_price: float
    ) -> Tuple[float, float]:
        """
        Calculate MAE (worst drawdown) and MFE (best profit) during hold.
        
        Returns:
            (mae, mfe) as percentages
        """
        if exit_idx >= len(prices):
            exit_idx = len(prices) - 1
        
        hold_prices = prices[entry_idx:exit_idx+1]
        
        # Calculate returns during hold period
        returns = (hold_prices - entry_price) / entry_price
        
        mae = np.min(returns)  # Most negative (worst drawdown)
        mfe = np.max(returns)  # Most positive (best profit)
        
        return mae, mfe
    
    def backtest_ticker(
        self,
        ticker: str,
        market_data: MarketData,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[Trade]:
        """
        Backtest position trading strategy on single ticker.
        
        Returns:
            List of Trade objects
        """
        trades = []
        
        # Set date range
        if start_date is None:
            start_date = market_data.timestamps[0]
        if end_date is None:
            end_date = market_data.timestamps[-1]
        
        # We need at least 90 days of history for context filter
        # and 63 days forward for exit
        lookback_days = 90
        forward_days = 63
        
        # Scan through history
        for i in range(lookback_days, len(market_data.timestamps) - forward_days):
            current_date = market_data.timestamps[i]
            
            # Skip if outside date range
            if current_date < start_date or current_date > end_date:
                continue
            
            # Create point-in-time market data (up to current date)
            pit_data = MarketData(
                timestamps=market_data.timestamps[:i+1],
                open_prices=market_data.open_prices[:i+1],
                high_prices=market_data.high_prices[:i+1],
                low_prices=market_data.low_prices[:i+1],
                close_prices=market_data.close_prices[:i+1],
                volume=market_data.volume[:i+1]
            )
            
            # Check market context
            context = self.context_filter.check_market_context(pit_data)
            
            if not context.is_valid_for_entry:
                continue  # Skip: market context not valid
            
            # Detect patterns
            patterns = self.pattern_detector.detect_all_position_patterns(pit_data)
            
            if len(patterns) == 0:
                continue  # Skip: no patterns detected
            
            # For each detected pattern, create trade
            for pattern_name, situation in patterns.items():
                # Get entry (last index in situation)
                if len(situation.timestamp_indices) == 0:
                    continue
                
                entry_idx = situation.timestamp_indices[-1]
                
                # Skip if entry is not at current date
                if entry_idx != i:
                    continue
                
                entry_price = market_data.close_prices[entry_idx]
                entry_date = market_data.timestamps[entry_idx]
                
                # Calculate exit points
                exit_21d_idx = min(entry_idx + 21, len(market_data.close_prices) - 1)
                exit_42d_idx = min(entry_idx + 42, len(market_data.close_prices) - 1)
                exit_63d_idx = min(entry_idx + 63, len(market_data.close_prices) - 1)
                
                exit_21d_price = market_data.close_prices[exit_21d_idx]
                exit_42d_price = market_data.close_prices[exit_42d_idx]
                exit_63d_price = market_data.close_prices[exit_63d_idx]
                
                return_21d = (exit_21d_price - entry_price) / entry_price
                return_42d = (exit_42d_price - entry_price) / entry_price
                return_63d = (exit_63d_price - entry_price) / entry_price
                
                # Calculate MAE/MFE for full 63-day hold
                mae, mfe = self.calculate_mae_mfe(
                    market_data.close_prices,
                    entry_idx,
                    exit_63d_idx,
                    entry_price
                )
                
                # Extract metadata
                decline_pct = situation.metadata.get('decline_pct', 0.0)
                volume_declining = situation.metadata.get('volume_declining', False)
                
                # Create trade
                trade = Trade(
                    ticker=ticker,
                    pattern_name=situation.description,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_21d_date=market_data.timestamps[exit_21d_idx],
                    exit_21d_price=exit_21d_price,
                    return_21d=return_21d,
                    exit_42d_date=market_data.timestamps[exit_42d_idx],
                    exit_42d_price=exit_42d_price,
                    return_42d=return_42d,
                    exit_63d_date=market_data.timestamps[exit_63d_idx],
                    exit_63d_price=exit_63d_price,
                    return_63d=return_63d,
                    mae=mae,
                    mfe=mfe,
                    decline_pct=decline_pct,
                    volume_confirmed=volume_declining
                )
                
                trades.append(trade)
        
        return trades
    
    def calculate_results(self, trades: List[Trade]) -> BacktestResults:
        """Calculate aggregate statistics from trades."""
        if len(trades) == 0:
            return BacktestResults(
                total_trades=0,
                win_rate_21d=0.0, avg_return_21d=0.0, best_trade_21d=0.0, worst_trade_21d=0.0,
                win_rate_42d=0.0, avg_return_42d=0.0, best_trade_42d=0.0, worst_trade_42d=0.0,
                win_rate_63d=0.0, avg_return_63d=0.0, best_trade_63d=0.0, worst_trade_63d=0.0,
                avg_mae=0.0, max_mae=0.0, avg_mfe=0.0,
                profit_factor_21d=0.0, profit_factor_42d=0.0, profit_factor_63d=0.0,
                trades=[]
            )
        
        # 21-day stats
        returns_21d = [t.return_21d for t in trades]
        wins_21d = [r for r in returns_21d if r > 0]
        losses_21d = [r for r in returns_21d if r < 0]
        win_rate_21d = len(wins_21d) / len(returns_21d) if returns_21d else 0.0
        avg_return_21d = np.mean(returns_21d)
        best_21d = max(returns_21d)
        worst_21d = min(returns_21d)
        pf_21d = sum(wins_21d) / abs(sum(losses_21d)) if losses_21d else float('inf')
        
        # 42-day stats
        returns_42d = [t.return_42d for t in trades]
        wins_42d = [r for r in returns_42d if r > 0]
        losses_42d = [r for r in returns_42d if r < 0]
        win_rate_42d = len(wins_42d) / len(returns_42d) if returns_42d else 0.0
        avg_return_42d = np.mean(returns_42d)
        best_42d = max(returns_42d)
        worst_42d = min(returns_42d)
        pf_42d = sum(wins_42d) / abs(sum(losses_42d)) if losses_42d else float('inf')
        
        # 63-day stats
        returns_63d = [t.return_63d for t in trades]
        wins_63d = [r for r in returns_63d if r > 0]
        losses_63d = [r for r in returns_63d if r < 0]
        win_rate_63d = len(wins_63d) / len(returns_63d) if returns_63d else 0.0
        avg_return_63d = np.mean(returns_63d)
        best_63d = max(returns_63d)
        worst_63d = min(returns_63d)
        pf_63d = sum(wins_63d) / abs(sum(losses_63d)) if losses_63d else float('inf')
        
        # MAE/MFE
        maes = [t.mae for t in trades]
        mfes = [t.mfe for t in trades]
        avg_mae = np.mean(maes)
        max_mae = min(maes)  # Most negative
        avg_mfe = np.mean(mfes)
        
        return BacktestResults(
            total_trades=len(trades),
            win_rate_21d=win_rate_21d,
            avg_return_21d=avg_return_21d,
            best_trade_21d=best_21d,
            worst_trade_21d=worst_21d,
            win_rate_42d=win_rate_42d,
            avg_return_42d=avg_return_42d,
            best_trade_42d=best_42d,
            worst_trade_42d=worst_42d,
            win_rate_63d=win_rate_63d,
            avg_return_63d=avg_return_63d,
            best_trade_63d=best_63d,
            worst_trade_63d=worst_63d,
            avg_mae=avg_mae,
            max_mae=max_mae,
            avg_mfe=avg_mfe,
            profit_factor_21d=pf_21d,
            profit_factor_42d=pf_42d,
            profit_factor_63d=pf_63d,
            trades=trades
        )


def run_backtest(ticker: str, period: str = "10y"):
    """Run backtest on single ticker."""
    print("="*80)
    print(f"POSITION TRADING BACKTEST: {ticker}")
    print("="*80)
    
    # Fetch data
    print(f"\nFetching {period} of data...")
    fetcher = DataFetcher()
    market_data = fetcher.fetch_stock_data(ticker, period=period)
    
    if market_data is None:
        print("ERROR: Could not fetch data")
        return
    
    # Run backtest
    print(f"\nRunning backtest...")
    print("  - Scanning for valid market context (Vattenpasset)")
    print("  - Detecting structural patterns (Double Bottom, IH&S, etc)")
    print("  - Simulating entries on breakout")
    print("  - Measuring 21/42/63-day returns\n")
    
    # Add debug: check if EVER had valid context
    print("DEBUG: Checking historical market context...")
    backtester = PositionTradingBacktester()
    
    valid_context_count = 0
    for i in range(90, len(market_data.timestamps) - 63):
        pit_data = MarketData(
            timestamps=market_data.timestamps[:i+1],
            open_prices=market_data.open_prices[:i+1],
            high_prices=market_data.high_prices[:i+1],
            low_prices=market_data.low_prices[:i+1],
            close_prices=market_data.close_prices[:i+1],
            volume=market_data.volume[:i+1]
        )
        context = backtester.context_filter.check_market_context(pit_data)
        if context.is_valid_for_entry:
            valid_context_count += 1
    
    print(f"  Valid context days: {valid_context_count} / {len(market_data.timestamps) - 153}")
    print(f"  ({valid_context_count / (len(market_data.timestamps) - 153) * 100:.1f}% of testable days)\n")
    
    trades = backtester.backtest_ticker(ticker, market_data)
    results = backtester.calculate_results(trades)
    
    # Display results
    print("-"*80)
    print("BACKTEST RESULTS")
    print("-"*80)
    
    print(f"\nTotal Trades: {results.total_trades}")
    
    if results.total_trades == 0:
        print("\n❌ No valid setups found in historical data")
        print("\nPossible reasons:")
        print("  - Instrument never had -15% decline + below EMA200")
        print("  - No structural patterns (Double Bottom, IH&S) formed")
        print("  - Volume confirmation failed")
        return
    
    # 21-day performance
    print(f"\n{'─'*80}")
    print("21-DAY PERFORMANCE (1 month hold)")
    print('─'*80)
    print(f"Win Rate: {results.win_rate_21d*100:.1f}%")
    print(f"Average Return: {results.avg_return_21d*100:+.2f}%")
    print(f"Best Trade: {results.best_trade_21d*100:+.2f}%")
    print(f"Worst Trade: {results.worst_trade_21d*100:.2f}%")
    print(f"Profit Factor: {results.profit_factor_21d:.2f}")
    
    # 42-day performance
    print(f"\n{'─'*80}")
    print("42-DAY PERFORMANCE (2 month hold)")
    print('─'*80)
    print(f"Win Rate: {results.win_rate_42d*100:.1f}%")
    print(f"Average Return: {results.avg_return_42d*100:+.2f}%")
    print(f"Best Trade: {results.best_trade_42d*100:+.2f}%")
    print(f"Worst Trade: {results.worst_trade_42d*100:.2f}%")
    print(f"Profit Factor: {results.profit_factor_42d:.2f}")
    
    # 63-day performance
    print(f"\n{'─'*80}")
    print("63-DAY PERFORMANCE (3 month hold)")
    print('─'*80)
    print(f"Win Rate: {results.win_rate_63d*100:.1f}%")
    print(f"Average Return: {results.avg_return_63d*100:+.2f}%")
    print(f"Best Trade: {results.best_trade_63d*100:+.2f}%")
    print(f"Worst Trade: {results.worst_trade_63d*100:.2f}%")
    print(f"Profit Factor: {results.profit_factor_63d:.2f}")
    
    # Risk metrics
    print(f"\n{'─'*80}")
    print("RISK METRICS (MAE = Max Adverse Excursion)")
    print('─'*80)
    print(f"Average MAE (drawdown): {results.avg_mae*100:.2f}%")
    print(f"Worst MAE: {results.max_mae*100:.2f}%")
    print(f"Average MFE (peak profit): {results.avg_mfe*100:.2f}%")
    
    # Success assessment
    print(f"\n{'─'*80}")
    print("VALIDATION ASSESSMENT")
    print('─'*80)
    
    criteria_met = 0
    criteria_total = 2
    
    print(f"\nTarget Criteria:")
    if results.win_rate_63d >= 0.60:
        print(f"  ✅ Win Rate > 60% at 63 days: {results.win_rate_63d*100:.1f}%")
        criteria_met += 1
    else:
        print(f"  ❌ Win Rate > 60% at 63 days: {results.win_rate_63d*100:.1f}%")
    
    if results.profit_factor_63d >= 2.0:
        print(f"  ✅ Profit Factor > 2.0: {results.profit_factor_63d:.2f}")
        criteria_met += 1
    else:
        print(f"  ❌ Profit Factor > 2.0: {results.profit_factor_63d:.2f}")
    
    print(f"\nCriteria Met: {criteria_met}/{criteria_total}")
    
    if criteria_met == criteria_total:
        print("\n🎯 STRATEGY VALIDATED - Meets all success criteria")
    elif criteria_met >= 1:
        print("\n⚠️ PARTIAL VALIDATION - Meets some criteria")
    else:
        print("\n❌ STRATEGY FAILED - Does not meet criteria")
    
    # Sample trades
    print(f"\n{'─'*80}")
    print("SAMPLE TRADES (First 5)")
    print('─'*80)
    
    for i, trade in enumerate(results.trades[:5], 1):
        print(f"\n{i}. {trade.pattern_name}")
        print(f"   Entry: {trade.entry_date.date()} @ {trade.entry_price:.2f}")
        print(f"   Decline: {trade.decline_pct:.1f}%")
        print(f"   Returns: 21d={trade.return_21d*100:+.1f}% | 42d={trade.return_42d*100:+.1f}% | 63d={trade.return_63d*100:+.1f}%")
        print(f"   MAE: {trade.mae*100:.2f}% | MFE: {trade.mfe*100:+.2f}%")
    
    print("\n" + "="*80)


def run_multi_ticker_backtest():
    """Run backtest on multiple tickers and show summary."""
    print("="*80)
    print("POSITION TRADING BACKTEST - MULTI-TICKER VALIDATION")
    print("Mode: RESEARCH (Relaxed Filters)")
    print("="*80)
    print(f"\nTickers: {', '.join(cfg.BACKTEST_TICKERS)}")
    print(f"Decline Threshold: -{cfg.BACKTEST_MIN_DECLINE_PCT}% (vs -15% live)")
    print(f"Pattern Tolerance: {cfg.BACKTEST_PATTERN_TOLERANCE*100:.0f}% (vs 2% live)")
    print(f"Volume Required: {'Yes' if cfg.BACKTEST_VOLUME_REQUIRED else 'No'}")
    print(f"\nGoal: Validate core 'bottom-fishing' strategy\n")
    
    all_results = {}
    
    for ticker in cfg.BACKTEST_TICKERS:
        print(f"\n{'─'*80}")
        print(f"Processing: {ticker}")
        print('─'*80)
        
        # Fetch data
        fetcher = DataFetcher()
        market_data = fetcher.fetch_stock_data(ticker, period="5y")
        
        if market_data is None:
            print(f"❌ Could not fetch data for {ticker}")
            continue
        
        # Run backtest
        backtester = PositionTradingBacktester()
        trades = backtester.backtest_ticker(ticker, market_data)
        results = backtester.calculate_results(trades)
        
        all_results[ticker] = results
        
        # Quick summary
        print(f"  Trades: {results.total_trades}")
        if results.total_trades > 0:
            print(f"  Win Rate (63d): {results.win_rate_63d*100:.1f}%")
            print(f"  Avg Return (63d): {results.avg_return_63d*100:+.2f}%")
            print(f"  Profit Factor (63d): {results.profit_factor_63d:.2f}")
    
    # AGGREGATE SUMMARY
    print("\n" + "="*80)
    print("AGGREGATE SUMMARY")
    print("="*80)
    
    summary_data = []
    for ticker, results in all_results.items():
        if results.total_trades > 0:
            summary_data.append({
                'ticker': ticker,
                'trades': results.total_trades,
                'win_rate_63d': results.win_rate_63d,
                'avg_return_63d': results.avg_return_63d,
                'profit_factor_63d': results.profit_factor_63d,
                'max_mae': results.max_mae
            })
    
    if len(summary_data) == 0:
        print("\n❌ No valid trades found across all tickers")
        print("\nConsider:")
        print("  - Lowering decline threshold further (< -10%)")
        print("  - Testing during market correction periods")
        print("  - Adding more volatile instruments")
        return
    
    print(f"\n{'Ticker':<15} {'Trades':<10} {'Win Rate':<12} {'Avg Return':<15} {'Profit Factor':<15} {'Max DD':<10}")
    print("─"*80)
    
    total_trades = 0
    total_wins_63d = 0
    all_returns_63d = []
    
    for data in summary_data:
        print(f"{data['ticker']:<15} {data['trades']:<10} {data['win_rate_63d']*100:>10.1f}% {data['avg_return_63d']*100:>13.2f}% {data['profit_factor_63d']:>14.2f} {data['max_mae']*100:>9.2f}%")
        
        total_trades += data['trades']
        # Collect all trades for aggregate stats
        result_obj = all_results[data['ticker']]
        for trade in result_obj.trades:
            all_returns_63d.append(trade.return_63d)
            if trade.return_63d > 0:
                total_wins_63d += 1
    
    # Calculate aggregate metrics
    if total_trades > 0:
        agg_win_rate = total_wins_63d / total_trades
        agg_avg_return = np.mean(all_returns_63d)
        wins = [r for r in all_returns_63d if r > 0]
        losses = [r for r in all_returns_63d if r < 0]
        agg_pf = sum(wins) / abs(sum(losses)) if losses else float('inf')
        agg_max_dd = min(all_returns_63d)
        
        print("─"*80)
        print(f"{'TOTAL':<15} {total_trades:<10} {agg_win_rate*100:>10.1f}% {agg_avg_return*100:>13.2f}% {agg_pf:>14.2f} {agg_max_dd*100:>9.2f}%")
        
        # Validation
        print(f"\n{'='*80}")
        print("STRATEGY VALIDATION")
        print('='*80)
        print(f"\nTotal Trades: {total_trades}")
        print(f"Aggregate Win Rate (63d): {agg_win_rate*100:.1f}%")
        print(f"Aggregate Avg Return (63d): {agg_avg_return*100:+.2f}%")
        print(f"Aggregate Profit Factor: {agg_pf:.2f}")
        print(f"Worst Drawdown: {agg_max_dd*100:.2f}%")
        
        print(f"\nCriteria Assessment:")
        if agg_win_rate >= 0.60:
            print(f"  ✅ Win Rate > 60%: {agg_win_rate*100:.1f}%")
        else:
            print(f"  ❌ Win Rate > 60%: {agg_win_rate*100:.1f}%")
        
        if agg_pf >= 2.0:
            print(f"  ✅ Profit Factor > 2.0: {agg_pf:.2f}")
        else:
            print(f"  ❌ Profit Factor > 2.0: {agg_pf:.2f}")
        
        if agg_win_rate >= 0.60 and agg_pf >= 2.0:
            print(f"\n🎯 STRATEGY VALIDATED - Bottom-fishing works!")
        else:
            print(f"\n⚠️ PARTIAL VALIDATION - Strategy shows promise but needs refinement")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    run_multi_ticker_backtest()
