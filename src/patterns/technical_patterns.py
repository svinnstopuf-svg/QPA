"""
Technical Pattern Detector - Momentum, Reversals, Gaps

Renaissance principle: Don't rely only on calendar effects.
Technical patterns capture market microstructure and psychology.
"""

import numpy as np
from typing import List, Dict
from dataclasses import dataclass

from ..utils.market_data import MarketData
from .detector import MarketSituation


class TechnicalPatternDetector:
    """
    Detects technical patterns beyond calendar effects.
    
    Patterns:
    1. RSI extremes (oversold/overbought)
    2. Moving average crosses (golden/death cross)
    3. Trend exhaustion (extended moves)
    4. Gap patterns (gap up/down with follow-through)
    5. Momentum divergence (price vs momentum)
    6. Support/resistance breakouts
    """
    
    def __init__(self):
        """Initialize technical pattern detector."""
        pass
    
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate RSI indicator."""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.zeros(len(prices))
        avg_losses = np.zeros(len(prices))
        
        # Initial averages
        if len(gains) >= period:
            avg_gains[period] = np.mean(gains[:period])
            avg_losses[period] = np.mean(losses[:period])
            
            # Smoothed averages
            for i in range(period + 1, len(prices)):
                avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
                avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
        
        # Fix divide-by-zero: hantera när avg_losses är 0
        with np.errstate(divide='ignore', invalid='ignore'):
            rs = np.where(avg_losses > 0, avg_gains / avg_losses, 0)
        rs = np.nan_to_num(rs, nan=0.0, posinf=100.0)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def detect_rsi_extremes(self, market_data: MarketData) -> Dict[str, MarketSituation]:
        """
        Detect RSI oversold (<30) conditions - Mean Reversion Setup.
        
        Oversold → potential bounce (BUY signal)
        
        NOTE: RSI Overbought (>70) REMOVED - contradicts bottom-fishing strategy.
        We buy at BOTTOMS, not tops. Overbought is a SELL signal, not a BUY signal.
        """
        rsi = self.calculate_rsi(market_data.close_prices)
        
        oversold_indices = np.where(rsi < 30)[0]
        # overbought_indices = np.where(rsi > 70)[0]  # REMOVED
        
        patterns = {}
        
        if len(oversold_indices) > 0:
            patterns['rsi_oversold'] = MarketSituation(
                situation_id='rsi_oversold',
                description="RSI Oversold (<30) - Potential Bounce",
                timestamp_indices=oversold_indices,
                confidence=0.60,
                metadata={
                    'signal_type': 'technical', 
                    'indicator': 'RSI', 
                    'threshold': 30,
                    'priority': 'SECONDARY'  # Supporting evidence for reversal, not PRIMARY entry.
                }
            )
        
        # RSI Overbought REMOVED - use for sell signals, not buy signals
        
        return patterns
    
    def detect_ma_crosses(self, market_data: MarketData) -> Dict[str, MarketSituation]:
        """
        Detect moving average crossovers.
        
        Golden cross: 50-day MA crosses above 200-day MA (bullish)
        Death cross: 50-day MA crosses below 200-day MA (bearish)
        """
        prices = market_data.close_prices
        
        # Calculate moving averages
        ma_50 = np.zeros(len(prices))
        ma_200 = np.zeros(len(prices))
        
        for i in range(50, len(prices)):
            ma_50[i] = np.mean(prices[i-50:i])
        
        for i in range(200, len(prices)):
            ma_200[i] = np.mean(prices[i-200:i])
        
        # Detect crosses
        diff = ma_50 - ma_200
        crosses = np.where(np.diff(np.sign(diff)) != 0)[0] + 1
        
        golden_crosses = []
        death_crosses = []
        
        for cross_idx in crosses:
            if cross_idx >= 200:
                if diff[cross_idx] > 0:  # 50 MA crossed above 200 MA
                    golden_crosses.append(cross_idx)
                else:
                    death_crosses.append(cross_idx)
        
        patterns = {}
        
        if len(golden_crosses) > 0:
            patterns['golden_cross'] = MarketSituation(
                situation_id='golden_cross',
                description="Golden Cross (50MA > 200MA) - Bullish",
                timestamp_indices=np.array(golden_crosses),
                confidence=0.60,
                metadata={
                    'signal_type': 'technical', 
                    'indicator': 'MA_Cross',
                    'priority': 'SECONDARY'  # Trend-following, not reversal. Use as supporting evidence only.
                }
            )
        
        if len(death_crosses) > 0:
            patterns['death_cross'] = MarketSituation(
                situation_id='death_cross',
                description="Death Cross (50MA < 200MA) - Bearish",
                timestamp_indices=np.array(death_crosses),
                confidence=0.60,
                metadata={
                    'signal_type': 'technical', 
                    'indicator': 'MA_Cross',
                    'priority': 'SECONDARY'  # Bearish signal. Context only, NOT reversal entry.
                }
            )
        
        return patterns
    
    def detect_trend_exhaustion(self, market_data: MarketData) -> Dict[str, MarketSituation]:
        """
        Detect extended trends that may be exhausted.
        
        7+ consecutive up days = overbought
        7+ consecutive down days = oversold
        """
        returns = market_data.returns
        
        consecutive_ups = []
        consecutive_downs = []
        
        current_streak = 0
        for i in range(1, len(returns)):
            if returns[i] > 0:
                if current_streak > 0:
                    current_streak += 1
                else:
                    current_streak = 1
            elif returns[i] < 0:
                if current_streak < 0:
                    current_streak -= 1
                else:
                    current_streak = -1
            else:
                current_streak = 0
            
            if current_streak >= 7:
                consecutive_ups.append(i)
            elif current_streak <= -7:
                consecutive_downs.append(i)
        
        patterns = {}
        
        if len(consecutive_ups) > 0:
            patterns['extended_rally'] = MarketSituation(
                situation_id='extended_rally',
                description="Extended Rally (7+ up days) - Exhaustion Risk",
                timestamp_indices=np.array(consecutive_ups),
                confidence=0.60,
                metadata={'signal_type': 'technical', 'pattern': 'exhaustion'}
            )
        
        if len(consecutive_downs) > 0:
            patterns['extended_selloff'] = MarketSituation(
                situation_id='extended_selloff',
                description="Extended Selloff (7+ down days) - Bounce Risk",
                timestamp_indices=np.array(consecutive_downs),
                confidence=0.60,
                metadata={'signal_type': 'technical', 'pattern': 'exhaustion'}
            )
        
        return patterns
    
    def detect_gaps(self, market_data: MarketData) -> Dict[str, MarketSituation]:
        """
        Detect gap patterns.
        
        Gap up >2% = strong buying
        Gap down >2% = strong selling
        """
        open_prices = market_data.open_prices
        prev_close = market_data.close_prices[:-1]
        
        # Gap = (Open[t] - Close[t-1]) / Close[t-1]
        gaps = (open_prices[1:] - prev_close) / prev_close
        
        gap_up_indices = np.where(gaps > 0.02)[0] + 1  # >2% gap up
        gap_down_indices = np.where(gaps < -0.02)[0] + 1  # >2% gap down
        
        patterns = {}
        
        if len(gap_up_indices) > 0:
            patterns['gap_up'] = MarketSituation(
                situation_id='gap_up',
                description="Gap Up (>2%) - Strong Buying",
                timestamp_indices=gap_up_indices,
                confidence=0.60,
                metadata={
                    'signal_type': 'technical', 
                    'pattern': 'gap',
                    'priority': 'SECONDARY'  # 39.5% occur after declines. Supporting evidence, not PRIMARY.
                }
            )
        
        if len(gap_down_indices) > 0:
            patterns['gap_down'] = MarketSituation(
                situation_id='gap_down',
                description="Gap Down (>2%) - Strong Selling",
                timestamp_indices=gap_down_indices,
                confidence=0.60,
                metadata={
                    'signal_type': 'technical', 
                    'pattern': 'gap',
                    'priority': 'SECONDARY'  # Panic selling. Good for reversal setup context.
                }
            )
        
        return patterns
    
    def detect_all_technical_patterns(self, market_data: MarketData) -> Dict[str, MarketSituation]:
        """
        Detect all technical patterns.
        
        Args:
            market_data: Market data
            
        Returns:
            Dictionary of pattern_id -> MarketSituation
        """
        all_patterns = {}
        
        # RSI extremes
        rsi_patterns = self.detect_rsi_extremes(market_data)
        all_patterns.update(rsi_patterns)
        
        # MA crosses
        ma_patterns = self.detect_ma_crosses(market_data)
        all_patterns.update(ma_patterns)
        
        # Trend exhaustion - REMOVED: Extended Rally contradicts mean reversion strategy
        # We buy at BOTTOMS after declines, not after 7+ day rallies (momentum/breakout)
        # Extended Selloff (7+ down days) could be kept, but removing entire function for clarity
        # exhaustion_patterns = self.detect_trend_exhaustion(market_data)
        # all_patterns.update(exhaustion_patterns)
        
        # Gaps
        gap_patterns = self.detect_gaps(market_data)
        all_patterns.update(gap_patterns)
        
        return all_patterns
