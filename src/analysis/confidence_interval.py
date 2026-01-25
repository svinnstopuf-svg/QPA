"""
Confidence Interval Calculator for Win Rates

Uses Wilson score interval for binomial proportions.
This is more accurate than normal approximation for small sample sizes.

Reference: https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
"""

import math
from typing import Tuple
from dataclasses import dataclass


@dataclass
class ConfidenceInterval:
    """Confidence interval for a proportion (e.g., win rate)."""
    point_estimate: float  # The observed win rate
    lower_bound: float  # Lower bound of CI
    upper_bound: float  # Upper bound of CI
    margin_of_error: float  # ± margin
    confidence_level: float  # 0.95 for 95%
    sample_size: int
    
    def __str__(self) -> str:
        return f"{self.point_estimate:.1%} ± {self.margin_of_error:.1%}"
    
    def format_range(self) -> str:
        """Format as range."""
        return f"[{self.lower_bound:.1%}, {self.upper_bound:.1%}]"


def wilson_score_interval(
    successes: int,
    trials: int,
    confidence_level: float = 0.95
) -> ConfidenceInterval:
    """
    Calculate Wilson score confidence interval for binomial proportion.
    
    This method is preferred over normal approximation because:
    - Works well for small sample sizes
    - Never produces bounds outside [0, 1]
    - Better coverage properties
    
    Args:
        successes: Number of wins
        trials: Total number of trials (sample size)
        confidence_level: Confidence level (0.95 = 95%)
        
    Returns:
        ConfidenceInterval object
        
    Example:
        >>> ci = wilson_score_interval(successes=60, trials=100, confidence_level=0.95)
        >>> print(ci)
        60.0% ± 9.6%
    """
    if trials == 0:
        return ConfidenceInterval(
            point_estimate=0.0,
            lower_bound=0.0,
            upper_bound=0.0,
            margin_of_error=0.0,
            confidence_level=confidence_level,
            sample_size=0
        )
    
    # Point estimate
    p_hat = successes / trials
    
    # Z-score for confidence level
    # 95% CI -> z = 1.96
    # 90% CI -> z = 1.645
    # 99% CI -> z = 2.576
    z_scores = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576
    }
    z = z_scores.get(confidence_level, 1.96)
    
    # Wilson score interval formula
    denominator = 1 + z**2 / trials
    centre = (p_hat + z**2 / (2 * trials)) / denominator
    margin = z * math.sqrt((p_hat * (1 - p_hat) / trials + z**2 / (4 * trials**2))) / denominator
    
    lower = max(0.0, centre - margin)
    upper = min(1.0, centre + margin)
    
    # Calculate margin of error from point estimate
    # (This is the ± value)
    margin_from_point = max(p_hat - lower, upper - p_hat)
    
    return ConfidenceInterval(
        point_estimate=p_hat,
        lower_bound=lower,
        upper_bound=upper,
        margin_of_error=margin_from_point,
        confidence_level=confidence_level,
        sample_size=trials
    )


def calculate_win_rate_ci(
    win_rate: float,
    sample_size: int,
    confidence_level: float = 0.95
) -> ConfidenceInterval:
    """
    Calculate confidence interval from win rate and sample size.
    
    Args:
        win_rate: Observed win rate (0.0 to 1.0)
        sample_size: Number of observations
        confidence_level: Confidence level (default 95%)
        
    Returns:
        ConfidenceInterval object
        
    Example:
        >>> ci = calculate_win_rate_ci(win_rate=0.65, sample_size=50)
        >>> print(ci)
        65.0% ± 13.0%
    """
    successes = int(win_rate * sample_size)
    return wilson_score_interval(successes, sample_size, confidence_level)


def interpret_confidence_width(margin_of_error: float) -> str:
    """
    Interpret the width of confidence interval.
    
    Returns:
        String describing confidence quality
    """
    if margin_of_error < 0.05:  # ±5%
        return "Very High Confidence"
    elif margin_of_error < 0.10:  # ±10%
        return "High Confidence"
    elif margin_of_error < 0.15:  # ±15%
        return "Moderate Confidence"
    elif margin_of_error < 0.20:  # ±20%
        return "Low Confidence"
    else:
        return "Very Low Confidence"


def sample_size_for_margin(
    p: float,
    margin: float,
    confidence_level: float = 0.95
) -> int:
    """
    Calculate required sample size to achieve desired margin of error.
    
    Args:
        p: Expected proportion (e.g., 0.65 for 65% win rate)
        margin: Desired margin of error (e.g., 0.05 for ±5%)
        confidence_level: Confidence level (default 95%)
        
    Returns:
        Required sample size
        
    Example:
        >>> sample_size_for_margin(p=0.65, margin=0.05)
        349  # Need ~350 samples for ±5% margin at 65% win rate
    """
    z_scores = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576
    }
    z = z_scores.get(confidence_level, 1.96)
    
    # Normal approximation formula for sample size
    n = (z**2 * p * (1 - p)) / (margin**2)
    return int(math.ceil(n))


if __name__ == "__main__":
    print("="*80)
    print("CONFIDENCE INTERVAL CALCULATOR - Examples")
    print("="*80)
    
    # Example 1: Different sample sizes at same win rate
    print("\nExample 1: Win Rate 65% with varying sample sizes")
    print("-" * 60)
    for n in [30, 50, 75, 100, 150, 200]:
        ci = calculate_win_rate_ci(0.65, n)
        quality = interpret_confidence_width(ci.margin_of_error)
        print(f"n={n:3d}: {ci} | Range: {ci.format_range()} | {quality}")
    
    # Example 2: Different win rates at same sample size
    print("\nExample 2: Sample Size 100 with varying win rates")
    print("-" * 60)
    for wr in [0.50, 0.60, 0.70, 0.80, 0.90]:
        ci = calculate_win_rate_ci(wr, 100)
        print(f"WR={wr:.0%}: {ci} | Range: {ci.format_range()}")
    
    # Example 3: Required sample sizes
    print("\nExample 3: Required sample size for ±5% margin")
    print("-" * 60)
    for wr in [0.50, 0.60, 0.65, 0.70, 0.80]:
        n_required = sample_size_for_margin(wr, 0.05)
        print(f"Win Rate {wr:.0%}: Need {n_required} samples")
    
    # Example 4: Tier thresholds
    print("\nExample 4: Confidence at tier thresholds")
    print("-" * 60)
    tiers = [
        ("SECONDARY", 30),
        ("SECONDARY (mid)", 50),
        ("PRIMARY", 75),
        ("PRIMARY (mid)", 110),
        ("CORE", 150),
        ("CORE (high)", 200)
    ]
    
    for tier_name, n in tiers:
        ci = calculate_win_rate_ci(0.65, n)
        quality = interpret_confidence_width(ci.margin_of_error)
        print(f"{tier_name:20s} (n={n:3d}): {ci} | {quality}")
    
    print("\n" + "="*80)
