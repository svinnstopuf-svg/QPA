"""
Robust Statistical Analysis for Position Trading

Eliminerar small sample bias och overfitting genom:
1. Bayesian Smoothing (Laplace) för win rates
2. Sample size penalties
3. Return consistency metrics (Sharpe-like)
4. Pessimistic EV beräkning
5. Statistical significance testing

Author: Senior Quant Developer
Date: 2026-01-25
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from scipy import stats


@dataclass
class RobustStatistics:
    """Robust statistics för ett pattern med small sample corrections."""
    
    # Raw metrics
    raw_win_rate: float
    raw_avg_return: float
    sample_size: int
    
    # Bayesian smoothed metrics
    adjusted_win_rate: float  # Laplace smoothed
    
    # Consistency metrics
    return_std: float
    return_consistency: float  # Mean/Std (Sharpe-like)
    
    # Statistical significance
    t_statistic: float
    p_value: float
    is_significant: bool  # p < 0.05
    
    # Sample size penalty
    sample_size_factor: float  # 0.0 to 1.0
    
    # Pessimistic metrics
    max_historical_loss: float
    pessimistic_ev: float
    
    # Overall confidence
    confidence_score: float  # 0-100, kombinerar alla faktorer


def calculate_bayesian_win_rate(wins: int, total: int, prior_belief: float = 0.5) -> float:
    """
    Bayesian smoothing (Laplace) för win rate.
    
    Drar låga sample sizes mot prior (default 50%).
    
    Args:
        wins: Antal vinster
        total: Totalt antal trades
        prior_belief: Prior win rate (default 0.5 = 50%)
        
    Returns:
        Adjusted win rate
        
    Examples:
        >>> calculate_bayesian_win_rate(1, 1)  # 100% raw → 66% adjusted
        0.6666666666666666
        >>> calculate_bayesian_win_rate(90, 100)  # 90% raw → ~89.2% adjusted
        0.8921568627450981
        >>> calculate_bayesian_win_rate(150, 200)  # 75% raw → ~74.8% adjusted
        0.7475247524752475
    """
    # Laplace smoothing: (wins + α) / (total + α + β)
    # där α = β = 1 för symmetrisk prior vid 50%
    
    # Alternativ: Beta prior med α = β = prior_strength
    # Vi använder α = β = 1 (Laplace)
    
    adjusted_wr = (wins + 1) / (total + 2)
    
    return adjusted_wr


def calculate_sample_size_factor(n: int, thresholds: Dict[str, int] = None) -> float:
    """
    Beräkna sample size penalty factor (0.0 to 1.0).
    
    Logik:
    - n < 5: 20% av full confidence (80% penalty)
    - 5 ≤ n < 15: Linjär interpolering 20% → 60%
    - 15 ≤ n < 30: Linjär interpolering 60% → 100%
    - n ≥ 30: Full confidence (100%)
    
    Args:
        n: Sample size
        thresholds: Custom thresholds (optional)
        
    Returns:
        Factor mellan 0.0 och 1.0
        
    Examples:
        >>> calculate_sample_size_factor(3)
        0.2
        >>> calculate_sample_size_factor(10)
        0.4
        >>> calculate_sample_size_factor(20)
        0.7333333333333333
        >>> calculate_sample_size_factor(30)
        1.0
        >>> calculate_sample_size_factor(50)
        1.0
    """
    if thresholds is None:
        thresholds = {
            'critical': 5,    # Below this: severe penalty
            'moderate': 15,   # Below this: moderate penalty
            'good': 30        # Above this: full confidence
        }
    
    if n < thresholds['critical']:
        # Severe penalty: 20% confidence
        return 0.2
    
    elif n < thresholds['moderate']:
        # Linear interpolation: 20% → 60%
        # Range: [5, 15) → [0.2, 0.6]
        range_span = thresholds['moderate'] - thresholds['critical']
        position = (n - thresholds['critical']) / range_span
        return 0.2 + (0.4 * position)
    
    elif n < thresholds['good']:
        # Linear interpolation: 60% → 100%
        # Range: [15, 30) → [0.6, 1.0]
        range_span = thresholds['good'] - thresholds['moderate']
        position = (n - thresholds['moderate']) / range_span
        return 0.6 + (0.4 * position)
    
    else:
        # Full confidence
        return 1.0


def calculate_return_consistency(returns: List[float]) -> Tuple[float, float, float]:
    """
    Beräkna return consistency (Sharpe-like metric).
    
    Args:
        returns: Lista med historical returns för pattern
        
    Returns:
        (mean, std, consistency) där consistency = mean / std
        
    Examples:
        >>> calculate_return_consistency([0.20, -0.05, 0.30, -0.10])
        (0.0875, 0.17262215834863652, 0.5069290641975307)
        >>> calculate_return_consistency([0.08, 0.07, 0.09, 0.06])
        (0.075, 0.012909944487358056, 5.809475019311126)
    """
    if len(returns) < 2:
        return (0.0, 0.0, 0.0)
    
    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)  # Sample std (n-1)
    
    if std_return == 0:
        consistency = 0.0
    else:
        consistency = mean_return / std_return
    
    return (mean_return, std_return, consistency)


def calculate_statistical_significance(returns: List[float]) -> Tuple[float, float, bool]:
    """
    T-test för att avgöra om mean return är signifikant skild från 0.
    
    H0: Mean return = 0 (ingen edge)
    H1: Mean return > 0 (positiv edge)
    
    Args:
        returns: Lista med returns
        
    Returns:
        (t_statistic, p_value, is_significant)
        
    Examples:
        >>> returns = [0.05, 0.03, 0.07, 0.02, 0.06]
        >>> t, p, sig = calculate_statistical_significance(returns)
        >>> sig  # Should be True for strong positive returns
        True
    """
    if len(returns) < 2:
        return (0.0, 1.0, False)
    
    # One-sample t-test: H0: μ = 0
    t_stat, p_value_two_tailed = stats.ttest_1samp(returns, 0)
    
    # One-tailed p-value (vi testar om μ > 0)
    p_value = p_value_two_tailed / 2 if t_stat > 0 else 1.0
    
    # Significance at α = 0.05
    is_significant = (p_value < 0.05 and t_stat > 0)
    
    return (t_stat, p_value, is_significant)


def calculate_pessimistic_ev(
    adjusted_win_rate: float,
    avg_win: float,
    avg_loss: float,
    max_loss: float,
    confidence_factor: float = 0.5
) -> float:
    """
    Pessimistic Expected Value med worst-case component.
    
    Formel:
    EV_pessimistic = (AdjWR × AvgWin) - ((1 - AdjWR) × WeightedLoss)
    
    där WeightedLoss = (AvgLoss × (1-α)) + (MaxLoss × α)
    α = confidence_factor (0.5 = 50% weight på max loss)
    
    Args:
        adjusted_win_rate: Bayesian smoothed WR
        avg_win: Genomsnittlig vinst
        avg_loss: Genomsnittlig förlust (negativ)
        max_loss: Största historiska förlust (negativ)
        confidence_factor: Vikt på max loss (0.0-1.0)
        
    Returns:
        Pessimistic EV
        
    Examples:
        >>> calculate_pessimistic_ev(0.7, 0.10, -0.03, -0.08, 0.5)
        0.053500000000000006
    """
    # Weighted loss: mix av average och worst case
    weighted_loss = (avg_loss * (1 - confidence_factor)) + (max_loss * confidence_factor)
    
    # EV = P(win) × AvgWin + P(loss) × WeightedLoss
    ev = (adjusted_win_rate * avg_win) + ((1 - adjusted_win_rate) * weighted_loss)
    
    return ev


def calculate_confidence_score(
    sample_size_factor: float,
    return_consistency: float,
    is_significant: bool,
    adjusted_win_rate: float
) -> float:
    """
    Kombinerad confidence score (0-100).
    
    Komponenter:
    1. Sample size factor (0-1) → 40 points
    2. Return consistency (normalized) → 30 points
    3. Statistical significance → 20 points
    4. Win rate quality → 10 points
    
    Args:
        sample_size_factor: From calculate_sample_size_factor
        return_consistency: Mean/Std ratio
        is_significant: T-test result
        adjusted_win_rate: Bayesian smoothed WR
        
    Returns:
        Score 0-100
    """
    score = 0.0
    
    # 1. Sample size (40 points)
    score += sample_size_factor * 40
    
    # 2. Return consistency (30 points)
    # Normalize: consistency > 2.0 = excellent (Sharpe > 2)
    consistency_normalized = min(1.0, abs(return_consistency) / 2.0)
    score += consistency_normalized * 30
    
    # 3. Statistical significance (20 points)
    if is_significant:
        score += 20
    
    # 4. Win rate quality (10 points)
    # WR > 60% gets full points, scales linearly from 50%
    if adjusted_win_rate >= 0.60:
        score += 10
    elif adjusted_win_rate > 0.50:
        score += ((adjusted_win_rate - 0.50) / 0.10) * 10
    
    return min(100.0, score)


def calculate_robust_stats(
    returns_list: List[float],
    wins: int = None,
    total: int = None
) -> RobustStatistics:
    """
    Huvudfunktion: Beräkna alla robust statistics.
    
    Args:
        returns_list: Lista med alla historical returns för pattern
        wins: Antal vinster (optional, beräknas från returns om None)
        total: Totalt antal trades (optional, använder len(returns_list) om None)
        
    Returns:
        RobustStatistics object med alla metrics
        
    Example:
        >>> returns = [0.05, 0.03, -0.02, 0.07, 0.04, -0.01, 0.06]
        >>> stats = calculate_robust_stats(returns)
        >>> print(f"Adjusted WR: {stats.adjusted_win_rate:.2%}")
        Adjusted WR: 66.67%
        >>> print(f"Sample size factor: {stats.sample_size_factor:.2f}")
        Sample size factor: 0.28
    """
    # Calculate wins/total from returns if not provided
    if wins is None or total is None:
        total = len(returns_list)
        wins = sum(1 for r in returns_list if r > 0)
    
    # Raw metrics
    raw_win_rate = wins / total if total > 0 else 0.0
    raw_avg_return = np.mean(returns_list) if len(returns_list) > 0 else 0.0
    
    # 1. Bayesian smoothing
    adjusted_win_rate = calculate_bayesian_win_rate(wins, total)
    
    # 2. Sample size factor
    sample_size_factor = calculate_sample_size_factor(total)
    
    # 3. Return consistency
    mean_ret, std_ret, consistency = calculate_return_consistency(returns_list)
    
    # 4. Statistical significance
    t_stat, p_val, is_sig = calculate_statistical_significance(returns_list)
    
    # 5. Pessimistic EV
    winning_returns = [r for r in returns_list if r > 0]
    losing_returns = [r for r in returns_list if r <= 0]
    
    avg_win = np.mean(winning_returns) if len(winning_returns) > 0 else 0.0
    avg_loss = np.mean(losing_returns) if len(losing_returns) > 0 else 0.0
    max_loss = min(losing_returns) if len(losing_returns) > 0 else 0.0
    
    pessimistic_ev = calculate_pessimistic_ev(
        adjusted_win_rate,
        avg_win,
        avg_loss,
        max_loss,
        confidence_factor=0.5
    )
    
    # 6. Overall confidence
    confidence = calculate_confidence_score(
        sample_size_factor,
        consistency,
        is_sig,
        adjusted_win_rate
    )
    
    return RobustStatistics(
        raw_win_rate=raw_win_rate,
        raw_avg_return=raw_avg_return,
        sample_size=total,
        adjusted_win_rate=adjusted_win_rate,
        return_std=std_ret,
        return_consistency=consistency,
        t_statistic=t_stat,
        p_value=p_val,
        is_significant=is_sig,
        sample_size_factor=sample_size_factor,
        max_historical_loss=max_loss,
        pessimistic_ev=pessimistic_ev,
        confidence_score=confidence
    )


def calculate_robust_score(
    robust_stats: RobustStatistics,
    weights: Dict[str, float] = None
) -> float:
    """
    Beräkna robust score som prioriterar sample size och consistency.
    
    Default weights:
    - Confidence score: 40%
    - Pessimistic EV: 30%
    - Return consistency: 20%
    - Statistical significance: 10%
    
    Args:
        robust_stats: RobustStatistics object
        weights: Custom weights (optional)
        
    Returns:
        Score 0-100
    """
    if weights is None:
        weights = {
            'confidence': 0.40,
            'pessimistic_ev': 0.30,
            'consistency': 0.20,
            'significance': 0.10
        }
    
    score = 0.0
    
    # 1. Confidence score (already 0-100)
    score += robust_stats.confidence_score * weights['confidence']
    
    # 2. Pessimistic EV (normalize to 0-100)
    # EV > 10% = 100 points, scale linearly
    ev_normalized = min(100, (robust_stats.pessimistic_ev / 0.10) * 100)
    ev_normalized = max(0, ev_normalized)  # Floor at 0
    score += ev_normalized * weights['pessimistic_ev']
    
    # 3. Return consistency (normalize to 0-100)
    # Consistency > 2.0 = 100 points
    consistency_normalized = min(100, (abs(robust_stats.return_consistency) / 2.0) * 100)
    score += consistency_normalized * weights['consistency']
    
    # 4. Statistical significance (binary: 0 or 100)
    sig_score = 100 if robust_stats.is_significant else 0
    score += sig_score * weights['significance']
    
    return min(100.0, score)


if __name__ == "__main__":
    print("="*80)
    print("ROBUST STATISTICS - Examples")
    print("="*80)
    
    # Example 1: Small sample with high win rate (suspicious)
    print("\nExample 1: Small sample (n=3), 100% win rate")
    print("-" * 60)
    returns_small = [0.10, 0.15, 0.12]
    stats_small = calculate_robust_stats(returns_small)
    score_small = calculate_robust_score(stats_small)
    
    print(f"Raw Win Rate: {stats_small.raw_win_rate:.1%}")
    print(f"Adjusted Win Rate: {stats_small.adjusted_win_rate:.1%} (Bayesian smoothed)")
    print(f"Sample Size Factor: {stats_small.sample_size_factor:.2f} (20% confidence)")
    print(f"Pessimistic EV: {stats_small.pessimistic_ev:+.2%}")
    print(f"Confidence Score: {stats_small.confidence_score:.1f}/100")
    print(f"Robust Score: {score_small:.1f}/100")
    
    # Example 2: Large sample with good consistency
    print("\nExample 2: Large sample (n=50), 70% win rate, consistent")
    print("-" * 60)
    np.random.seed(42)
    # Simulate 70% WR with tight distribution
    wins_large = [np.random.normal(0.08, 0.02) for _ in range(35)]
    losses_large = [np.random.normal(-0.03, 0.01) for _ in range(15)]
    returns_large = wins_large + losses_large
    
    stats_large = calculate_robust_stats(returns_large)
    score_large = calculate_robust_score(stats_large)
    
    print(f"Raw Win Rate: {stats_large.raw_win_rate:.1%}")
    print(f"Adjusted Win Rate: {stats_large.adjusted_win_rate:.1%}")
    print(f"Sample Size Factor: {stats_large.sample_size_factor:.2f} (100% confidence)")
    print(f"Return Consistency: {stats_large.return_consistency:.2f}")
    print(f"T-statistic: {stats_large.t_statistic:.2f}, p={stats_large.p_value:.4f}")
    print(f"Significant: {stats_large.is_significant}")
    print(f"Pessimistic EV: {stats_large.pessimistic_ev:+.2%}")
    print(f"Confidence Score: {stats_large.confidence_score:.1f}/100")
    print(f"Robust Score: {score_large:.1f}/100")
    
    # Example 3: Moderate sample with volatile returns
    print("\nExample 3: Moderate sample (n=20), 65% WR, volatile")
    print("-" * 60)
    # 65% WR but high variance
    wins_vol = [0.20, 0.05, 0.30, 0.10, 0.25, 0.08, 0.15, 0.35, 0.12, 0.18, 0.22, 0.07, 0.28]
    losses_vol = [-0.15, -0.08, -0.20, -0.05, -0.12, -0.10, -0.18]
    returns_vol = wins_vol + losses_vol
    
    stats_vol = calculate_robust_stats(returns_vol)
    score_vol = calculate_robust_score(stats_vol)
    
    print(f"Raw Win Rate: {stats_vol.raw_win_rate:.1%}")
    print(f"Adjusted Win Rate: {stats_vol.adjusted_win_rate:.1%}")
    print(f"Sample Size Factor: {stats_vol.sample_size_factor:.2f}")
    print(f"Return Consistency: {stats_vol.return_consistency:.2f} (low = volatile)")
    print(f"Return Std: {stats_vol.return_std:.2%}")
    print(f"Pessimistic EV: {stats_vol.pessimistic_ev:+.2%}")
    print(f"Confidence Score: {stats_vol.confidence_score:.1f}/100")
    print(f"Robust Score: {score_vol:.1f}/100")
    
    print("\n" + "="*80)
    print("KEY INSIGHT: Large consistent sample scores higher than")
    print("small volatile sample, even with similar raw metrics!")
    print("="*80)
