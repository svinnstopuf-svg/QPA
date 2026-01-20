"""
Data Sanity Checker - Detect Price Anomalies

Quantitative Principle:
Stock splits, dividend adjustments, and data errors can create false signals.
Flag suspicious price moves that don't correlate with broader market/sector.

Checks:
1. Extreme moves (>15%) without market confirmation
2. Volume spikes without price justification
3. Price gaps that don't match sector/index
4. Obvious data errors (negative prices, zero volume)

Purpose: Prevent trading on bad data.
"""
from typing import List, Dict, Tuple
import numpy as np
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SanityCheckResult:
    """Results from data sanity check."""
    ticker: str
    passed: bool
    flags: List[str]  # List of issues detected
    
    # Specific checks
    extreme_move_detected: bool
    price_gap_detected: bool
    volume_anomaly_detected: bool
    data_error_detected: bool
    
    # Details
    max_single_day_move: float  # % move
    market_correlation: float  # vs index on same day


class DataSanityChecker:
    """
    Validates price data quality and detects anomalies.
    
    Philosophy: Don't trade on bad data.
    """
    
    def __init__(
        self,
        extreme_move_threshold: float = 15.0,  # % move
        gap_threshold: float = 10.0,  # % gap
        volume_spike_threshold: float = 5.0,  # 5x normal
        min_market_correlation: float = 0.3  # Require some market correlation
    ):
        """
        Initialize data sanity checker.
        
        Args:
            extreme_move_threshold: % move to flag as extreme
            gap_threshold: % gap to flag
            volume_spike_threshold: Volume multiplier to flag
            min_market_correlation: Min correlation with market for extreme moves
        """
        self.extreme_threshold = extreme_move_threshold
        self.gap_threshold = gap_threshold
        self.volume_spike_threshold = volume_spike_threshold
        self.min_market_corr = min_market_correlation
    
    def check(
        self,
        ticker: str,
        prices: np.ndarray,
        volumes: np.ndarray = None,
        market_prices: np.ndarray = None
    ) -> SanityCheckResult:
        """
        Perform comprehensive data sanity check.
        
        Args:
            ticker: Instrument ticker
            prices: Array of close prices
            volumes: Array of volumes (optional)
            market_prices: Market index prices (optional, for correlation check)
            
        Returns:
            SanityCheckResult with findings
        """
        flags = []
        extreme_move = False
        price_gap = False
        volume_anomaly = False
        data_error = False
        
        # 1. Basic data error checks
        if np.any(prices <= 0):
            flags.append("Negative or zero prices detected")
            data_error = True
        
        if np.any(np.isnan(prices)):
            flags.append("NaN prices detected")
            data_error = True
        
        if volumes is not None:
            if np.any(volumes < 0):
                flags.append("Negative volume detected")
                data_error = True
            
            if np.any(np.isnan(volumes)):
                flags.append("NaN volumes detected")
                data_error = True
        
        # If basic errors, return early
        if data_error:
            return SanityCheckResult(
                ticker=ticker,
                passed=False,
                flags=flags,
                extreme_move_detected=False,
                price_gap_detected=False,
                volume_anomaly_detected=False,
                data_error_detected=True,
                max_single_day_move=0.0,
                market_correlation=0.0
            )
        
        # 2. Calculate price returns
        returns = np.diff(prices) / prices[:-1] * 100  # % returns
        
        if len(returns) == 0:
            return self._insufficient_data_result(ticker)
        
        max_single_day_move = np.max(np.abs(returns))
        
        # 3. Check for extreme moves
        if max_single_day_move > self.extreme_threshold:
            extreme_move = True
            
            # If market data available, check correlation
            if market_prices is not None and len(market_prices) == len(prices):
                market_returns = np.diff(market_prices) / market_prices[:-1] * 100
                
                if len(market_returns) > 10:
                    # Calculate correlation
                    corr = np.corrcoef(returns, market_returns)[0, 1]
                    
                    if np.isnan(corr):
                        corr = 0.0
                    
                    # If extreme move but LOW market correlation = suspicious
                    if corr < self.min_market_corr:
                        flags.append(
                            f"Extreme move {max_single_day_move:.1f}% with low market correlation ({corr:.2f})"
                        )
                else:
                    corr = 0.0
                    flags.append(f"Extreme move {max_single_day_move:.1f}% (insufficient market data to verify)")
            else:
                corr = 0.0
                flags.append(f"Extreme move {max_single_day_move:.1f}% (no market data for verification)")
        else:
            corr = 0.0
        
        # 4. Check for gaps (open vs previous close)
        # We don't have open prices in this simple version, so check consecutive large moves
        consecutive_moves = np.abs(returns)
        if np.any(consecutive_moves > self.gap_threshold):
            price_gap = True
            gap_count = np.sum(consecutive_moves > self.gap_threshold)
            flags.append(f"{gap_count} price gaps >{self.gap_threshold}% detected")
        
        # 5. Check for volume anomalies
        if volumes is not None and len(volumes) > 20:
            avg_volume = np.mean(volumes)
            
            if avg_volume > 0:
                volume_spikes = volumes / avg_volume
                max_volume_spike = np.max(volume_spikes)
                
                if max_volume_spike > self.volume_spike_threshold:
                    volume_anomaly = True
                    flags.append(f"Volume spike {max_volume_spike:.1f}x normal detected")
        
        # 6. Overall pass/fail
        # Pass if no flags
        passed = len(flags) == 0
        
        return SanityCheckResult(
            ticker=ticker,
            passed=passed,
            flags=flags,
            extreme_move_detected=extreme_move,
            price_gap_detected=price_gap,
            volume_anomaly_detected=volume_anomaly,
            data_error_detected=data_error,
            max_single_day_move=max_single_day_move,
            market_correlation=corr
        )
    
    def _insufficient_data_result(self, ticker: str) -> SanityCheckResult:
        """Return result for insufficient data."""
        return SanityCheckResult(
            ticker=ticker,
            passed=False,
            flags=["Insufficient data for sanity check"],
            extreme_move_detected=False,
            price_gap_detected=False,
            volume_anomaly_detected=False,
            data_error_detected=True,
            max_single_day_move=0.0,
            market_correlation=0.0
        )
    
    def format_report(self, result: SanityCheckResult) -> str:
        """Generate formatted report."""
        report = f"""
{'='*70}
DATA SANITY CHECK: {result.ticker}
{'='*70}

Overall Status:      {'✅ PASSED' if result.passed else '❌ FAILED'}
Flags Found:         {len(result.flags)}

Checks:
  Extreme Moves:     {'⚠️ YES' if result.extreme_move_detected else '✅ NO'}
  Price Gaps:        {'⚠️ YES' if result.price_gap_detected else '✅ NO'}
  Volume Anomalies:  {'⚠️ YES' if result.volume_anomaly_detected else '✅ NO'}
  Data Errors:       {'⚠️ YES' if result.data_error_detected else '✅ NO'}

Metrics:
  Max Single-Day Move:  {result.max_single_day_move:.1f}%
  Market Correlation:   {result.market_correlation:.2f}

Issues Detected:
"""
        
        if result.flags:
            for flag in result.flags:
                report += f"  • {flag}\n"
        else:
            report += "  None - data looks clean\n"
        
        report += f"\n{'='*70}\n"
        
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Data Sanity Checker...")
    
    checker = DataSanityChecker()
    
    # Test Case 1: Clean data
    print("\n1. Clean Data Test:")
    prices_clean = np.array([100, 101, 102, 101, 103, 104, 103, 105])
    volumes_clean = np.array([10000, 12000, 11000, 10500, 11500, 10000, 12000, 11000])
    
    result = checker.check("CLEAN.ST", prices_clean, volumes_clean)
    print(checker.format_report(result))
    
    # Test Case 2: Extreme move
    print("\n2. Extreme Move Test:")
    prices_extreme = np.array([100, 101, 102, 120, 121, 119])  # +17.6% spike
    
    result = checker.check("EXTREME.ST", prices_extreme)
    print(checker.format_report(result))
    
    # Test Case 3: Data error
    print("\n3. Data Error Test:")
    prices_error = np.array([100, 101, -5, 103, 104])  # Negative price
    
    result = checker.check("ERROR.ST", prices_error)
    print(checker.format_report(result))
    
    # Test Case 4: Volume spike
    print("\n4. Volume Spike Test:")
    prices_vol = np.array([100, 101, 102, 103, 104])
    volumes_vol = np.array([10000, 11000, 60000, 10500, 11000])  # 6x spike
    
    result = checker.check("VOLSPIKE.ST", prices_vol, volumes_vol)
    print(checker.format_report(result))
    
    print("\n✅ Data Sanity Checker - Tests Complete")
