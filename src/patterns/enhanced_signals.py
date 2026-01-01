"""
Enhanced Signal Detection - Beyond Calendar Patterns

Renaissance principle: Combine diverse signal types.
Calendar + Technical + Volume + Volatility = stronger edge.
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

from ..utils.market_data import MarketData
from .detector import MarketSituation


@dataclass
class VolatilityBurst:
    """Volatility burst signal."""
    timestamp_indices: np.ndarray
    description: str
    burst_magnitude: float  # How many std devs above normal


@dataclass
class MomentumFlip:
    """Momentum reversal signal."""
    timestamp_indices: np.ndarray
    description: str
    flip_strength: float  # Magnitude of momentum change


class EnhancedSignalDetector:
    """
    Detects advanced signals beyond simple calendar patterns.
    
    Signals:
    1. Volatility bursts (sudden vol expansion)
    2. Momentum flips (trend reversals)
    3. Volume spikes (unusual trading activity)
    4. Regime transitions (vol/trend state changes)
    """
    
    def __init__(
        self,
        vol_window: int = 20,
        vol_threshold: float = 2.0,  # Std devs above normal
        momentum_window: int = 10,
        volume_threshold: float = 2.0  # Times normal volume
    ):
        """
        Initialize enhanced signal detector.
        
        Args:
            vol_window: Window for volatility calculation
            vol_threshold: Threshold for volatility burst (std devs)
            momentum_window: Window for momentum calculation
            volume_threshold: Threshold for volume spike
        """
        self.vol_window = vol_window
        self.vol_threshold = vol_threshold
        self.momentum_window = momentum_window
        self.volume_threshold = volume_threshold
    
    def detect_volatility_bursts(self, market_data: MarketData) -> MarketSituation:
        """
        Detect periods of abnormally high volatility.
        
        Volatility bursts often precede mean reversion or continued trending.
        
        Args:
            market_data: Market data
            
        Returns:
            MarketSituation with volatility burst indices
        """
        returns = market_data.returns
        
        # Rolling volatility
        rolling_vol = np.zeros(len(returns))
        for i in range(self.vol_window, len(returns)):
            window = returns[i-self.vol_window:i]
            rolling_vol[i] = np.std(window)
        
        # Volatility of volatility (baseline)
        vol_mean = np.mean(rolling_vol[self.vol_window:])
        vol_std = np.std(rolling_vol[self.vol_window:])
        
        # Detect bursts (vol > mean + threshold * std)
        threshold = vol_mean + self.vol_threshold * vol_std
        burst_indices = np.where(rolling_vol > threshold)[0]
        
        if len(burst_indices) == 0:
            burst_indices = np.array([])
        
        avg_magnitude = np.mean(
            (rolling_vol[burst_indices] - vol_mean) / vol_std
        ) if len(burst_indices) > 0 else 0
        
        return MarketSituation(
            timestamp_indices=burst_indices,
            description=f"Volatility Burst (>{self.vol_threshold}σ)",
            metadata={
                'signal_type': 'volatility_burst',
                'avg_magnitude': float(avg_magnitude),
                'threshold': float(threshold)
            }
        )
    
    def detect_momentum_flips(self, market_data: MarketData) -> MarketSituation:
        """
        Detect momentum reversals (trend changes).
        
        Momentum flip = when short-term momentum crosses long-term momentum.
        
        Args:
            market_data: Market data
            
        Returns:
            MarketSituation with momentum flip indices
        """
        prices = market_data.close_prices
        
        # Short-term momentum (10-day)
        short_momentum = np.zeros(len(prices))
        for i in range(self.momentum_window, len(prices)):
            short_momentum[i] = prices[i] / prices[i-self.momentum_window] - 1
        
        # Long-term momentum (50-day)
        long_window = 50
        long_momentum = np.zeros(len(prices))
        for i in range(long_window, len(prices)):
            long_momentum[i] = prices[i] / prices[i-long_window] - 1
        
        # Detect crosses (sign change in difference)
        momentum_diff = short_momentum - long_momentum
        crosses = np.where(np.diff(np.sign(momentum_diff)) != 0)[0] + 1
        
        # Filter to only significant crosses (>1% momentum change)
        significant_crosses = []
        for idx in crosses:
            if idx < len(momentum_diff):
                if abs(momentum_diff[idx]) > 0.01:  # 1% threshold
                    significant_crosses.append(idx)
        
        flip_indices = np.array(significant_crosses)
        
        avg_flip_strength = np.mean(
            np.abs(momentum_diff[flip_indices])
        ) if len(flip_indices) > 0 else 0
        
        return MarketSituation(
            timestamp_indices=flip_indices,
            description=f"Momentum Flip (10d vs 50d cross)",
            metadata={
                'signal_type': 'momentum_flip',
                'avg_flip_strength': float(avg_flip_strength),
                'flip_count': len(flip_indices)
            }
        )
    
    def detect_volume_spikes(self, market_data: MarketData) -> MarketSituation:
        """
        Detect unusual volume activity.
        
        Volume spikes often precede price moves or signal institutional activity.
        
        Args:
            market_data: Market data
            
        Returns:
            MarketSituation with volume spike indices
        """
        volume = market_data.volume
        
        # Rolling average volume
        avg_volume = np.zeros(len(volume))
        for i in range(self.vol_window, len(volume)):
            avg_volume[i] = np.mean(volume[i-self.vol_window:i])
        
        # Detect spikes (volume > threshold * average)
        spike_threshold = avg_volume * self.volume_threshold
        spike_indices = np.where(volume > spike_threshold)[0]
        
        # Filter out early period (no baseline yet)
        spike_indices = spike_indices[spike_indices >= self.vol_window]
        
        avg_spike_ratio = np.mean(
            volume[spike_indices] / avg_volume[spike_indices]
        ) if len(spike_indices) > 0 else 0
        
        return MarketSituation(
            timestamp_indices=spike_indices,
            description=f"Volume Spike (>{self.volume_threshold}x avg)",
            metadata={
                'signal_type': 'volume_spike',
                'avg_spike_ratio': float(avg_spike_ratio),
                'threshold_multiplier': self.volume_threshold
            }
        )
    
    def detect_regime_transitions(
        self,
        market_data: MarketData,
        prev_regime: Optional[str] = None
    ) -> MarketSituation:
        """
        Detect when market transitions between regimes.
        
        Transitions: low_vol→high_vol, uptrend→downtrend, etc.
        
        Args:
            market_data: Market data
            prev_regime: Previous regime (for transition detection)
            
        Returns:
            MarketSituation with regime transition indices
        """
        returns = market_data.returns
        prices = market_data.close_prices
        
        # Calculate rolling regimes
        regimes = []
        for i in range(50, len(prices)):
            window_returns = returns[i-20:i]
            window_prices = prices[i-50:i]
            
            # Volatility regime
            vol = np.std(window_returns)
            vol_regime = 'high_vol' if vol > 0.02 else 'low_vol' if vol < 0.01 else 'normal_vol'
            
            # Trend regime
            ma_50 = np.mean(window_prices)
            trend_regime = 'uptrend' if prices[i] > ma_50 else 'downtrend'
            
            regimes.append((vol_regime, trend_regime))
        
        # Detect transitions (any regime change)
        transition_indices = []
        for i in range(1, len(regimes)):
            if regimes[i] != regimes[i-1]:
                transition_indices.append(i + 50)  # Offset back to original index
        
        transition_indices = np.array(transition_indices)
        
        return MarketSituation(
            timestamp_indices=transition_indices,
            description="Regime Transition (vol/trend change)",
            metadata={
                'signal_type': 'regime_transition',
                'transition_count': len(transition_indices),
                'regimes': regimes[-1] if regimes else None
            }
        )
    
    def detect_all_enhanced_signals(self, market_data: MarketData) -> Dict[str, MarketSituation]:
        """
        Run all enhanced signal detectors.
        
        Args:
            market_data: Market data
            
        Returns:
            Dictionary of signal_id -> MarketSituation
        """
        signals = {}
        
        # Volatility bursts
        vol_bursts = self.detect_volatility_bursts(market_data)
        if len(vol_bursts.timestamp_indices) > 0:
            signals['volatility_burst'] = vol_bursts
        
        # Momentum flips
        momentum_flips = self.detect_momentum_flips(market_data)
        if len(momentum_flips.timestamp_indices) > 0:
            signals['momentum_flip'] = momentum_flips
        
        # Volume spikes
        volume_spikes = self.detect_volume_spikes(market_data)
        if len(volume_spikes.timestamp_indices) > 0:
            signals['volume_spike'] = volume_spikes
        
        # Regime transitions
        regime_transitions = self.detect_regime_transitions(market_data)
        if len(regime_transitions.timestamp_indices) > 0:
            signals['regime_transition'] = regime_transitions
        
        return signals
