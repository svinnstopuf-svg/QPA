"""
Regime Detection - Market Stress Index

Detects when correlation → 1 (everything falls together).
When technical analysis doesn't work: Time to "turn off the machine".

Philosophy:
- When >80% of instruments are RED, lower max exposure
- High correlation = diversification fails
- Different regimes require different strategies
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class MarketRegime(Enum):
    """Market regime classification."""
    EUPHORIA = "EUPHORIA"  # >70% GREEN/YELLOW
    HEALTHY = "HEALTHY"  # 50-70% GREEN/YELLOW
    CAUTIOUS = "CAUTIOUS"  # 30-50% GREEN/YELLOW
    STRESSED = "STRESSED"  # 10-30% GREEN/YELLOW
    CRISIS = "CRISIS"  # <10% GREEN/YELLOW


@dataclass
class RegimeAnalysis:
    """Market regime analysis result."""
    regime: MarketRegime
    stress_index: float  # 0-100 (100 = maximum stress)
    red_pct: float  # % RED signals
    green_yellow_pct: float  # % GREEN/YELLOW signals
    recommended_exposure: float  # Maximum portfolio exposure (%)
    position_size_multiplier: float  # Multiply all positions by this
    recommendation: str  # Action advice


class RegimeDetector:
    """
    Detects market regime and adjusts exposure accordingly.
    
    Rules:
    - CRISIS (>90% RED): Max 10% exposure, 0.2x position sizes
    - STRESSED (>80% RED): Max 20% exposure, 0.4x position sizes
    - CAUTIOUS (>70% RED): Max 40% exposure, 0.7x position sizes
    - HEALTHY (50-70% RED): Max 60% exposure, 1.0x position sizes
    - EUPHORIA (<30% RED): Max 80% exposure, 1.0x position sizes
    
    Examples:
    - 245 instruments: 231 RED (94%) → CRISIS regime
      - Recommended exposure: 10%
      - If GREEN signal recommends 5%, actual position = 5% * 0.2 = 1%
    
    - 245 instruments: 100 RED (41%) → HEALTHY regime
      - Recommended exposure: 60%
      - If GREEN signal recommends 5%, actual position = 5% * 1.0 = 5%
    """
    
    def __init__(self):
        """Initialize regime detector."""
        pass
    
    def calculate_stress_index(
        self,
        signal_distribution: Dict[str, int]
    ) -> float:
        """
        Calculate market stress index (0-100).
        
        Higher = more stress.
        Based on % of RED signals.
        
        Args:
            signal_distribution: Dict with counts for GREEN/YELLOW/ORANGE/RED
            
        Returns:
            Stress index (0-100)
        """
        total = sum(signal_distribution.values())
        
        if total == 0:
            return 50.0  # Neutral
        
        red_pct = signal_distribution.get('RED', 0) / total
        
        # Stress index: 0% RED = 0 stress, 100% RED = 100 stress
        stress = red_pct * 100
        
        return stress
    
    def detect_regime(
        self,
        signal_distribution: Dict[str, int]
    ) -> RegimeAnalysis:
        """
        Detect market regime based on signal distribution.
        
        Args:
            signal_distribution: Dict with signal counts
            
        Returns:
            RegimeAnalysis with recommendations
        """
        total = sum(signal_distribution.values())
        
        if total == 0:
            # No data
            return RegimeAnalysis(
                regime=MarketRegime.CRISIS,
                stress_index=100,
                red_pct=100,
                green_yellow_pct=0,
                recommended_exposure=0,
                position_size_multiplier=0,
                recommendation="NO DATA - Stay in cash"
            )
        
        # Calculate percentages
        red_count = signal_distribution.get('RED', 0)
        green_count = signal_distribution.get('GREEN', 0)
        yellow_count = signal_distribution.get('YELLOW', 0)
        orange_count = signal_distribution.get('ORANGE', 0)
        
        red_pct = (red_count / total) * 100
        green_yellow_pct = ((green_count + yellow_count) / total) * 100
        
        # Calculate stress index
        stress = self.calculate_stress_index(signal_distribution)
        
        # Determine regime
        if green_yellow_pct > 70:
            regime = MarketRegime.EUPHORIA
            recommended_exposure = 80.0
            multiplier = 1.0
            rec = "EUPHORISKT - Hög exponering OK, men var försiktig"
        
        elif green_yellow_pct > 50:
            regime = MarketRegime.HEALTHY
            recommended_exposure = 60.0
            multiplier = 1.0
            rec = "HÄLSOSAMT - Normal exponering"
        
        elif green_yellow_pct > 30:
            regime = MarketRegime.CAUTIOUS
            recommended_exposure = 40.0
            multiplier = 0.7
            rec = "FÖRSIKTIGT - Reducerad exponering"
        
        elif green_yellow_pct > 10:
            regime = MarketRegime.STRESSED
            recommended_exposure = 20.0
            multiplier = 0.4
            rec = "STRESSAT - Minimal exponering"
        
        else:
            regime = MarketRegime.CRISIS
            recommended_exposure = 10.0
            multiplier = 0.2
            rec = "KRIS - Nästan ingen exponering! Korrelation = 1"
        
        return RegimeAnalysis(
            regime=regime,
            stress_index=stress,
            red_pct=red_pct,
            green_yellow_pct=green_yellow_pct,
            recommended_exposure=recommended_exposure,
            position_size_multiplier=multiplier,
            recommendation=rec
        )
    
    def adjust_positions_for_regime(
        self,
        base_positions: Dict[str, float],
        regime: RegimeAnalysis
    ) -> Dict[str, float]:
        """
        Adjust position sizes based on market regime.
        
        Args:
            base_positions: Dict mapping ticker to base position size (%)
            regime: Current regime analysis
            
        Returns:
            Adjusted position sizes
        """
        adjusted = {}
        
        for ticker, base_size in base_positions.items():
            adjusted_size = base_size * regime.position_size_multiplier
            adjusted[ticker] = adjusted_size
        
        return adjusted
    
    def calculate_correlation_estimate(
        self,
        signal_distribution: Dict[str, int]
    ) -> float:
        """
        Estimate average correlation based on signal clustering.
        
        When signals cluster (all RED or all GREEN), correlation is high.
        
        Args:
            signal_distribution: Signal counts
            
        Returns:
            Estimated correlation (0-1)
        """
        total = sum(signal_distribution.values())
        
        if total == 0:
            return 0.5
        
        # Calculate entropy (diversity of signals)
        probs = [count / total for count in signal_distribution.values() if count > 0]
        entropy = -sum(p * np.log(p) for p in probs if p > 0)
        
        # Max entropy for 4 categories = log(4) ≈ 1.39
        max_entropy = np.log(4)
        
        # Normalized entropy (1 = maximum diversity, 0 = all same)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        # Correlation estimate (inverse of diversity)
        # High entropy (diverse signals) = low correlation
        # Low entropy (clustered signals) = high correlation
        correlation_estimate = 1 - normalized_entropy
        
        return correlation_estimate
    
    def should_halt_trading(
        self,
        regime: RegimeAnalysis,
        halt_threshold: float = 90.0
    ) -> Tuple[bool, str]:
        """
        Determine if trading should be halted completely.
        
        Args:
            regime: Current regime
            halt_threshold: Stress threshold for halt
            
        Returns:
            (should_halt, reason)
        """
        if regime.stress_index >= halt_threshold:
            return (
                True,
                f"HALT TRADING - Stress index {regime.stress_index:.0f}% "
                f"({regime.red_pct:.0f}% RED signals). "
                f"Correlation → 1, technical analysis unreliable."
            )
        
        if regime.regime == MarketRegime.CRISIS and regime.green_yellow_pct < 5:
            return (
                True,
                f"HALT TRADING - CRISIS regime with only {regime.green_yellow_pct:.1f}% positive signals. "
                "Wait for market stabilization."
            )
        
        return (False, "Trading allowed")


def format_regime_report(analysis: RegimeAnalysis) -> str:
    """Format regime analysis report."""
    lines = []
    lines.append("=" * 80)
    lines.append("MARKET REGIME DETECTION")
    lines.append("=" * 80)
    lines.append("")
    
    # Regime indicator
    regime_icons = {
        MarketRegime.EUPHORIA: "🚀",
        MarketRegime.HEALTHY: "✅",
        MarketRegime.CAUTIOUS: "⚠️",
        MarketRegime.STRESSED: "😰",
        MarketRegime.CRISIS: "🚨"
    }
    
    icon = regime_icons.get(analysis.regime, "")
    lines.append(f"{icon} AKTUELLT REGIME: {analysis.regime.value}")
    lines.append("")
    
    # Metrics
    lines.append(f"Stress Index: {analysis.stress_index:.1f}/100")
    lines.append(f"RED signals: {analysis.red_pct:.1f}%")
    lines.append(f"GREEN/YELLOW signals: {analysis.green_yellow_pct:.1f}%")
    lines.append("")
    
    # Recommendations
    lines.append("-" * 80)
    lines.append("REKOMMENDATIONER")
    lines.append("-" * 80)
    lines.append(f"Max Portfolio Exponering: {analysis.recommended_exposure:.0f}%")
    lines.append(f"Position Size Multiplier: {analysis.position_size_multiplier:.1f}x")
    lines.append("")
    lines.append(f"Åtgärd: {analysis.recommendation}")
    lines.append("")
    
    # Examples
    lines.append("-" * 80)
    lines.append("EXEMPEL PÅ JUSTERING")
    lines.append("-" * 80)
    
    example_bases = [5.0, 3.0, 1.0]
    for base in example_bases:
        adjusted = base * analysis.position_size_multiplier
        lines.append(f"  Base {base:.1f}% → Adjusted {adjusted:.1f}%")
    
    lines.append("")
    
    # Regime-specific guidance
    lines.append("-" * 80)
    lines.append("REGIMSPECIFIK VÄGLEDNING")
    lines.append("-" * 80)
    
    if analysis.regime == MarketRegime.CRISIS:
        lines.append("🚨 KRIS-LÄGE:")
        lines.append("  • Korrelation närmar sig 1 - alla tillgångar rör sig tillsammans")
        lines.append("  • Teknisk analys fungerar INTE i detta läge")
        lines.append("  • Håll >90% cash, vänta på stabilisering")
        lines.append("  • Diversifiering ger INGEN skydd")
    
    elif analysis.regime == MarketRegime.STRESSED:
        lines.append("😰 STRESSAT LÄGE:")
        lines.append("  • Hög korrelation - diversifiering försämrad")
        lines.append("  • Reducera positioner kraftigt")
        lines.append("  • Endast starkaste GREEN-signaler")
        lines.append("  • Håll >80% cash")
    
    elif analysis.regime == MarketRegime.CAUTIOUS:
        lines.append("⚠️  FÖRSIKTIGT LÄGE:")
        lines.append("  • Öka korrelation - var selektiv")
        lines.append("  • Reducera positioner måttligt")
        lines.append("  • Fokusera på högkvalitativa signaler")
        lines.append("  • Håll >60% cash")
    
    elif analysis.regime == MarketRegime.HEALTHY:
        lines.append("✅ HÄLSOSAMT LÄGE:")
        lines.append("  • Normal korrelation - teknisk analys fungerar")
        lines.append("  • Normala positioner OK")
        lines.append("  • Diversifiering ger skydd")
        lines.append("  • Håll 40-60% cash")
    
    elif analysis.regime == MarketRegime.EUPHORIA:
        lines.append("🚀 EUPHORISKT LÄGE:")
        lines.append("  • Låg korrelation - många möjligheter")
        lines.append("  • Aggressiva positioner möjliga")
        lines.append("  • VAR FÖRSIKTIG - euphoria föregår ofta crashes")
        lines.append("  • Överväg trailing stops")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Market Regime Detection Module")
    print("Usage:")
    print("  from src.risk.regime_detection import RegimeDetector")
    print("  detector = RegimeDetector()")
    print("  regime = detector.detect_regime(signal_distribution)")
