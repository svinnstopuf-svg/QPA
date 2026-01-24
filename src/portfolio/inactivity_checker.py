"""
Inactivity Checker - Dead Trade Detector

Flags positions that haven't moved significantly in 21+ days.
Helps free capital from stagnant trades.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class InactivityCheck:
    """Inactivity assessment."""
    ticker: str
    is_inactive: bool
    days_stagnant: int
    price_movement_pct: float  # Total movement in period
    avg_daily_movement: float  # Avg absolute daily move
    recommendation: str


class InactivityChecker:
    """
    Detect inactive/stagnant positions.
    
    Logic:
    - If price movement < 2% over 21 days → INACTIVE
    - Flag for potential exit to free capital
    """
    
    def __init__(
        self,
        inactivity_threshold: float = 0.02,  # 2% total movement
        lookback_days: int = 21
    ):
        self.inactivity_threshold = inactivity_threshold
        self.lookback_days = lookback_days
    
    def check_inactivity(
        self,
        ticker: str,
        prices: np.ndarray,  # Recent prices (at least lookback_days)
        entry_price: float,
        days_held: int
    ) -> InactivityCheck:
        """
        Check if position is inactive.
        
        Args:
            ticker: Instrument ticker
            prices: Array of recent prices
            entry_price: Original entry price
            days_held: Days since entry
            
        Returns:
            InactivityCheck with recommendation
        """
        
        if len(prices) < self.lookback_days:
            # Not enough data
            return InactivityCheck(
                ticker=ticker,
                is_inactive=False,
                days_stagnant=0,
                price_movement_pct=0.0,
                avg_daily_movement=0.0,
                recommendation="Insufficient data"
            )
        
        # Take last lookback_days
        recent_prices = prices[-self.lookback_days:]
        
        # Calculate total price movement
        high = float(np.max(recent_prices))
        low = float(np.min(recent_prices))
        current = float(recent_prices[-1])
        
        price_range = high - low
        price_movement_pct = price_range / entry_price
        
        # Calculate average daily movement
        daily_changes = np.abs(np.diff(recent_prices) / recent_prices[:-1])
        avg_daily_movement = float(np.mean(daily_changes))
        
        # Check if inactive
        is_inactive = price_movement_pct < self.inactivity_threshold
        
        # Determine days stagnant
        if is_inactive:
            days_stagnant = min(days_held, self.lookback_days)
        else:
            days_stagnant = 0
        
        # Create recommendation
        if is_inactive:
            if days_held > 42:  # More than 6 weeks
                recommendation = f"EXIT - Dead trade after {days_held} days (moved only {price_movement_pct*100:.1f}%)"
            else:
                recommendation = f"MONITOR - Low movement ({price_movement_pct*100:.1f}%) but < 6 weeks held"
        else:
            recommendation = f"Active - {price_movement_pct*100:.1f}% movement in {self.lookback_days} days"
        
        return InactivityCheck(
            ticker=ticker,
            is_inactive=is_inactive,
            days_stagnant=days_stagnant,
            price_movement_pct=price_movement_pct,
            avg_daily_movement=avg_daily_movement,
            recommendation=recommendation
        )
