"""
Signal aggregation with correlation awareness.

Jim Simons principle: Multiple correlated signals ≠ multiple independent edges.
Aggregate with uncertainty, not naive summation.
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class AggregatedSignal:
    """Aggregated signal with uncertainty."""
    bias: str  # "svagt positiv", "neutral", "svagt negativ"
    confidence: str  # "låg", "måttlig", "hög"
    n_signals: int
    correlation_warning: bool
    description: str


class SignalAggregator:
    """
    Aggregates multiple signals with correlation awareness.
    
    Avoids naive summation: 3 correlated signals ≠ 3x strength.
    """
    
    def __init__(self):
        # Known correlations (pattern types that often correlate)
        self.correlation_groups = [
            {'consecutive_up', 'positive_momentum'},  # Both momentum-related
            {'consecutive_down', 'negative_momentum'},
            {'high_volatility', 'vol_regime_increase'},
            {'new_high', 'positive_momentum'},
            {'new_low', 'negative_momentum'},
        ]
    
    def detect_correlation(self, signal_ids: List[str]) -> bool:
        """
        Detect if multiple signals are likely correlated.
        
        Args:
            signal_ids: List of active signal IDs
            
        Returns:
            True if likely correlation detected
        """
        # Check if any signals belong to same correlation group
        for group in self.correlation_groups:
            matching_signals = [s for s in signal_ids if any(g in s for g in group)]
            if len(matching_signals) >= 2:
                return True
        
        # Weekday patterns with month patterns = potential correlation
        weekday_signals = [s for s in signal_ids if 'weekday' in s]
        month_signals = [s for s in signal_ids if any(x in s for x in ['january', 'sell_in_may', 'winter'])]
        if weekday_signals and month_signals:
            return True
        
        return False
    
    def aggregate_signals(
        self,
        active_signals: List[Dict],
        pattern_evaluations: Dict = None
    ) -> AggregatedSignal:
        """
        Aggregate multiple signals into single bias with uncertainty.
        
        Args:
            active_signals: List of active signal dictionaries
            pattern_evaluations: Optional dict mapping signal IDs to evaluations
            
        Returns:
            AggregatedSignal with bias and confidence
        """
        if not active_signals:
            return AggregatedSignal(
                bias="neutral",
                confidence="hög",
                n_signals=0,
                correlation_warning=False,
                description="Inga aktiva signaler"
            )
        
        signal_ids = [s['id'] for s in active_signals]
        n_signals = len(signal_ids)
        
        # Check for correlation
        has_correlation = self.detect_correlation(signal_ids)
        
        # Simple heuristic aggregation (not naive summation)
        # Count positive/negative indicators
        positive_indicators = sum(1 for s in signal_ids if any(x in s for x in [
            'positive_momentum', 'consecutive_up', 'new_high', 'winter_rally',
            'gap_up'
        ]))
        
        negative_indicators = sum(1 for s in signal_ids if any(x in s for x in [
            'negative_momentum', 'consecutive_down', 'new_low', 'sell_in_may',
            'gap_down', 'extreme_move_down'
        ]))
        
        # Neutral/ambiguous signals
        neutral_indicators = n_signals - positive_indicators - negative_indicators
        
        # Determine bias (conservative due to correlation)
        net_signal = positive_indicators - negative_indicators
        
        if has_correlation:
            # Dampen signal strength due to correlation
            net_signal = net_signal * 0.5
        
        if net_signal > 1.5:
            bias = "svagt positiv"
        elif net_signal < -1.5:
            bias = "svagt negativ"
        else:
            bias = "neutral"
        
        # Determine confidence
        if n_signals <= 2:
            confidence = "låg"
        elif n_signals <= 4:
            confidence = "måttlig"
        else:
            confidence = "låg" if has_correlation else "måttlig"  # Correlation reduces confidence
        
        # Description
        description = self._create_description(bias, n_signals, has_correlation)
        
        return AggregatedSignal(
            bias=bias,
            confidence=confidence,
            n_signals=n_signals,
            correlation_warning=has_correlation,
            description=description
        )
    
    def _create_description(self, bias: str, n_signals: int, has_correlation: bool) -> str:
        """Create human-readable description."""
        lines = []
        
        lines.append(f"Samlad marknadsbias: **{bias.upper()}**")
        lines.append(f"({n_signals} aktiva signaler)")
        
        if has_correlation:
            lines.append("\n⚠️ Signalerna är troligen KORRELERADE - de är inte oberoende.")
            lines.append("Styrkan är INTE {n_signals}x - undvik dubbel-counting.")
        
        # Uncertainty acknowledgment
        if bias == "neutral":
            lines.append("\nSignalerna pekar i olika riktningar eller är för svaga.")
        else:
            lines.append(f"\nHistoriskt sett har liknande kombinationer visat {bias} tendens.")
            lines.append("OBS: Ingen garanti - endast historisk observation.")
        
        return " ".join(lines)
