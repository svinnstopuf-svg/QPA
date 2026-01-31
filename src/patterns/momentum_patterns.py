"""
Momentum Pattern Detector - Breakout Patterns

Philosophy:
- Buy strength, not weakness
- Breakouts from consolidation after uptrend
- High relative strength leaders
- Volume confirms breakout

Primary Momentum Patterns:
1. Cup & Handle - Classic accumulation → breakout
2. Ascending Triangle - Higher lows, flat top
3. Bull Pennant - Tight consolidation after strong move
4. Stage 2 Uptrend - Weinstein method validation
5. VCP Breakout - Volatility contraction → expansion

Requirements:
- Must be in established uptrend (Price > EMA50 > EMA200)
- RS-Rating ≥ 90 (top 10% minimum)
- Volume surge on breakout (2x+ average)
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from ..utils.market_data import MarketData


@dataclass
class MomentumPattern:
    """A momentum breakout pattern setup."""
    pattern_name: str
    pattern_type: str  # "BREAKOUT", "CONTINUATION", "STAGE2"
    entry_price: float
    breakout_level: float
    stop_loss: float  # ATR-based
    target_price: float  # Based on pattern height
    
    # Pattern-specific metrics
    base_length_days: int  # Consolidation period
    base_depth_pct: float  # % depth of consolidation
    handle_depth_pct: float  # For Cup & Handle
    
    # Validation
    volume_surge_ratio: float  # Breakout vol / avg vol
    price_above_ema50: bool
    ema50_above_ema200: bool
    rs_rating: float
    
    # Strength
    pattern_quality: float  # 0-100 quality score
    breakout_strength: float  # 0-1 strength of breakout
    description: str


class MomentumPatternDetector:
    """
    Detects momentum breakout patterns for position trading.
    
    Focus: Instruments in uptrend ready to break higher.
    Entry: On breakout from consolidation with volume.
    """
    
    def __init__(
        self,
        min_rs_rating: float = 90.0,
        min_volume_surge: float = 2.0,
        min_consolidation_days: int = 15
    ):
        self.min_rs_rating = min_rs_rating
        self.min_volume_surge = min_volume_surge
        self.min_consolidation_days = min_consolidation_days
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)
        
        ema = np.zeros(len(prices))
        ema[:period] = np.nan
        ema[period-1] = np.mean(prices[:period])
        
        multiplier = 2.0 / (period + 1)
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def calculate_atr(self, market_data: MarketData, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = market_data.high_prices
        low = market_data.low_prices
        close = market_data.close_prices
        
        if len(close) < period:
            return 0.0
        
        tr = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - np.roll(close, 1)),
                np.abs(low - np.roll(close, 1))
            )
        )
        tr[0] = high[0] - low[0]
        
        atr = np.mean(tr[-period:])
        return atr
    
    def check_uptrend(self, prices: np.ndarray) -> Tuple[bool, float, float]:
        """
        Check if instrument is in valid uptrend.
        
        Returns:
            (is_uptrend, ema50, ema200)
        """
        if len(prices) < 200:
            return False, 0.0, 0.0
        
        ema50 = self.calculate_ema(prices, 50)
        ema200 = self.calculate_ema(prices, 200)
        
        current_ema50 = ema50[-1]
        current_ema200 = ema200[-1]
        current_price = prices[-1]
        
        # Valid uptrend: Price > EMA50 > EMA200
        is_uptrend = (current_price > current_ema50) and (current_ema50 > current_ema200)
        
        return is_uptrend, current_ema50, current_ema200
    
    def find_pivot_highs(
        self,
        prices: np.ndarray,
        window: int = 5
    ) -> List[Tuple[int, float]]:
        """Find local maxima (pivot highs)"""
        pivots = []
        
        for i in range(window, len(prices) - window):
            is_high = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j] > prices[i]:
                    is_high = False
                    break
            
            if is_high:
                pivots.append((i, prices[i]))
        
        return pivots
    
    def find_pivot_lows(
        self,
        prices: np.ndarray,
        window: int = 5
    ) -> List[Tuple[int, float]]:
        """Find local minima (pivot lows)"""
        pivots = []
        
        for i in range(window, len(prices) - window):
            is_low = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j] < prices[i]:
                    is_low = False
                    break
            
            if is_low:
                pivots.append((i, prices[i]))
        
        return pivots
    
    def detect_cup_and_handle(
        self,
        market_data: MarketData,
        rs_rating: float
    ) -> List[MomentumPattern]:
        """
        Detect Cup & Handle pattern.
        
        Criteria:
        1. Cup: U-shaped base, 7-65 weeks (35-325 days)
        2. Depth: 12-33% from prior high
        3. Handle: 1-4 weeks, pullback <12% from cup high
        4. Breakout: Volume 2x+ average
        5. Must be in uptrend before cup
        
        Returns:
            List of MomentumPattern objects
        """
        patterns = []
        prices = market_data.close_prices
        volume = market_data.volume
        
        if len(prices) < 200:
            return patterns
        
        # Check uptrend
        is_uptrend, ema50, ema200 = self.check_uptrend(prices)
        if not is_uptrend:
            return patterns
        
        # Check RS-Rating
        if rs_rating < self.min_rs_rating:
            return patterns
        
        # Find pivot highs and lows
        pivot_highs = self.find_pivot_highs(prices, window=10)
        pivot_lows = self.find_pivot_lows(prices, window=10)
        
        if len(pivot_highs) < 2 or len(pivot_lows) < 1:
            return patterns
        
        # Look for Cup & Handle
        for i in range(len(pivot_highs) - 1):
            left_rim_idx, left_rim_price = pivot_highs[i]
            
            # Find potential cup bottom after left rim
            cup_bottoms = [p for p in pivot_lows if p[0] > left_rim_idx]
            if not cup_bottoms:
                continue
            
            for cup_bottom_idx, cup_bottom_price in cup_bottoms:
                # Find right rim (pivot high after cup bottom)
                right_rims = [p for p in pivot_highs if p[0] > cup_bottom_idx]
                if not right_rims:
                    continue
                
                right_rim_idx, right_rim_price = right_rims[0]
                
                # Cup depth check (12-33%)
                cup_depth = ((left_rim_price - cup_bottom_price) / left_rim_price) * 100
                if cup_depth < 12 or cup_depth > 33:
                    continue
                
                # Cup length check (35-325 days)
                cup_length = right_rim_idx - left_rim_idx
                if cup_length < 35 or cup_length > 325:
                    continue
                
                # Right rim should be near left rim price (±5%)
                rim_price_diff = abs(right_rim_price - left_rim_price) / left_rim_price
                if rim_price_diff > 0.05:
                    continue
                
                # Find handle (pullback after right rim)
                handle_start_idx = right_rim_idx
                handle_end_idx = min(handle_start_idx + 28, len(prices) - 1)  # Max 4 weeks
                
                if handle_end_idx - handle_start_idx < 5:  # Min 1 week
                    continue
                
                handle_prices = prices[handle_start_idx:handle_end_idx+1]
                handle_low = np.min(handle_prices)
                handle_depth = ((right_rim_price - handle_low) / right_rim_price) * 100
                
                # Handle depth check (<12%)
                if handle_depth > 12:
                    continue
                
                # Check if we're at/past handle and price is breaking out
                current_idx = len(prices) - 1
                if current_idx < handle_end_idx:
                    continue
                
                current_price = prices[-1]
                breakout_level = right_rim_price
                
                # Check breakout volume
                recent_volume = volume[-5:]  # Last 5 days
                avg_volume = np.mean(volume[-60:-5])  # Previous 60 days
                max_recent_vol = np.max(recent_volume)
                volume_surge_ratio = max_recent_vol / avg_volume if avg_volume > 0 else 0
                
                if volume_surge_ratio < self.min_volume_surge:
                    continue
                
                # Calculate stop loss (handle low or ATR-based)
                atr = self.calculate_atr(market_data)
                stop_loss = max(handle_low, current_price - 2 * atr)
                
                # Calculate target (cup depth projected up)
                target_price = breakout_level + (left_rim_price - cup_bottom_price)
                
                # Pattern quality score
                quality_score = min(100, (
                    (volume_surge_ratio / self.min_volume_surge) * 30 +  # 30pts for volume
                    (rs_rating / 100) * 40 +  # 40pts for RS
                    (1 - rim_price_diff / 0.05) * 30  # 30pts for rim symmetry
                ))
                
                pattern = MomentumPattern(
                    pattern_name="Cup & Handle",
                    pattern_type="BREAKOUT",
                    entry_price=current_price,
                    breakout_level=breakout_level,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    base_length_days=cup_length,
                    base_depth_pct=cup_depth,
                    handle_depth_pct=handle_depth,
                    volume_surge_ratio=volume_surge_ratio,
                    price_above_ema50=True,
                    ema50_above_ema200=True,
                    rs_rating=rs_rating,
                    pattern_quality=quality_score,
                    breakout_strength=(current_price - breakout_level) / breakout_level,
                    description=f"Cup: {cup_length}d, {cup_depth:.1f}% deep | Handle: {handle_depth:.1f}% | Vol: {volume_surge_ratio:.1f}x"
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def detect_ascending_triangle(
        self,
        market_data: MarketData,
        rs_rating: float
    ) -> List[MomentumPattern]:
        """
        Detect Ascending Triangle pattern.
        
        Criteria:
        1. Flat resistance: 3+ touches at same level (±2%)
        2. Rising support: Series of higher lows
        3. Duration: 15-90 days
        4. Breakout: Above resistance on 2x volume
        
        Returns:
            List of MomentumPattern objects
        """
        patterns = []
        prices = market_data.close_prices
        volume = market_data.volume
        
        if len(prices) < 60:
            return patterns
        
        # Check uptrend
        is_uptrend, ema50, ema200 = self.check_uptrend(prices)
        if not is_uptrend:
            return patterns
        
        if rs_rating < self.min_rs_rating:
            return patterns
        
        # Find pivot highs and lows in last 90 days
        lookback = min(90, len(prices))
        recent_prices = prices[-lookback:]
        
        pivot_highs = self.find_pivot_highs(recent_prices, window=3)
        pivot_lows = self.find_pivot_lows(recent_prices, window=3)
        
        if len(pivot_highs) < 3 or len(pivot_lows) < 3:
            return patterns
        
        # Check for flat resistance (highs at same level)
        high_prices = [p[1] for p in pivot_highs[-5:]]  # Last 5 highs
        resistance_level = np.mean(high_prices)
        resistance_std = np.std(high_prices)
        
        # Highs should be within 2% of each other
        if resistance_std / resistance_level > 0.02:
            return patterns
        
        # Check for rising support (higher lows)
        low_prices = [p[1] for p in pivot_lows[-5:]]  # Last 5 lows
        higher_lows = all(low_prices[i] < low_prices[i+1] for i in range(len(low_prices)-1))
        
        if not higher_lows:
            return patterns
        
        # Calculate triangle metrics
        triangle_start_idx = pivot_lows[0][0]
        triangle_length = lookback - triangle_start_idx
        
        if triangle_length < self.min_consolidation_days:
            return patterns
        
        # Check if price is breaking resistance
        current_price = prices[-1]
        if current_price <= resistance_level * 1.01:  # Must be above resistance
            return patterns
        
        # Check volume surge
        recent_volume = volume[-5:]
        avg_volume = np.mean(volume[-60:-5])
        max_recent_vol = np.max(recent_volume)
        volume_surge_ratio = max_recent_vol / avg_volume if avg_volume > 0 else 0
        
        if volume_surge_ratio < self.min_volume_surge:
            return patterns
        
        # Calculate stop loss (below last low or ATR-based)
        atr = self.calculate_atr(market_data)
        last_low = low_prices[-1]
        stop_loss = max(last_low, current_price - 2 * atr)
        
        # Calculate target (triangle height projected up)
        triangle_height = resistance_level - low_prices[0]
        target_price = resistance_level + triangle_height
        
        # Pattern quality
        quality_score = min(100, (
            (volume_surge_ratio / self.min_volume_surge) * 35 +
            (rs_rating / 100) * 40 +
            (len(pivot_highs) / 5) * 25  # More touches = better
        ))
        
        pattern = MomentumPattern(
            pattern_name="Ascending Triangle",
            pattern_type="BREAKOUT",
            entry_price=current_price,
            breakout_level=resistance_level,
            stop_loss=stop_loss,
            target_price=target_price,
            base_length_days=triangle_length,
            base_depth_pct=0.0,  # N/A for triangle
            handle_depth_pct=0.0,
            volume_surge_ratio=volume_surge_ratio,
            price_above_ema50=True,
            ema50_above_ema200=True,
            rs_rating=rs_rating,
            pattern_quality=quality_score,
            breakout_strength=(current_price - resistance_level) / resistance_level,
            description=f"Triangle: {triangle_length}d | {len(pivot_highs)} touches | Vol: {volume_surge_ratio:.1f}x"
        )
        
        patterns.append(pattern)
        
        return patterns
    
    def detect_bull_pennant(
        self,
        market_data: MarketData,
        rs_rating: float
    ) -> List[MomentumPattern]:
        """
        Detect Bull Pennant (continuation pattern).
        
        Criteria:
        1. Strong prior move: +20%+ in <30 days (flagpole)
        2. Tight consolidation: 5-20 days, <10% range
        3. Converging trendlines (pennant shape)
        4. Breakout: Above resistance on volume
        
        Returns:
            List of MomentumPattern objects
        """
        patterns = []
        prices = market_data.close_prices
        volume = market_data.volume
        
        if len(prices) < 60:
            return patterns
        
        # Check uptrend
        is_uptrend, ema50, ema200 = self.check_uptrend(prices)
        if not is_uptrend:
            return patterns
        
        if rs_rating < self.min_rs_rating:
            return patterns
        
        # Look for strong prior move (flagpole)
        for lookback in [20, 25, 30]:
            if len(prices) < lookback + 20:
                continue
            
            pole_start_price = prices[-(lookback + 20)]
            pole_end_price = prices[-20]
            pole_gain = ((pole_end_price - pole_start_price) / pole_start_price) * 100
            
            if pole_gain < 20:  # Need 20%+ move
                continue
            
            # Check consolidation after pole (last 20 days)
            consolidation_prices = prices[-20:]
            cons_high = np.max(consolidation_prices)
            cons_low = np.min(consolidation_prices)
            cons_range = ((cons_high - cons_low) / cons_low) * 100
            
            if cons_range > 10:  # Max 10% range
                continue
            
            # Check for converging range (pennant shape)
            first_half_range = (np.max(consolidation_prices[:10]) - np.min(consolidation_prices[:10])) / np.min(consolidation_prices[:10])
            second_half_range = (np.max(consolidation_prices[10:]) - np.min(consolidation_prices[10:])) / np.min(consolidation_prices[10:])
            
            if second_half_range >= first_half_range:  # Must be tightening
                continue
            
            # Check current breakout
            current_price = prices[-1]
            breakout_level = cons_high
            
            if current_price <= breakout_level:
                continue
            
            # Volume check
            recent_volume = volume[-5:]
            avg_volume = np.mean(volume[-60:-5])
            max_recent_vol = np.max(recent_volume)
            volume_surge_ratio = max_recent_vol / avg_volume if avg_volume > 0 else 0
            
            if volume_surge_ratio < self.min_volume_surge:
                continue
            
            # Calculate targets
            atr = self.calculate_atr(market_data)
            stop_loss = cons_low
            target_price = breakout_level + (pole_end_price - pole_start_price)  # Project pole height
            
            quality_score = min(100, (
                (pole_gain / 20) * 30 +  # Stronger pole = better
                (volume_surge_ratio / self.min_volume_surge) * 35 +
                (rs_rating / 100) * 35
            ))
            
            pattern = MomentumPattern(
                pattern_name="Bull Pennant",
                pattern_type="CONTINUATION",
                entry_price=current_price,
                breakout_level=breakout_level,
                stop_loss=stop_loss,
                target_price=target_price,
                base_length_days=20,
                base_depth_pct=cons_range,
                handle_depth_pct=0.0,
                volume_surge_ratio=volume_surge_ratio,
                price_above_ema50=True,
                ema50_above_ema200=True,
                rs_rating=rs_rating,
                pattern_quality=quality_score,
                breakout_strength=(current_price - breakout_level) / breakout_level,
                description=f"Pole: +{pole_gain:.1f}% in {lookback}d | Pennant: {cons_range:.1f}% range | Vol: {volume_surge_ratio:.1f}x"
            )
            
            patterns.append(pattern)
            break  # Take first valid pennant
        
        return patterns
    
    def detect_all_patterns(
        self,
        market_data: MarketData,
        rs_rating: float
    ) -> List[MomentumPattern]:
        """
        Run all momentum pattern detectors.
        
        Returns:
            Combined list of all detected patterns
        """
        all_patterns = []
        
        # Cup & Handle
        all_patterns.extend(self.detect_cup_and_handle(market_data, rs_rating))
        
        # Ascending Triangle
        all_patterns.extend(self.detect_ascending_triangle(market_data, rs_rating))
        
        # Bull Pennant
        all_patterns.extend(self.detect_bull_pennant(market_data, rs_rating))
        
        # Sort by quality score
        all_patterns.sort(key=lambda p: p.pattern_quality, reverse=True)
        
        return all_patterns
