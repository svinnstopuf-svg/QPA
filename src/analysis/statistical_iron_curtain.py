"""
Statistical Iron Curtain - Extreme Validation

Two brutal filters that eliminate false positives:

1. Bootstrap Resampling (Monte Carlo)
   - Run 1000 simulations resampling historical returns
   - REQUIRE: ≥950/1000 show EV > 0
   - This enforces P-Value < 0.05

2. Kaufman Efficiency Ratio (ER)
   - ER = Total_Price_Change / Sum_of_Absolute_Daily_Changes
   - Measures signal-to-noise ratio
   - REJECT: ER < 0.3 (too much noise/whipsaw)

Philosophy: If math doesn't converge in 95% of scenarios, trade doesn't exist.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class BootstrapResult:
    """Result of bootstrap resampling validation"""
    ticker: str
    n_simulations: int
    n_positive_ev: int
    pass_rate: float  # % of simulations with EV > 0
    passed: bool  # pass_rate >= 0.95
    
    mean_ev: float
    std_ev: float
    ci_95_lower: float
    ci_95_upper: float
    
    reason: str


@dataclass
class KaufmanERResult:
    """Result of Kaufman Efficiency Ratio check"""
    ticker: str
    efficiency_ratio: float  # 0-1
    passed: bool  # ER >= 0.30
    
    total_price_change: float
    sum_absolute_changes: float
    
    reason: str


class StatisticalIronCurtain:
    """
    Brutal statistical validation that eliminates false positives.
    
    Filter 1: Bootstrap Resampling
    - 1000 Monte Carlo simulations
    - Require 950/1000 with EV > 0
    
    Filter 2: Kaufman Efficiency Ratio
    - Require ER ≥ 0.30
    """
    
    def __init__(
        self,
        n_bootstrap: int = 1000,
        min_pass_rate: float = 0.95,
        min_efficiency_ratio: float = 0.30
    ):
        """
        Args:
            n_bootstrap: Number of bootstrap simulations (default 1000)
            min_pass_rate: Minimum % of simulations with EV>0 (default 0.95)
            min_efficiency_ratio: Minimum Kaufman ER (default 0.30)
        """
        self.n_bootstrap = n_bootstrap
        self.min_pass_rate = min_pass_rate
        self.min_efficiency_ratio = min_efficiency_ratio
    
    def bootstrap_resample(
        self,
        ticker: str,
        forward_returns: np.ndarray,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> BootstrapResult:
        """
        Run bootstrap resampling to validate Expected Value robustness.
        
        Process:
        1. For each simulation (1000x):
           - Resample forward_returns with replacement
           - Calculate EV = (WR × AvgWin) - ((1-WR) × AvgLoss)
        2. Count how many simulations have EV > 0
        3. PASS if ≥950/1000 (95%)
        
        Args:
            ticker: Stock ticker
            forward_returns: Historical forward returns array
            win_rate: Current win rate
            avg_win: Average winning return
            avg_loss: Average losing return (negative)
        
        Returns:
            BootstrapResult with pass/fail verdict
        """
        if len(forward_returns) < 5:
            return BootstrapResult(
                ticker=ticker,
                n_simulations=0,
                n_positive_ev=0,
                pass_rate=0.0,
                passed=False,
                mean_ev=0.0,
                std_ev=0.0,
                ci_95_lower=0.0,
                ci_95_upper=0.0,
                reason="Insufficient sample size (<5 returns)"
            )
        
        # Run bootstrap simulations
        bootstrap_evs = []
        n_positive = 0
        
        np.random.seed(42)  # Reproducibility
        
        for _ in range(self.n_bootstrap):
            # Resample with replacement
            resampled = np.random.choice(
                forward_returns,
                size=len(forward_returns),
                replace=True
            )
            
            # Calculate EV for this sample
            wins = resampled[resampled > 0]
            losses = resampled[resampled <= 0]
            
            if len(resampled) > 0:
                wr = len(wins) / len(resampled)
                aw = np.mean(wins) if len(wins) > 0 else 0.0
                al = abs(np.mean(losses)) if len(losses) > 0 else 0.0
                
                ev = (wr * aw) - ((1 - wr) * al)
                bootstrap_evs.append(ev)
                
                if ev > 0:
                    n_positive += 1
        
        # Statistics
        pass_rate = n_positive / self.n_bootstrap
        passed = pass_rate >= self.min_pass_rate
        
        mean_ev = np.mean(bootstrap_evs)
        std_ev = np.std(bootstrap_evs)
        
        # 95% confidence interval
        bootstrap_evs_sorted = np.sort(bootstrap_evs)
        ci_95_lower = bootstrap_evs_sorted[int(0.025 * len(bootstrap_evs))]
        ci_95_upper = bootstrap_evs_sorted[int(0.975 * len(bootstrap_evs))]
        
        if passed:
            reason = f"✅ IRON CURTAIN PASSED: {n_positive}/{self.n_bootstrap} simulations positive ({pass_rate*100:.1f}%)"
        else:
            reason = f"❌ IRON CURTAIN FAILED: Only {n_positive}/{self.n_bootstrap} simulations positive ({pass_rate*100:.1f}% < {self.min_pass_rate*100:.0f}%)"
        
        return BootstrapResult(
            ticker=ticker,
            n_simulations=self.n_bootstrap,
            n_positive_ev=n_positive,
            pass_rate=pass_rate,
            passed=passed,
            mean_ev=mean_ev,
            std_ev=std_ev,
            ci_95_lower=ci_95_lower,
            ci_95_upper=ci_95_upper,
            reason=reason
        )
    
    def calculate_kaufman_er(
        self,
        ticker: str,
        prices: np.ndarray,
        period: int = 63
    ) -> KaufmanERResult:
        """
        Calculate Kaufman Efficiency Ratio.
        
        ER = Total_Price_Change / Sum_of_Absolute_Daily_Changes
        
        Interpretation:
        - ER close to 1.0: Trending (very efficient)
        - ER close to 0.0: Choppy/noisy (inefficient)
        - ER ≥ 0.30: Acceptable signal-to-noise
        - ER < 0.30: Too much whipsaw → REJECT
        
        Args:
            ticker: Stock ticker
            prices: Price array
            period: Lookback period (default 63 days = 3 months)
        
        Returns:
            KaufmanERResult with ER and pass/fail
        """
        if len(prices) < period:
            return KaufmanERResult(
                ticker=ticker,
                efficiency_ratio=0.0,
                passed=False,
                total_price_change=0.0,
                sum_absolute_changes=0.0,
                reason=f"Insufficient data (<{period} days)"
            )
        
        # Get last `period` days
        recent_prices = prices[-period:]
        
        # Total net price change
        total_price_change = abs(recent_prices[-1] - recent_prices[0])
        
        # Sum of absolute daily changes
        daily_changes = np.diff(recent_prices)
        sum_absolute_changes = np.sum(np.abs(daily_changes))
        
        # Efficiency Ratio
        if sum_absolute_changes > 0:
            efficiency_ratio = total_price_change / sum_absolute_changes
        else:
            efficiency_ratio = 0.0
        
        # Validation
        passed = efficiency_ratio >= self.min_efficiency_ratio
        
        if passed:
            reason = f"✅ Kaufman ER PASS: {efficiency_ratio:.3f} ≥ {self.min_efficiency_ratio} (efficient trend)"
        else:
            reason = f"❌ Kaufman ER FAIL: {efficiency_ratio:.3f} < {self.min_efficiency_ratio} (too choppy/noisy)"
        
        return KaufmanERResult(
            ticker=ticker,
            efficiency_ratio=efficiency_ratio,
            passed=passed,
            total_price_change=total_price_change,
            sum_absolute_changes=sum_absolute_changes,
            reason=reason
        )
    
    def validate_pattern(
        self,
        ticker: str,
        prices: np.ndarray,
        forward_returns: np.ndarray,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> tuple[bool, BootstrapResult, KaufmanERResult]:
        """
        Run both Iron Curtain filters.
        
        Args:
            ticker: Stock ticker
            prices: Price history
            forward_returns: Pattern's historical forward returns
            win_rate: Win rate
            avg_win: Average win
            avg_loss: Average loss
        
        Returns:
            (passed_both: bool, bootstrap_result, kaufman_result)
        """
        # Filter 1: Bootstrap
        bootstrap = self.bootstrap_resample(
            ticker,
            forward_returns,
            win_rate,
            avg_win,
            avg_loss
        )
        
        # Filter 2: Kaufman ER
        kaufman = self.calculate_kaufman_er(ticker, prices, period=63)
        
        # Both must pass
        passed_both = bootstrap.passed and kaufman.passed
        
        return passed_both, bootstrap, kaufman


def eliminate_correlated_by_er(
    setups: List,
    correlation_matrix: np.ndarray,
    efficiency_ratios: Dict[str, float],
    correlation_threshold: float = 0.70
) -> List[str]:
    """
    Enhanced correlation clustering using Kaufman ER.
    
    For Top 10 setups:
    - If Correlation(i, j) > 0.70
    - Eliminate the one with LOWER Kaufman ER
    
    Args:
        setups: List of setup objects (must have .ticker attribute)
        correlation_matrix: NxN correlation matrix
        efficiency_ratios: Dict[ticker, ER]
        correlation_threshold: Correlation cutoff (default 0.70)
    
    Returns:
        List of tickers to eliminate
    """
    if len(setups) <= 1:
        return []
    
    to_eliminate = set()
    tickers = [s.ticker for s in setups]
    
    # Check all pairs
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            ticker_i = tickers[i]
            ticker_j = tickers[j]
            
            # Skip if already marked for elimination
            if ticker_i in to_eliminate or ticker_j in to_eliminate:
                continue
            
            # Check correlation
            corr = correlation_matrix[i][j]
            
            if corr > correlation_threshold:
                # Highly correlated → keep the one with HIGHER ER
                er_i = efficiency_ratios.get(ticker_i, 0.0)
                er_j = efficiency_ratios.get(ticker_j, 0.0)
                
                if er_i < er_j:
                    to_eliminate.add(ticker_i)
                else:
                    to_eliminate.add(ticker_j)
    
    return list(to_eliminate)
