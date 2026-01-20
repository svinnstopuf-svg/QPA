"""
Out-of-Sample (OOS) Validation - Walk-Forward Testing

Quantitative Principle:
A strategy that works in-sample (on training data) might not work out-of-sample.
This is the #1 cause of strategy failure in production.

Methodology:
1. Split data into rolling windows: Train (60d) → Test (30d)
2. Calculate performance on both train and test
3. Track degradation: OOS_Performance / IS_Performance
4. Flag strategies where OOS << IS (overfitting)

Walk-Forward Example:
- Window 1: Train on days 1-60, test on days 61-90
- Window 2: Train on days 31-90, test on days 91-120
- Window 3: Train on days 61-120, test on days 121-150
- etc.

Degradation Thresholds:
- OOS/IS > 0.8: EXCELLENT (strategy generalizes well)
- OOS/IS 0.5-0.8: ACCEPTABLE (some degradation)
- OOS/IS < 0.5: WARNING (overfitting detected)
"""
from typing import List, Dict, Tuple
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class OOSWindow:
    """Single walk-forward window results."""
    window_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    
    # Performance
    is_return: float  # In-sample return (%)
    oos_return: float  # Out-of-sample return (%)
    degradation_ratio: float  # OOS / IS
    
    # Quality
    is_sharpe: float  # In-sample Sharpe
    oos_sharpe: float  # Out-of-sample Sharpe


@dataclass
class OOSValidation:
    """Complete OOS validation results."""
    ticker: str
    total_windows: int
    
    # Aggregated metrics
    avg_is_return: float
    avg_oos_return: float
    avg_degradation_ratio: float
    
    # Stability
    oos_consistency: float  # % of windows with positive OOS
    overfitting_detected: bool  # degradation < 0.5
    
    # Recommendation
    strategy_quality: str  # EXCELLENT, ACCEPTABLE, WARNING
    tradable: bool
    
    # Details
    windows: List[OOSWindow]


class OOSValidator:
    """
    Performs walk-forward out-of-sample validation.
    
    Philosophy: Only trust strategies that work OOS.
    """
    
    def __init__(
        self,
        train_days: int = 60,
        test_days: int = 30,
        step_days: int = 30,
        degradation_threshold: float = 0.5
    ):
        """
        Initialize OOS validator.
        
        Args:
            train_days: Training window size
            test_days: Testing window size
            step_days: Step between windows (overlap control)
            degradation_threshold: Min OOS/IS ratio to avoid overfitting
        """
        self.train_days = train_days
        self.test_days = test_days
        self.step_days = step_days
        self.degradation_threshold = degradation_threshold
    
    def validate(
        self,
        ticker: str,
        prices: np.ndarray,
        signals: np.ndarray = None
    ) -> OOSValidation:
        """
        Perform walk-forward OOS validation.
        
        Args:
            ticker: Instrument ticker
            prices: Array of prices
            signals: Optional array of trading signals (1=long, 0=flat, -1=short)
                     If None, uses simple momentum strategy
            
        Returns:
            OOSValidation with results
        """
        if len(prices) < self.train_days + self.test_days:
            return self._insufficient_data_result(ticker)
        
        # Generate walk-forward windows
        windows = []
        window_id = 0
        
        start_idx = 0
        while start_idx + self.train_days + self.test_days <= len(prices):
            train_start = start_idx
            train_end = start_idx + self.train_days
            test_start = train_end
            test_end = test_start + self.test_days
            
            # Calculate in-sample performance
            train_prices = prices[train_start:train_end]
            is_return, is_sharpe = self._calculate_performance(
                train_prices,
                signals[train_start:train_end] if signals is not None else None
            )
            
            # Calculate out-of-sample performance
            test_prices = prices[test_start:test_end]
            oos_return, oos_sharpe = self._calculate_performance(
                test_prices,
                signals[test_start:test_end] if signals is not None else None
            )
            
            # Calculate degradation
            if is_return != 0:
                degradation_ratio = oos_return / is_return
            else:
                degradation_ratio = 0.0
            
            windows.append(OOSWindow(
                window_id=window_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                is_return=is_return,
                oos_return=oos_return,
                degradation_ratio=degradation_ratio,
                is_sharpe=is_sharpe,
                oos_sharpe=oos_sharpe
            ))
            
            window_id += 1
            start_idx += self.step_days
        
        if not windows:
            return self._insufficient_data_result(ticker)
        
        # Aggregate results
        avg_is_return = np.mean([w.is_return for w in windows])
        avg_oos_return = np.mean([w.oos_return for w in windows])
        
        # Only count degradation for profitable IS windows
        valid_degradations = [w.degradation_ratio for w in windows if w.is_return > 0]
        avg_degradation_ratio = np.mean(valid_degradations) if valid_degradations else 0.0
        
        # OOS consistency: % of windows with positive OOS return
        oos_positive_count = sum(1 for w in windows if w.oos_return > 0)
        oos_consistency = (oos_positive_count / len(windows)) * 100
        
        # Detect overfitting
        overfitting_detected = avg_degradation_ratio < self.degradation_threshold
        
        # Determine strategy quality
        if avg_degradation_ratio >= 0.8 and oos_consistency >= 70:
            strategy_quality = "EXCELLENT"
            tradable = True
        elif avg_degradation_ratio >= 0.5 and oos_consistency >= 50:
            strategy_quality = "ACCEPTABLE"
            tradable = True
        else:
            strategy_quality = "WARNING"
            tradable = False
        
        return OOSValidation(
            ticker=ticker,
            total_windows=len(windows),
            avg_is_return=avg_is_return,
            avg_oos_return=avg_oos_return,
            avg_degradation_ratio=avg_degradation_ratio,
            oos_consistency=oos_consistency,
            overfitting_detected=overfitting_detected,
            strategy_quality=strategy_quality,
            tradable=tradable,
            windows=windows
        )
    
    def _calculate_performance(
        self,
        prices: np.ndarray,
        signals: np.ndarray = None
    ) -> Tuple[float, float]:
        """
        Calculate return and Sharpe ratio for a window.
        
        Args:
            prices: Price array
            signals: Trading signals (optional)
            
        Returns:
            (return_pct, sharpe_ratio)
        """
        if len(prices) < 2:
            return 0.0, 0.0
        
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # If no signals, use buy-and-hold
        if signals is None:
            strategy_returns = returns
        else:
            # Use signals (align with returns)
            strategy_returns = returns * signals[:-1]
        
        # Total return
        total_return = (np.prod(1 + strategy_returns) - 1) * 100
        
        # Sharpe ratio (annualized)
        if len(strategy_returns) > 1 and np.std(strategy_returns) > 0:
            sharpe = (np.mean(strategy_returns) / np.std(strategy_returns)) * np.sqrt(252)
        else:
            sharpe = 0.0
        
        return total_return, sharpe
    
    def _insufficient_data_result(self, ticker: str) -> OOSValidation:
        """Return default result when insufficient data."""
        return OOSValidation(
            ticker=ticker,
            total_windows=0,
            avg_is_return=0.0,
            avg_oos_return=0.0,
            avg_degradation_ratio=0.0,
            oos_consistency=0.0,
            overfitting_detected=False,
            strategy_quality="INSUFFICIENT_DATA",
            tradable=False,
            windows=[]
        )
    
    def format_validation_report(self, validation: OOSValidation) -> str:
        """Generate formatted validation report."""
        report = f"""
{'='*70}
OUT-OF-SAMPLE VALIDATION: {validation.ticker}
{'='*70}

Walk-Forward Setup:
  Training window:     {self.train_days} days
  Testing window:      {self.test_days} days
  Total windows:       {validation.total_windows}

Performance:
  Avg IS Return:       {validation.avg_is_return:+.2f}%
  Avg OOS Return:      {validation.avg_oos_return:+.2f}%
  Degradation Ratio:   {validation.avg_degradation_ratio:.2f}

Stability:
  OOS Consistency:     {validation.oos_consistency:.1f}% (positive windows)
  Overfitting:         {'⚠️ YES' if validation.overfitting_detected else '✅ NO'}

Strategy Quality:
  Classification:      {validation.strategy_quality}
  Tradable:            {'✅ YES' if validation.tradable else '❌ NO'}

Interpretation:
  {'Strategy generalizes well - minimal degradation OOS' if validation.strategy_quality == 'EXCELLENT' else ''}
  {'Acceptable performance but some degradation' if validation.strategy_quality == 'ACCEPTABLE' else ''}
  {'⚠️ Severe degradation or overfitting detected' if validation.strategy_quality == 'WARNING' else ''}

Window Details (first 5):
"""
        
        for i, window in enumerate(validation.windows[:5]):
            report += f"\n  Window {window.window_id}:"
            report += f" IS={window.is_return:+.1f}%"
            report += f" OOS={window.oos_return:+.1f}%"
            report += f" Ratio={window.degradation_ratio:.2f}"
        
        if len(validation.windows) > 5:
            report += f"\n  ... ({len(validation.windows) - 5} more windows)"
        
        report += f"\n{'='*70}\n"
        
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Out-of-Sample Validator...")
    
    validator = OOSValidator(
        train_days=60,
        test_days=30,
        step_days=30
    )
    
    # Test Case 1: Good strategy (consistent uptrend)
    print("\n1. EXCELLENT Strategy (Consistent Growth):")
    np.random.seed(42)
    prices_good = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.01, 200)))
    
    validation = validator.validate("GOOD.ST", prices_good)
    print(validator.format_validation_report(validation))
    
    # Test Case 2: Overfit strategy (random walk)
    print("\n2. WARNING Strategy (Random Walk - Overfitting):")
    np.random.seed(123)
    prices_random = 100 * np.exp(np.cumsum(np.random.normal(0, 0.02, 200)))
    
    validation = validator.validate("RANDOM.ST", prices_random)
    print(validator.format_validation_report(validation))
    
    # Test Case 3: Declining strategy
    print("\n3. WARNING Strategy (Degrading Trend):")
    # First half good, second half bad
    prices_decline = np.concatenate([
        100 * np.exp(np.cumsum(np.random.normal(0.002, 0.01, 100))),
        100 * np.exp(np.cumsum(np.random.normal(-0.002, 0.015, 100)))
    ])
    
    validation = validator.validate("DECLINE.ST", prices_decline)
    print(validator.format_validation_report(validation))
    
    print("\n✅ Out-of-Sample Validator - Tests Complete")
