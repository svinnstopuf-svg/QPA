"""
Market Context Filter - "Vattenpasset"

Philosophy:
Before looking for patterns, check if we're in the RIGHT CONTEXT for position trading.
We are BOTTOM FISHERS, not top chasers.

Pre-Conditions (ALL must be true):
1. Decline Filter: -15%+ from 90-day high
2. Trend Filter: Price below EMA 200

Only if context is valid do we look for PRIMARY patterns.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from ..utils.market_data import MarketData


@dataclass
class MarketContext:
    """Market context assessment result."""
    is_valid_for_entry: bool
    decline_from_high: float  # % from 90-day high
    price_vs_ema200: float  # % below/above EMA 200
    high_90d: float
    current_price: float
    ema200: float
    reason: str  # Why valid or invalid


class MarketContextFilter:
    """
    'Vattenpasset' - Pre-condition filter for position trading setups.
    
    Rules:
    1. Must have declined 15%+ from 90-day high (structural decline)
    2. Must be below EMA 200 (long-term downtrend)
    
    If these aren't met, we have 'No Setup' - don't even look for patterns.
    """
    
    def __init__(
        self,
        min_decline_pct: float = 15.0,  # Minimum decline from high
        lookback_high: int = 90,  # Days to look back for high
        ema_period: int = 200  # EMA period for trend
    ):
        self.min_decline_pct = min_decline_pct
        self.lookback_high = lookback_high
        self.ema_period = ema_period
    
    def calculate_ema(
        self,
        prices: np.ndarray,
        period: int
    ) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return np.full(len(prices), np.nan)
        
        ema = np.zeros(len(prices))
        ema[:period] = np.nan
        
        # Start with SMA for first value
        ema[period-1] = np.mean(prices[:period])
        
        # Calculate multiplier
        multiplier = 2.0 / (period + 1)
        
        # Calculate EMA
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def check_market_context(
        self,
        market_data: MarketData
    ) -> MarketContext:
        """
        Check if market context is valid for position trading entry.
        
        This is the 'Vattenpass' - if it's not level, we don't build.
        
        Args:
            market_data: Market data to analyze
            
        Returns:
            MarketContext with validity and details
        """
        prices = market_data.close_prices
        
        if len(prices) < max(self.lookback_high, self.ema_period):
            return MarketContext(
                is_valid_for_entry=False,
                decline_from_high=0.0,
                price_vs_ema200=0.0,
                high_90d=0.0,
                current_price=prices[-1] if len(prices) > 0 else 0.0,
                ema200=0.0,
                reason=f"Insufficient data: need {max(self.lookback_high, self.ema_period)} days"
            )
        
        # Current price
        current_price = prices[-1]
        
        # 1. DECLINE FILTER: Check decline from 90-day high
        lookback_start = max(0, len(prices) - self.lookback_high)
        high_90d = np.max(prices[lookback_start:])
        decline_from_high = ((current_price - high_90d) / high_90d) * 100
        
        # 2. TREND FILTER: Check position vs EMA 200
        ema200 = self.calculate_ema(prices, self.ema_period)
        current_ema200 = ema200[-1]
        
        if np.isnan(current_ema200):
            return MarketContext(
                is_valid_for_entry=False,
                decline_from_high=decline_from_high,
                price_vs_ema200=0.0,
                high_90d=high_90d,
                current_price=current_price,
                ema200=0.0,
                reason="Cannot calculate EMA 200 (insufficient data)"
            )
        
        price_vs_ema200 = ((current_price - current_ema200) / current_ema200) * 100
        
        # VALIDATION
        decline_ok = decline_from_high <= -self.min_decline_pct
        trend_ok = current_price < current_ema200
        
        if decline_ok and trend_ok:
            reason = f"VALID CONTEXT: {decline_from_high:.1f}% from high, {price_vs_ema200:.1f}% below EMA200"
            is_valid = True
        elif not decline_ok and not trend_ok:
            reason = f"NO SETUP: Insufficient decline ({decline_from_high:.1f}% vs {-self.min_decline_pct:.1f}% req) AND above EMA200"
            is_valid = False
        elif not decline_ok:
            reason = f"NO SETUP: Insufficient decline ({decline_from_high:.1f}% vs {-self.min_decline_pct:.1f}% required)"
            is_valid = False
        else:  # not trend_ok
            reason = f"NO SETUP: Price above EMA200 ({price_vs_ema200:.1f}% above)"
            is_valid = False
        
        return MarketContext(
            is_valid_for_entry=is_valid,
            decline_from_high=decline_from_high,
            price_vs_ema200=price_vs_ema200,
            high_90d=high_90d,
            current_price=current_price,
            ema200=current_ema200,
            reason=reason
        )
    
    def batch_check_context(
        self,
        instruments_data: dict
    ) -> dict:
        """
        Check context for multiple instruments.
        
        Args:
            instruments_data: Dict[ticker, market_data]
            
        Returns:
            Dict[ticker, MarketContext]
        """
        results = {}
        
        for ticker, market_data in instruments_data.items():
            results[ticker] = self.check_market_context(market_data)
        
        return results


def format_context_report(context: MarketContext, ticker: str = "") -> str:
    """Format market context report."""
    lines = []
    
    if ticker:
        lines.append(f"\n{'='*80}")
        lines.append(f"MARKET CONTEXT CHECK: {ticker}")
        lines.append(f"{'='*80}")
    
    lines.append(f"\nCURRENT STATE:")
    lines.append(f"  Current Price: {context.current_price:.2f}")
    lines.append(f"  90-day High: {context.high_90d:.2f}")
    lines.append(f"  EMA 200: {context.ema200:.2f}")
    
    lines.append(f"\nDECLINE FILTER:")
    lines.append(f"  Decline from High: {context.decline_from_high:.1f}%")
    if context.decline_from_high <= -15.0:
        lines.append(f"  Status: PASS (sufficient decline)")
    else:
        lines.append(f"  Status: FAIL (need -15% minimum)")
    
    lines.append(f"\nTREND FILTER:")
    lines.append(f"  Price vs EMA200: {context.price_vs_ema200:.1f}%")
    if context.current_price < context.ema200:
        lines.append(f"  Status: PASS (below EMA200)")
    else:
        lines.append(f"  Status: FAIL (must be below EMA200)")
    
    lines.append(f"\nFINAL VERDICT:")
    if context.is_valid_for_entry:
        lines.append(f"  ✓ VALID CONTEXT FOR POSITION TRADING")
        lines.append(f"  → Proceed with PRIMARY pattern detection")
    else:
        lines.append(f"  ✗ NO SETUP")
        lines.append(f"  → Skip pattern detection (wrong context)")
    
    lines.append(f"\nREASON: {context.reason}")
    
    return "\n".join(lines)
