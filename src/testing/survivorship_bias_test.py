"""
Survivorship Bias Test Framework

Tests whether strategy performance is inflated due to survivorship bias
by including delisted/bankrupt companies in backtest.

Survivorship bias occurs when:
- We only test on companies that survived until today
- We ignore companies that went bankrupt, delisted, or got acquired
- This artificially inflates win rates and returns

Example:
    If strategy shows 70% win rate on current universe,
    but 55% win rate when including delisted stocks,
    there's a 15% survivorship bias.

References:
- Brown, Goetzmann, Ross (1995): Survival bias in mutual funds
- Elton, Gruber, Blake (1996): Survivorship bias in mutual funds
"""

import yfinance as yf
import pandas as pd
from typing import List, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np


@dataclass
class SurvivorshipTestResult:
    """Results from survivorship bias test."""
    
    # Survivor universe (current stocks)
    survivor_tickers: List[str]
    survivor_win_rate: float
    survivor_avg_return: float
    survivor_sample_size: int
    
    # Full universe (survivors + delisted)
    full_tickers: List[str]
    full_win_rate: float
    full_avg_return: float
    full_sample_size: int
    
    # Delisted stocks
    delisted_tickers: List[str]
    delisted_win_rate: float
    delisted_avg_return: float
    delisted_sample_size: int
    
    # Bias metrics
    win_rate_bias: float  # Percentage points
    return_bias: float  # Percentage points
    bias_severity: str  # "Negligible", "Moderate", "Severe"
    
    def __str__(self) -> str:
        return f"""
SURVIVORSHIP BIAS TEST RESULTS
{'='*80}

SURVIVOR UNIVERSE (Current Stocks):
  Tickers: {len(self.survivor_tickers)}
  Win Rate: {self.survivor_win_rate:.1%}
  Avg Return: {self.survivor_avg_return:+.2%}
  Trades: {self.survivor_sample_size}

DELISTED UNIVERSE (Bankrupt/Acquired/Delisted):
  Tickers: {len(self.delisted_tickers)}
  Win Rate: {self.delisted_win_rate:.1%}
  Avg Return: {self.delisted_avg_return:+.2%}
  Trades: {self.delisted_sample_size}

FULL UNIVERSE (Survivors + Delisted):
  Tickers: {len(self.full_tickers)}
  Win Rate: {self.full_win_rate:.1%}
  Avg Return: {self.full_avg_return:+.2%}
  Trades: {self.full_sample_size}

SURVIVORSHIP BIAS:
  Win Rate Bias: {self.win_rate_bias:+.1f} pp
  Return Bias: {self.return_bias:+.2f} pp
  Severity: {self.bias_severity}

{'='*80}
"""


class SurvivorshipBiasTester:
    """
    Test for survivorship bias by comparing performance on:
    1. Survivor universe (current stocks)
    2. Full universe (survivors + delisted)
    """
    
    def __init__(self):
        """Initialize tester."""
        pass
    
    def get_delisted_swedish_stocks(self, cutoff_year: int = 2015) -> List[str]:
        """
        Get list of Swedish stocks that were delisted after cutoff_year.
        
        This is a MANUAL LIST for demonstration. In production, you would:
        1. Query financial database (Bloomberg, Refinitiv, etc.)
        2. Use exchange delisting data
        3. Scrape historical constituent lists
        
        Args:
            cutoff_year: Only include stocks delisted after this year
            
        Returns:
            List of delisted tickers
        """
        # Example delisted Swedish stocks (MANUAL - for demonstration)
        # Format: ticker, name, delisting_year, reason
        delisted_examples = [
            ("BURE.ST", "Bure Equity", 2020, "Delisted"),
            ("KARO.ST", "Karolinska Development", 2019, "Delisted"),
            ("KLED.ST", "Klovern", 2021, "Acquired by Corem"),
            # Add more from historical data
        ]
        
        # Filter by cutoff year
        tickers = [t[0] for t in delisted_examples if t[2] >= cutoff_year]
        
        return tickers
    
    def fetch_delisted_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch historical data for delisted stock.
        
        Args:
            ticker: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLCV data, or None if unavailable
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return None
            
            return hist
        except Exception as e:
            print(f"⚠️ Failed to fetch {ticker}: {e}")
            return None
    
    def run_backtest_on_universe(
        self,
        tickers: List[str],
        strategy_func,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Run backtest on a universe of tickers.
        
        Args:
            tickers: List of tickers to test
            strategy_func: Function that takes MarketData and returns signals
            start_date: Backtest start
            end_date: Backtest end
            
        Returns:
            Dict with aggregate stats
        """
        results = []
        
        for ticker in tickers:
            data = self.fetch_delisted_data(ticker, start_date, end_date)
            if data is None:
                continue
            
            # Run strategy
            signals = strategy_func(data)
            
            # Aggregate results
            for signal in signals:
                results.append(signal)
        
        if len(results) == 0:
            return {
                'win_rate': 0.0,
                'avg_return': 0.0,
                'sample_size': 0
            }
        
        # Calculate aggregate stats
        wins = sum(1 for r in results if r['return'] > 0)
        total = len(results)
        win_rate = wins / total if total > 0 else 0.0
        avg_return = np.mean([r['return'] for r in results])
        
        return {
            'win_rate': win_rate,
            'avg_return': avg_return,
            'sample_size': total
        }
    
    def test_survivorship_bias(
        self,
        survivor_tickers: List[str],
        delisted_tickers: List[str],
        strategy_func,
        start_date: str = "2015-01-01",
        end_date: str = "2024-12-31"
    ) -> SurvivorshipTestResult:
        """
        Test for survivorship bias.
        
        Args:
            survivor_tickers: Current stocks (survivor universe)
            delisted_tickers: Delisted stocks
            strategy_func: Strategy to test
            start_date: Backtest start
            end_date: Backtest end
            
        Returns:
            SurvivorshipTestResult
        """
        print("="*80)
        print("SURVIVORSHIP BIAS TEST")
        print("="*80)
        
        # Test on survivor universe
        print(f"\n1️⃣ Testing on SURVIVOR universe ({len(survivor_tickers)} tickers)...")
        survivor_stats = self.run_backtest_on_universe(
            survivor_tickers,
            strategy_func,
            start_date,
            end_date
        )
        
        # Test on delisted universe
        print(f"\n2️⃣ Testing on DELISTED universe ({len(delisted_tickers)} tickers)...")
        delisted_stats = self.run_backtest_on_universe(
            delisted_tickers,
            strategy_func,
            start_date,
            end_date
        )
        
        # Combine for full universe
        full_tickers = survivor_tickers + delisted_tickers
        full_sample_size = survivor_stats['sample_size'] + delisted_stats['sample_size']
        
        if full_sample_size > 0:
            # Weighted average
            full_win_rate = (
                survivor_stats['win_rate'] * survivor_stats['sample_size'] +
                delisted_stats['win_rate'] * delisted_stats['sample_size']
            ) / full_sample_size
            
            full_avg_return = (
                survivor_stats['avg_return'] * survivor_stats['sample_size'] +
                delisted_stats['avg_return'] * delisted_stats['sample_size']
            ) / full_sample_size
        else:
            full_win_rate = 0.0
            full_avg_return = 0.0
        
        # Calculate bias
        win_rate_bias = (survivor_stats['win_rate'] - full_win_rate) * 100  # In percentage points
        return_bias = (survivor_stats['avg_return'] - full_avg_return) * 100  # In percentage points
        
        # Classify severity
        if abs(win_rate_bias) < 2.0 and abs(return_bias) < 1.0:
            severity = "Negligible"
        elif abs(win_rate_bias) < 5.0 and abs(return_bias) < 3.0:
            severity = "Moderate"
        else:
            severity = "Severe"
        
        return SurvivorshipTestResult(
            survivor_tickers=survivor_tickers,
            survivor_win_rate=survivor_stats['win_rate'],
            survivor_avg_return=survivor_stats['avg_return'],
            survivor_sample_size=survivor_stats['sample_size'],
            full_tickers=full_tickers,
            full_win_rate=full_win_rate,
            full_avg_return=full_avg_return,
            full_sample_size=full_sample_size,
            delisted_tickers=delisted_tickers,
            delisted_win_rate=delisted_stats['win_rate'],
            delisted_avg_return=delisted_stats['avg_return'],
            delisted_sample_size=delisted_stats['sample_size'],
            win_rate_bias=win_rate_bias,
            return_bias=return_bias,
            bias_severity=severity
        )


def example_strategy(data: pd.DataFrame) -> List[Dict]:
    """
    Example strategy for testing.
    
    Simple rule: Buy when price crosses above 50-day MA.
    Hold for 21 days.
    """
    signals = []
    
    if len(data) < 50:
        return signals
    
    # Calculate 50-day MA
    data['MA50'] = data['Close'].rolling(50).mean()
    
    # Find crossovers
    for i in range(50, len(data) - 21):
        # Crossover: price was below MA, now above
        if data['Close'].iloc[i-1] < data['MA50'].iloc[i-1] and \
           data['Close'].iloc[i] > data['MA50'].iloc[i]:
            
            entry_price = data['Close'].iloc[i]
            exit_price = data['Close'].iloc[i + 21]
            ret = (exit_price - entry_price) / entry_price
            
            signals.append({
                'entry_date': data.index[i],
                'exit_date': data.index[i + 21],
                'return': ret
            })
    
    return signals


if __name__ == "__main__":
    # Example usage
    tester = SurvivorshipBiasTester()
    
    # Current stocks (survivor universe)
    survivor_tickers = [
        "VOLV-B.ST",  # Volvo
        "ERIC-B.ST",  # Ericsson
        "SEB-A.ST",   # SEB
        "SWED-A.ST",  # Swedbank
        "HM-B.ST"     # H&M
    ]
    
    # Delisted stocks (for demonstration)
    delisted_tickers = tester.get_delisted_swedish_stocks(cutoff_year=2015)
    
    if len(delisted_tickers) == 0:
        print("\n⚠️ No delisted tickers available for test.")
        print("\nTo run a proper survivorship bias test, you need:")
        print("1. A database of delisted stocks (Bloomberg, Refinitiv, etc.)")
        print("2. Historical price data for these delisted stocks")
        print("3. Metadata about delisting reason (bankruptcy, acquisition, etc.)")
        print("\nThis framework provides the structure - add your data sources!")
    else:
        # Run test
        result = tester.test_survivorship_bias(
            survivor_tickers,
            delisted_tickers,
            example_strategy,
            start_date="2015-01-01",
            end_date="2023-12-31"
        )
        
        print(result)
        
        # Interpretation
        if result.bias_severity == "Severe":
            print("\n🚨 SEVERE SURVIVORSHIP BIAS DETECTED!")
            print("   Strategy performance is likely overstated.")
            print("   Real-world results will be significantly worse.")
        elif result.bias_severity == "Moderate":
            print("\n⚠️ MODERATE SURVIVORSHIP BIAS DETECTED")
            print("   Strategy performance is somewhat inflated.")
            print("   Adjust expectations downward.")
        else:
            print("\n✅ NEGLIGIBLE SURVIVORSHIP BIAS")
            print("   Strategy appears robust to survivorship.")
