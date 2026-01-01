"""
Jämför mönster mot baseline (marknadens genomsnitt).

Detta är KRITISKT för att förstå om ett mönster faktiskt ger edge.
"""

from typing import Dict, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class BaselineComparison:
    """Resultat från baseline-jämförelse."""
    pattern_mean: float
    baseline_mean: float
    excess_return: float  # pattern - baseline
    is_better_than_baseline: bool
    statistical_significance: float  # p-value från t-test
    effect_size: float  # Cohen's d
    

class BaselineComparator:
    """
    Jämför alla mönster mot marknadens baseline.
    
    Jim Simons princip: "Edge är skillnaden mot slumpen, inte absolut avkastning"
    """
    
    def __init__(self):
        pass
    
    def compare_to_baseline(
        self,
        pattern_returns: np.ndarray,
        baseline_returns: np.ndarray
    ) -> BaselineComparison:
        """
        Jämför ett mönster mot baseline.
        
        Args:
            pattern_returns: Avkastningar för mönstret
            baseline_returns: Avkastningar för hela marknaden
            
        Returns:
            BaselineComparison med detaljerad jämförelse
        """
        if len(pattern_returns) == 0 or len(baseline_returns) == 0:
            return BaselineComparison(
                pattern_mean=0.0,
                baseline_mean=0.0,
                excess_return=0.0,
                is_better_than_baseline=False,
                statistical_significance=1.0,
                effect_size=0.0
            )
        
        pattern_mean = np.mean(pattern_returns)
        baseline_mean = np.mean(baseline_returns)
        excess_return = pattern_mean - baseline_mean
        
        # T-test för statistisk signifikans
        from scipy import stats
        if len(pattern_returns) > 1 and len(baseline_returns) > 1:
            t_stat, p_value = stats.ttest_ind(pattern_returns, baseline_returns)
        else:
            p_value = 1.0
        
        # Cohen's d för effect size
        if len(pattern_returns) > 1 and len(baseline_returns) > 1:
            pooled_std = np.sqrt(
                ((len(pattern_returns) - 1) * np.var(pattern_returns) +
                 (len(baseline_returns) - 1) * np.var(baseline_returns)) /
                (len(pattern_returns) + len(baseline_returns) - 2)
            )
            if pooled_std > 0:
                effect_size = excess_return / pooled_std
            else:
                effect_size = 0.0
        else:
            effect_size = 0.0
        
        return BaselineComparison(
            pattern_mean=pattern_mean,
            baseline_mean=baseline_mean,
            excess_return=excess_return,
            is_better_than_baseline=excess_return > 0 and p_value < 0.05,
            statistical_significance=p_value,
            effect_size=effect_size
        )
    
    def format_comparison(self, comparison: BaselineComparison) -> str:
        """
        Formaterar baseline-jämförelse till läsbar text.
        
        Args:
            comparison: BaselineComparison att formatera
            
        Returns:
            Formaterad text
        """
        lines = []
        lines.append("### Jämförelse mot marknadens genomsnitt")
        lines.append(f"Mönster: {comparison.pattern_mean*100:.2f}% per dag")
        lines.append(f"Marknad (baseline): {comparison.baseline_mean*100:.2f}% per dag")
        lines.append(f"**Excess avkastning: {comparison.excess_return*100:.2f}%**")
        
        if comparison.is_better_than_baseline:
            lines.append("✅ Detta mönster presterar statistiskt bättre än genomsnittet")
        elif comparison.excess_return > 0:
            lines.append("⚠️ Mönstret är svagt positivt men inte statistiskt signifikant")
        else:
            lines.append("❌ Detta mönster presterar INTE bättre än genomsnittet")
        
        # Effect size interpretation
        if abs(comparison.effect_size) < 0.2:
            effect_desc = "försumbar"
        elif abs(comparison.effect_size) < 0.5:
            effect_desc = "liten"
        elif abs(comparison.effect_size) < 0.8:
            effect_desc = "medelstor"
        else:
            effect_desc = "stor"
        
        lines.append(f"Effektstorlek: {effect_desc} (Cohen's d = {comparison.effect_size:.2f})")
        
        return "\n".join(lines)
