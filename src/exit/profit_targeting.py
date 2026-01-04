"""
Profit-Targeting med Standardavvikelser (Sigma-Based Exits)

Kasinot vet exakt när spelet är slut. Trading är annorlunda - men vi kan
använda statistik för att veta när en rörelse är "osannolikt att fortsätta".

Philosophy:
- När priset rör sig +2 eller +3 standardavvikelser från medelvärdet
  är sannolikheten för rekyl extremt hög
- Ta hem delar av vinsten vid statistiskt extrema nivåer
- Låt resten löpa för att fånga "tail events"

Strategy:
- +2 Sigma: Sälj 50% av position (säkra hälften av vinsten)
- +3 Sigma: Sälj återstående 50% (total exit)
- Detta ökar genomsnittlig vinst per affär
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ExitTrigger(Enum):
    """Exit trigger types."""
    NONE = "NONE"  # No exit
    HALF_AT_2_SIGMA = "HALF_AT_2_SIGMA"  # Take 50% at +2σ
    FULL_AT_3_SIGMA = "FULL_AT_3_SIGMA"  # Take 100% at +3σ
    STOP_LOSS = "STOP_LOSS"  # Hit stop loss
    SIGNAL_RED = "SIGNAL_RED"  # Signal turned RED


@dataclass
class ProfitTarget:
    """Profit target levels."""
    mean_price: float  # Mean price (reference)
    std_dev: float  # Standard deviation
    sigma_2_level: float  # +2 sigma target
    sigma_3_level: float  # +3 sigma target
    current_sigma: float  # Current position in sigmas


@dataclass
class ExitRecommendation:
    """Exit recommendation."""
    trigger: ExitTrigger
    exit_percentage: float  # % of position to exit (0-100)
    current_price: float
    target_level: float
    sigma_distance: float
    message: str


class ProfitTargetingSystem:
    """
    Sigma-based profit targeting system.
    
    Usage for live trading:
    1. Calculate mean and std dev over lookback period
    2. Monitor current price relative to sigma levels
    3. Exit 50% at +2σ, remaining 50% at +3σ
    
    This is NOT a screening tool - it's for actual trading.
    """
    
    def __init__(
        self,
        lookback_period: int = 20,  # Days for mean/std calculation
        sigma_2_exit: float = 0.5,  # Exit 50% at +2 sigma
        sigma_3_exit: float = 1.0   # Exit 100% at +3 sigma
    ):
        """
        Initialize profit targeting system.
        
        Args:
            lookback_period: Days to calculate mean and std dev
            sigma_2_exit: Fraction to exit at +2 sigma
            sigma_3_exit: Fraction to exit at +3 sigma
        """
        self.lookback_period = lookback_period
        self.sigma_2_exit = sigma_2_exit
        self.sigma_3_exit = sigma_3_exit
    
    def calculate_profit_targets(
        self,
        prices: pd.Series
    ) -> ProfitTarget:
        """
        Calculate profit target levels.
        
        Args:
            prices: Price series (most recent last)
            
        Returns:
            ProfitTarget with sigma levels
        """
        # Use last N prices for calculation
        recent_prices = prices.iloc[-self.lookback_period:]
        
        # Calculate mean and std dev
        mean_price = recent_prices.mean()
        std_dev = recent_prices.std()
        
        # Calculate sigma levels
        sigma_2_level = mean_price + 2 * std_dev
        sigma_3_level = mean_price + 3 * std_dev
        
        # Current sigma distance
        current_price = prices.iloc[-1]
        current_sigma = (current_price - mean_price) / std_dev if std_dev > 0 else 0
        
        return ProfitTarget(
            mean_price=mean_price,
            std_dev=std_dev,
            sigma_2_level=sigma_2_level,
            sigma_3_level=sigma_3_level,
            current_sigma=current_sigma
        )
    
    def check_exit_signal(
        self,
        current_price: float,
        target: ProfitTarget,
        position_remaining: float = 1.0  # Fraction of position remaining
    ) -> ExitRecommendation:
        """
        Check if exit signal triggered.
        
        Args:
            current_price: Current price
            target: Profit targets
            position_remaining: Fraction of position still held (0-1)
            
        Returns:
            ExitRecommendation
        """
        # Check +3 sigma (full exit)
        if current_price >= target.sigma_3_level and position_remaining > 0:
            return ExitRecommendation(
                trigger=ExitTrigger.FULL_AT_3_SIGMA,
                exit_percentage=position_remaining * 100,
                current_price=current_price,
                target_level=target.sigma_3_level,
                sigma_distance=target.current_sigma,
                message=f"EXIT FULL POSITION at +3σ ({current_price:.2f})"
            )
        
        # Check +2 sigma (half exit)
        if current_price >= target.sigma_2_level and position_remaining == 1.0:
            return ExitRecommendation(
                trigger=ExitTrigger.HALF_AT_2_SIGMA,
                exit_percentage=self.sigma_2_exit * 100,
                current_price=current_price,
                target_level=target.sigma_2_level,
                sigma_distance=target.current_sigma,
                message=f"EXIT 50% at +2σ ({current_price:.2f}), let rest run"
            )
        
        # No exit
        return ExitRecommendation(
            trigger=ExitTrigger.NONE,
            exit_percentage=0,
            current_price=current_price,
            target_level=0,
            sigma_distance=target.current_sigma,
            message=f"HOLD - Current {target.current_sigma:+.2f}σ from mean"
        )
    
    def backtest_exit_strategy(
        self,
        prices: pd.Series,
        entry_price: float,
        entry_idx: int
    ) -> Dict:
        """
        Backtest sigma-based exit strategy.
        
        Args:
            prices: Full price series
            entry_price: Entry price
            entry_idx: Entry index in series
            
        Returns:
            Dict with exit results
        """
        position_remaining = 1.0  # Full position
        exits = []
        total_return = 0
        
        # Walk forward from entry
        for i in range(entry_idx + 1, len(prices)):
            # Calculate targets using data up to this point
            target = self.calculate_profit_targets(prices.iloc[:i+1])
            
            # Check exit
            current_price = prices.iloc[i]
            exit_rec = self.check_exit_signal(
                current_price,
                target,
                position_remaining
            )
            
            # Execute exit if triggered
            if exit_rec.exit_percentage > 0:
                exit_fraction = exit_rec.exit_percentage / 100
                exit_return = (current_price - entry_price) / entry_price
                
                exits.append({
                    'idx': i,
                    'price': current_price,
                    'fraction': exit_fraction,
                    'return': exit_return,
                    'trigger': exit_rec.trigger.value
                })
                
                total_return += exit_return * exit_fraction
                position_remaining -= exit_fraction
                
                # If fully exited, stop
                if position_remaining <= 0:
                    break
        
        # If position still open, close at last price
        if position_remaining > 0:
            final_price = prices.iloc[-1]
            final_return = (final_price - entry_price) / entry_price
            exits.append({
                'idx': len(prices) - 1,
                'price': final_price,
                'fraction': position_remaining,
                'return': final_return,
                'trigger': 'END_OF_DATA'
            })
            total_return += final_return * position_remaining
        
        return {
            'exits': exits,
            'total_return': total_return,
            'entry_price': entry_price,
            'num_exits': len(exits)
        }


def format_profit_target_report(target: ProfitTarget, current_price: float) -> str:
    """Format profit target report."""
    lines = []
    lines.append("=" * 60)
    lines.append("PROFIT TARGET LEVELS")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Current Price: {current_price:.2f}")
    lines.append(f"Mean ({target.lookback_period}d): {target.mean_price:.2f}")
    lines.append(f"Std Dev: {target.std_dev:.2f}")
    lines.append("")
    lines.append(f"📊 SIGMA LEVELS")
    lines.append("-" * 60)
    lines.append(f"+2 Sigma (50% exit): {target.sigma_2_level:.2f}")
    lines.append(f"+3 Sigma (100% exit): {target.sigma_3_level:.2f}")
    lines.append("")
    lines.append(f"Current Position: {target.current_sigma:+.2f}σ from mean")
    lines.append("")
    
    # Visual indicator
    if target.current_sigma >= 3:
        lines.append("🔴 EXTREME - Full exit recommended")
    elif target.current_sigma >= 2:
        lines.append("🟡 HIGH - Partial exit recommended (50%)")
    elif target.current_sigma >= 1:
        lines.append("🟢 NORMAL - Hold position")
    else:
        lines.append("⚪ BELOW MEAN - Hold or consider stop loss")
    
    lines.append("=" * 60)
    return "\n".join(lines)


# Example usage and guide
USAGE_GUIDE = """
===============================================================================
PROFIT-TARGETING GUIDE - Sigma-Based Exits
===============================================================================

Detta är en TRADING-strategi, inte ett screening-verktyg.
Använd detta när du är i en position och vill veta när du ska ta vinst.

FILOSOFI:
---------
Kasinot vet när spelet är slut. I trading använder vi statistik:
- När priset rör sig +2 eller +3 standardavvikelser från medelvärdet
  är fortsatt uppgång statistiskt osannolikt
- Ta hem delar av vinsten vid extrema nivåer
- Låt resten löpa för att fånga "tail events"

STRATEGI:
---------
1. När du går in i en position, starta tracking
2. Beräkna medelvärde och standardavvikelse (20-dagars lookback)
3. Vid +2σ: Sälj 50% av positionen (säkra hälften)
4. Vid +3σ: Sälj resterande 50% (full exit)

EXEMPEL:
--------
Aktie handlas runt 100 kr (mean), std dev = 5 kr

+2 Sigma Level = 100 + (2 × 5) = 110 kr → Sälj 50%
+3 Sigma Level = 100 + (3 × 5) = 115 kr → Sälj 100%

Om priset går till 110 kr:
- Du tar hem 50% av vinsten (+10%)
- Låter resten löpa för att fånga +15% eller mer

IMPLEMENTERING:
--------------
```python
from src.exit.profit_targeting import ProfitTargetingSystem
import yfinance as yf

# Hämta data
ticker = yf.Ticker("AAPL")
prices = ticker.history(period="3mo")['Close']

# Skapa system
system = ProfitTargetingSystem(lookback_period=20)

# Beräkna targets
target = system.calculate_profit_targets(prices)
print(f"Mean: {target.mean_price:.2f}")
print(f"+2σ Level: {target.sigma_2_level:.2f}")
print(f"+3σ Level: {target.sigma_3_level:.2f}")

# Kolla exit signal
current_price = prices.iloc[-1]
exit_rec = system.check_exit_signal(current_price, target)
print(exit_rec.message)
```

VARFÖR DETTA FUNGERAR:
---------------------
1. Matematisk grund: Normalfördelning → 95% av rörelser inom ±2σ
2. Mean reversion: Extrema rörelser tenderar att revertera
3. Ta hem vinst när oddsen vänder: +2σ = statistiskt osannolikt att fortsätta
4. Psykologiskt: Eliminerar "ska jag sälja nu?"-beslut

INTEGRATION MED SCREENER:
-------------------------
- Screener ger dig GREEN signal → Du köper
- Profit-targeting säger när du ska sälja (baserat på statistik)
- Signal blir RED → Alternativ exit trigger

Detta kompletterar traffic light-systemet med matematisk exit-disciplin.
===============================================================================
"""


if __name__ == "__main__":
    print(USAGE_GUIDE)
