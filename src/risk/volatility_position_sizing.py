"""
Volatility-Adjusted Position Sizing (V-Kelly)

Risk Parity approach: Adjust position size based on instrument volatility.
1% in a stable bond (BND) ≠ 1% in a volatile stock (SBB)

Uses Average True Range (ATR) to normalize risk across instruments.
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class PositionSize:
    """Position sizing recommendation."""
    base_allocation: float  # From traffic light (3-5%, 1-3%, etc)
    volatility_adjusted: float  # After ATR adjustment
    atr_percentile: float  # Where this instrument ranks in volatility
    risk_units: float  # Normalized risk units
    recommendation: str  # "FULL", "REDUCED", "MINIMAL"


class VolatilityPositionSizer:
    """
    Adjusts position sizes based on instrument volatility.
    
    Philosophy:
    - High volatility instruments get smaller positions
    - Low volatility instruments can take larger positions
    - Maintains equal risk across positions (Risk Parity)
    
    Example:
    - BND (stable bond, ATR 0.5%): Can allocate 5%
    - SBB (volatile stock, ATR 3%): Only allocate 0.8%
    - Both contribute ~same portfolio risk
    """
    
    def __init__(
        self,
        target_volatility: float = 1.0,  # Target 1% volatility per position
        max_position: float = 0.05,  # Max 5% per position
        min_position: float = 0.001  # Min 0.1% per position
    ):
        """
        Initialize volatility position sizer.
        
        Args:
            target_volatility: Target volatility per position (%)
            max_position: Maximum position size (%)
            min_position: Minimum position size (%)
        """
        self.target_volatility = target_volatility
        self.max_position = max_position
        self.min_position = min_position
    
    def calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Calculate Average True Range (ATR).
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period (default 14)
            
        Returns:
            ATR values
        """
        # True Range components
        tr1 = high[1:] - low[1:]  # High - Low
        tr2 = np.abs(high[1:] - close[:-1])  # |High - Previous Close|
        tr3 = np.abs(low[1:] - close[:-1])  # |Low - Previous Close|
        
        # True Range = max of the three
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # ATR = exponential moving average of TR
        atr = np.zeros(len(close))
        if len(tr) >= period:
            atr[period] = np.mean(tr[:period])
            
            # Exponential smoothing
            multiplier = 1.0 / period
            for i in range(period + 1, len(atr)):
                atr[i] = atr[i-1] + multiplier * (tr[i-1] - atr[i-1])
        
        return atr
    
    def calculate_atr_percent(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> float:
        """
        Calculate current ATR as percentage of price.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            
        Returns:
            Current ATR as percentage
        """
        atr = self.calculate_atr(high, low, close, period)
        current_atr = atr[-1]
        current_price = close[-1]
        
        if current_price > 0:
            atr_percent = (current_atr / current_price) * 100
        else:
            atr_percent = 0
        
        return atr_percent
    
    def adjust_position_size(
        self,
        base_allocation: float,
        atr_percent: float,
        signal_strength: str = "YELLOW"
    ) -> PositionSize:
        """
        Adjust position size based on volatility.
        
        Args:
            base_allocation: Base allocation from traffic light (%)
            atr_percent: ATR as percentage of price
            signal_strength: Signal strength (GREEN/YELLOW/ORANGE/RED)
            
        Returns:
            PositionSize with adjusted allocation
        """
        # Calculate risk units (how much risk per 1% position)
        # Higher ATR = more risk per 1%
        risk_per_percent = atr_percent / 100
        
        # Calculate position size for target volatility
        # target_vol = position_size * atr_percent
        # position_size = target_vol / atr_percent
        if atr_percent > 0:
            volatility_adjusted = (self.target_volatility / atr_percent) * 100
        else:
            volatility_adjusted = base_allocation
        
        # Cap at base allocation (don't increase beyond traffic light recommendation)
        volatility_adjusted = min(volatility_adjusted, base_allocation)
        
        # Apply floor and ceiling
        volatility_adjusted = max(self.min_position, min(self.max_position, volatility_adjusted))
        
        # Determine ATR percentile (rough estimate)
        # Typical ranges: Low <1%, Medium 1-2%, High 2-3%, Very High >3%
        if atr_percent < 1.0:
            atr_percentile = 25  # Low volatility
            recommendation = "FULL"
        elif atr_percent < 2.0:
            atr_percentile = 50  # Medium volatility
            recommendation = "FULL" if signal_strength == "GREEN" else "REDUCED"
        elif atr_percent < 3.0:
            atr_percentile = 75  # High volatility
            recommendation = "REDUCED"
        else:
            atr_percentile = 90  # Very high volatility
            recommendation = "MINIMAL"
        
        # Calculate risk units (normalized risk contribution)
        risk_units = volatility_adjusted * atr_percent / 100
        
        return PositionSize(
            base_allocation=base_allocation,
            volatility_adjusted=volatility_adjusted,
            atr_percentile=atr_percentile,
            risk_units=risk_units,
            recommendation=recommendation
        )
    
    def batch_adjust_positions(
        self,
        instruments_data: Dict[str, Dict]
    ) -> Dict[str, PositionSize]:
        """
        Adjust positions for multiple instruments to achieve risk parity.
        
        Args:
            instruments_data: Dict mapping ticker to data dict with:
                - high: High prices
                - low: Low prices
                - close: Close prices
                - base_allocation: Base allocation (%)
                - signal: Signal strength
                
        Returns:
            Dict mapping ticker to PositionSize
        """
        results = {}
        
        for ticker, data in instruments_data.items():
            # Calculate ATR
            atr_percent = self.calculate_atr_percent(
                high=data['high'],
                low=data['low'],
                close=data['close']
            )
            
            # Adjust position
            position = self.adjust_position_size(
                base_allocation=data.get('base_allocation', 2.0),
                atr_percent=atr_percent,
                signal_strength=data.get('signal', 'YELLOW')
            )
            
            results[ticker] = position
        
        return results
    
    def normalize_portfolio_risk(
        self,
        positions: Dict[str, PositionSize],
        total_capital: float = 100000,
        target_portfolio_vol: float = 10.0
    ) -> Dict[str, float]:
        """
        Normalize portfolio to target total volatility.
        
        Args:
            positions: Dict of position sizes
            total_capital: Total capital (SEK)
            target_portfolio_vol: Target portfolio volatility (%)
            
        Returns:
            Dict mapping ticker to capital allocation (SEK)
        """
        # Calculate total risk units
        total_risk = sum(pos.risk_units for pos in positions.values())
        
        if total_risk == 0:
            return {ticker: 0 for ticker in positions.keys()}
        
        # Scale factor to achieve target portfolio volatility
        # Assuming uncorrelated positions (conservative)
        n_positions = len(positions)
        diversification_benefit = np.sqrt(n_positions)  # Simple model
        
        actual_portfolio_vol = total_risk / diversification_benefit * 100
        
        if actual_portfolio_vol > 0:
            scale_factor = target_portfolio_vol / actual_portfolio_vol
        else:
            scale_factor = 1.0
        
        # Allocate capital
        allocations = {}
        for ticker, pos in positions.items():
            scaled_allocation = pos.volatility_adjusted * scale_factor
            scaled_allocation = max(self.min_position, min(self.max_position, scaled_allocation))
            allocations[ticker] = total_capital * scaled_allocation
        
        return allocations


def format_position_report(positions: Dict[str, PositionSize]) -> str:
    """Format position sizing report."""
    lines = []
    lines.append("=" * 80)
    lines.append("VOLATILITETSJUSTERAD POSITION SIZING (V-KELLY)")
    lines.append("=" * 80)
    lines.append("")
    
    # Sort by volatility adjusted size
    sorted_positions = sorted(
        positions.items(),
        key=lambda x: x[1].volatility_adjusted,
        reverse=True
    )
    
    lines.append(f"{'Ticker':<10} {'Base':<8} {'Adjusted':<10} {'ATR%':<8} {'Risk':<8} {'Rec':<10}")
    lines.append("-" * 80)
    
    for ticker, pos in sorted_positions:
        lines.append(
            f"{ticker:<10} "
            f"{pos.base_allocation:>6.2f}% "
            f"{pos.volatility_adjusted:>8.2f}% "
            f"{pos.atr_percentile:>6.0f}% "
            f"{pos.risk_units:>6.3f} "
            f"{pos.recommendation:<10}"
        )
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Volatility-Adjusted Position Sizing Module")
    print("Usage:")
    print("  from src.risk.volatility_position_sizing import VolatilityPositionSizer")
    print("  sizer = VolatilityPositionSizer()")
    print("  position = sizer.adjust_position_size(base_allocation=3.0, atr_percent=2.5)")
