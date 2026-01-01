"""
Microstructure Signals - Order Flow and Volume Analysis

NOTE: Limited by yfinance data (no bid/ask, no L2 orderbook).
This implements what's possible with OHLCV data only.

For full microstructure:
- Use Polygon.io, IEX Cloud, or direct exchange feeds
- Get tick-by-tick data with bid/ask spreads
- Access L2 orderbook depth
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..utils.market_data import MarketData


@dataclass
class MicrostructureSignal:
    """Signal from microstructure analysis."""
    signal_type: str  # 'volume_imbalance', 'large_print', 'unusual_spread'
    timestamp_indices: np.ndarray
    strength: float  # 0-1
    description: str
    actionable: bool


class MicrostructureAnalyzer:
    """
    Analyzes microstructure signals from OHLCV data.
    
    Limitations:
    - No actual bid/ask spreads (yfinance doesn't provide)
    - No orderbook depth
    - No tick-by-tick data
    - No time & sales
    
    What we CAN detect:
    - Volume spikes (proxy for institutional flow)
    - Price-volume divergence
    - Intrabar volatility (High-Low range)
    - Buy/sell pressure (Close vs Open within bar)
    """
    
    def __init__(
        self,
        volume_threshold: float = 2.0,  # 2x average volume
        large_move_threshold: float = 0.02  # 2% move
    ):
        """
        Initialize microstructure analyzer.
        
        Args:
            volume_threshold: Multiplier for volume spike detection
            large_move_threshold: Threshold for large price move
        """
        self.volume_threshold = volume_threshold
        self.large_move_threshold = large_move_threshold
    
    def detect_volume_imbalance(
        self,
        market_data: MarketData,
        window: int = 20
    ) -> MicrostructureSignal:
        """
        Detect unusual volume patterns (proxy for order flow imbalance).
        
        High volume + small price move = absorption (strong hands)
        High volume + large price move = momentum
        
        Args:
            market_data: Market data
            window: Lookback window for average volume
            
        Returns:
            MicrostructureSignal
        """
        volume = market_data.volume
        returns = market_data.returns
        
        # Rolling average volume
        avg_volume = np.zeros(len(volume))
        for i in range(window, len(volume)):
            avg_volume[i] = np.mean(volume[i-window:i])
        
        # Volume ratio
        volume_ratio = np.where(avg_volume > 0, volume / avg_volume, 0)
        
        # Find high volume + divergence patterns
        imbalance_indices = []
        for i in range(window, len(volume)):
            if volume_ratio[i] > self.volume_threshold:
                price_move = abs(returns[i])
                
                # High volume but small move = absorption
                if price_move < 0.005:  # <0.5% move
                    imbalance_indices.append(i)
        
        imbalance_indices = np.array(imbalance_indices)
        
        return MicrostructureSignal(
            signal_type='volume_imbalance',
            timestamp_indices=imbalance_indices,
            strength=0.6,
            description=f"Volume absorption detected ({len(imbalance_indices)} occurrences)",
            actionable=len(imbalance_indices) > 0
        )
    
    def detect_large_prints(
        self,
        market_data: MarketData
    ) -> MicrostructureSignal:
        """
        Detect large institutional prints.
        
        Large volume + large price move = institutional flow
        
        Args:
            market_data: Market data
            
        Returns:
            MicrostructureSignal
        """
        volume = market_data.volume
        returns = market_data.returns
        
        # Z-score for volume
        volume_mean = np.mean(volume)
        volume_std = np.std(volume)
        volume_zscore = (volume - volume_mean) / volume_std if volume_std > 0 else np.zeros_like(volume)
        
        # Find large prints: high volume (z>2) + large move (>2%)
        large_print_indices = []
        for i in range(len(volume)):
            if volume_zscore[i] > 2 and abs(returns[i]) > self.large_move_threshold:
                large_print_indices.append(i)
        
        large_print_indices = np.array(large_print_indices)
        
        return MicrostructureSignal(
            signal_type='large_print',
            timestamp_indices=large_print_indices,
            strength=0.7,
            description=f"Large institutional prints ({len(large_print_indices)} detected)",
            actionable=len(large_print_indices) > 0
        )
    
    def detect_intrabar_volatility(
        self,
        market_data: MarketData,
        threshold: float = 0.015  # 1.5% intrabar range
    ) -> MicrostructureSignal:
        """
        Detect unusual intrabar volatility (High-Low range).
        
        Large H-L range = uncertainty, potential reversal
        
        Args:
            market_data: Market data
            threshold: Minimum H-L range to flag
            
        Returns:
            MicrostructureSignal
        """
        high = market_data.high_prices
        low = market_data.low_prices
        close = market_data.close_prices
        
        # Intrabar range as % of close
        intrabar_range = (high - low) / close
        
        # Find large ranges
        high_volatility_indices = np.where(intrabar_range > threshold)[0]
        
        return MicrostructureSignal(
            signal_type='unusual_volatility',
            timestamp_indices=high_volatility_indices,
            strength=0.5,
            description=f"High intrabar volatility ({len(high_volatility_indices)} bars with >{threshold:.1%} range)",
            actionable=len(high_volatility_indices) > 0
        )
    
    def detect_buying_pressure(
        self,
        market_data: MarketData
    ) -> MicrostructureSignal:
        """
        Detect buying vs selling pressure.
        
        Close > Open = buying pressure
        Close < Open = selling pressure
        
        Args:
            market_data: Market data
            
        Returns:
            MicrostructureSignal
        """
        open_prices = market_data.open_prices
        close_prices = market_data.close_prices
        
        # Buying pressure: close significantly above open
        buying_pressure = (close_prices - open_prices) / open_prices
        
        # Strong buying: close >1% above open
        strong_buying_indices = np.where(buying_pressure > 0.01)[0]
        
        # Strong selling: close >1% below open
        strong_selling_indices = np.where(buying_pressure < -0.01)[0]
        
        net_pressure = len(strong_buying_indices) - len(strong_selling_indices)
        
        if net_pressure > 0:
            description = f"Net buying pressure ({len(strong_buying_indices)} buy bars vs {len(strong_selling_indices)} sell bars)"
        else:
            description = f"Net selling pressure ({len(strong_selling_indices)} sell bars vs {len(strong_buying_indices)} buy bars)"
        
        return MicrostructureSignal(
            signal_type='pressure_imbalance',
            timestamp_indices=strong_buying_indices if net_pressure > 0 else strong_selling_indices,
            strength=min(1.0, abs(net_pressure) / 100),
            description=description,
            actionable=abs(net_pressure) > 10
        )
    
    def generate_all_signals(
        self,
        market_data: MarketData
    ) -> List[MicrostructureSignal]:
        """
        Generate all microstructure signals.
        
        Args:
            market_data: Market data
            
        Returns:
            List of detected signals
        """
        signals = []
        
        # Volume imbalance
        vol_signal = self.detect_volume_imbalance(market_data)
        if vol_signal.actionable:
            signals.append(vol_signal)
        
        # Large prints
        print_signal = self.detect_large_prints(market_data)
        if print_signal.actionable:
            signals.append(print_signal)
        
        # Intrabar volatility
        vol_signal = self.detect_intrabar_volatility(market_data)
        if vol_signal.actionable:
            signals.append(vol_signal)
        
        # Buying/selling pressure
        pressure_signal = self.detect_buying_pressure(market_data)
        if pressure_signal.actionable:
            signals.append(pressure_signal)
        
        return signals
    
    def create_signal_report(
        self,
        signals: List[MicrostructureSignal]
    ) -> str:
        """Create report for microstructure signals."""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("MICROSTRUCTURE SIGNALS")
        lines.append("=" * 80)
        lines.append("\n⚠️ LIMITED DATA: yfinance only provides OHLCV (no bid/ask, no L2)")
        lines.append("")
        
        if not signals:
            lines.append("❌ No actionable microstructure signals detected.")
            return "\n".join(lines)
        
        lines.append(f"Signals detected: {len(signals)}")
        lines.append("")
        
        for i, sig in enumerate(signals, 1):
            lines.append(f"{i}. {sig.description}")
            lines.append(f"   Type: {sig.signal_type}")
            lines.append(f"   Strength: {sig.strength:.2f}")
            lines.append(f"   Occurrences: {len(sig.timestamp_indices)}")
        
        lines.append("")
        lines.append("⚠️ For true microstructure signals, use:")
        lines.append("   - Polygon.io (tick-by-tick + L2 orderbook)")
        lines.append("   - IEX Cloud (bid/ask spreads)")
        lines.append("   - Direct exchange feeds")
        
        return "\n".join(lines)
