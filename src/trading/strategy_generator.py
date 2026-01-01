"""
Trading Strategy Generator - Regime-Filtered Execution

Jim Simons principle: Don't trade weak patterns in all conditions.
Only trade when regime is optimal.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ..analysis.regime_analyzer import RegimeStats


@dataclass
class TradingSignal:
    """A regime-filtered trading signal."""
    pattern_id: str
    timestamp: str
    direction: str  # "LONG", "SHORT", "NEUTRAL"
    confidence: float  # 0-1
    edge: float  # Expected edge in %
    regime: Dict[str, str]
    should_trade: bool
    reason: str


class TradingStrategyGenerator:
    """
    Generates actionable trading signals based on regime filtering.
    
    Philosophy:
    - Pattern edge +0.01% in all regimes = DON'T TRADE
    - Pattern edge +0.18% in high vol = TRADE
    - Combine multiple regime-specific edges
    """
    
    def __init__(
        self,
        min_edge_threshold: float = 0.10,  # Minimum 0.10% edge to trade
        min_regime_observations: int = 20,  # Need 20+ observations in regime
        transaction_cost: float = 0.02  # 0.02% per trade (realistic)
    ):
        """
        Initialize strategy generator.
        
        Args:
            min_edge_threshold: Minimum edge required to trade
            min_regime_observations: Minimum observations in regime
            transaction_cost: Cost per round-trip trade
        """
        self.min_edge_threshold = min_edge_threshold
        self.min_regime_observations = min_regime_observations
        self.transaction_cost = transaction_cost
    
    def generate_signal(
        self,
        pattern_id: str,
        pattern_edge: float,
        regime_stats: Dict[str, RegimeStats],
        current_regime: Dict[str, str],
        timestamp: str
    ) -> TradingSignal:
        """
        Generate trading signal with regime filtering.
        
        Args:
            pattern_id: ID of the pattern
            pattern_edge: Overall pattern edge
            regime_stats: Performance by regime
            current_regime: Current market regime
            timestamp: Current timestamp
            
        Returns:
            TradingSignal with trading decision
        """
        # Find regime-specific edge
        trend = current_regime.get('trend', 'unknown')
        vol = current_regime.get('volatility', 'unknown')
        
        # Get regime-specific performance
        trend_stat = regime_stats.get(trend)
        vol_stat = regime_stats.get(vol)
        
        # Calculate regime-adjusted edge
        regime_edges = []
        reasons = []
        
        if trend_stat and trend_stat.is_sufficient_data:
            regime_edges.append(trend_stat.mean_return * 100)  # Convert to %
            reasons.append(f"{trend}: {trend_stat.mean_return*100:+.2f}%")
        
        if vol_stat and vol_stat.is_sufficient_data:
            regime_edges.append(vol_stat.mean_return * 100)
            reasons.append(f"{vol}: {vol_stat.mean_return*100:+.2f}%")
        
        # Use maximum regime edge (conservative)
        if regime_edges:
            regime_edge = max(regime_edges)
        else:
            regime_edge = pattern_edge * 100  # Fallback to overall edge
        
        # Subtract transaction costs
        net_edge = regime_edge - self.transaction_cost
        
        # Trading decision
        should_trade = False
        direction = "NEUTRAL"
        confidence = 0.0
        
        if net_edge >= self.min_edge_threshold:
            should_trade = True
            direction = "LONG" if net_edge > 0 else "SHORT"
            
            # Confidence based on regime data quality
            n_obs = min(
                trend_stat.n_observations if trend_stat else 0,
                vol_stat.n_observations if vol_stat else 0
            )
            confidence = min(1.0, n_obs / 100)  # Scale to 0-1
            
            reason = f"✅ TRADE: Net edge {net_edge:.2f}% ({', '.join(reasons)})"
        else:
            reason = f"❌ SKIP: Net edge {net_edge:.2f}% < threshold {self.min_edge_threshold:.2f}%"
            if not regime_edges:
                reason += " (insufficient regime data)"
        
        return TradingSignal(
            pattern_id=pattern_id,
            timestamp=timestamp,
            direction=direction,
            confidence=confidence,
            edge=net_edge,
            regime=current_regime,
            should_trade=should_trade,
            reason=reason
        )
    
    def filter_tradeable_patterns(
        self,
        patterns_with_regimes: List[Dict]
    ) -> List[Dict]:
        """
        Filter patterns to only those worth trading.
        
        Args:
            patterns_with_regimes: List of patterns with regime analysis
            
        Returns:
            Filtered list of tradeable patterns
        """
        tradeable = []
        
        for pattern in patterns_with_regimes:
            regime_stats = pattern.get('regime_stats', {})
            
            # Check if ANY regime has sufficient edge
            max_edge = 0
            best_regime = None
            
            for regime_name, stats in regime_stats.items():
                if stats.is_sufficient_data:
                    edge = stats.mean_return * 100 - self.transaction_cost
                    if edge > max_edge:
                        max_edge = edge
                        best_regime = regime_name
            
            if max_edge >= self.min_edge_threshold:
                pattern['max_edge'] = max_edge
                pattern['best_regime'] = best_regime
                tradeable.append(pattern)
        
        return tradeable
    
    def create_strategy_report(
        self,
        tradeable_patterns: List[Dict]
    ) -> str:
        """
        Create a report of tradeable strategies.
        
        Args:
            tradeable_patterns: Patterns worth trading
            
        Returns:
            Formatted strategy report
        """
        if not tradeable_patterns:
            return "❌ Inga handelbara strategier hittades med nuvarande parametrar."
        
        lines = []
        lines.append("=" * 80)
        lines.append("HANDELBARA STRATEGIER (Renaissance-filtrerade)")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Hittade {len(tradeable_patterns)} strategier värda att handla")
        lines.append(f"Minimikriterier: Edge ≥ {self.min_edge_threshold:.2f}% efter kostnader")
        lines.append("")
        
        for i, pattern in enumerate(tradeable_patterns, 1):
            lines.append(f"{i}. {pattern['description']}")
            lines.append(f"   Max edge: {pattern['max_edge']:.2f}% i {pattern['best_regime']}")
            
            # Show all profitable regimes
            lines.append("   Handla endast när:")
            for regime, stats in pattern.get('regime_stats', {}).items():
                if stats.is_sufficient_data:
                    edge = stats.mean_return * 100 - self.transaction_cost
                    if edge >= self.min_edge_threshold:
                        lines.append(f"     • {regime}: {edge:+.2f}% edge ({stats.n_observations} obs)")
            lines.append("")
        
        return "\n".join(lines)
