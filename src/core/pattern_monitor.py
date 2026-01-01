"""
Kontinuerlig utvärdering av mönsters styrka över tid.

Övervakar mönster för att identifiera när de förlorar statistisk styrka
eller uppvisar försämrad riskjusterad avkastning.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from ..core.pattern_evaluator import PatternEvaluation


@dataclass
class PatternStatus:
    """Status för ett övervakat mönster."""
    pattern_id: str
    is_active: bool
    weight: float  # 0.0 - 1.0
    degradation_reason: Optional[str]
    recent_performance: float
    historical_performance: float
    sharpe_ratio: float
    stability_trend: str  # "improving", "stable", "degrading"
    last_evaluated: datetime


class PatternMonitor:
    """
    Övervakar och utvärderar mönsters prestanda över tid.
    
    Funktioner:
    - Identifierar mönster som förlorar statistisk styrka
    - Beräknar riskjusterad avkastning (Sharpe ratio)
    - Justerar vikter baserat på prestanda
    - Markerar mönster som inaktiva när de inte längre är robusta
    """
    
    def __init__(
        self,
        degradation_threshold: float = 0.15,  # 15% försämring
        min_sharpe_ratio: float = 0.0,
        stability_threshold: float = 0.60
    ):
        """
        Initialiserar mönsterövervakning.
        
        Args:
            degradation_threshold: Maximal acceptabel försämring i prestanda
            min_sharpe_ratio: Minsta acceptabla Sharpe ratio
            stability_threshold: Minsta acceptabla stabilitet
        """
        self.degradation_threshold = degradation_threshold
        self.min_sharpe_ratio = min_sharpe_ratio
        self.stability_threshold = stability_threshold
        
    def evaluate_pattern_health(
        self,
        pattern_id: str,
        recent_returns: np.ndarray,
        historical_returns: np.ndarray,
        recent_timestamps: np.ndarray,
        historical_timestamps: np.ndarray
    ) -> PatternStatus:
        """
        Utvärderar ett mönsters hälsa genom att jämföra recent prestanda
        med historisk prestanda.
        
        Args:
            pattern_id: Mönster-ID
            recent_returns: Senaste observationernas avkastningar
            historical_returns: Alla historiska avkastningar
            recent_timestamps: Tidsstämplar för senaste observationer
            historical_timestamps: Alla historiska tidsstämplar
            
        Returns:
            PatternStatus med information om mönstrets hälsa
        """
        # Beräkna prestanda
        recent_perf = np.mean(recent_returns) if len(recent_returns) > 0 else 0.0
        historical_perf = np.mean(historical_returns)
        
        # Beräkna Sharpe ratio (riskjusterad avkastning)
        sharpe = self._calculate_sharpe_ratio(recent_returns)
        
        # Utvärdera stabilitet över tid
        stability_trend = self._evaluate_stability_trend(
            historical_returns,
            historical_timestamps
        )
        
        # Beräkna försämring
        if historical_perf != 0:
            degradation = (historical_perf - recent_perf) / abs(historical_perf)
        else:
            degradation = 0.0
        
        # Bestäm om mönstret är aktivt och beräkna vikt
        is_active = True
        weight = 1.0
        degradation_reason = None
        
        # Kontrollera olika kriterier för nedgradering
        if degradation > self.degradation_threshold:
            is_active = False
            degradation_reason = f"Prestanda försämrad med {degradation*100:.1f}%"
            weight = 0.0
        elif sharpe < self.min_sharpe_ratio:
            weight = 0.5
            degradation_reason = f"Låg riskjusterad avkastning (Sharpe: {sharpe:.2f})"
        elif stability_trend == "degrading":
            weight = 0.7
            degradation_reason = "Stabilitet försämras över tid"
        elif len(recent_returns) < 10:
            weight = 0.8
            degradation_reason = "För få senaste observationer"
        
        return PatternStatus(
            pattern_id=pattern_id,
            is_active=is_active,
            weight=weight,
            degradation_reason=degradation_reason,
            recent_performance=recent_perf,
            historical_performance=historical_perf,
            sharpe_ratio=sharpe,
            stability_trend=stability_trend,
            last_evaluated=datetime.now()
        )
    
    def monitor_all_patterns(
        self,
        patterns_data: Dict[str, Dict],
        lookback_recent: int = 50
    ) -> Dict[str, PatternStatus]:
        """
        Övervakar alla mönster och returnerar deras status.
        
        Args:
            patterns_data: Dictionary med mönsterdata
                Format: {pattern_id: {
                    'returns': np.ndarray,
                    'timestamps': np.ndarray
                }}
            lookback_recent: Antal senaste observationer att använda för recent prestanda
            
        Returns:
            Dictionary med PatternStatus för varje mönster
        """
        pattern_statuses = {}
        
        for pattern_id, data in patterns_data.items():
            returns = data['returns']
            timestamps = data['timestamps']
            
            if len(returns) < lookback_recent:
                # För få observationer totalt
                recent_returns = returns
                recent_timestamps = timestamps
            else:
                # Dela upp i recent och historical
                recent_returns = returns[-lookback_recent:]
                recent_timestamps = timestamps[-lookback_recent:]
            
            status = self.evaluate_pattern_health(
                pattern_id=pattern_id,
                recent_returns=recent_returns,
                historical_returns=returns,
                recent_timestamps=recent_timestamps,
                historical_timestamps=timestamps
            )
            
            pattern_statuses[pattern_id] = status
        
        return pattern_statuses
    
    def _calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Beräknar Sharpe ratio (riskjusterad avkastning).
        
        Args:
            returns: Array med avkastningar
            risk_free_rate: Riskfri ränta
            
        Returns:
            Sharpe ratio
        """
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns)
        
        if std_excess == 0:
            return 0.0
        
        return mean_excess / std_excess
    
    def _evaluate_stability_trend(
        self,
        returns: np.ndarray,
        timestamps: np.ndarray,
        n_periods: int = 4
    ) -> str:
        """
        Utvärderar om mönstrets stabilitet förbättras, är stabil, eller försämras.
        
        Args:
            returns: Array med avkastningar
            timestamps: Array med tidsstämplar
            n_periods: Antal perioder att dela upp datan i
            
        Returns:
            "improving", "stable", eller "degrading"
        """
        if len(returns) < n_periods * 10:
            return "stable"  # För lite data för att utvärdera trend
        
        # Dela upp i perioder
        period_size = len(returns) // n_periods
        period_means = []
        period_stds = []
        
        for i in range(n_periods):
            start_idx = i * period_size
            end_idx = (i + 1) * period_size if i < n_periods - 1 else len(returns)
            period_returns = returns[start_idx:end_idx]
            
            period_means.append(np.mean(period_returns))
            period_stds.append(np.std(period_returns))
        
        # Beräkna trend i medelvärde och standardavvikelse
        mean_trend = np.polyfit(range(n_periods), period_means, 1)[0]
        std_trend = np.polyfit(range(n_periods), period_stds, 1)[0]
        
        # Bedöm trend
        if mean_trend < -0.001 or std_trend > 0.002:
            return "degrading"  # Medelvärde minskar eller volatilitet ökar
        elif mean_trend > 0.001 and std_trend < -0.001:
            return "improving"  # Medelvärde ökar och volatilitet minskar
        else:
            return "stable"
    
    def generate_monitoring_report(
        self,
        pattern_statuses: Dict[str, PatternStatus]
    ) -> str:
        """
        Genererar en rapport över mönsterens hälsa.
        
        Args:
            pattern_statuses: Dictionary med PatternStatus
            
        Returns:
            Formaterad rapport som sträng
        """
        lines = []
        lines.append("=" * 80)
        lines.append("MÖNSTERÖVERVAKNING - KONTINUERLIG UTVÄRDERING")
        lines.append("=" * 80)
        lines.append("")
        
        # Dela upp i aktiva och inaktiva
        active_patterns = {k: v for k, v in pattern_statuses.items() if v.is_active}
        inactive_patterns = {k: v for k, v in pattern_statuses.items() if not v.is_active}
        degraded_patterns = {k: v for k, v in active_patterns.items() if v.weight < 1.0}
        
        lines.append(f"Totalt antal mönster: {len(pattern_statuses)}")
        lines.append(f"  Aktiva: {len(active_patterns)}")
        lines.append(f"  Degraderade (aktiva men reducerad vikt): {len(degraded_patterns)}")
        lines.append(f"  Inaktiva: {len(inactive_patterns)}")
        lines.append("")
        
        # Degraderade mönster
        if degraded_patterns:
            lines.append("-" * 80)
            lines.append("DEGRADERADE MÖNSTER (Reducerad vikt)")
            lines.append("-" * 80)
            for pattern_id, status in degraded_patterns.items():
                lines.append(f"\n{pattern_id}:")
                lines.append(f"  Vikt: {status.weight*100:.0f}%")
                lines.append(f"  Orsak: {status.degradation_reason}")
                lines.append(f"  Recent prestanda: {status.recent_performance*100:.2f}%")
                lines.append(f"  Historisk prestanda: {status.historical_performance*100:.2f}%")
                lines.append(f"  Sharpe ratio: {status.sharpe_ratio:.2f}")
                lines.append(f"  Stabilitetstrend: {status.stability_trend}")
        
        # Inaktiva mönster
        if inactive_patterns:
            lines.append("")
            lines.append("-" * 80)
            lines.append("INAKTIVA MÖNSTER (Markerade som inaktiva)")
            lines.append("-" * 80)
            for pattern_id, status in inactive_patterns.items():
                lines.append(f"\n{pattern_id}:")
                lines.append(f"  Orsak: {status.degradation_reason}")
                lines.append(f"  Recent prestanda: {status.recent_performance*100:.2f}%")
                lines.append(f"  Historisk prestanda: {status.historical_performance*100:.2f}%")
                lines.append(f"  Sharpe ratio: {status.sharpe_ratio:.2f}")
        
        # Friska mönster
        healthy_patterns = {k: v for k, v in active_patterns.items() if v.weight == 1.0}
        if healthy_patterns:
            lines.append("")
            lines.append("-" * 80)
            lines.append(f"FRISKA MÖNSTER ({len(healthy_patterns)} mönster)")
            lines.append("-" * 80)
            lines.append("Dessa mönster har full vikt och god prestanda.")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
