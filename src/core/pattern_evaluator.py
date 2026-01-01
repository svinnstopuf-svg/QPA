"""
Kärnmodul för att utvärdera statistiska mönster i finansiella marknader.

Detta är hjärtat i analysverktyget - det utvärderar om identifierade mönster
är statistiskt robusta nog för att vara meningsfulla.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class PatternEvaluation:
    """Resultat av en mönsterutvärdering."""
    pattern_id: str
    occurrence_count: int
    mean_return: float
    std_return: float
    win_rate: float
    max_drawdown: float
    is_significant: bool
    stability_score: float  # Hur stabilt mönstret är över tid (0-1)
    statistical_strength: float  # Statistisk styrka baserat på sample size och konsistens (0-1)
    # OBS: Dessa är HISTORISKA mått, inte framtidsprediktioner!
    
    
class PatternEvaluator:
    """
    Utvärderar om statistiska mönster är robusta och meningsfulla.
    
    Principer:
    - Mönster måste uppträda tillräckligt ofta för att vara relevanta
    - Mönster måste vara stabila över tid
    - Ingen överanpassning tillåts
    - Varje mönster är svagt isolerat men kan vara värdefullt i aggregation
    """
    
    def __init__(
        self,
        min_occurrences: int = 30,
        min_confidence: float = 0.70,
        stability_window: int = 252  # ~1 år av handelsdagar
    ):
        self.min_occurrences = min_occurrences
        self.min_confidence = min_confidence
        self.stability_window = stability_window
        
    def evaluate_pattern(
        self,
        pattern_id: str,
        historical_returns: np.ndarray,
        timestamps: np.ndarray
    ) -> PatternEvaluation:
        """
        Utvärderar ett mönster baserat på historiska utfall.
        
        Args:
            pattern_id: Unik identifierare för mönstret
            historical_returns: Array med historiska avkastningar när mönstret inträffat
            timestamps: Tidsstämplar för varje observation
            
        Returns:
            PatternEvaluation med resultat och metadatar
        """
        if len(historical_returns) < self.min_occurrences:
            return self._create_insufficient_data_evaluation(pattern_id, len(historical_returns))
        
        # Beräkna grundläggande statistik
        mean_return = np.mean(historical_returns)
        std_return = np.std(historical_returns)
        win_rate = np.sum(historical_returns > 0) / len(historical_returns)
        max_drawdown = self._calculate_max_drawdown(historical_returns)
        
        # Utvärdera stabilitet över tid
        stability_score = self._evaluate_stability(historical_returns, timestamps)
        
        # Beräkna statistisk styrka
        statistical_strength = self._calculate_statistical_strength(historical_returns)
        
        # Avgör om mönstret är signifikant
        is_significant = (
            len(historical_returns) >= self.min_occurrences and
            stability_score >= self.min_confidence and
            statistical_strength >= self.min_confidence
        )
        
        return PatternEvaluation(
            pattern_id=pattern_id,
            occurrence_count=len(historical_returns),
            mean_return=mean_return,
            std_return=std_return,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            is_significant=is_significant,
            stability_score=stability_score,
            statistical_strength=statistical_strength
        )
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Beräknar maximal historisk drawdown."""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)
    
    def _evaluate_stability(self, returns: np.ndarray, timestamps: np.ndarray) -> float:
        """
        Utvärderar om mönstret är stabilt över olika tidsperioder.
        
        Delar upp datan i segmenter och jämför om mönstret beter sig liknande.
        """
        if len(returns) < 2 * self.min_occurrences:
            return 0.5  # Otillräcklig data för stabilitetsanalys
        
        # Dela upp i tidsperioder
        n_periods = min(4, len(returns) // self.min_occurrences)
        period_size = len(returns) // n_periods
        
        period_means = []
        for i in range(n_periods):
            start_idx = i * period_size
            end_idx = (i + 1) * period_size if i < n_periods - 1 else len(returns)
            period_returns = returns[start_idx:end_idx]
            period_means.append(np.mean(period_returns))
        
        # Beräkna variation mellan perioder
        # Lägre variation = högre stabilitet
        if len(period_means) > 1:
            mean_of_means = np.mean(period_means)
            if mean_of_means != 0:
                coefficient_of_variation = np.std(period_means) / abs(mean_of_means)
                # Omvandla till stabilitetsscore (högre = bättre)
                stability = max(0.0, min(1.0, 1.0 - coefficient_of_variation))
            else:
                stability = 0.5
        else:
            stability = 0.5
            
        return stability
    
    def _calculate_statistical_strength(self, returns: np.ndarray) -> float:
        """
        Beräknar statistisk styrka baserat på antal observationer och variation.
        
        Fler observationer och lägre variation ger högre statistisk styrka.
        OBS: Detta är INTE sannolikheten att mönstret fungerar i framtiden!
        """
        n = len(returns)
        
        # Sample size komponent (mer data = högre konfidensgrad)
        size_confidence = min(1.0, n / (3 * self.min_occurrences))
        
        # Konsistens komponent
        if len(returns) > 1:
            # Använd standardfel för att mäta precision
            std_error = np.std(returns) / np.sqrt(n)
            mean_return = abs(np.mean(returns))
            
            if mean_return > 0:
                # Låg standardfel relativt mean = hög konfidensgrad
                consistency = max(0.0, min(1.0, 1.0 - (std_error / mean_return)))
            else:
                consistency = 0.3  # Låg konfidensgrad om mean är nära noll
        else:
            consistency = 0.0
        
        # Kombinera komponenterna
        confidence = (size_confidence + consistency) / 2
        
        return confidence
    
    def _create_insufficient_data_evaluation(
        self,
        pattern_id: str,
        actual_count: int
    ) -> PatternEvaluation:
        """Skapar en utvärdering för mönster med otillräcklig data."""
        return PatternEvaluation(
            pattern_id=pattern_id,
            occurrence_count=actual_count,
            mean_return=0.0,
            std_return=0.0,
            win_rate=0.0,
            max_drawdown=0.0,
            is_significant=False,
            stability_score=0.0,
            statistical_strength=0.0
        )
