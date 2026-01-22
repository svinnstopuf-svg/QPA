"""
Position Trading Pattern Detector - Structural Reversals

Philosophy:
- We are POSITION TRADERS, not day traders
- We buy at structural bottoms after declines, not at tops
- We hold for 1-3 months (21-63 days), not 1-3 days
- Patterns must show: DECLINE -> STABILIZATION -> REVERSAL

Primary Patterns (Structural):
1. Double Bottom - Price tests same low twice, forms "W"
2. Inverse Head & Shoulders - Classic reversal after decline
3. Bull Flag After Decline - Consolidation after -15%+ drop
4. Higher Lows Pattern - Downtrend ending, uptrend starting

Secondary Patterns (Noise):
- Day of week effects (Wednesday, etc.)
- Calendar effects (January, etc.)
- Short-term momentum (Extended Rally, etc.)
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from ..utils.market_data import MarketData
from .detector import MarketSituation

@dataclass
class PositionTradingSetup:
    """A position trading setup with structural validity."""
    pattern_name: str
    pattern_type: str  # "PRIMARY" or "SECONDARY"
    entry_date_idx: int
    decline_magnitude: float  # % decline before pattern (e.g. -15%)
    stabilization_days: int  # Days of stabilization
    reversal_strength: float  # 0-1, strength of reversal signal
    description: str


class PositionTradingPatternDetector:
    """
    Detects structural bottom patterns for position trading.
    
    Rules:
    1. Must have prior decline (-10% minimum over 60+ days)
    2. Must show stabilization (lower volatility, base forming)
    3. Reversal must be structural (double bottom, etc.), not noise
    """
    
    def __init__(
        self,
        min_decline_pct: float = 10.0,  # Minimum decline to qualify as "bottom"
        lookback_decline: int = 60,  # Days to check for decline
        min_stabilization_days: int = 10  # Days of base-building
    ):
        self.min_decline_pct = min_decline_pct
        self.lookback_decline = lookback_decline
        self.min_stabilization_days = min_stabilization_days
    
    def find_pivot_lows(
        self,
        prices: np.ndarray,
        volume: np.ndarray,
        window: int = 5
    ) -> List[Tuple[int, float, float]]:
        """
        Find significant pivot lows (local minima with volume context).
        
        Returns:
            List of (index, price, volume) tuples
        """
        pivots = []
        
        for i in range(window, len(prices) - window):
            # Check if this is a local minimum
            is_low = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j] < prices[i]:
                    is_low = False
                    break
            
            if is_low:
                pivots.append((i, prices[i], volume[i]))
        
        return pivots
    
    def find_pivot_highs(
        self,
        prices: np.ndarray,
        window: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Find significant pivot highs (local maxima).
        
        Returns:
            List of (index, price) tuples
        """
        pivots = []
        
        for i in range(window, len(prices) - window):
            # Check if this is a local maximum
            is_high = True
            for j in range(i - window, i + window + 1):
                if j != i and prices[j] > prices[i]:
                    is_high = False
                    break
            
            if is_high:
                pivots.append((i, prices[i]))
        
        return pivots
    
    def detect_double_bottom(
        self,
        market_data: MarketData,
        price_tolerance: float = 0.02,  # 2% tolerance for "same" low
        min_bounce_pct: float = 0.05  # 5% minimum bounce
    ) -> List[MarketSituation]:
        """
        Detect double bottom (W-pattern) using pivot-based analysis.
        
        Advanced Criteria:
        1. Pivot Low 1: Significant local bottom
        2. Reaction High: Peak at least 5% above Low 1
        3. Pivot Low 2: New bottom within +/- 2% of Low 1 price
        4. Volume Check: Volume at Low 2 < Volume at Low 1 (sellers exhausted)
        5. Trigger: Price breaks above Reaction High on high volume
        """
        situations = []
        prices = market_data.close_prices
        volume = market_data.volume
        
        # Need sufficient data
        if len(prices) < 60:
            return situations
        
        # Find all pivot lows and highs
        pivot_lows = self.find_pivot_lows(prices, volume, window=5)
        pivot_highs = self.find_pivot_highs(prices, window=5)
        
        if len(pivot_lows) < 2:
            return situations
        
        # Look for W-patterns
        for i in range(len(pivot_lows) - 1):
            low1_idx, low1_price, low1_vol = pivot_lows[i]
            
            # Look for second low after first
            for j in range(i + 1, len(pivot_lows)):
                low2_idx, low2_price, low2_vol = pivot_lows[j]
                
                # Must be at least 10 days apart
                if low2_idx - low1_idx < 10:
                    continue
                
                # Check if Low 2 is within tolerance of Low 1 ("same" level)
                price_diff = abs(low2_price - low1_price) / low1_price
                if price_diff > price_tolerance:
                    continue
                
                # Find reaction high between the two lows
                highs_between = [h for h in pivot_highs if low1_idx < h[0] < low2_idx]
                if not highs_between:
                    continue
                
                # Get the highest peak between lows
                reaction_high_idx, reaction_high_price = max(highs_between, key=lambda x: x[1])
                bounce_height = (reaction_high_price - low1_price) / low1_price
                
                # Reaction high must be significant (5%+ bounce)
                if bounce_height < min_bounce_pct:
                    continue
                
                # VOLUME CHECK: Volume at Low 2 should be lower (sellers exhausted)
                volume_declining = low2_vol < low1_vol
                
                # Check for prior decline before Low 1
                decline_start_idx = max(0, low1_idx - self.lookback_decline)
                decline_high = np.max(prices[decline_start_idx:low1_idx])
                decline_pct = ((low1_price - decline_high) / decline_high) * 100
                
                if abs(decline_pct) < self.min_decline_pct:
                    continue
                
                # Check if we're past Low 2 and potentially triggering
                current_idx = len(prices) - 1
                if low2_idx < current_idx:
                    # Check if price has broken above reaction high
                    price_after_low2 = prices[low2_idx:]
                    triggered = np.any(price_after_low2 > reaction_high_price)
                    
                    # Check volume on breakout
                    if triggered:
                        breakout_idx = low2_idx + np.argmax(price_after_low2 > reaction_high_price)
                        breakout_vol = volume[breakout_idx]
                        avg_vol = np.mean(volume[max(0, breakout_idx-20):breakout_idx])
                        high_volume_breakout = breakout_vol > avg_vol * 1.5
                    else:
                        breakout_idx = low2_idx
                        high_volume_breakout = False
                    
                    situations.append(MarketSituation(
                        description=f"Double Bottom (W-Pattern) after {decline_pct:.0f}% decline",
                        timestamp_indices=np.array([breakout_idx if triggered else low2_idx]),
                        metadata={
                            'signal_type': 'structural_reversal',
                            'pattern': 'double_bottom',
                            'priority': 'PRIMARY',
                            'decline_pct': decline_pct,
                            'bounce_height': bounce_height * 100,
                            'low1_idx': low1_idx,
                            'low2_idx': low2_idx,
                            'reaction_high_idx': reaction_high_idx,
                            'volume_declining': volume_declining,
                            'triggered': triggered,
                            'high_volume_breakout': high_volume_breakout if triggered else False
                        }
                    ))
                    
                    # Only report most recent double bottom per instrument
                    break
            
            if situations:
                break
        
        return situations
    
    def detect_inverse_head_and_shoulders(
        self,
        market_data: MarketData
    ) -> List[MarketSituation]:
        """
        Detect inverse head & shoulders.
        
        Structure:
        1. Left shoulder (low)
        2. Head (lower low)
        3. Right shoulder (low, similar to left)
        4. Neckline break
        """
        situations = []
        prices = market_data.close_prices
        
        if len(prices) < 60:
            return situations
        
        # Scan for IH&S
        for i in range(40, len(prices) - 20):
            # Look for three lows in a 40-day window
            window = prices[i-40:i]
            
            # Find local minima
            lows = []
            for j in range(5, len(window) - 5):
                if window[j] == np.min(window[j-5:j+5]):
                    lows.append((i-40+j, window[j]))
            
            # Need exactly 3 lows for H&S
            if len(lows) >= 3:
                # Sort by price to find head (lowest)
                lows_sorted = sorted(lows, key=lambda x: x[1])
                head_idx, head_price = lows_sorted[0]
                
                # Left and right shoulders should be higher than head
                shoulder_candidates = [l for l in lows if l[1] > head_price]
                
                if len(shoulder_candidates) >= 2:
                    # Find shoulders on either side of head
                    left_shoulders = [l for l in shoulder_candidates if l[0] < head_idx]
                    right_shoulders = [l for l in shoulder_candidates if l[0] > head_idx]
                    
                    if left_shoulders and right_shoulders:
                        left_shoulder = left_shoulders[-1]  # Closest to head
                        right_shoulder = right_shoulders[0]  # Closest to head
                        
                        # Check if shoulders are similar height
                        shoulder_diff = abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1]
                        
                        if shoulder_diff < 0.10:  # Within 10%
                            # Check for prior decline
                            decline_start_idx = max(0, head_idx - self.lookback_decline)
                            decline_high = np.max(prices[decline_start_idx:head_idx])
                            decline_pct = ((head_price - decline_high) / decline_high) * 100
                            
                            if abs(decline_pct) >= self.min_decline_pct:
                                situations.append(MarketSituation(
                                    description=f"Inverse Head & Shoulders after {decline_pct:.0f}% decline",
                                    timestamp_indices=np.array([i]),
                                    metadata={
                                        'signal_type': 'structural_reversal',
                                        'pattern': 'inverse_head_shoulders',
                                        'priority': 'PRIMARY',
                                        'decline_pct': decline_pct
                                    }
                                ))
                                break  # Found one, move on
        
        return situations
    
    def detect_bull_flag_after_decline(
        self,
        market_data: MarketData
    ) -> List[MarketSituation]:
        """
        Detect bull flag AFTER a significant decline.
        
        This is different from traditional bull flag (continuation).
        Here we want: DECLINE -> STABILIZATION (flag) -> REVERSAL
        """
        situations = []
        prices = market_data.close_prices
        
        if len(prices) < 80:
            return situations
        
        # Scan for consolidation after decline
        for i in range(60, len(prices) - 10):
            # Check for prior decline
            decline_start_idx = max(0, i - self.lookback_decline)
            decline_high = np.max(prices[decline_start_idx:i-20])
            recent_low = np.min(prices[i-20:i])
            decline_pct = ((recent_low - decline_high) / decline_high) * 100
            
            if abs(decline_pct) >= self.min_decline_pct:
                # Check for consolidation (flag)
                consolidation = prices[i-10:i]
                if len(consolidation) >= self.min_stabilization_days:
                    # Measure volatility in consolidation
                    cons_std = np.std(consolidation) / np.mean(consolidation)
                    
                    # Compare to volatility during decline
                    decline_std = np.std(prices[i-30:i-10]) / np.mean(prices[i-30:i-10])
                    
                    # Flag should have lower volatility (stabilization)
                    if cons_std < decline_std * 0.7:
                        situations.append(MarketSituation(
                            description=f"Bull Flag (Base) after {decline_pct:.0f}% decline",
                            timestamp_indices=np.array([i]),
                            metadata={
                                'signal_type': 'structural_reversal',
                                'pattern': 'bull_flag_after_decline',
                                'priority': 'PRIMARY',
                                'decline_pct': decline_pct,
                                'stabilization_days': len(consolidation)
                            }
                        ))
        
        return situations
    
    def detect_higher_lows_reversal(
        self,
        market_data: MarketData
    ) -> List[MarketSituation]:
        """
        Detect transition from lower lows to higher lows.
        
        This signals the end of a downtrend and start of uptrend.
        """
        situations = []
        prices = market_data.close_prices
        
        if len(prices) < 60:
            return situations
        
        # Scan for higher lows pattern
        for i in range(40, len(prices) - 10):
            # Find lows in last 40 days
            window = prices[i-40:i]
            
            # Find local lows (5-day minima)
            lows = []
            for j in range(5, len(window) - 5):
                if window[j] == np.min(window[j-5:j+5]):
                    lows.append((j, window[j]))
            
            # Need at least 3 lows
            if len(lows) >= 3:
                # Check if they're ascending (higher lows)
                lows_sorted = sorted(lows, key=lambda x: x[0])  # Sort by time
                
                # Check if each low is higher than previous
                higher_lows_count = 0
                for k in range(1, len(lows_sorted)):
                    if lows_sorted[k][1] > lows_sorted[k-1][1]:
                        higher_lows_count += 1
                
                # If most lows are higher, it's a reversal
                if higher_lows_count >= len(lows_sorted) - 1:
                    # Check for prior decline
                    decline_start_idx = max(0, i - self.lookback_decline)
                    decline_high = np.max(prices[decline_start_idx:i-30])
                    current_price = prices[i-1]
                    decline_pct = ((current_price - decline_high) / decline_high) * 100
                    
                    if abs(decline_pct) >= self.min_decline_pct:
                        situations.append(MarketSituation(
                            description=f"Higher Lows (Trend Reversal) after {decline_pct:.0f}% decline",
                            timestamp_indices=np.array([i]),
                            metadata={
                                'signal_type': 'structural_reversal',
                                'pattern': 'higher_lows',
                                'priority': 'PRIMARY',
                                'decline_pct': decline_pct,
                                'num_higher_lows': higher_lows_count
                            }
                        ))
                        break
        
        return situations
    
    def detect_all_position_patterns(
        self,
        market_data: MarketData
    ) -> dict:
        """Detect all position trading patterns."""
        patterns = {}
        
        # Structural reversals (PRIMARY)
        double_bottoms = self.detect_double_bottom(market_data)
        for i, db in enumerate(double_bottoms):
            patterns[f'double_bottom_{i}'] = db
        
        ihs_patterns = self.detect_inverse_head_and_shoulders(market_data)
        for i, ihs in enumerate(ihs_patterns):
            patterns[f'inverse_hs_{i}'] = ihs
        
        bull_flags = self.detect_bull_flag_after_decline(market_data)
        for i, bf in enumerate(bull_flags):
            patterns[f'bull_flag_decline_{i}'] = bf
        
        higher_lows = self.detect_higher_lows_reversal(market_data)
        for i, hl in enumerate(higher_lows):
            patterns[f'higher_lows_{i}'] = hl
        
        return patterns


def is_primary_pattern(pattern_metadata: dict) -> bool:
    """Check if a pattern is PRIMARY (structural) or SECONDARY (noise)."""
    priority = pattern_metadata.get('priority', 'SECONDARY')
    return priority == 'PRIMARY'


def calculate_position_trading_score(
    pattern_metadata: dict,
    forward_21d_return: float,
    forward_42d_return: float,
    forward_63d_return: float
) -> float:
    """
    Calculate position trading score.
    
    Primary patterns get full weight.
    Secondary patterns (calendar, day-of-week) get 0.2x weight.
    
    Score based on 21/42/63-day returns, not 1-day.
    """
    if is_primary_pattern(pattern_metadata):
        weight = 1.0
    else:
        weight = 0.2  # Demote calendar effects
    
    # Average of multi-timeframe returns
    avg_return = (forward_21d_return + forward_42d_return + forward_63d_return) / 3
    
    # Decline magnitude bonus (deeper decline = better setup)
    decline_pct = abs(pattern_metadata.get('decline_pct', 0))
    decline_bonus = min(20, decline_pct / 2)  # Up to 20 points for 40%+ decline
    
    base_score = (avg_return / 10.0) * 50 + decline_bonus  # 0-70 points
    
    return base_score * weight
