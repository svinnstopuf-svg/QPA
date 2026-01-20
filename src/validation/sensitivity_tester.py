"""
Sensitivity Test - Pattern Robustness Validation

Quantitative Principle:
A robust pattern should perform consistently across parameter variations.
Fragile patterns that work with exact parameters but fail with ±5% changes
are likely curve-fitted and won't generalize.

Methodology:
1. Test pattern with original parameters → baseline edge
2. Test with +5% parameter variation → edge_high
3. Test with -5% parameter variation → edge_low
4. Calculate stability: std(edges) / mean(edges)
5. Reject if edge disappears or reverses with small changes

Example:
Original: lookback=20, threshold=2.0 → edge=1.5%
+5%: lookback=21, threshold=2.1 → edge=1.4%
-5%: lookback=19, threshold=1.9 → edge=1.6%
Stability = std([1.4, 1.5, 1.6]) / mean([1.4, 1.5, 1.6]) = 0.05 (GOOD)

Rejection Criteria:
- Stability > 0.5 (too volatile)
- Sign flip (positive → negative edge)
- Edge drops >50% with variation
"""
from typing import List, Dict, Callable, Any, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class SensitivityResult:
    """Results from sensitivity testing."""
    pattern_name: str
    baseline_edge: float
    
    # Variations
    high_variation_edge: float  # +5% parameters
    low_variation_edge: float  # -5% parameters
    
    # Stability metrics
    stability_coefficient: float  # std / mean
    max_edge_drop: float  # % drop from baseline
    sign_flip_detected: bool  # Edge changes sign
    
    # Pass/fail
    robust: bool
    rejection_reason: str


class SensitivityTester:
    """
    Tests pattern robustness with parameter perturbation.
    
    Philosophy: Only trust patterns that work across parameter space.
    """
    
    def __init__(
        self,
        variation_pct: float = 5.0,
        max_stability: float = 0.5,
        max_edge_drop_pct: float = 50.0,
        allow_sign_flip: bool = False
    ):
        """
        Initialize sensitivity tester.
        
        Args:
            variation_pct: Parameter variation percentage
            max_stability: Maximum allowed stability coefficient
            max_edge_drop_pct: Maximum allowed edge drop percentage
            allow_sign_flip: Allow edge to change sign
        """
        self.variation_pct = variation_pct
        self.max_stability = max_stability
        self.max_edge_drop_pct = max_edge_drop_pct
        self.allow_sign_flip = allow_sign_flip
    
    def test_pattern(
        self,
        pattern_name: str,
        pattern_function: Callable,
        baseline_params: Dict[str, Any],
        data: np.ndarray
    ) -> SensitivityResult:
        """
        Test pattern sensitivity to parameter variations.
        
        Args:
            pattern_name: Name of pattern
            pattern_function: Function that takes params and data, returns edge
            baseline_params: Dictionary of baseline parameters
            data: Price data array
            
        Returns:
            SensitivityResult with stability analysis
        """
        # 1. Baseline edge
        try:
            baseline_edge = pattern_function(baseline_params, data)
        except Exception as e:
            return self._error_result(pattern_name, f"Baseline failed: {e}")
        
        # 2. High variation (+5%)
        high_params = self._vary_params(baseline_params, +self.variation_pct)
        try:
            high_edge = pattern_function(high_params, data)
        except Exception as e:
            return self._error_result(pattern_name, f"High variation failed: {e}")
        
        # 3. Low variation (-5%)
        low_params = self._vary_params(baseline_params, -self.variation_pct)
        try:
            low_edge = pattern_function(low_params, data)
        except Exception as e:
            return self._error_result(pattern_name, f"Low variation failed: {e}")
        
        # 4. Calculate stability
        edges = np.array([baseline_edge, high_edge, low_edge])
        
        # Handle zero/near-zero edges
        mean_edge = np.mean(edges)
        if abs(mean_edge) < 1e-6:
            stability = 0.0
        else:
            stability = np.std(edges) / abs(mean_edge)
        
        # 5. Check for sign flip
        sign_flip = False
        if baseline_edge > 0 and (high_edge < 0 or low_edge < 0):
            sign_flip = True
        elif baseline_edge < 0 and (high_edge > 0 or low_edge > 0):
            sign_flip = True
        
        # 6. Calculate max edge drop
        if baseline_edge != 0:
            drops = [
                abs((high_edge - baseline_edge) / baseline_edge) * 100,
                abs((low_edge - baseline_edge) / baseline_edge) * 100
            ]
            max_edge_drop = max(drops)
        else:
            max_edge_drop = 0.0
        
        # 7. Determine robustness
        robust = True
        rejection_reason = ""
        
        if stability > self.max_stability:
            robust = False
            rejection_reason = f"Too volatile (stability={stability:.2f} > {self.max_stability})"
        
        elif sign_flip and not self.allow_sign_flip:
            robust = False
            rejection_reason = "Sign flip detected"
        
        elif max_edge_drop > self.max_edge_drop_pct:
            robust = False
            rejection_reason = f"Edge drops {max_edge_drop:.1f}% (>{self.max_edge_drop_pct}%)"
        
        return SensitivityResult(
            pattern_name=pattern_name,
            baseline_edge=baseline_edge,
            high_variation_edge=high_edge,
            low_variation_edge=low_edge,
            stability_coefficient=stability,
            max_edge_drop=max_edge_drop,
            sign_flip_detected=sign_flip,
            robust=robust,
            rejection_reason=rejection_reason if not robust else "PASSED"
        )
    
    def _vary_params(
        self,
        params: Dict[str, Any],
        variation_pct: float
    ) -> Dict[str, Any]:
        """
        Create varied parameter set.
        
        Args:
            params: Original parameters
            variation_pct: Percentage to vary (+/-)
            
        Returns:
            Varied parameters
        """
        varied = {}
        
        for key, value in params.items():
            if isinstance(value, (int, float)):
                # Numeric parameter - apply variation
                varied_value = value * (1 + variation_pct / 100)
                
                # Preserve type (int vs float)
                if isinstance(value, int):
                    varied[key] = int(round(varied_value))
                else:
                    varied[key] = varied_value
            else:
                # Non-numeric - keep as is
                varied[key] = value
        
        return varied
    
    def _error_result(self, pattern_name: str, reason: str) -> SensitivityResult:
        """Return error result."""
        return SensitivityResult(
            pattern_name=pattern_name,
            baseline_edge=0.0,
            high_variation_edge=0.0,
            low_variation_edge=0.0,
            stability_coefficient=0.0,
            max_edge_drop=0.0,
            sign_flip_detected=False,
            robust=False,
            rejection_reason=reason
        )
    
    def format_report(self, result: SensitivityResult) -> str:
        """Generate formatted report."""
        report = f"""
{'='*70}
SENSITIVITY TEST: {result.pattern_name}
{'='*70}

Baseline Edge:       {result.baseline_edge:+.3f}%

Parameter Variations (±{self.variation_pct}%):
  High (+{self.variation_pct}%):     {result.high_variation_edge:+.3f}%
  Low (-{self.variation_pct}%):      {result.low_variation_edge:+.3f}%

Stability Analysis:
  Stability Coeff:   {result.stability_coefficient:.3f} (threshold: {self.max_stability})
  Max Edge Drop:     {result.max_edge_drop:.1f}% (threshold: {self.max_edge_drop_pct}%)
  Sign Flip:         {'⚠️ YES' if result.sign_flip_detected else '✅ NO'}

Result:
  Robust:            {'✅ YES' if result.robust else '❌ NO'}
  Status:            {result.rejection_reason}

Interpretation:
  {'Pattern is stable across parameter variations' if result.robust else 'Pattern is fragile - likely curve-fitted'}
{'='*70}
"""
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Sensitivity Tester...")
    
    tester = SensitivityTester()
    
    # Test Case 1: Robust pattern (stable across variations)
    print("\n1. Robust Pattern Test:")
    
    def robust_pattern(params, data):
        """Simple moving average crossover - stable pattern."""
        lookback = params['lookback']
        ma = np.mean(data[-lookback:])
        current = data[-1]
        
        # Edge: current vs MA
        edge = ((current - ma) / ma) * 100
        return edge
    
    prices = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110])
    result = tester.test_pattern(
        "MA_Crossover",
        robust_pattern,
        {'lookback': 5},
        prices
    )
    print(tester.format_report(result))
    
    # Test Case 2: Fragile pattern (sensitive to parameters)
    print("\n2. Fragile Pattern Test:")
    
    def fragile_pattern(params, data):
        """Fragile pattern that breaks with small changes."""
        threshold = params['threshold']
        lookback = params['lookback']
        
        # Highly sensitive calculation
        recent_vol = np.std(data[-lookback:])
        
        if recent_vol > threshold:
            return 5.0  # High edge
        else:
            return -2.0  # Negative edge
    
    result = tester.test_pattern(
        "Fragile_Volatility",
        fragile_pattern,
        {'threshold': 2.5, 'lookback': 5},
        prices
    )
    print(tester.format_report(result))
    
    # Test Case 3: Sign flip pattern
    print("\n3. Sign Flip Test:")
    
    def sign_flip_pattern(params, data):
        """Pattern that flips sign with small changes."""
        cutoff = params['cutoff']
        value = np.mean(data[-3:])
        
        return 3.0 if value > cutoff else -3.0
    
    result = tester.test_pattern(
        "Sign_Flip",
        sign_flip_pattern,
        {'cutoff': 105.0},
        prices
    )
    print(tester.format_report(result))
    
    print("\n✅ Sensitivity Tester - Tests Complete")
