"""
Pattern Combiner - Intelligent Multi-Signal Aggregation

Jim Simons approach: Combine many weak signals with proper weighting.
Not naive summation - account for correlation and regime.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CombinedSignal:
    """Combined signal from multiple patterns."""
    combined_edge: float  # Aggregate edge
    confidence: float  # 0-1
    contributing_patterns: List[Dict]
    regime_adjusted: bool
    correlation_penalty: float
    recommendation: str


class PatternCombiner:
    """
    Combines multiple weak patterns into stronger aggregate signals.
    
    Renaissance principle: 
    - 10 patterns × 0.01% edge each ≠ 0.10% edge
    - Must account for correlation
    - Weight by regime performance
    - Penalize overlapping signals
    """
    
    def __init__(
        self,
        correlation_penalty: float = 0.5,  # Reduce edge by 50% if correlated
        min_patterns: int = 2,  # Need at least 2 patterns
        max_patterns: int = 10  # Cap at 10 to avoid overfitting
    ):
        """
        Initialize pattern combiner.
        
        Args:
            correlation_penalty: How much to reduce edge for correlation
            min_patterns: Minimum patterns to combine
            max_patterns: Maximum patterns to combine
        """
        self.correlation_penalty = correlation_penalty
        self.min_patterns = min_patterns
        self.max_patterns = max_patterns
    
    def combine_patterns(
        self,
        tradeable_patterns: List[Dict],
        current_regime: Dict[str, str],
        correlation_matrix: Optional[np.ndarray] = None
    ) -> CombinedSignal:
        """
        Combine multiple patterns into aggregate signal.
        
        Args:
            tradeable_patterns: List of tradeable patterns with regime stats
            current_regime: Current market regime
            correlation_matrix: Optional correlation between patterns
            
        Returns:
            CombinedSignal with aggregate edge
        """
        if len(tradeable_patterns) == 0:
            return CombinedSignal(
                combined_edge=0.0,
                confidence=0.0,
                contributing_patterns=[],
                regime_adjusted=False,
                correlation_penalty=0.0,
                recommendation="No tradeable patterns available"
            )
        
        # Select patterns active in current regime
        active_patterns = []
        for pattern in tradeable_patterns[:self.max_patterns]:
            regime_stats = pattern.get('regime_stats', {})
            
            # Check if pattern works in current regime
            trend = current_regime.get('trend', 'unknown')
            vol = current_regime.get('volatility', 'unknown')
            
            # Try to find best regime match (trend first, then vol, then overall)
            best_edge = 0.0
            best_regime = None
            best_obs = 0
            
            # Check trend regime
            trend_stat = regime_stats.get(trend)
            if trend_stat and hasattr(trend_stat, 'mean_return'):
                edge = trend_stat.mean_return * 100
                if edge > best_edge:
                    best_edge = edge
                    best_regime = trend
                    best_obs = trend_stat.n_observations
            
            # Check vol regime
            vol_stat = regime_stats.get(vol)
            if vol_stat and hasattr(vol_stat, 'mean_return'):
                edge = vol_stat.mean_return * 100
                if edge > best_edge:
                    best_edge = edge
                    best_regime = vol
                    best_obs = vol_stat.n_observations
            
            # If no regime match, use overall edge
            if best_edge == 0.0:
                overall_edge = pattern.get('overall_edge', 0.0)
                if isinstance(overall_edge, float):
                    best_edge = overall_edge * 100
                    best_regime = 'overall'
                    best_obs = pattern.get('observations', 0)
            
            # Add if edge is meaningful (>0.01%)
            if best_edge > 0.01:
                active_patterns.append({
                    'pattern': pattern,
                    'edge': best_edge,
                    'regime': best_regime,
                    'weight': max(1.0, best_obs / 100)  # Weight by data, min 1.0
                })
        
        if not active_patterns:
            return CombinedSignal(
                combined_edge=0.0,
                confidence=0.0,
                contributing_patterns=[],
                regime_adjusted=True,
                correlation_penalty=0.0,
                recommendation="No patterns active in current regime"
            )
        
        # Calculate weighted average edge
        total_weight = sum(p['weight'] for p in active_patterns)
        weighted_edge = sum(p['edge'] * p['weight'] for p in active_patterns) / total_weight
        
        # Apply correlation penalty
        # Assume moderate correlation if not provided
        if correlation_matrix is None:
            # Heuristic: More patterns = more correlation
            correlation_factor = 1.0 - (len(active_patterns) - 1) * 0.1
            correlation_factor = max(0.5, correlation_factor)  # Max 50% penalty
        else:
            # Use actual correlation matrix
            avg_correlation = np.mean(correlation_matrix)
            correlation_factor = 1.0 - (avg_correlation * self.correlation_penalty)
        
        # Adjusted edge
        adjusted_edge = weighted_edge * correlation_factor
        correlation_penalty_pct = (1.0 - correlation_factor) * 100
        
        # Confidence based on number and quality of patterns
        confidence = min(1.0, len(active_patterns) / 5.0)  # Scale 0-1
        
        # Recommendation
        if adjusted_edge >= 0.15:
            recommendation = f"✅ STRONG: {adjusted_edge:.2f}% aggregate edge - Worth trading"
        elif adjusted_edge >= 0.10:
            recommendation = f"✅ MODERATE: {adjusted_edge:.2f}% aggregate edge - Consider trading"
        elif adjusted_edge >= 0.05:
            recommendation = f"⚠️ WEAK: {adjusted_edge:.2f}% aggregate edge - Monitor only"
        else:
            recommendation = f"❌ TOO WEAK: {adjusted_edge:.2f}% aggregate edge - Skip"
        
        return CombinedSignal(
            combined_edge=adjusted_edge,
            confidence=confidence,
            contributing_patterns=active_patterns,
            regime_adjusted=True,
            correlation_penalty=correlation_penalty_pct,
            recommendation=recommendation
        )
    
    def create_combination_report(
        self,
        combined_signal: CombinedSignal
    ) -> str:
        """
        Create report for combined signal.
        
        Args:
            combined_signal: Result from combine_patterns
            
        Returns:
            Formatted report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("KOMBINERAD STRATEGI (Multi-Pattern Aggregation)")
        lines.append("=" * 80)
        lines.append("")
        
        if not combined_signal.contributing_patterns:
            lines.append(combined_signal.recommendation)
            return "\n".join(lines)
        
        lines.append(f"Antal kombinerade mönster: {len(combined_signal.contributing_patterns)}")
        lines.append(f"Aggregerad edge: {combined_signal.combined_edge:.2f}%")
        lines.append(f"Korrelationsstraff: -{combined_signal.correlation_penalty:.1f}%")
        lines.append(f"Konfidensgrad: {combined_signal.confidence*100:.0f}%")
        lines.append("")
        lines.append(combined_signal.recommendation)
        lines.append("")
        
        lines.append("Bidragande mönster:")
        for i, p in enumerate(combined_signal.contributing_patterns, 1):
            pattern = p['pattern']
            lines.append(f"  {i}. {pattern['description']}")
            lines.append(f"     Edge: {p['edge']:.2f}% i {p['regime']}")
            lines.append(f"     Vikt: {p['weight']:.2f}")
        
        lines.append("")
        lines.append("💡 Renaissance-princip:")
        lines.append("   Flera svaga signaler → stark aggregerad signal")
        lines.append("   Men: Korrelationsstraff förhindrar överdriven optimism")
        
        return "\n".join(lines)
    
    def estimate_annual_return(
        self,
        combined_edge: float,
        trades_per_year: int,
        transaction_cost: float = 0.02
    ) -> Dict[str, float]:
        """
        Estimate annual return from combined strategy.
        
        Args:
            combined_edge: Edge per trade (%)
            trades_per_year: Expected number of trades
            transaction_cost: Cost per trade (%)
            
        Returns:
            Dictionary with return estimates
        """
        net_edge = combined_edge - transaction_cost
        
        # Simple compounding (conservative)
        annual_return = net_edge * trades_per_year
        
        # With leverage (if appropriate)
        leveraged_1_5x = annual_return * 1.5
        leveraged_2x = annual_return * 2.0
        
        return {
            'unleveraged': annual_return,
            'leveraged_1_5x': leveraged_1_5x,
            'leveraged_2x': leveraged_2x,
            'edge_per_trade': net_edge,
            'trades_per_year': trades_per_year
        }
