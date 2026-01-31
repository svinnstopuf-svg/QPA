"""
Momentum Pattern Statistical Analyzer

Similar to robust_statistics.py but optimized for momentum patterns.

Key differences from mean reversion:
- Higher expected win rates (60-75% vs 50-60%)
- Different risk/reward profiles (2-5R vs 3-6R)
- Shorter holding periods (10-30 days vs 21-63 days)
- Different Bayesian priors

Statistical Validation:
1. Bayesian Win Rate Adjustment
2. Bootstrap Resampling (1000 simulations)
3. P-Value Statistical Significance
4. Return Consistency (Sharpe-like)
5. Sample Size Confidence Factor
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats


@dataclass
class MomentumStatistics:
    """Statistical analysis of momentum pattern"""
    pattern_name: str
    
    # Raw metrics
    sample_size: int
    win_rate_raw: float
    avg_win: float
    avg_loss: float
    expected_value_raw: float
    
    # Adjusted metrics (Bayesian)
    win_rate_adjusted: float
    bayesian_edge: float  # Difference from prior
    
    # Bootstrap results
    bootstrap_ev_mean: float
    bootstrap_ev_std: float
    bootstrap_pass_rate: float  # % of simulations with EV > 0
    bootstrap_confidence_95: Tuple[float, float]  # 95% CI
    
    # Statistical significance
    p_value: float
    is_significant: bool  # p < 0.05
    
    # Consistency
    return_consistency: float  # Sharpe-like ratio
    max_drawdown: float
    
    # Confidence
    sample_size_factor: float  # 0-1, confidence in sample size
    overall_confidence: float  # Combined confidence score
    
    # Risk metrics
    risk_reward_ratio: float
    profit_factor: float
    
    # Final score
    momentum_score: float  # 0-100, combined quality


class MomentumStatisticsAnalyzer:
    """
    Analyze momentum pattern statistics with Bayesian adjustment.
    
    Momentum-specific priors (different from mean reversion):
    - Expected win rate: 65% (vs 55% for mean reversion)
    - Expected RRR: 3.0 (vs 4.0 for mean reversion)
    - Confidence threshold: Higher (momentum is riskier)
    """
    
    def __init__(
        self,
        prior_win_rate: float = 0.65,  # Momentum typically 60-75%
        prior_confidence: float = 10,   # Equivalent to 10 trades
        min_sample_size: int = 20,      # Need more samples for momentum
        bootstrap_simulations: int = 1000
    ):
        self.prior_win_rate = prior_win_rate
        self.prior_confidence = prior_confidence
        self.min_sample_size = min_sample_size
        self.bootstrap_simulations = bootstrap_simulations
    
    def calculate_bayesian_win_rate(
        self,
        observed_wins: int,
        observed_total: int
    ) -> Tuple[float, float]:
        """
        Calculate Bayesian-adjusted win rate.
        
        Uses Beta distribution with momentum-specific prior.
        
        Returns:
            (adjusted_win_rate, bayesian_edge)
        """
        if observed_total == 0:
            return self.prior_win_rate, 0.0
        
        # Beta distribution parameters
        alpha_prior = self.prior_win_rate * self.prior_confidence
        beta_prior = (1 - self.prior_win_rate) * self.prior_confidence
        
        # Posterior parameters
        alpha_posterior = alpha_prior + observed_wins
        beta_posterior = beta_prior + (observed_total - observed_wins)
        
        # Posterior mean (adjusted win rate)
        adjusted_wr = alpha_posterior / (alpha_posterior + beta_posterior)
        
        # Bayesian edge (how much better than prior)
        bayesian_edge = adjusted_wr - self.prior_win_rate
        
        return adjusted_wr, bayesian_edge
    
    def bootstrap_resample(
        self,
        returns: np.ndarray,
        n_simulations: int = 1000
    ) -> Tuple[float, float, float, Tuple[float, float]]:
        """
        Bootstrap resampling to estimate EV distribution.
        
        Returns:
            (mean_ev, std_ev, pass_rate, confidence_interval_95)
        """
        if len(returns) == 0:
            return 0.0, 0.0, 0.0, (0.0, 0.0)
        
        bootstrap_evs = []
        
        for _ in range(n_simulations):
            # Resample with replacement
            sample = np.random.choice(returns, size=len(returns), replace=True)
            ev = np.mean(sample)
            bootstrap_evs.append(ev)
        
        bootstrap_evs = np.array(bootstrap_evs)
        
        # Statistics
        mean_ev = np.mean(bootstrap_evs)
        std_ev = np.std(bootstrap_evs)
        pass_rate = np.sum(bootstrap_evs > 0) / n_simulations
        
        # 95% confidence interval
        ci_lower = np.percentile(bootstrap_evs, 2.5)
        ci_upper = np.percentile(bootstrap_evs, 97.5)
        
        return mean_ev, std_ev, pass_rate, (ci_lower, ci_upper)
    
    def calculate_p_value(
        self,
        returns: np.ndarray
    ) -> float:
        """
        Calculate p-value for statistical significance.
        
        H0: True mean return = 0 (no edge)
        H1: True mean return > 0 (positive edge)
        
        Returns:
            p-value (lower is better, <0.05 = significant)
        """
        if len(returns) < 2:
            return 1.0
        
        # One-sample t-test (one-tailed)
        t_stat, p_value = stats.ttest_1samp(returns, 0.0, alternative='greater')
        
        return p_value
    
    def calculate_return_consistency(
        self,
        returns: np.ndarray
    ) -> float:
        """
        Calculate return consistency (Sharpe-like ratio).
        
        Higher = more consistent returns
        
        Returns:
            Consistency ratio
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        consistency = mean_return / std_return
        
        return consistency
    
    def calculate_sample_size_factor(
        self,
        sample_size: int
    ) -> float:
        """
        Calculate confidence factor based on sample size.
        
        Momentum requires more samples than mean reversion.
        
        Returns:
            0-1 confidence factor
        """
        if sample_size < 10:
            return 0.3
        elif sample_size < 20:
            return 0.5 + (sample_size - 10) * 0.03  # 0.5-0.8
        elif sample_size < 50:
            return 0.8 + (sample_size - 20) * 0.006  # 0.8-0.98
        else:
            return 1.0
    
    def calculate_max_drawdown(
        self,
        returns: np.ndarray
    ) -> float:
        """
        Calculate maximum drawdown.
        
        Returns:
            Max drawdown as decimal (e.g., -0.15 for -15%)
        """
        if len(returns) == 0:
            return 0.0
        
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_dd = np.min(drawdown)
        
        return max_dd
    
    def analyze_pattern(
        self,
        pattern_name: str,
        forward_returns: np.ndarray
    ) -> MomentumStatistics:
        """
        Complete statistical analysis of momentum pattern.
        
        Args:
            pattern_name: Name of pattern (e.g., "Cup & Handle")
            forward_returns: Array of forward returns (10-30 day exits)
        
        Returns:
            MomentumStatistics with full analysis
        """
        if len(forward_returns) == 0:
            # Return empty stats
            return self._create_empty_stats(pattern_name)
        
        sample_size = len(forward_returns)
        
        # Raw metrics
        wins = np.sum(forward_returns > 0)
        losses = np.sum(forward_returns <= 0)
        
        win_rate_raw = wins / sample_size if sample_size > 0 else 0.0
        
        winning_returns = forward_returns[forward_returns > 0]
        losing_returns = forward_returns[forward_returns <= 0]
        
        avg_win = np.mean(winning_returns) if len(winning_returns) > 0 else 0.0
        avg_loss = np.mean(losing_returns) if len(losing_returns) > 0 else 0.0
        
        expected_value_raw = np.mean(forward_returns)
        
        # Bayesian adjustment
        win_rate_adjusted, bayesian_edge = self.calculate_bayesian_win_rate(
            wins, sample_size
        )
        
        # Bootstrap
        bs_mean, bs_std, bs_pass_rate, bs_ci = self.bootstrap_resample(
            forward_returns,
            self.bootstrap_simulations
        )
        
        # Statistical significance
        p_value = self.calculate_p_value(forward_returns)
        is_significant = p_value < 0.05
        
        # Consistency
        return_consistency = self.calculate_return_consistency(forward_returns)
        max_drawdown = self.calculate_max_drawdown(forward_returns)
        
        # Sample size confidence
        sample_size_factor = self.calculate_sample_size_factor(sample_size)
        
        # Overall confidence (combination of factors)
        overall_confidence = min(1.0, (
            sample_size_factor * 0.4 +
            bs_pass_rate * 0.3 +
            (1.0 if is_significant else 0.5) * 0.3
        ))
        
        # Risk metrics
        risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
        
        total_wins = np.sum(winning_returns)
        total_losses = abs(np.sum(losing_returns))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        # Momentum Score (0-100)
        momentum_score = self._calculate_momentum_score(
            win_rate_adjusted,
            risk_reward_ratio,
            expected_value_raw,
            bs_pass_rate,
            is_significant,
            sample_size_factor,
            return_consistency
        )
        
        return MomentumStatistics(
            pattern_name=pattern_name,
            sample_size=sample_size,
            win_rate_raw=win_rate_raw,
            avg_win=avg_win,
            avg_loss=avg_loss,
            expected_value_raw=expected_value_raw,
            win_rate_adjusted=win_rate_adjusted,
            bayesian_edge=bayesian_edge,
            bootstrap_ev_mean=bs_mean,
            bootstrap_ev_std=bs_std,
            bootstrap_pass_rate=bs_pass_rate,
            bootstrap_confidence_95=bs_ci,
            p_value=p_value,
            is_significant=is_significant,
            return_consistency=return_consistency,
            max_drawdown=max_drawdown,
            sample_size_factor=sample_size_factor,
            overall_confidence=overall_confidence,
            risk_reward_ratio=risk_reward_ratio,
            profit_factor=profit_factor,
            momentum_score=momentum_score
        )
    
    def _calculate_momentum_score(
        self,
        win_rate: float,
        rrr: float,
        ev: float,
        bootstrap_pass: float,
        is_significant: bool,
        sample_factor: float,
        consistency: float
    ) -> float:
        """
        Calculate overall momentum quality score (0-100).
        
        Weights:
        - Win Rate: 25%
        - RRR: 20%
        - EV: 20%
        - Bootstrap: 15%
        - Significance: 10%
        - Sample Size: 5%
        - Consistency: 5%
        """
        # Win rate component (target: 65%)
        wr_score = min(100, (win_rate / 0.65) * 100) * 0.25
        
        # RRR component (target: 3.0)
        rrr_score = min(100, (rrr / 3.0) * 100) * 0.20
        
        # EV component (target: 10%)
        ev_score = min(100, (ev / 0.10) * 100 * 2) * 0.20  # 5% EV = 100pts
        
        # Bootstrap component
        bs_score = bootstrap_pass * 100 * 0.15
        
        # Significance component
        sig_score = (100 if is_significant else 50) * 0.10
        
        # Sample size component
        sample_score = sample_factor * 100 * 0.05
        
        # Consistency component (normalize to 0-100)
        cons_score = min(100, max(0, (consistency + 1) * 50)) * 0.05
        
        total_score = (
            wr_score + rrr_score + ev_score + bs_score + 
            sig_score + sample_score + cons_score
        )
        
        return min(100, max(0, total_score))
    
    def _create_empty_stats(self, pattern_name: str) -> MomentumStatistics:
        """Create empty statistics object"""
        return MomentumStatistics(
            pattern_name=pattern_name,
            sample_size=0,
            win_rate_raw=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            expected_value_raw=0.0,
            win_rate_adjusted=self.prior_win_rate,
            bayesian_edge=0.0,
            bootstrap_ev_mean=0.0,
            bootstrap_ev_std=0.0,
            bootstrap_pass_rate=0.0,
            bootstrap_confidence_95=(0.0, 0.0),
            p_value=1.0,
            is_significant=False,
            return_consistency=0.0,
            max_drawdown=0.0,
            sample_size_factor=0.0,
            overall_confidence=0.0,
            risk_reward_ratio=0.0,
            profit_factor=0.0,
            momentum_score=0.0
        )


def format_momentum_stats(stats: MomentumStatistics) -> str:
    """Format momentum statistics report"""
    lines = []
    
    lines.append("="*80)
    lines.append(f"MOMENTUM STATISTICS: {stats.pattern_name}")
    lines.append("="*80)
    
    lines.append(f"\nSAMPLE:")
    lines.append(f"  Trades: {stats.sample_size}")
    lines.append(f"  Confidence: {stats.sample_size_factor*100:.0f}%")
    
    lines.append(f"\nPERFORMANCE:")
    lines.append(f"  Win Rate (Raw): {stats.win_rate_raw*100:.1f}%")
    lines.append(f"  Win Rate (Bayesian): {stats.win_rate_adjusted*100:.1f}%")
    lines.append(f"  Bayesian Edge: {stats.bayesian_edge*100:+.1f}%")
    lines.append(f"  Avg Win: {stats.avg_win*100:+.1f}%")
    lines.append(f"  Avg Loss: {stats.avg_loss*100:+.1f}%")
    lines.append(f"  Risk/Reward: 1:{stats.risk_reward_ratio:.2f}")
    
    lines.append(f"\nEXPECTED VALUE:")
    lines.append(f"  EV (Raw): {stats.expected_value_raw*100:+.1f}%")
    lines.append(f"  EV (Bootstrap): {stats.bootstrap_ev_mean*100:+.1f}% ± {stats.bootstrap_ev_std*100:.1f}%")
    lines.append(f"  95% CI: [{stats.bootstrap_confidence_95[0]*100:.1f}%, {stats.bootstrap_confidence_95[1]*100:.1f}%]")
    
    lines.append(f"\nSTATISTICAL VALIDATION:")
    lines.append(f"  Bootstrap Pass Rate: {stats.bootstrap_pass_rate*100:.1f}%")
    sig_marker = "✓" if stats.is_significant else "✗"
    lines.append(f"  P-Value: {sig_marker} {stats.p_value:.4f} ({'significant' if stats.is_significant else 'not significant'})")
    lines.append(f"  Return Consistency: {stats.return_consistency:.2f}")
    lines.append(f"  Max Drawdown: {stats.max_drawdown*100:.1f}%")
    
    lines.append(f"\nRISK METRICS:")
    lines.append(f"  Profit Factor: {stats.profit_factor:.2f}")
    
    lines.append(f"\nMOMENTUM SCORE: {stats.momentum_score:.1f}/100")
    if stats.momentum_score >= 80:
        quality = "EXCELLENT"
    elif stats.momentum_score >= 60:
        quality = "GOOD"
    elif stats.momentum_score >= 40:
        quality = "ACCEPTABLE"
    else:
        quality = "POOR"
    lines.append(f"  Quality: {quality}")
    
    lines.append(f"\nOVERALL CONFIDENCE: {stats.overall_confidence*100:.0f}%")
    
    return "\n".join(lines)
