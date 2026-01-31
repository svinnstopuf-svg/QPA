"""
Alpha-Switch: Convergence Detection

Identifies "holy grail" setups where an instrument:
1. Triggered Motor A (Mean Reversion) within last 15 days
2. Now triggers Motor B (Momentum/Launchpad)

This convergence indicates:
- Bought at bottom (Motor A)
- Now showing strength (Motor B)
- Optimal risk/reward positioning

Convergence_Multiplier: 1.2x applied to Robust_Score
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

from ..utils.market_data import MarketData
from ..patterns.momentum_engine import MomentumSignal


@dataclass
class ConvergenceDetection:
    """Result of Alpha-Switch convergence check"""
    ticker: str
    is_convergence: bool
    
    # Motor A (Mean Reversion) History
    motor_a_triggered: bool
    motor_a_trigger_date: Optional[datetime]
    days_since_motor_a: Optional[int]
    motor_a_entry_price: Optional[float]
    
    # Motor B (Momentum) Current
    motor_b_active: bool
    motor_b_signal: Optional[MomentumSignal]
    
    # Convergence Metrics
    convergence_multiplier: float  # 1.0 (no convergence) or 1.2 (convergence)
    price_move_since_motor_a: Optional[float]  # % move from Motor A entry
    
    # Reasoning
    reason: str


class AlphaSwitchDetector:
    """
    Detect convergence between Motor A and Motor B.
    
    Motor A: Mean Reversion (Vattenpasset + Pattern detected)
    Motor B: Momentum (RS-Rating ≥95, VCP, near 52w high)
    
    Convergence = Motor A triggered within T-15 days AND Motor B active now
    
    Reward: 1.2x Convergence_Multiplier on Robust_Score
    """
    
    def __init__(self, lookback_days: int = 15):
        """
        Args:
            lookback_days: Max days to look back for Motor A trigger (default 15)
        """
        self.lookback_days = lookback_days
        self.convergence_multiplier = 1.2
    
    def detect_motor_a_trigger(
        self,
        market_data: MarketData,
        current_date: datetime,
        lookback_days: int
    ) -> tuple[bool, Optional[datetime], Optional[float]]:
        """
        Check if Motor A (Mean Reversion) was triggered within lookback window.
        
        Motor A indicators:
        - New low on 63/126/252 day timeframe
        - Price crossed below EMA200 then stabilized
        - Double bottom formation detected
        
        For simplicity, we detect: Price made new low AND was below EMA200
        within last `lookback_days`.
        
        Args:
            market_data: OHLCV data
            current_date: Today's date
            lookback_days: Days to look back
        
        Returns:
            (triggered: bool, trigger_date: datetime, entry_price: float)
        """
        prices = market_data.close_prices
        timestamps = market_data.timestamps
        
        if len(prices) < 200:
            return False, None, None
        
        # Calculate EMA200
        ema200 = self._calculate_ema(prices, 200)
        
        # Get lookback window
        lookback_start_idx = max(0, len(prices) - lookback_days - 1)
        lookback_prices = prices[lookback_start_idx:]
        lookback_ema = ema200[lookback_start_idx:]
        lookback_timestamps = timestamps[lookback_start_idx:]
        
        # Find days where:
        # 1. Price was at local low (lower than prev/next days)
        # 2. Price was below EMA200
        motor_a_triggers = []
        
        for i in range(1, len(lookback_prices) - 1):
            # Local low check
            is_local_low = (
                lookback_prices[i] < lookback_prices[i-1] and
                lookback_prices[i] < lookback_prices[i+1]
            )
            
            # Below EMA200
            below_ema = lookback_prices[i] < lookback_ema[i]
            
            # Check if made 63-day low
            if i >= 63:
                lookback_63 = lookback_prices[i-63:i+1]
                is_63d_low = lookback_prices[i] == np.min(lookback_63)
            else:
                is_63d_low = False
            
            if (is_local_low and below_ema) or is_63d_low:
                motor_a_triggers.append({
                    'date': lookback_timestamps[i],
                    'price': lookback_prices[i],
                    'index': i
                })
        
        if len(motor_a_triggers) > 0:
            # Return most recent trigger
            latest_trigger = motor_a_triggers[-1]
            return True, latest_trigger['date'], latest_trigger['price']
        else:
            return False, None, None
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)
        
        ema = np.zeros(len(prices))
        ema[:period] = np.nan
        ema[period-1] = np.mean(prices[:period])
        
        multiplier = 2.0 / (period + 1)
        
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def detect_convergence(
        self,
        ticker: str,
        market_data: MarketData,
        motor_b_signal: MomentumSignal,
        current_date: Optional[datetime] = None
    ) -> ConvergenceDetection:
        """
        Detect if Alpha-Switch convergence has occurred.
        
        Args:
            ticker: Stock ticker
            market_data: OHLCV data
            motor_b_signal: Motor B momentum signal (must be checked first)
            current_date: Current date (defaults to last timestamp in data)
        
        Returns:
            ConvergenceDetection with convergence status and multiplier
        """
        if current_date is None:
            current_date = market_data.timestamps[-1]
        
        # Check Motor B status
        motor_b_active = motor_b_signal.is_valid
        
        if not motor_b_active:
            # Motor B not active → no convergence possible
            return ConvergenceDetection(
                ticker=ticker,
                is_convergence=False,
                motor_a_triggered=False,
                motor_a_trigger_date=None,
                days_since_motor_a=None,
                motor_a_entry_price=None,
                motor_b_active=False,
                motor_b_signal=motor_b_signal,
                convergence_multiplier=1.0,
                price_move_since_motor_a=None,
                reason="Motor B not active (no momentum signal)"
            )
        
        # Check Motor A history
        motor_a_triggered, trigger_date, entry_price = self.detect_motor_a_trigger(
            market_data,
            current_date,
            self.lookback_days
        )
        
        if not motor_a_triggered:
            return ConvergenceDetection(
                ticker=ticker,
                is_convergence=False,
                motor_a_triggered=False,
                motor_a_trigger_date=None,
                days_since_motor_a=None,
                motor_a_entry_price=None,
                motor_b_active=True,
                motor_b_signal=motor_b_signal,
                convergence_multiplier=1.0,
                price_move_since_motor_a=None,
                reason=f"Motor A not triggered within last {self.lookback_days} days"
            )
        
        # CONVERGENCE DETECTED!
        days_since_motor_a = (current_date - trigger_date).days
        current_price = market_data.close_prices[-1]
        price_move_pct = ((current_price - entry_price) / entry_price) * 100
        
        reason = (
            f"🎯 CONVERGENCE DETECTED! "
            f"Motor A triggered {days_since_motor_a}d ago @ {entry_price:.2f}, "
            f"Motor B now active (RS={motor_b_signal.rs_rating:.0f}). "
            f"Price moved {price_move_pct:+.1f}% since bottom. "
            f"Robust_Score multiplier: {self.convergence_multiplier}x"
        )
        
        return ConvergenceDetection(
            ticker=ticker,
            is_convergence=True,
            motor_a_triggered=True,
            motor_a_trigger_date=trigger_date,
            days_since_motor_a=days_since_motor_a,
            motor_a_entry_price=entry_price,
            motor_b_active=True,
            motor_b_signal=motor_b_signal,
            convergence_multiplier=self.convergence_multiplier,
            price_move_since_motor_a=price_move_pct,
            reason=reason
        )


def apply_convergence_boost(
    robust_score: float,
    convergence: ConvergenceDetection
) -> tuple[float, bool]:
    """
    Apply convergence multiplier to Robust Score.
    
    Args:
        robust_score: Original robust score (0-100)
        convergence: Convergence detection result
    
    Returns:
        (boosted_score, was_boosted)
    """
    if convergence.is_convergence:
        boosted = robust_score * convergence.convergence_multiplier
        boosted = min(100, boosted)  # Cap at 100
        return boosted, True
    else:
        return robust_score, False
