"""
Traffic Light Decision Model

Ett översättningslager som konverterar kvantitativ analys till beslutstöd.
Svarar på EN fråga: "Hur aggressiv bör jag vara just nu?"

INTE: När marknaden vänder, vilken aktie som är bäst, vad som händer imorgon
VÄL: Hur du justerar risknivå och investeringstempo
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple


class Signal(Enum):
    """Traffic light signals."""
    GREEN = "🟢 GRÖN"
    YELLOW = "🟡 GUL" 
    RED = "🔴 RÖD"


@dataclass
class TrafficLightResult:
    """Result from traffic light evaluation."""
    signal: Signal
    confidence: str
    risk_level: str
    risk_change: str
    action_recommendation: str
    reasoning: List[str]
    requirements_for_change: Dict[str, List[str]]
    contributing_factors: Dict[str, any]


class TrafficLightEvaluator:
    """
    Utvärderar marknadsläge och ger beslutstöd genom traffic-light-modell.
    
    Regler:
    - 🟢 GRÖN: Statistiskt gynnsam miljö → Risk på
    - 🟡 GUL: Osäker miljö → Vänta / Skala ner
    - 🔴 RÖD: Statistiskt ogynnsam miljö → Risk av
    
    Viktigt:
    - Färg ändras sällan (ingen snabba flippar)
    - Endast EN färg åt gången
    - Du agerar på FÄRG - inte på enskilda siffror
    """
    
    def __init__(self):
        pass
    
    def evaluate(
        self, 
        analysis_results: Dict,
        current_situation: Dict
    ) -> TrafficLightResult:
        """
        Huvudfunktion: Utvärdera marknadsläge och returnera färgsignal.
        
        Args:
            analysis_results: Resultat från QuantPatternAnalyzer
            current_situation: Nuvarande marknadssituation
            
        Returns:
            TrafficLightResult med signal och rekommendationer
        """
        # Extrahera nödvändig data
        significant_patterns = analysis_results.get('significant_patterns', [])
        aggregated_signal = current_situation.get('aggregated_signal')
        
        # Utvärdera villkor för varje färg
        green_score, green_reasons = self._evaluate_green_conditions(
            significant_patterns, aggregated_signal
        )
        red_score, red_reasons = self._evaluate_red_conditions(
            significant_patterns, aggregated_signal
        )
        
        # Bestäm färg baserat på poäng
        if red_score >= 2:
            signal = Signal.RED
            reasoning = red_reasons
        elif green_score >= 3:
            signal = Signal.GREEN
            reasoning = green_reasons
        else:
            signal = Signal.YELLOW
            reasoning = self._get_yellow_reasoning(
                significant_patterns, aggregated_signal
            )
        
        # Bygg komplett resultat
        result = self._build_result(
            signal=signal,
            reasoning=reasoning,
            significant_patterns=significant_patterns,
            aggregated_signal=aggregated_signal,
            green_score=green_score,
            red_score=red_score
        )
        
        return result
    
    def _evaluate_green_conditions(
        self, 
        patterns: List,
        aggregated_signal
    ) -> Tuple[int, List[str]]:
        """
        Utvärdera villkor för GRÖN signal.
        
        Krav: Minst 3 av 5 uppfyllda:
        1. Samlad marknadsbias ≠ Bearish
        2. Minst 1 friskt mönster med edge ≥ 0.10%
        3. Inga aktiva mönster med kraftigt negativ edge
        4. Stabilitet > 60% för huvudmönstren
        5. Konfidens ≠ LÅG
        
        Returns:
            (score, reasons) där score är antal uppfyllda villkor
        """
        score = 0
        reasons = []
        
        # 1. Samlad bias ≠ Bearish
        if aggregated_signal:
            bias = aggregated_signal.get('bias', 'NEUTRAL')
            if bias != 'BEARISH':
                score += 1
                reasons.append(f"✅ Marknadsbias är {bias} (inte bearish)")
            else:
                reasons.append(f"❌ Marknadsbias är BEARISH")
        
        # 2. Minst 1 friskt mönster med edge ≥ 0.10%
        fresh_patterns_with_edge = [
            p for p in patterns
            if self._is_fresh_pattern(p) and self._get_pattern_edge(p) >= 0.10
        ]
        if fresh_patterns_with_edge:
            score += 1
            reasons.append(
                f"✅ {len(fresh_patterns_with_edge)} friska mönster med edge ≥ 0.10%"
            )
        else:
            reasons.append("❌ Inga friska mönster med tillräcklig edge")
        
        # 3. Inga aktiva mönster med kraftigt negativ edge (<-0.10%)
        negative_patterns = [
            p for p in patterns
            if self._get_pattern_edge(p) < -0.10
        ]
        if not negative_patterns:
            score += 1
            reasons.append("✅ Inga kraftigt negativa mönster aktiva")
        else:
            reasons.append(
                f"❌ {len(negative_patterns)} mönster med negativ edge < -0.10%"
            )
        
        # 4. Stabilitet > 60% för huvudmönstren
        stable_patterns = [
            p for p in patterns
            if self._get_pattern_stability(p) > 0.60
        ]
        if len(stable_patterns) >= len(patterns) * 0.5:  # Minst hälften stabila
            score += 1
            reasons.append(
                f"✅ {len(stable_patterns)}/{len(patterns)} mönster har stabilitet > 60%"
            )
        else:
            reasons.append(
                f"❌ För få stabila mönster ({len(stable_patterns)}/{len(patterns)})"
            )
        
        # 5. Konfidens ≠ LÅG
        if aggregated_signal:
            confidence = aggregated_signal.get('confidence', 'LÅG').upper()
            if confidence != 'LÅG':
                score += 1
                reasons.append(f"✅ Konfidens är {confidence} (inte låg)")
            else:
                reasons.append("❌ Konfidens är LÅG")
        
        return score, reasons
    
    def _evaluate_red_conditions(
        self, 
        patterns: List,
        aggregated_signal
    ) -> Tuple[int, List[str]]:
        """
        Utvärdera villkor för RÖD signal.
        
        Krav: Minst 2 av följande:
        1. Aktivt negativt mönster med edge < -0.10%
        2. Bearish regim + hög volatilitet
        3. Flera degraderade mönster samtidigt (>30% degradering)
        4. Konfidens = LÅG och korrelation HÖG
        5. Historiskt drawdown-miljö (ex. death cross + high vol)
        
        Returns:
            (score, reasons) där score är antal uppfyllda villkor
        """
        score = 0
        reasons = []
        
        # 1. Aktivt negativt mönster med edge < -0.10%
        negative_patterns = [
            p for p in patterns
            if self._get_pattern_edge(p) < -0.10
        ]
        if negative_patterns:
            score += 1
            pattern_names = [self._get_pattern_name(p) for p in negative_patterns[:2]]
            reasons.append(
                f"⚠️ {len(negative_patterns)} negativt mönster aktivt: {', '.join(pattern_names)}"
            )
        
        # 2. Bearish regim + hög volatilitet (approximation)
        if aggregated_signal:
            bias = aggregated_signal.get('bias', 'NEUTRAL')
            # Kolla efter high vol patterns
            high_vol_patterns = [
                p for p in patterns
                if 'high_vol' in str(p).lower() or 'volatility' in str(p).lower()
            ]
            if bias == 'BEARISH' and high_vol_patterns:
                score += 1
                reasons.append("⚠️ Bearish regim kombinerat med hög volatilitet")
        
        # 3. Flera degraderade mönster samtidigt
        # Använd pattern_statuses om tillgängligt, annars uppskatta
        degraded_count = sum(
            1 for p in patterns
            if self._is_pattern_degraded(p)
        )
        if degraded_count >= 2:
            score += 1
            reasons.append(f"⚠️ {degraded_count} mönster visar degradering")
        
        # 4. Konfidens = LÅG och korrelation HÖG
        if aggregated_signal:
            confidence = aggregated_signal.get('confidence', '').upper()
            correlation_warning = aggregated_signal.get('correlation_warning', False)
            if confidence == 'LÅG' and correlation_warning:
                score += 1
                reasons.append("⚠️ Låg konfidens kombinerat med hög signalkorrelation")
        
        # 5. Historiskt drawdown-miljö (death cross, extended selloff, etc.)
        drawdown_patterns = [
            p for p in patterns
            if any(keyword in self._get_pattern_name(p).lower() 
                   for keyword in ['death cross', 'selloff', 'crash', 'bear'])
        ]
        if drawdown_patterns:
            score += 1
            reasons.append(
                f"⚠️ Drawdown-mönster aktiva: {len(drawdown_patterns)} st"
            )
        
        return score, reasons
    
    def _get_yellow_reasoning(
        self, 
        patterns: List,
        aggregated_signal
    ) -> List[str]:
        """Generera förklaring för varför signalen är GUL."""
        reasons = []
        
        if aggregated_signal:
            bias = aggregated_signal.get('bias', 'NEUTRAL')
            confidence = aggregated_signal.get('confidence', 'LÅG').upper()
            correlation = aggregated_signal.get('correlation_warning', False)
            
            reasons.append(f"📊 Marknadsbias: {bias}")
            reasons.append(f"📊 Konfidens: {confidence}")
            
            if correlation:
                reasons.append("⚠️ Hög korrelation mellan signaler")
        
        # Edge-analys
        edges = [self._get_pattern_edge(p) for p in patterns]
        avg_edge = sum(edges) / len(edges) if edges else 0
        
        if abs(avg_edge) < 0.10:
            reasons.append(f"⚠️ Genomsnittlig edge är låg: {avg_edge:.2%}")
        
        reasons.append("💡 Ingen tydlig statistisk fördel - vänteläge är korrekt")
        
        return reasons
    
    def _build_result(
        self,
        signal: Signal,
        reasoning: List[str],
        significant_patterns: List,
        aggregated_signal,
        green_score: int,
        red_score: int
    ) -> TrafficLightResult:
        """Bygg komplett TrafficLightResult."""
        
        # Confidence
        confidence = "HÖG"
        if aggregated_signal:
            confidence = aggregated_signal.get('confidence', 'LÅG').upper()
        
        # Risk level och change
        if signal == Signal.GREEN:
            risk_level = "NORMAL"
            risk_change = "→ NORMAL"
            action = self._get_green_action()
        elif signal == Signal.YELLOW:
            risk_level = "NORMAL → LÅG"
            risk_change = "↓ REDUCERA"
            action = self._get_yellow_action()
        else:  # RED
            risk_level = "LÅG"
            risk_change = "↓↓ MINIMAL"
            action = self._get_red_action()
        
        # Requirements for change
        requirements = self._get_requirements_for_change(
            signal, green_score, red_score
        )
        
        # Contributing factors
        factors = {
            'green_score': green_score,
            'red_score': red_score,
            'total_patterns': len(significant_patterns),
            'bias': aggregated_signal.get('bias') if aggregated_signal else 'UNKNOWN',
            'confidence': confidence
        }
        
        return TrafficLightResult(
            signal=signal,
            confidence=confidence,
            risk_level=risk_level,
            risk_change=risk_change,
            action_recommendation=action,
            reasoning=reasoning,
            requirements_for_change=requirements,
            contributing_factors=factors
        )
    
    def _get_green_action(self) -> str:
        """Handlingsrekommendation för GRÖN signal."""
        return """
🟢 RISK PÅ - Marknaden är statistiskt gynnsam

Hur du agerar:
  • Investera enligt din plan
  • Full normal positionering
  • Ingen överanalys
  • Rebalansera lugnt

Mentalt tillstånd:
  "Jag behöver inte ha rätt – sannolikheterna är på min sida."
"""
    
    def _get_yellow_action(self) -> str:
        """Handlingsrekommendation för GUL signal."""
        return """
🟡 VÄNTA / SKALA NER - Ingen tydlig edge

Hur du agerar:
  • Vänta med nya större beslut
  • Skala ner tempo, inte panik
  • Endast små justeringar
  • Låt tid göra jobbet

📌 Detta är det vanligaste läget (och det är bra)

Mentalt tillstånd:
  "Jag gör inget dumt – och det är ett aktivt val."
"""
    
    def _get_red_action(self) -> str:
        """Handlingsrekommendation för RÖD signal."""
        return """
🔴 RISK AV - Statistiskt ogynnsam miljö

Hur du agerar:
  • Pausa nya investeringar
  • Skydda kapital
  • Vänta – inga försök att vara smart
  • Låt signalerna återgå till gult/grönt

📌 Rött betyder INTE "sälj allt"
📌 Det betyder: sluta ta ny risk

Mentalt tillstånd:
  "Jag förlorar inte pengar för att jag är uttråkad."
"""
    
    def _get_requirements_for_change(
        self,
        current_signal: Signal,
        green_score: int,
        red_score: int
    ) -> Dict[str, List[str]]:
        """Definiera vad som krävs för att byta färg."""
        requirements = {}
        
        if current_signal == Signal.GREEN:
            requirements['Till GUL'] = [
                "Marknadsbias blir NEUTRAL",
                "Edge minskar under 0.10%",
                "Konfidens sjunker till LÅG"
            ]
            requirements['Till RÖD'] = [
                "Minst 2 negativa villkor aktiveras",
                "Negativt mönster med edge < -0.10%",
                "Bearish + hög volatilitet"
            ]
        
        elif current_signal == Signal.YELLOW:
            requirements['Till GRÖN'] = [
                f"Uppnå minst 3/5 gröna villkor (nu: {green_score}/5)",
                "Bias blir BULLISH eller NEUTRAL med edge",
                "Konfidens ökar till MÅTTLIG eller HÖG"
            ]
            requirements['Till RÖD'] = [
                f"Minst 2 röda villkor aktiveras (nu: {red_score})",
                "Flera degraderade mönster",
                "Bearish regim + hög volatilitet"
            ]
        
        else:  # RED
            requirements['Till GUL'] = [
                f"Färre än 2 röda villkor (nu: {red_score})",
                "Negativa mönster inaktiveras",
                "Volatilitet normaliseras"
            ]
            requirements['Till GRÖN'] = [
                "Röda villkor < 2 OCH gröna villkor ≥ 3",
                "Bullish eller neutral bias",
                "Stabila mönster med positiv edge"
            ]
        
        return requirements
    
    # Helper methods för pattern-extraktion
    
    def _is_fresh_pattern(self, pattern) -> bool:
        """Kontrollera om mönster är friskt (stabilitet hög, inte degraderat)."""
        stability = self._get_pattern_stability(pattern)
        return stability > 0.60
    
    def _get_pattern_edge(self, pattern) -> float:
        """Extrahera edge från pattern."""
        if isinstance(pattern, dict):
            eval_data = pattern.get('pattern_eval', {})
            if hasattr(eval_data, 'outcome_stats'):
                return eval_data.outcome_stats.mean_return * 100  # Convert to %
            return 0.0
        return 0.0
    
    def _get_pattern_stability(self, pattern) -> float:
        """Extrahera stabilitet från pattern."""
        if isinstance(pattern, dict):
            eval_data = pattern.get('pattern_eval', {})
            if hasattr(eval_data, 'stability_score'):
                return eval_data.stability_score
            return 0.5
        return 0.5
    
    def _get_pattern_name(self, pattern) -> str:
        """Extrahera mönsternamn."""
        if isinstance(pattern, dict):
            situation = pattern.get('situation', {})
            if hasattr(situation, 'description'):
                return situation.description
            return str(situation)
        return str(pattern)
    
    def _is_pattern_degraded(self, pattern) -> bool:
        """Kontrollera om mönster är degraderat."""
        # Approximation: låg stabilitet indikerar degradering
        stability = self._get_pattern_stability(pattern)
        return stability < 0.50


def format_traffic_light_report(result: TrafficLightResult) -> str:
    """
    Formatera traffic light-resultat för display.
    
    Args:
        result: TrafficLightResult objekt
        
    Returns:
        Formaterad sträng för utskrift
    """
    lines = []
    
    lines.append("=" * 80)
    lines.append("🚦 MARKNADSLÄGE (TRAFFIC LIGHT)")
    lines.append("=" * 80)
    lines.append("")
    
    # Huvudsignal
    lines.append(f"Signal: {result.signal.value}")
    lines.append(f"Konfidens: {result.confidence}")
    lines.append(f"Risknivå: {result.risk_level}")
    lines.append(f"Förändring: {result.risk_change}")
    lines.append("")
    
    # Handlingsrekommendation
    lines.append("REKOMMENDERAD HANDLING:")
    lines.append(result.action_recommendation)
    lines.append("")
    
    # Förklaring
    lines.append("-" * 80)
    lines.append("VARFÖR DENNA FÄRG?")
    lines.append("-" * 80)
    for reason in result.reasoning:
        lines.append(f"  {reason}")
    lines.append("")
    
    # Krav för färgbyte (expanderbar sektion)
    lines.append("-" * 80)
    lines.append("VAD KRÄVS FÖR FÄRGBYTE?")
    lines.append("-" * 80)
    for target, requirements in result.requirements_for_change.items():
        lines.append(f"\n{target}:")
        for req in requirements:
            lines.append(f"  • {req}")
    lines.append("")
    
    # Teknisk info (kompakt)
    lines.append("-" * 80)
    lines.append("TEKNISK INFO")
    lines.append("-" * 80)
    factors = result.contributing_factors
    lines.append(f"  Gröna villkor: {factors.get('green_score', 0)}/5")
    lines.append(f"  Röda villkor: {factors.get('red_score', 0)}")
    lines.append(f"  Mönster analyserade: {factors.get('total_patterns', 0)}")
    lines.append(f"  Marknadsbias: {factors.get('bias', 'UNKNOWN')}")
    lines.append("")
    
    # Viktig påminnelse
    lines.append("=" * 80)
    lines.append("🧠 VIKTIGASTE REGLERNA")
    lines.append("=" * 80)
    lines.append("  1️⃣ Färg ändras sällan – inga snabba flippar")
    lines.append("  2️⃣ Endast EN färg åt gången")
    lines.append("  3️⃣ Du agerar på FÄRG – inte på enskilda siffror")
    lines.append("")
    lines.append("⚠️ Denna modell kommer INTE förutsäga krascher eller göra dig rik snabbt")
    lines.append("✅ Den hjälper dig skydda från stora misstag och vara konsekvent")
    lines.append("")
    
    return "\n".join(lines)
