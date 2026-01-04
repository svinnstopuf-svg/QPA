"""
Volatility Breakout Filter - Entry Timing

Kasinot tjänar när oddsen är tydliga. I trading är oddsen bäst när
marknaden går från "stilla" till "explosiv".

Philosophy:
- GREEN signal + låg volatilitet = WAIT
- GREEN signal + ATR expansion = ENTER
- Prevents whipsaws (sideways choppy action)
- Catches moves with momentum behind them
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class VolatilityRegime(Enum):
    """Volatility regime classification."""
    CONTRACTING = "CONTRACTING"  # ATR falling, avoid entry
    STABLE = "STABLE"  # ATR stable, neutral
    EXPANDING = "EXPANDING"  # ATR rising, good for entry
    EXPLOSIVE = "EXPLOSIVE"  # ATR spiking, enter aggressively


@dataclass
class BreakoutAnalysis:
    """Volatility breakout analysis result."""
    current_atr: float
    atr_change_pct: float  # % change in ATR
    regime: VolatilityRegime
    allow_entry: bool
    volume_confirmation: bool
    recommendation: str
    confidence: float  # 0-1


class VolatilityBreakoutFilter:
    """
    Filters entries based on ATR expansion.
    
    Rules:
    1. Only enter when ATR is expanding (increasing volatility)
    2. Require volume confirmation
    3. Avoid entries during contracting volatility (whipsaw risk)
    
    Example:
    - GREEN signal + ATR +15% + volume spike = ENTER NOW
    - GREEN signal + ATR -10% + low volume = WAIT
    """
    
    def __init__(
        self,
        atr_period: int = 14,
        expansion_threshold: float = 5.0,  # % ATR increase required
        explosive_threshold: float = 20.0,  # % for explosive regime
        volume_threshold: float = 1.2  # Volume > 1.2x average
    ):
        """
        Initialize volatility breakout filter.
        
        Args:
            atr_period: Period for ATR calculation
            expansion_threshold: Min % ATR increase for expansion
            explosive_threshold: % ATR increase for explosive regime
            volume_threshold: Min volume multiplier for confirmation
        """
        self.atr_period = atr_period
        self.expansion_threshold = expansion_threshold
        self.explosive_threshold = explosive_threshold
        self.volume_threshold = volume_threshold
    
    def calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = None
    ) -> np.ndarray:
        """Calculate ATR series."""
        if period is None:
            period = self.atr_period
        
        # True Range
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # ATR (exponential moving average)
        atr = np.zeros(len(close))
        if len(tr) >= period:
            atr[period] = np.mean(tr[:period])
            multiplier = 1.0 / period
            for i in range(period + 1, len(atr)):
                atr[i] = atr[i-1] + multiplier * (tr[i-1] - atr[i-1])
        
        return atr
    
    def calculate_atr_change(
        self,
        atr: np.ndarray,
        lookback: int = 5
    ) -> float:
        """
        Calculate % change in ATR over lookback period.
        
        Args:
            atr: ATR series
            lookback: Periods to look back
            
        Returns:
            Percentage change in ATR
        """
        if len(atr) < lookback + 1:
            return 0.0
        
        current_atr = atr[-1]
        past_atr = atr[-lookback-1]
        
        if past_atr > 0:
            change_pct = ((current_atr - past_atr) / past_atr) * 100
        else:
            change_pct = 0.0
        
        return change_pct
    
    def check_volume_confirmation(
        self,
        volume: np.ndarray,
        lookback: int = 20
    ) -> bool:
        """
        Check if current volume confirms breakout.
        
        Args:
            volume: Volume series
            lookback: Period for average calculation
            
        Returns:
            True if volume is elevated
        """
        if len(volume) < lookback + 1:
            return False
        
        current_volume = volume[-1]
        avg_volume = np.mean(volume[-lookback-1:-1])
        
        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
            return volume_ratio >= self.volume_threshold
        
        return False
    
    def analyze_breakout(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        signal: str = "GREEN"
    ) -> BreakoutAnalysis:
        """
        Analyze if conditions are right for entry.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data
            signal: Current traffic light signal
            
        Returns:
            BreakoutAnalysis with entry recommendation
        """
        # Calculate ATR
        atr = self.calculate_atr(high, low, close)
        current_atr = atr[-1]
        
        # Calculate ATR change
        atr_change_pct = self.calculate_atr_change(atr, lookback=5)
        
        # Check volume
        volume_conf = self.check_volume_confirmation(volume)
        
        # Determine regime
        if atr_change_pct >= self.explosive_threshold:
            regime = VolatilityRegime.EXPLOSIVE
        elif atr_change_pct >= self.expansion_threshold:
            regime = VolatilityRegime.EXPANDING
        elif atr_change_pct >= -self.expansion_threshold:
            regime = VolatilityRegime.STABLE
        else:
            regime = VolatilityRegime.CONTRACTING
        
        # Determine if entry allowed
        allow_entry = self._should_allow_entry(
            regime, volume_conf, signal, atr_change_pct
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            regime, volume_conf, allow_entry, signal
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            regime, volume_conf, atr_change_pct
        )
        
        return BreakoutAnalysis(
            current_atr=current_atr,
            atr_change_pct=atr_change_pct,
            regime=regime,
            allow_entry=allow_entry,
            volume_confirmation=volume_conf,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def _should_allow_entry(
        self,
        regime: VolatilityRegime,
        volume_conf: bool,
        signal: str,
        atr_change: float
    ) -> bool:
        """Determine if entry should be allowed."""
        # Only consider entry for positive signals
        if signal not in ["GREEN", "YELLOW"]:
            return False
        
        # EXPLOSIVE: Always allow (strong conviction)
        if regime == VolatilityRegime.EXPLOSIVE:
            return True
        
        # EXPANDING: Allow if volume confirms
        if regime == VolatilityRegime.EXPANDING:
            return volume_conf
        
        # STABLE: Allow only for GREEN with volume
        if regime == VolatilityRegime.STABLE:
            return signal == "GREEN" and volume_conf
        
        # CONTRACTING: Block (whipsaw risk)
        return False
    
    def _generate_recommendation(
        self,
        regime: VolatilityRegime,
        volume_conf: bool,
        allow_entry: bool,
        signal: str
    ) -> str:
        """Generate entry recommendation."""
        if not allow_entry:
            if regime == VolatilityRegime.CONTRACTING:
                return "WAIT - ATR contracting, whipsaw risk"
            elif not volume_conf:
                return "WAIT - No volume confirmation"
            else:
                return f"WAIT - Conditions not met for {signal}"
        
        if regime == VolatilityRegime.EXPLOSIVE:
            return "ENTER AGGRESSIVELY - Explosive volatility expansion!"
        elif regime == VolatilityRegime.EXPANDING:
            return "ENTER - ATR expanding with volume"
        elif regime == VolatilityRegime.STABLE:
            return "ENTER CAUTIOUSLY - Stable regime, volume confirmed"
        
        return "WAIT"
    
    def _calculate_confidence(
        self,
        regime: VolatilityRegime,
        volume_conf: bool,
        atr_change: float
    ) -> float:
        """Calculate entry confidence (0-1)."""
        base_confidence = {
            VolatilityRegime.EXPLOSIVE: 0.9,
            VolatilityRegime.EXPANDING: 0.7,
            VolatilityRegime.STABLE: 0.5,
            VolatilityRegime.CONTRACTING: 0.2
        }.get(regime, 0.5)
        
        # Boost for volume confirmation
        if volume_conf:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        # Boost for strong ATR expansion
        if atr_change > 30:
            base_confidence = min(1.0, base_confidence + 0.1)
        
        return base_confidence
    
    def batch_analyze_breakouts(
        self,
        instruments_data: Dict[str, Dict]
    ) -> Dict[str, BreakoutAnalysis]:
        """
        Analyze breakouts for multiple instruments.
        
        Args:
            instruments_data: Dict mapping ticker to data with:
                - high, low, close, volume arrays
                - signal (GREEN/YELLOW/etc)
                
        Returns:
            Dict mapping ticker to BreakoutAnalysis
        """
        results = {}
        
        for ticker, data in instruments_data.items():
            analysis = self.analyze_breakout(
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume'],
                signal=data.get('signal', 'YELLOW')
            )
            results[ticker] = analysis
        
        return results


def format_breakout_report(analyses: Dict[str, BreakoutAnalysis]) -> str:
    """Format breakout analysis report."""
    lines = []
    lines.append("=" * 80)
    lines.append("VOLATILITY BREAKOUT FILTER - ENTRY TIMING")
    lines.append("=" * 80)
    lines.append("")
    
    # Group by regime
    by_regime = {}
    for ticker, analysis in analyses.items():
        regime = analysis.regime.value
        if regime not in by_regime:
            by_regime[regime] = []
        by_regime[regime].append((ticker, analysis))
    
    # Sort regimes
    regime_order = ["EXPLOSIVE", "EXPANDING", "STABLE", "CONTRACTING"]
    
    for regime_name in regime_order:
        if regime_name not in by_regime:
            continue
        
        items = by_regime[regime_name]
        icon = {
            "EXPLOSIVE": "🚀",
            "EXPANDING": "📈",
            "STABLE": "➡️",
            "CONTRACTING": "📉"
        }.get(regime_name, "")
        
        lines.append(f"{icon} {regime_name}: {len(items)} instruments")
        lines.append("-" * 80)
        
        for ticker, analysis in sorted(items, key=lambda x: x[1].atr_change_pct, reverse=True):
            entry_icon = "✅" if analysis.allow_entry else "⛔"
            vol_icon = "📊" if analysis.volume_confirmation else "  "
            
            lines.append(
                f"  {ticker:<10} {entry_icon} ATR: {analysis.atr_change_pct:>+6.1f}% | "
                f"Conf: {analysis.confidence*100:>3.0f}% {vol_icon}"
            )
            lines.append(f"    → {analysis.recommendation}")
        
        lines.append("")
    
    # Summary
    total = len(analyses)
    allowed = sum(1 for a in analyses.values() if a.allow_entry)
    explosive = sum(1 for a in analyses.values() if a.regime == VolatilityRegime.EXPLOSIVE)
    
    lines.append("=" * 80)
    lines.append("SAMMANFATTNING")
    lines.append(f"Total: {total} | Ready to Enter: {allowed} | Explosive: {explosive}")
    lines.append("=" * 80)
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Volatility Breakout Filter - Entry Timing")
    print("Usage:")
    print("  from src.entry.volatility_breakout import VolatilityBreakoutFilter")
    print("  filter = VolatilityBreakoutFilter()")
    print("  analysis = filter.analyze_breakout(high, low, close, volume, 'GREEN')")
