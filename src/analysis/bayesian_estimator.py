"""
Bayesian Edge Estimation - Confidence Intervals for Small Samples

Renaissance principle: With small samples (N < 100), point estimates are unreliable.
Use Bayesian inference to quantify uncertainty.
"""

import numpy as np
from typing import Tuple, Dict
from dataclasses import dataclass
from scipy import stats


@dataclass
class BayesianEdgeEstimate:
    """Bayesian estimate of pattern edge with uncertainty."""
    point_estimate: float  # Mean edge
    credible_interval_95: Tuple[float, float]  # 95% credible interval
    credible_interval_68: Tuple[float, float]  # 68% credible interval (1σ)
    probability_positive: float  # P(edge > 0)
    probability_above_threshold: float  # P(edge > threshold)
    sample_size: int
    uncertainty_level: str  # 'high', 'medium', 'low'


class BayesianEdgeEstimator:
    """
    Estimates pattern edge using Bayesian inference.
    
    Approach:
    1. Use conjugate prior (normal distribution for returns)
    2. Update with observed data
    3. Compute posterior distribution
    4. Extract credible intervals
    
    This gives honest uncertainty quantification for small samples.
    """
    
    def __init__(
        self,
        prior_mean: float = 0.0,  # Assume no edge a priori
        prior_std: float = 0.01,  # 1% daily volatility
        min_threshold: float = 0.001  # 0.1% edge threshold
    ):
        """
        Initialize Bayesian estimator.
        
        Args:
            prior_mean: Prior belief about edge (typically 0)
            prior_std: Prior uncertainty (market volatility)
            min_threshold: Minimum edge to consider tradeable
        """
        self.prior_mean = prior_mean
        self.prior_std = prior_std
        self.min_threshold = min_threshold
    
    def estimate_edge(
        self,
        returns: np.ndarray,
        transaction_cost: float = 0.0002  # 0.02%
    ) -> BayesianEdgeEstimate:
        """
        Estimate edge with Bayesian inference.
        
        Args:
            returns: Historical returns array
            transaction_cost: Transaction cost to subtract
            
        Returns:
            BayesianEdgeEstimate with confidence intervals
        """
        n = len(returns)
        
        if n == 0:
            return BayesianEdgeEstimate(
                point_estimate=0.0,
                credible_interval_95=(0.0, 0.0),
                credible_interval_68=(0.0, 0.0),
                probability_positive=0.5,
                probability_above_threshold=0.0,
                sample_size=0,
                uncertainty_level='extreme'
            )
        
        # Observed statistics
        sample_mean = np.mean(returns)
        sample_std = np.std(returns, ddof=1) if n > 1 else self.prior_std
        
        # Bayesian update (normal-normal conjugate)
        # Posterior mean: weighted average of prior and sample
        prior_precision = 1 / (self.prior_std ** 2)
        sample_precision = n / (sample_std ** 2)
        
        posterior_precision = prior_precision + sample_precision
        posterior_mean = (prior_precision * self.prior_mean + sample_precision * sample_mean) / posterior_precision
        posterior_std = np.sqrt(1 / posterior_precision)
        
        # Credible intervals (Bayesian equivalent of confidence intervals)
        ci_95 = (
            posterior_mean - 1.96 * posterior_std,
            posterior_mean + 1.96 * posterior_std
        )
        
        ci_68 = (
            posterior_mean - 1.0 * posterior_std,
            posterior_mean + 1.0 * posterior_std
        )
        
        # Probability edge is positive
        prob_positive = 1 - stats.norm.cdf(0, loc=posterior_mean, scale=posterior_std)
        
        # Probability edge exceeds threshold (after costs)
        effective_threshold = self.min_threshold + transaction_cost
        prob_above_threshold = 1 - stats.norm.cdf(
            effective_threshold,
            loc=posterior_mean,
            scale=posterior_std
        )
        
        # Uncertainty level based on sample size and CI width
        ci_width = ci_95[1] - ci_95[0]
        if n < 30:
            uncertainty = 'high'
        elif n < 100:
            uncertainty = 'medium'
        else:
            uncertainty = 'low'
        
        return BayesianEdgeEstimate(
            point_estimate=posterior_mean,
            credible_interval_95=ci_95,
            credible_interval_68=ci_68,
            probability_positive=prob_positive,
            probability_above_threshold=prob_above_threshold,
            sample_size=n,
            uncertainty_level=uncertainty
        )
    
    def compare_patterns(
        self,
        pattern_a_returns: np.ndarray,
        pattern_b_returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Compare two patterns probabilistically.
        
        Args:
            pattern_a_returns: Returns for pattern A
            pattern_b_returns: Returns for pattern B
            
        Returns:
            Dictionary with comparison statistics
        """
        est_a = self.estimate_edge(pattern_a_returns)
        est_b = self.estimate_edge(pattern_b_returns)
        
        # Approximate probability A > B using normal approximation
        diff_mean = est_a.point_estimate - est_b.point_estimate
        
        # Variance of difference (assuming independence)
        var_a = ((est_a.credible_interval_95[1] - est_a.credible_interval_95[0]) / 3.92) ** 2
        var_b = ((est_b.credible_interval_95[1] - est_b.credible_interval_95[0]) / 3.92) ** 2
        diff_std = np.sqrt(var_a + var_b)
        
        prob_a_better = 1 - stats.norm.cdf(0, loc=diff_mean, scale=diff_std)
        
        return {
            'pattern_a_edge': est_a.point_estimate,
            'pattern_b_edge': est_b.point_estimate,
            'edge_difference': diff_mean,
            'probability_a_better': prob_a_better,
            'confidence': 'high' if prob_a_better > 0.95 or prob_a_better < 0.05 else 'low'
        }
    
    def create_uncertainty_report(
        self,
        estimate: BayesianEdgeEstimate,
        pattern_name: str = "Pattern"
    ) -> str:
        """
        Create report showing uncertainty quantification.
        
        Args:
            estimate: BayesianEdgeEstimate object
            pattern_name: Name of pattern
            
        Returns:
            Formatted report
        """
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append(f"BAYESIAN UNCERTAINTY ANALYSIS: {pattern_name}")
        lines.append("=" * 80)
        lines.append(f"Sample Size: {estimate.sample_size} observations")
        lines.append(f"Uncertainty Level: {estimate.uncertainty_level.upper()}")
        lines.append("")
        
        # Point estimate
        lines.append(f"Point Estimate: {estimate.point_estimate:+.3%}")
        lines.append("")
        
        # Credible intervals
        lines.append("Credible Intervals:")
        lines.append(f"  68% (1σ): [{estimate.credible_interval_68[0]:+.3%}, {estimate.credible_interval_68[1]:+.3%}]")
        lines.append(f"  95% (2σ): [{estimate.credible_interval_95[0]:+.3%}, {estimate.credible_interval_95[1]:+.3%}]")
        lines.append("")
        
        # Probabilities
        lines.append("Probabilities:")
        lines.append(f"  P(edge > 0): {estimate.probability_positive:.1%}")
        lines.append(f"  P(edge > {self.min_threshold:.2%}): {estimate.probability_above_threshold:.1%}")
        lines.append("")
        
        # Interpretation
        ci_width = estimate.credible_interval_95[1] - estimate.credible_interval_95[0]
        lines.append("Interpretation:")
        
        if estimate.sample_size < 30:
            lines.append(f"  ⚠️ SMALL SAMPLE WARNING: Only {estimate.sample_size} observations!")
            lines.append(f"  ⚠️ True edge could be anywhere in [{estimate.credible_interval_95[0]:+.3%}, {estimate.credible_interval_95[1]:+.3%}]")
            lines.append(f"  ⚠️ CI width: {ci_width:.3%} (very uncertain)")
        elif estimate.sample_size < 100:
            lines.append(f"  📊 MODERATE SAMPLE: {estimate.sample_size} observations")
            lines.append(f"  📊 Edge estimate is somewhat reliable but CI is still wide ({ci_width:.3%})")
        else:
            lines.append(f"  ✅ LARGE SAMPLE: {estimate.sample_size} observations")
            lines.append(f"  ✅ Edge estimate is reliable with narrow CI ({ci_width:.3%})")
        
        lines.append("")
        
        # Trading recommendation
        if estimate.probability_above_threshold < 0.50:
            lines.append("❌ RECOMMENDATION: DO NOT TRADE")
            lines.append(f"   Less than 50% probability edge exceeds threshold after costs")
        elif estimate.probability_above_threshold < 0.75:
            lines.append("⚠️ RECOMMENDATION: TRADE WITH CAUTION")
            lines.append(f"   {estimate.probability_above_threshold:.0%} probability edge is real")
            lines.append(f"   Use fractional Kelly (0.25x) due to uncertainty")
        else:
            lines.append("✅ RECOMMENDATION: PATTERN LOOKS REAL")
            lines.append(f"   {estimate.probability_above_threshold:.0%} probability edge exceeds threshold")
            lines.append(f"   Standard Kelly sizing appropriate")
        
        lines.append("")
        lines.append("⚠️ Renaissance principle: With small samples, be honest about uncertainty.")
        lines.append("⚠️ Point estimates lie. Always show confidence intervals.")
        
        return "\n".join(lines)
