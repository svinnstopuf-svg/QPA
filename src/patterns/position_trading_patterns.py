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
    
    def detect_double_bottom(
        self,
        market_data: MarketData,
        tolerance: float = 0.03  # 3% tolerance for "same" low
    ) -> List[MarketSituation]:
        """
        Detect double bottom (W-pattern).
        
        Criteria:
        1. Price makes a low
        2. Bounces up
        3. Comes back down to test same low (within tolerance)
        4. Starts to move up again
        """
        situations = []
        prices = market_data.close_prices
        
        # Need at least 40 days of data
        if len(prices) < 40:
            return situations
        
        # Scan for double bottoms
        for i in range(30, len(prices) - 10):
            # Look back 20 days for first low
            lookback_window = prices[i-20:i]
            first_low_idx = i - 20 + np.argmin(lookback_window)
            first_low = prices[first_low_idx]
            
            # Look for second low (current area)
            current_low = np.min(prices[i:i+10])
            
            # Check if they're similar (double bottom)
            if abs(current_low - first_low) / first_low <= tolerance:
                # Check if there was a peak between them
                middle_section = prices[first_low_idx:i]
                if len(middle_section) > 0:
                    peak = np.max(middle_section)
                    bounce_height = (peak - first_low) / first_low
                    
                    # Valid double bottom if bounce was significant
                    if bounce_height > 0.05:  # 5% bounce
                        # Check for prior decline
                        decline_start_idx = max(0, i - self.lookback_decline)
                        decline_high = np.max(prices[decline_start_idx:first_low_idx])
                        decline_pct = ((first_low - decline_high) / decline_high) * 100
                        
                        if abs(decline_pct) >= self.min_decline_pct:
                            situations.append(MarketSituation(
                                description=f"Double Bottom (W-Pattern) after {decline_pct:.0f}% decline",
                                timestamp_indices=np.array([i]),
                                metadata={
                                    'signal_type': 'structural_reversal',
                                    'pattern': 'double_bottom',
                                    'priority': 'PRIMARY',
                                    'decline_pct': decline_pct,
                                    'bounce_height': bounce_height * 100
                                }
                            ))
        
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
