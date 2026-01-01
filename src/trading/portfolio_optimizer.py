"""
Portfolio Optimization - Kelly Criterion & Position Sizing

Renaissance principle: Never bet too much on any single pattern.
Use Kelly Criterion for optimal sizing.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PositionSize:
    """Recommended position size for a pattern."""
    pattern_id: str
    description: str
    full_kelly: float  # Full Kelly fraction (0-1)
    half_kelly: float  # Half Kelly (safer)
    quarter_kelly: float  # Quarter Kelly (very safe)
    expected_return: float  # Expected return per trade
    win_rate: float
    avg_win: float
    avg_loss: float
    recommendation: str  # 'full', 'half', 'quarter', or 'skip'


class PortfolioOptimizer:
    """
    Optimizes portfolio allocation using Kelly Criterion.
    
    The Kelly Criterion determines optimal bet size:
    f* = (p*b - q) / b
    
    Where:
    - f* = fraction of capital to bet
    - p = probability of winning
    - q = probability of losing (1-p)
    - b = ratio of win amount to loss amount
    
    Renaissance approach: Use fractional Kelly (0.25-0.5) for safety.
    """
    
    def __init__(
        self,
        max_position_size: float = 0.25,  # Never risk more than 25%
        kelly_fraction: float = 0.5,  # Use half-Kelly for safety
        min_edge: float = 0.001  # Minimum edge to trade (0.1%)
    ):
        """
        Initialize portfolio optimizer.
        
        Args:
            max_position_size: Maximum position size (fraction of capital)
            kelly_fraction: Fraction of Kelly to use (0.25-0.5 recommended)
            min_edge: Minimum statistical edge required
        """
        self.max_position_size = max_position_size
        self.kelly_fraction = kelly_fraction
        self.min_edge = min_edge
    
    def calculate_kelly(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly Criterion position size.
        
        Args:
            win_rate: Probability of winning (0-1)
            avg_win: Average winning return (%)
            avg_loss: Average losing return (%) - should be positive
            
        Returns:
            Optimal Kelly fraction (0-1)
        """
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
        
        p = win_rate
        q = 1 - win_rate
        b = avg_win / avg_loss  # Payoff ratio
        
        # Kelly formula: f* = (p*b - q) / b
        kelly = (p * b - q) / b
        
        # Clamp to valid range
        kelly = max(0.0, min(1.0, kelly))
        
        return kelly
    
    def calculate_position_sizes(
        self,
        patterns: List[Dict]
    ) -> List[PositionSize]:
        """
        Calculate optimal position sizes for all patterns.
        
        Args:
            patterns: List of pattern dicts with stats
            
        Returns:
            List of PositionSize recommendations
        """
        results = []
        
        for pattern in patterns:
            # Extract statistics
            win_rate = pattern.get('win_rate', 0.5)
            avg_return = pattern.get('overall_edge', 0.0)
            
            # Estimate avg win/loss from returns
            # Simplified: assume symmetric distribution
            volatility = pattern.get('volatility', abs(avg_return) * 2)
            avg_win = abs(avg_return) + volatility if avg_return > 0 else volatility
            avg_loss = volatility
            
            # Calculate Kelly
            full_kelly = self.calculate_kelly(win_rate, avg_win, avg_loss)
            
            # Apply fractional Kelly
            half_kelly = full_kelly * 0.5
            quarter_kelly = full_kelly * 0.25
            
            # Cap at max position size
            full_kelly = min(full_kelly, self.max_position_size)
            half_kelly = min(half_kelly, self.max_position_size)
            quarter_kelly = min(quarter_kelly, self.max_position_size)
            
            # Recommendation
            if avg_return < self.min_edge:
                recommendation = 'skip'
            elif full_kelly > 0.15:
                recommendation = 'quarter'  # Too risky, use quarter Kelly
            elif full_kelly > 0.05:
                recommendation = 'half'
            elif full_kelly > 0:
                recommendation = 'quarter'
            else:
                recommendation = 'skip'
            
            results.append(PositionSize(
                pattern_id=pattern.get('pattern_id', 'unknown'),
                description=pattern.get('description', 'Unknown pattern'),
                full_kelly=full_kelly,
                half_kelly=half_kelly,
                quarter_kelly=quarter_kelly,
                expected_return=avg_return,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                recommendation=recommendation
            ))
        
        return results
    
    def create_portfolio_allocation(
        self,
        position_sizes: List[PositionSize],
        total_capital: float = 100000
    ) -> str:
        """
        Create portfolio allocation report.
        
        Args:
            position_sizes: List of PositionSize objects
            total_capital: Total capital to allocate
            
        Returns:
            Formatted report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("PORTFOLIO OPTIMIZATION (Kelly Criterion)")
        lines.append("=" * 80)
        lines.append(f"Total Capital: ${total_capital:,.0f}")
        lines.append(f"Max Position: {self.max_position_size:.1%}")
        lines.append(f"Kelly Fraction: {self.kelly_fraction:.1%} (safer than full Kelly)")
        lines.append("")
        
        # Filter tradeable patterns
        tradeable = [ps for ps in position_sizes if ps.recommendation != 'skip']
        
        if not tradeable:
            lines.append("❌ No patterns meet minimum edge requirement.")
            return "\n".join(lines)
        
        lines.append(f"Tradeable Patterns: {len(tradeable)}")
        lines.append("")
        
        for i, ps in enumerate(tradeable, 1):
            kelly_to_use = {
                'full': ps.full_kelly,
                'half': ps.half_kelly,
                'quarter': ps.quarter_kelly
            }.get(ps.recommendation, ps.quarter_kelly)
            
            allocation = total_capital * kelly_to_use
            
            lines.append(f"{i}. {ps.description}")
            lines.append(f"   Expected edge: {ps.expected_return:+.2%}")
            lines.append(f"   Win rate: {ps.win_rate:.1%}")
            lines.append(f"   Full Kelly: {ps.full_kelly:.1%}")
            lines.append(f"   ✅ Recommendation: {ps.recommendation.upper()} KELLY")
            lines.append(f"   Position size: {kelly_to_use:.1%} = ${allocation:,.0f}")
            lines.append("")
        
        # Total allocation
        total_allocation = sum(
            total_capital * {
                'full': ps.full_kelly,
                'half': ps.half_kelly,
                'quarter': ps.quarter_kelly
            }.get(ps.recommendation, ps.quarter_kelly)
            for ps in tradeable
        )
        
        lines.append("-" * 80)
        lines.append(f"Total Allocated: ${total_allocation:,.0f} ({total_allocation/total_capital:.1%})")
        lines.append(f"Cash Reserve: ${total_capital - total_allocation:,.0f}")
        lines.append("")
        lines.append("⚠️ Renaissance principle: NEVER use full Kelly. Use 0.25-0.5x Kelly.")
        lines.append("⚠️ This protects against estimation errors and black swan events.")
        
        return "\n".join(lines)
