"""
Timing Score Module - Predicts immediate trend reversal probability for New Lows

Analyzes 4 key signals to identify which New Low candidates are most likely to
bounce within 1-3 days, minimizing initial drawdown:

1. Short-term Momentum Flip: RSI(2) < 10 and rising
2. Mean Reversion Distance: Price > 3 std deviations from 5-day EMA
3. Volume Exhaustion: Declining volume during last 3 days of price decline
4. Price Action Signal: Hammer or Bullish Engulfing candle

Output: Timing Confidence Score (0-100%)
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
import pandas as pd
import numpy as np


@dataclass
class TimingSignals:
    """Individual timing signals for reversal detection"""
    rsi_momentum_flip: float  # 0-25 points
    mean_reversion_distance: float  # 0-25 points
    volume_exhaustion: float  # 0-25 points
    price_action_signal: float  # 0-25 points
    
    # Details for transparency
    rsi_2_current: float
    rsi_2_previous: float
    rsi_2_two_days_ago: float  # For RSI Hook detection
    distance_from_ema5_std: float
    volume_trend_last_3d: str  # "Decreasing", "Flat", "Increasing"
    volume_confirmed: bool  # Enhanced volume confirmation
    candle_pattern: str  # "Hammer", "Bullish Engulfing", "Neutral", "Bearish"
    rsi_hook_boost: float  # RSI Hook bonus (0 or 20%)
    
    @property
    def total_score(self) -> float:
        """Calculate total timing confidence (0-100) with RSI Hook boost"""
        base_score = (
            self.rsi_momentum_flip +
            self.mean_reversion_distance +
            self.volume_exhaustion +
            self.price_action_signal
        )
        # Apply RSI Hook boost (up to 20% increase)
        boosted_score = base_score * (1 + self.rsi_hook_boost)
        return min(100.0, boosted_score)  # Cap at 100


class TimingScoreCalculator:
    """Calculate timing confidence for immediate reversal probability"""
    
    # THRESHOLD FOR ACTIVE BUY SIGNALS
    TIMING_THRESHOLD = 50.0  # Minimum timing confidence for buy signal
    
    def __init__(self):
        self.rsi_period = 2
        self.ema_period = 5
        self.std_threshold = 3.0
        self.volume_lookback = 3
    
    def calculate_timing_score(
        self,
        ticker: str,
        price_data: pd.DataFrame
    ) -> Optional[TimingSignals]:
        """
        Calculate timing confidence score for a New Low candidate
        
        Args:
            ticker: Stock ticker symbol
            price_data: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)
                       Index should be datetime, sorted ascending
        
        Returns:
            TimingSignals with score breakdown, or None if insufficient data
        """
        if price_data is None or len(price_data) < 20:
            return None
        
        try:
            # Ensure we have required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in price_data.columns for col in required_cols):
                return None
            
            # Calculate all signals
            rsi_score, rsi_current, rsi_prev, rsi_two_days = self._calculate_rsi_momentum_flip(price_data)
            mean_rev_score, distance_std = self._calculate_mean_reversion_distance(price_data)
            vol_exh_score, vol_trend = self._calculate_volume_exhaustion(price_data)
            price_action_score, candle_pattern = self._calculate_price_action_signal(price_data)
            
            # Enhanced volume confirmation
            volume_confirmed = self.check_volume_exhaustion(price_data)
            
            # RSI Hook detection (RSI < 10 for 2 days, then turns up > 15)
            rsi_hook_boost = self._detect_rsi_hook(rsi_current, rsi_prev, rsi_two_days)
            
            return TimingSignals(
                rsi_momentum_flip=rsi_score,
                mean_reversion_distance=mean_rev_score,
                volume_exhaustion=vol_exh_score,
                price_action_signal=price_action_score,
                rsi_2_current=rsi_current,
                rsi_2_previous=rsi_prev,
                rsi_2_two_days_ago=rsi_two_days,
                distance_from_ema5_std=distance_std,
                volume_trend_last_3d=vol_trend,
                volume_confirmed=volume_confirmed,
                candle_pattern=candle_pattern,
                rsi_hook_boost=rsi_hook_boost
            )
        
        except Exception as e:
            print(f"Error calculating timing score for {ticker}: {e}")
            return None
    
    def _calculate_rsi_momentum_flip(self, df: pd.DataFrame) -> tuple[float, float, float, float]:
        """
        Calculate RSI(2) momentum flip signal
        
        Returns:
            (score 0-25, current RSI, previous RSI, two days ago RSI)
        """
        # Calculate RSI(2)
        close = df['Close'].values
        delta = np.diff(close)
        
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)
        
        # Use simple moving average for RSI(2)
        avg_gains = pd.Series(gains).rolling(window=self.rsi_period).mean()
        avg_losses = pd.Series(losses).rolling(window=self.rsi_period).mean()
        
        rs = avg_gains / (avg_losses + 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        
        if len(rsi) < 3:
            return 0.0, 0.0, 0.0, 0.0
        
        rsi_current = rsi.iloc[-1]
        rsi_previous = rsi.iloc[-2]
        rsi_two_days_ago = rsi.iloc[-3]
        
        # Scoring logic:
        # - RSI < 10 and rising: 25 points (perfect)
        # - RSI < 15 and rising: 20 points (good)
        # - RSI < 20 and rising: 15 points (ok)
        # - RSI < 10 but flat/falling: 10 points (oversold but no flip yet)
        # - Otherwise: 0 points
        
        is_rising = rsi_current > rsi_previous
        
        if rsi_current < 10 and is_rising:
            score = 25.0
        elif rsi_current < 15 and is_rising:
            score = 20.0
        elif rsi_current < 20 and is_rising:
            score = 15.0
        elif rsi_current < 10:
            score = 10.0
        else:
            score = 0.0
        
        return score, rsi_current, rsi_previous, rsi_two_days_ago
    
    def _calculate_mean_reversion_distance(self, df: pd.DataFrame) -> tuple[float, float]:
        """
        Calculate distance from 5-day EMA in standard deviations
        
        Returns:
            (score 0-25, distance in std deviations)
        """
        close = df['Close']
        
        # Calculate 5-day EMA
        ema5 = close.ewm(span=self.ema_period, adjust=False).mean()
        
        # Calculate rolling standard deviation (5-day window)
        rolling_std = close.rolling(window=self.ema_period).std()
        
        current_price = close.iloc[-1]
        current_ema = ema5.iloc[-1]
        current_std = rolling_std.iloc[-1]
        
        if current_std == 0 or pd.isna(current_std):
            return 0.0, 0.0
        
        # Distance below EMA in standard deviations (negative = below)
        distance_std = (current_price - current_ema) / current_std
        
        # Scoring logic (only score if below EMA):
        # - More than 3 std below: 25 points (extreme rubber band)
        # - 2.5 to 3 std below: 20 points
        # - 2 to 2.5 std below: 15 points
        # - 1.5 to 2 std below: 10 points
        # - Less than 1.5 std below: 0 points
        
        if distance_std >= 0:  # Above EMA - not oversold
            score = 0.0
        elif distance_std < -3.0:
            score = 25.0
        elif distance_std < -2.5:
            score = 20.0
        elif distance_std < -2.0:
            score = 15.0
        elif distance_std < -1.5:
            score = 10.0
        else:
            score = 0.0
        
        return score, distance_std
    
    def _calculate_volume_exhaustion(self, df: pd.DataFrame) -> tuple[float, str]:
        """
        Check if last 3 days of decline happened on decreasing volume
        
        Returns:
            (score 0-25, volume trend description)
        """
        if len(df) < self.volume_lookback:
            return 0.0, "Insufficient Data"
        
        # Get last 3 days
        recent = df.tail(self.volume_lookback)
        
        # Check if price declined all 3 days
        closes = recent['Close'].values
        price_declining = all(closes[i] < closes[i-1] for i in range(1, len(closes)))
        
        # Check volume trend
        volumes = recent['Volume'].values
        volume_decreasing = all(volumes[i] < volumes[i-1] for i in range(1, len(volumes)))
        volume_flat = np.std(volumes) < (np.mean(volumes) * 0.1)  # CV < 10%
        
        # Scoring logic:
        # - Price declining + volume decreasing: 25 points (perfect exhaustion)
        # - Price declining + volume flat: 15 points (potential exhaustion)
        # - Price declining + volume increasing: 0 points (strong selling)
        # - Price not declining consistently: 0 points
        
        if price_declining and volume_decreasing:
            score = 25.0
            trend = "Decreasing"
        elif price_declining and volume_flat:
            score = 15.0
            trend = "Flat"
        elif price_declining:
            score = 0.0
            trend = "Increasing"
        else:
            score = 0.0
            trend = "Price Not Declining"
        
        return score, trend
    
    def _calculate_price_action_signal(self, df: pd.DataFrame) -> tuple[float, str]:
        """
        Identify Hammer or Bullish Engulfing pattern on most recent candle
        
        Returns:
            (score 0-25, pattern name)
        """
        if len(df) < 2:
            return 0.0, "Insufficient Data"
        
        # Get last 2 candles
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        o, h, l, c = current['Open'], current['High'], current['Low'], current['Close']
        prev_o, prev_c = previous['Open'], previous['Close']
        
        # Calculate candle metrics
        body = abs(c - o)
        total_range = h - l
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        
        # Avoid division by zero
        if total_range == 0:
            return 0.0, "Doji"
        
        # 1. Check for HAMMER
        # - Small body (< 30% of range)
        # - Long lower wick (> 2x body)
        # - Small upper wick
        # - Close in upper 25% of range
        is_small_body = body < (total_range * 0.3)
        is_long_lower_wick = lower_wick > (2 * body)
        is_small_upper_wick = upper_wick < body
        close_position = (c - l) / total_range
        is_close_high = close_position > 0.75
        
        is_hammer = (is_small_body and is_long_lower_wick and 
                     is_small_upper_wick and is_close_high)
        
        # 2. Check for BULLISH ENGULFING
        # - Previous candle was bearish
        # - Current candle is bullish
        # - Current body engulfs previous body
        # - Close in upper 25% of range
        prev_bearish = prev_c < prev_o
        current_bullish = c > o
        engulfs = (o < prev_c) and (c > prev_o)
        
        is_bullish_engulfing = (prev_bearish and current_bullish and 
                                engulfs and is_close_high)
        
        # 3. Check for any bullish candle with close in upper 25%
        is_bullish_high_close = (c > o) and is_close_high
        
        # Scoring logic:
        # - Hammer: 25 points (strongest reversal signal)
        # - Bullish Engulfing: 25 points (strongest reversal signal)
        # - Bullish with high close: 15 points (good signal)
        # - Otherwise: 0 points
        
        if is_hammer:
            return 25.0, "Hammer"
        elif is_bullish_engulfing:
            return 25.0, "Bullish Engulfing"
        elif is_bullish_high_close:
            return 15.0, "Bullish High Close"
        elif c > o:
            return 5.0, "Bullish"
        else:
            return 0.0, "Bearish/Neutral"
    
    def check_volume_exhaustion(self, df: pd.DataFrame) -> bool:
        """
        Enhanced volume confirmation logic
        
        Returns True if:
        - Latest day volume is 15%+ lower than 5-day average during price decline (seller exhaustion), OR
        - Latest day is green with volume 10%+ higher than 5-day average (buyers stepping in)
        
        Returns:
            bool: True if volume confirms reversal setup
        """
        if len(df) < 6:
            return False
        
        try:
            # Get last 6 days (5 for average + 1 current)
            recent = df.tail(6)
            
            # Current day
            current_close = recent['Close'].iloc[-1]
            current_open = recent['Open'].iloc[-1]
            current_volume = recent['Volume'].iloc[-1]
            
            # Previous day
            prev_close = recent['Close'].iloc[-2]
            
            # 5-day average volume (excluding current day)
            avg_volume_5d = recent['Volume'].iloc[:-1].mean()
            
            if avg_volume_5d == 0:
                return False
            
            # Check if price is declining
            is_declining = current_close < prev_close
            
            # Check if current day is green (bullish)
            is_green = current_close > current_open
            
            # Calculate volume deviation
            volume_ratio = current_volume / avg_volume_5d
            
            # Condition 1: Declining price with volume 15%+ below average (seller exhaustion)
            seller_exhaustion = is_declining and volume_ratio < 0.85
            
            # Condition 2: Green day with volume 10%+ above average (buyers stepping in)
            buyer_entry = is_green and volume_ratio > 1.10
            
            return seller_exhaustion or buyer_entry
        
        except Exception as e:
            return False
    
    def _detect_rsi_hook(self, rsi_current: float, rsi_prev: float, rsi_two_days: float) -> float:
        """
        Detect RSI(2) 'Hook' pattern for 20% timing boost
        
        Hook pattern:
        - RSI was below 10 for the last 2 days
        - RSI has now turned up and closed above 15
        - Indicates short-term momentum spring is releasing
        
        Args:
            rsi_current: Current RSI(2) value
            rsi_prev: Previous day RSI(2)
            rsi_two_days: Two days ago RSI(2)
        
        Returns:
            float: 0.20 (20% boost) if hook detected, else 0.0
        """
        # Check if RSI was below 10 for last 2 days
        was_oversold = (rsi_prev < 10) and (rsi_two_days < 10)
        
        # Check if RSI has turned up above 15
        has_hooked_up = rsi_current > 15 and rsi_current > rsi_prev
        
        if was_oversold and has_hooked_up:
            return 0.20  # 20% boost
        else:
            return 0.0


def format_timing_summary(signals: TimingSignals) -> str:
    """
    Format timing signals into readable summary
    
    Args:
        signals: TimingSignals object
    
    Returns:
        Multi-line string summary
    """
    summary = []
    summary.append(f"TIMING CONFIDENCE: {signals.total_score:.1f}% (0-100)")
    summary.append("")
    summary.append("Signal Breakdown:")
    summary.append(f"  • RSI Momentum Flip: {signals.rsi_momentum_flip:.1f}/25")
    summary.append(f"    RSI(2): {signals.rsi_2_current:.1f} (prev: {signals.rsi_2_previous:.1f})")
    summary.append(f"  • Mean Reversion: {signals.mean_reversion_distance:.1f}/25")
    summary.append(f"    Distance: {signals.distance_from_ema5_std:.2f} std from EMA(5)")
    summary.append(f"  • Volume Exhaustion: {signals.volume_exhaustion:.1f}/25")
    summary.append(f"    Volume Trend: {signals.volume_trend_last_3d}")
    summary.append(f"  • Price Action: {signals.price_action_signal:.1f}/25")
    summary.append(f"    Candle Pattern: {signals.candle_pattern}")
    
    return "\n".join(summary)
