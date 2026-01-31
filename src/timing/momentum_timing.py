"""
Momentum Breakout Timing

Optimize entry timing for momentum breakouts:
1. Volume Surge Detection (2x+ average)
2. Price Acceleration (increasing gains)
3. Gap-Up Analysis (strength indicator)
4. Multi-Timeframe Confirmation
5. Intraday Strength (high vs low)

Different from mean reversion timing which looks for:
- Exhaustion signals
- RSI hooks
- Volume declining
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class MomentumTiming:
    """Breakout timing analysis"""
    ticker: str
    
    # Volume analysis
    current_volume: float
    avg_volume_20d: float
    volume_surge_ratio: float  # current / avg
    volume_score: float  # 0-100
    
    # Price acceleration
    gain_1d: float
    gain_5d: float
    gain_10d: float
    is_accelerating: bool
    acceleration_score: float  # 0-100
    
    # Gap analysis
    gap_pct: float  # % gap up/down
    gap_type: str  # "NONE", "SMALL", "SIGNIFICANT", "BREAKAWAY"
    gap_score: float  # 0-100
    
    # Intraday strength
    high_low_range_pct: float
    close_position_in_range: float  # 0-1 (0=low, 1=high)
    intraday_score: float  # 0-100
    
    # Multi-timeframe
    daily_trend: str  # "UP", "DOWN", "SIDEWAYS"
    weekly_trend: str
    monthly_trend: str
    timeframe_alignment: bool
    timeframe_score: float  # 0-100
    
    # Overall
    timing_confidence: float  # 0-100
    recommended_action: str  # "BUY_NOW", "WAIT", "NO_ENTRY"
    reason: str


class MomentumTimingAnalyzer:
    """
    Analyze optimal timing for momentum breakout entry.
    
    Best entries:
    - Volume surge 2x+ on breakout
    - Price accelerating (higher highs)
    - Gap up (strength)
    - Close near high of day
    - All timeframes aligned
    """
    
    def __init__(
        self,
        min_volume_surge: float = 2.0,
        min_gap_pct: float = 0.02,
        min_close_position: float = 0.70
    ):
        self.min_volume_surge = min_volume_surge
        self.min_gap_pct = min_gap_pct
        self.min_close_position = min_close_position
    
    def analyze_timing(
        self,
        ticker: str,
        price_data: pd.DataFrame
    ) -> MomentumTiming:
        """
        Analyze breakout timing.
        
        Args:
            ticker: Stock ticker
            price_data: DataFrame with OHLCV columns
        
        Returns:
            MomentumTiming with analysis
        """
        if len(price_data) < 20:
            return self._create_empty_timing(ticker, "Insufficient data")
        
        # Volume analysis
        current_vol = price_data['Volume'].iloc[-1]
        avg_vol_20d = price_data['Volume'].rolling(20).mean().iloc[-2]  # Exclude today
        volume_surge = current_vol / avg_vol_20d if avg_vol_20d > 0 else 0
        volume_score = self._score_volume(volume_surge)
        
        # Price acceleration
        closes = price_data['Close']
        gain_1d = ((closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2]) * 100 if len(closes) >= 2 else 0
        gain_5d = ((closes.iloc[-1] - closes.iloc[-6]) / closes.iloc[-6]) * 100 if len(closes) >= 6 else 0
        gain_10d = ((closes.iloc[-1] - closes.iloc[-11]) / closes.iloc[-11]) * 100 if len(closes) >= 11 else 0
        
        is_accelerating = (gain_1d > 0) and (gain_5d > gain_1d * 3) and (gain_10d > gain_5d * 1.5)
        acceleration_score = self._score_acceleration(gain_1d, gain_5d, gain_10d, is_accelerating)
        
        # Gap analysis
        if len(price_data) >= 2:
            prev_close = price_data['Close'].iloc[-2]
            today_open = price_data['Open'].iloc[-1]
            gap_pct = ((today_open - prev_close) / prev_close) * 100
        else:
            gap_pct = 0.0
        
        gap_type, gap_score = self._analyze_gap(gap_pct)
        
        # Intraday strength
        today_high = price_data['High'].iloc[-1]
        today_low = price_data['Low'].iloc[-1]
        today_close = price_data['Close'].iloc[-1]
        
        range_pct = ((today_high - today_low) / today_low) * 100 if today_low > 0 else 0
        close_position = ((today_close - today_low) / (today_high - today_low)) if (today_high - today_low) > 0 else 0.5
        intraday_score = self._score_intraday(close_position, range_pct)
        
        # Multi-timeframe analysis
        daily_trend = self._detect_trend(closes, period=20)
        weekly_trend = self._detect_trend(closes, period=60) if len(closes) >= 60 else "UNKNOWN"
        monthly_trend = self._detect_trend(closes, period=120) if len(closes) >= 120 else "UNKNOWN"
        
        timeframe_alignment = (daily_trend == "UP") and (weekly_trend in ["UP", "UNKNOWN"]) and (monthly_trend in ["UP", "UNKNOWN"])
        timeframe_score = self._score_timeframes(daily_trend, weekly_trend, monthly_trend)
        
        # Overall timing confidence
        timing_confidence = (
            volume_score * 0.30 +
            acceleration_score * 0.25 +
            gap_score * 0.15 +
            intraday_score * 0.15 +
            timeframe_score * 0.15
        )
        
        # Recommendation
        if timing_confidence >= 75:
            action = "BUY_NOW"
            reason = "Excellent breakout setup - all signals confirming"
        elif timing_confidence >= 50:
            action = "BUY_NOW"
            reason = "Good breakout setup - proceed with entry"
        elif timing_confidence >= 30:
            action = "WAIT"
            reason = "Weak signals - wait for confirmation"
        else:
            action = "NO_ENTRY"
            reason = "Poor timing - signals not aligned"
        
        return MomentumTiming(
            ticker=ticker,
            current_volume=current_vol,
            avg_volume_20d=avg_vol_20d,
            volume_surge_ratio=volume_surge,
            volume_score=volume_score,
            gain_1d=gain_1d,
            gain_5d=gain_5d,
            gain_10d=gain_10d,
            is_accelerating=is_accelerating,
            acceleration_score=acceleration_score,
            gap_pct=gap_pct,
            gap_type=gap_type,
            gap_score=gap_score,
            high_low_range_pct=range_pct,
            close_position_in_range=close_position,
            intraday_score=intraday_score,
            daily_trend=daily_trend,
            weekly_trend=weekly_trend,
            monthly_trend=monthly_trend,
            timeframe_alignment=timeframe_alignment,
            timeframe_score=timeframe_score,
            timing_confidence=timing_confidence,
            recommended_action=action,
            reason=reason
        )
    
    def _score_volume(self, surge_ratio: float) -> float:
        """Score volume surge (0-100)"""
        if surge_ratio < 1.0:
            return 0.0  # Below average
        elif surge_ratio < self.min_volume_surge:
            return (surge_ratio / self.min_volume_surge) * 60  # 0-60
        elif surge_ratio < 3.0:
            return 60 + ((surge_ratio - self.min_volume_surge) / (3.0 - self.min_volume_surge)) * 30  # 60-90
        else:
            return min(100, 90 + ((surge_ratio - 3.0) / 2.0) * 10)  # 90-100
    
    def _score_acceleration(
        self,
        gain_1d: float,
        gain_5d: float,
        gain_10d: float,
        is_accelerating: bool
    ) -> float:
        """Score price acceleration (0-100)"""
        score = 0.0
        
        # Recent gain
        if gain_1d > 0:
            score += min(30, gain_1d * 3)  # Up to 30 points
        
        # 5-day gain
        if gain_5d > 0:
            score += min(30, gain_5d * 2)  # Up to 30 points
        
        # 10-day gain
        if gain_10d > 0:
            score += min(20, gain_10d)  # Up to 20 points
        
        # Acceleration bonus
        if is_accelerating:
            score += 20
        
        return min(100, score)
    
    def _analyze_gap(self, gap_pct: float) -> Tuple[str, float]:
        """Analyze gap and return (type, score)"""
        abs_gap = abs(gap_pct)
        
        if abs_gap < self.min_gap_pct:
            return "NONE", 50.0  # Neutral
        elif gap_pct > 0:  # Gap up
            if abs_gap < 1.0:
                return "SMALL", 70.0
            elif abs_gap < 3.0:
                return "SIGNIFICANT", 90.0
            else:
                return "BREAKAWAY", 100.0
        else:  # Gap down
            return "NEGATIVE", 20.0  # Bad for momentum
    
    def _score_intraday(self, close_position: float, range_pct: float) -> float:
        """Score intraday strength (0-100)"""
        # Close position score (want close near high)
        position_score = close_position * 70  # 0-70
        
        # Range score (moderate range is good, too tight is weak)
        if range_pct < 1.0:
            range_score = range_pct * 15  # 0-15
        elif range_pct < 5.0:
            range_score = 15 + ((range_pct - 1.0) / 4.0) * 15  # 15-30
        else:
            range_score = 30  # Cap at 30
        
        return min(100, position_score + range_score)
    
    def _detect_trend(self, prices: pd.Series, period: int) -> str:
        """Detect trend direction"""
        if len(prices) < period:
            return "UNKNOWN"
        
        # Simple EMA comparison
        recent = prices.iloc[-1]
        ema = prices.rolling(period).mean().iloc[-1]
        
        if recent > ema * 1.02:
            return "UP"
        elif recent < ema * 0.98:
            return "DOWN"
        else:
            return "SIDEWAYS"
    
    def _score_timeframes(self, daily: str, weekly: str, monthly: str) -> float:
        """Score multi-timeframe alignment (0-100)"""
        score = 0.0
        
        # Daily (most important)
        if daily == "UP":
            score += 50
        elif daily == "SIDEWAYS":
            score += 25
        
        # Weekly
        if weekly == "UP":
            score += 30
        elif weekly in ["SIDEWAYS", "UNKNOWN"]:
            score += 15
        
        # Monthly
        if monthly == "UP":
            score += 20
        elif monthly in ["SIDEWAYS", "UNKNOWN"]:
            score += 10
        
        return min(100, score)
    
    def _create_empty_timing(self, ticker: str, reason: str) -> MomentumTiming:
        """Create empty timing object"""
        return MomentumTiming(
            ticker=ticker,
            current_volume=0,
            avg_volume_20d=0,
            volume_surge_ratio=0,
            volume_score=0,
            gain_1d=0,
            gain_5d=0,
            gain_10d=0,
            is_accelerating=False,
            acceleration_score=0,
            gap_pct=0,
            gap_type="NONE",
            gap_score=0,
            high_low_range_pct=0,
            close_position_in_range=0,
            intraday_score=0,
            daily_trend="UNKNOWN",
            weekly_trend="UNKNOWN",
            monthly_trend="UNKNOWN",
            timeframe_alignment=False,
            timeframe_score=0,
            timing_confidence=0,
            recommended_action="NO_ENTRY",
            reason=reason
        )


def format_momentum_timing(timing: MomentumTiming) -> str:
    """Format momentum timing report"""
    lines = []
    
    lines.append("="*80)
    lines.append(f"MOMENTUM BREAKOUT TIMING: {timing.ticker}")
    lines.append("="*80)
    
    lines.append(f"\nTIMING CONFIDENCE: {timing.timing_confidence:.0f}/100")
    lines.append(f"RECOMMENDATION: {timing.recommended_action}")
    lines.append(f"Reason: {timing.reason}")
    
    lines.append(f"\nVOLUME ({timing.volume_score:.0f}/100):")
    lines.append(f"  Current: {timing.current_volume/1e6:.1f}M")
    lines.append(f"  20-day Avg: {timing.avg_volume_20d/1e6:.1f}M")
    lines.append(f"  Surge Ratio: {timing.volume_surge_ratio:.1f}x")
    
    lines.append(f"\nPRICE ACCELERATION ({timing.acceleration_score:.0f}/100):")
    lines.append(f"  1-day: {timing.gain_1d:+.1f}%")
    lines.append(f"  5-day: {timing.gain_5d:+.1f}%")
    lines.append(f"  10-day: {timing.gain_10d:+.1f}%")
    lines.append(f"  Accelerating: {'✓ YES' if timing.is_accelerating else '✗ No'}")
    
    lines.append(f"\nGAP ANALYSIS ({timing.gap_score:.0f}/100):")
    lines.append(f"  Gap: {timing.gap_pct:+.2f}%")
    lines.append(f"  Type: {timing.gap_type}")
    
    lines.append(f"\nINTRADAY STRENGTH ({timing.intraday_score:.0f}/100):")
    lines.append(f"  Range: {timing.high_low_range_pct:.1f}%")
    lines.append(f"  Close Position: {timing.close_position_in_range*100:.0f}% (0=low, 100=high)")
    
    lines.append(f"\nMULTI-TIMEFRAME ({timing.timeframe_score:.0f}/100):")
    lines.append(f"  Daily: {timing.daily_trend}")
    lines.append(f"  Weekly: {timing.weekly_trend}")
    lines.append(f"  Monthly: {timing.monthly_trend}")
    lines.append(f"  Aligned: {'✓ YES' if timing.timeframe_alignment else '✗ No'}")
    
    return "\n".join(lines)
