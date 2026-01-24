"""
Exit Guard - Structure Break Detection

Monitors existing positions and flags when technical structure breaks.
Triggers: Close below Higher Low, EMA50 break, neckline violation.
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np


@dataclass
class ExitSignal:
    """Exit signal for a position."""
    ticker: str
    action: str  # "HOLD", "EXIT NOW", "TRAIL STOP"
    reason: str
    structure_intact: bool
    trailing_stop_price: Optional[float] = None
    current_profit_pct: float = 0.0


class ExitGuard:
    """
    Monitors positions for structure breaks and trailing stops.
    
    Exit Triggers:
    1. Close below Higher Low (invalidates uptrend)
    2. Close below EMA50 (momentum lost)
    3. Neckline break (Double Bottom/IH&S invalidated)
    4. Trailing stop triggered (lock in profits)
    """
    
    def __init__(
        self,
        ema_period: int = 50,
        trailing_stop_activation: float = 0.20,  # Activate at +20%
        trailing_stop_distance: float = 0.10     # Trail 10% below peak
    ):
        self.ema_period = ema_period
        self.trailing_activation = trailing_stop_activation
        self.trailing_distance = trailing_stop_distance
    
    def check_exit(
        self,
        ticker: str,
        entry_price: float,
        current_price: float,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        pattern_type: str,
        neckline_price: Optional[float] = None
    ) -> ExitSignal:
        """
        Check if position should be exited.
        
        Args:
            ticker: Instrument ticker
            entry_price: Original entry price
            current_price: Current price
            highs/lows/closes: Recent price arrays (last 60 days)
            pattern_type: "DOUBLE_BOTTOM", "IHS", etc.
            neckline_price: Neckline level (if applicable)
            
        Returns:
            ExitSignal with action and reason
        """
        
        current_profit_pct = (current_price - entry_price) / entry_price
        
        # Calculate EMA50
        ema50 = self._calculate_ema(closes, self.ema_period)
        
        # Check 1: Trailing Stop (if activated)
        if current_profit_pct >= self.trailing_activation:
            peak_price = max(current_price, entry_price * (1 + self.trailing_activation))
            trailing_stop = peak_price * (1 - self.trailing_distance)
            
            if current_price < trailing_stop:
                return ExitSignal(
                    ticker=ticker,
                    action="EXIT NOW",
                    reason=f"Trailing stop hit at {trailing_stop:.2f} (locked in +{current_profit_pct*100:.1f}%)",
                    structure_intact=True,
                    trailing_stop_price=trailing_stop,
                    current_profit_pct=current_profit_pct
                )
            else:
                return ExitSignal(
                    ticker=ticker,
                    action="TRAIL STOP",
                    reason=f"Trailing at {trailing_stop:.2f} (current profit: +{current_profit_pct*100:.1f}%)",
                    structure_intact=True,
                    trailing_stop_price=trailing_stop,
                    current_profit_pct=current_profit_pct
                )
        
        # Check 2: EMA50 Break
        if current_price < ema50:
            return ExitSignal(
                ticker=ticker,
                action="EXIT NOW",
                reason=f"Closed below EMA50 ({ema50:.2f}) - momentum lost",
                structure_intact=False,
                current_profit_pct=current_profit_pct
            )
        
        # Check 3: Higher Low Break (last 20 days)
        if len(lows) >= 20:
            recent_lows = lows[-20:]
            # Find pivot lows (local minima)
            pivot_lows = self._find_pivot_lows(recent_lows)
            
            if len(pivot_lows) >= 2:
                # Check if we broke below most recent pivot low
                latest_pivot = pivot_lows[-1]
                if current_price < latest_pivot * 0.98:  # 2% buffer
                    return ExitSignal(
                        ticker=ticker,
                        action="EXIT NOW",
                        reason=f"Broke below Higher Low at {latest_pivot:.2f} - uptrend invalidated",
                        structure_intact=False,
                        current_profit_pct=current_profit_pct
                    )
        
        # Check 4: Neckline Break (for Double Bottom / IH&S)
        if neckline_price and pattern_type in ["DOUBLE_BOTTOM", "IHS"]:
            if current_price < neckline_price * 0.98:  # 2% below neckline
                return ExitSignal(
                    ticker=ticker,
                    action="EXIT NOW",
                    reason=f"Broke below neckline ({neckline_price:.2f}) - pattern invalidated",
                    structure_intact=False,
                    current_profit_pct=current_profit_pct
                )
        
        # All checks passed - HOLD
        return ExitSignal(
            ticker=ticker,
            action="HOLD",
            reason="Structure intact, no exit triggers",
            structure_intact=True,
            current_profit_pct=current_profit_pct
        )
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA."""
        if len(prices) < period:
            return float(np.mean(prices))
        
        multiplier = 2 / (period + 1)
        ema = float(prices[0])
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _find_pivot_lows(self, lows: np.ndarray, window: int = 3) -> List[float]:
        """Find pivot lows (local minima)."""
        pivots = []
        
        for i in range(window, len(lows) - window):
            is_pivot = True
            for j in range(1, window + 1):
                if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                    is_pivot = False
                    break
            
            if is_pivot:
                pivots.append(float(lows[i]))
        
        return pivots
