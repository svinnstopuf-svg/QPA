"""
Kommunikationslager för användarvänlig presentation av resultat.

Översätter statistiska resultat till enkelt, neutralt språk som uttrycker
sannolikheter och historiska tendenser - aldrig absoluta påståenden.
"""

from typing import Dict, List, Optional
from ..core.pattern_evaluator import PatternEvaluation
from ..analysis.outcome_analyzer import OutcomeStatistics
from ..patterns.detector import MarketSituation


class InsightFormatter:
    """
    Formaterar analysresultat för icke-expertanvändare.
    
    Principer:
    - Enkelt, neutralt språk
    - Inga tekniska termer om möjligt
    - Presentera som historiska tendenser
    - Visa alltid osäkerhet och begränsningar
    - ALDRIG köp/säljrekommendationer
    """
    
    def __init__(self):
        pass
    
    def format_pattern_insight(
        self,
        situation: MarketSituation,
        outcome_stats: OutcomeStatistics,
        pattern_eval: PatternEvaluation,
        baseline_comparison: Optional[Dict] = None,
        permutation_result: Optional[object] = None
    ) -> str:
        """
        Skapar en användarvänlig beskrivning av ett mönster och dess utfall.
        
        Args:
            situation: Den identifierade marknadssituationen
            outcome_stats: Statistik över historiska utfall
            pattern_eval: Utvärdering av mönstrets robusthet
            baseline_comparison: Optionell jämförelse mot baseline (marknadens genomsnitt)
            permutation_result: Optionell permutation test result (shuffle test)
            
        Returns:
            Formaterad sträng med insikt
        """
        if not pattern_eval.is_significant:
            return self._format_insignificant_pattern(situation, pattern_eval)
        
        lines = []
        
        # Beskrivning av situationen
        lines.append(f"## {situation.description}")
        lines.append("")
        
        # Hur ofta mönstret förekommit
        lines.append(self._format_frequency(outcome_stats.sample_size))
        lines.append("")
        
        # BASELINE JÄMFÖRELSE - Visa edge relativt genomsnittet
        if baseline_comparison:
            lines.append("### Edge relativt marknadens genomsnitt")
            lines.append(self._format_baseline_edge(outcome_stats, baseline_comparison))
            lines.append("")
        
        # PERMUTATION TEST - Validering mot slump
        if permutation_result:
            lines.append(self._format_permutation_test(permutation_result))
            lines.append("")
        
        # Historiskt beteende
        lines.append("### Historiskt beteende")
        lines.append(self._format_central_tendency(outcome_stats))
        lines.append(self._format_win_rate(outcome_stats))
        lines.append(self._format_risk_profile(outcome_stats))
        lines.append("")
        
        # Stabilitet och konfidensgrad
        lines.append("### Tillförlitlighet")
        lines.append(self._format_stability(pattern_eval))
        lines.append("")
        
        # Negativ information - när mönstret INTE fungerar
        lines.append("### När mönstret varit mindre tillförlitligt")
        lines.append(self._format_negative_information(outcome_stats, pattern_eval))
        lines.append("")
        
        # Begränsningar
        lines.append("### Viktigt att komma ihåg")
        lines.append(self._format_limitations(outcome_stats))
        
        return "\n".join(lines)
    
    def format_comparison_insight(
        self,
        situation: MarketSituation,
        comparison: Dict[str, float]
    ) -> str:
        """
        Formaterar jämförelse mellan mönster och baslinje.
        
        Args:
            situation: Marknadssituationen
            comparison: Jämförelsestatistik
            
        Returns:
            Formaterad jämförelse
        """
        if not comparison:
            return "Otillräcklig data för jämförelse."
        
        lines = []
        lines.append(f"## Jämförelse: {situation.description}")
        lines.append("")
        
        # Genomsnittlig avkastning
        pattern_mean = comparison['pattern_mean'] * 100
        baseline_mean = comparison['baseline_mean'] * 100
        diff = comparison['mean_difference'] * 100
        
        if diff > 0:
            direction = "högre"
            verb = "ökat"
        elif diff < 0:
            direction = "lägre"
            verb = "minskat"
        else:
            direction = "liknande"
            verb = "varit oförändrat"
        
        lines.append(f"Historiskt sett har marknaden i genomsnitt {verb} med {abs(diff):.2f}% ")
        lines.append(f"i denna situation, jämfört med {baseline_mean:.2f}% under normala förhållanden.")
        lines.append("")
        
        # Vinstfrekvens
        pattern_wr = comparison['pattern_win_rate'] * 100
        baseline_wr = comparison['baseline_win_rate'] * 100
        wr_diff = comparison['win_rate_difference'] * 100
        
        lines.append(f"Positiva utfall har inträffat {pattern_wr:.1f}% av gångerna ")
        lines.append(f"(jämfört med {baseline_wr:.1f}% normalt).")
        lines.append("")
        
        # Statistisk signifikans
        if comparison.get('is_significant_5pct'):
            lines.append("Skillnaden är statistiskt mätbar, men detta garanterar inte ")
            lines.append("att mönstret kommer fortsätta bete sig på samma sätt.")
        else:
            lines.append("Skillnaden mot normalt beteende är relativt liten. ")
            lines.append("Detta mönster kanske inte är särskilt användbart isolerat.")
        
        return "\n".join(lines)
    
    def format_summary(
        self,
        significant_patterns: List[Dict],
        total_patterns: int
    ) -> str:
        """
        Formaterar en sammanfattning av analysresultat.
        
        Args:
            significant_patterns: Lista med signifikanta mönster
            total_patterns: Totalt antal analyserade mönster
            
        Returns:
            Formaterad sammanfattning
        """
        lines = []
        lines.append("# Analyssammanfattning")
        lines.append("")
        lines.append(f"Av {total_patterns} analyserade marknadssituationer identifierades ")
        lines.append(f"{len(significant_patterns)} mönster med tillräcklig historisk data ")
        lines.append("och stabilitet för att vara potentiellt meningsfulla.")
        lines.append("")
        
        if len(significant_patterns) == 0:
            lines.append("Inga robusta mönster hittades i den tillgängliga datan. ")
            lines.append("Detta kan bero på:")
            lines.append("- Otillräcklig historisk data")
            lines.append("- För snäva sökkriterier")
            lines.append("- Avsaknad av tydliga statistiska mönster i denna marknad")
        else:
            lines.append("## Identifierade mönster")
            lines.append("")
            for i, pattern in enumerate(significant_patterns, 1):
                lines.append(f"{i}. **{pattern['description']}**")
                lines.append(f"   - Observerat {pattern['sample_size']} gånger")
                lines.append(f"   - Historisk styrka: {pattern['statistical_strength']*100:.0f}%")
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_baseline_edge(self, stats: OutcomeStatistics, baseline_comparison: Dict) -> str:
        """Formaterar edge relativt baseline - KRITISKT för att förstå värde."""
        pattern_mean = stats.mean_return * 100
        baseline_mean = baseline_comparison.get('baseline_mean', 0.0) * 100
        edge = pattern_mean - baseline_mean
        
        lines = []
        lines.append(f"Mönstrets genomsnitt: **{pattern_mean:+.2f}%** per dag")
        lines.append(f"Marknadens genomsnitt: **{baseline_mean:+.2f}%** per dag")
        lines.append(f"**Edge (skillnad): {edge:+.2f}%**")
        
        # Interpret edge
        if abs(edge) < 0.05:
            interpretation = "⚠️ Edge är MYCKET liten - mönstret är knappt bättre än genomsnittet"
        elif abs(edge) < 0.10:
            interpretation = "⚠️ Edge är liten - endast marginal fördel mot genomsnittet"
        elif abs(edge) < 0.20:
            interpretation = "✅ Edge är måttlig - tydlig skillnad mot genomsnittet"
        else:
            interpretation = "✅ Edge är betydande - stor skillnad mot genomsnittet"
        
        lines.append(interpretation)
        
        return " ".join(lines)
    
    def _format_permutation_test(self, permutation_result) -> str:
        """Formaterar permutation test - Jim Simons validering mot slump."""
        lines = []
        lines.append("### Shuffle Test (Validering mot slumpen)")
        lines.append(f"Mönstrets avkastning: {permutation_result.real_mean_return*100:.2f}%")
        lines.append(f"Jämfört med {permutation_result.n_permutations} slumpmässiga dagindelningar:")
        lines.append(f"**Bättre än {permutation_result.percentile_rank:.1f}% av slumpmässiga mönster**")
        
        if permutation_result.is_better_than_random:
            lines.append("✅ Detta mönster är statistiskt bättre än slump")
        else:
            lines.append("❌ Detta mönster är INTE tydligt bättre än slump")
            lines.append("⚠️ Kan vara överanpassning eller brus")
        
        lines.append(f"P-värde: {permutation_result.p_value:.3f}")
        
        return " ".join(lines)
    
    def _format_frequency(self, sample_size: int) -> str:
        """Formaterar hur ofta något inträffat."""
        if sample_size < 30:
            qualifier = "sällan"
        elif sample_size < 100:
            qualifier = "då och då"
        elif sample_size < 300:
            qualifier = "ganska ofta"
        else:
            qualifier = "ofta"
        
        return f"Denna situation har inträffat {qualifier} historiskt ({sample_size} observationer)."
    
    def _format_central_tendency(self, stats: OutcomeStatistics) -> str:
        """Formaterar centraltendensen på ett användarvänligt sätt."""
        mean_pct = stats.mean_return * 100
        median_pct = stats.median_return * 100
        
        if abs(mean_pct) < 0.1:
            return "I liknande situationer har marknaden tenderat att röra sig mycket lite."
        
        direction = "stigit" if mean_pct > 0 else "fallit"
        
        # Använd median om fördelningen är skev
        if abs(stats.skewness) > 0.5:
            central_value = median_pct
            measure = "typiskt"
        else:
            central_value = mean_pct
            measure = "i genomsnitt"
        
        return f"I liknande situationer har marknaden {measure} {direction} med {abs(central_value):.2f}%."
    
    def _format_win_rate(self, stats: OutcomeStatistics) -> str:
        """Formaterar vinstfrekvens på ett begripligt sätt."""
        win_pct = stats.win_rate * 100
        
        if win_pct > 60:
            qualifier = "oftare än inte"
        elif win_pct > 50:
            qualifier = "något oftare än inte"
        elif win_pct == 50:
            qualifier = "ungefär hälften av gångerna"
        elif win_pct > 40:
            qualifier = "något mindre än hälften av gångerna"
        else:
            qualifier = "i en minoritet av fallen"
        
        return f"Positiva utfall har inträffat {qualifier} ({win_pct:.0f}% av observationerna)."
    
    def _format_risk_profile(self, stats: OutcomeStatistics) -> str:
        """Formaterar riskprofil på ett begripligt sätt."""
        lines = []
        
        # Spridning
        std_pct = stats.std_return * 100
        if std_pct < 1:
            volatility = "låg variation"
        elif std_pct < 3:
            volatility = "måttlig variation"
        else:
            volatility = "hög variation"
        
        lines.append(f"Utfallen har visat {volatility} (standardavvikelse: {std_pct:.2f}%).")
        
        # Worst case
        worst_pct = stats.percentile_5 * 100
        lines.append(f"I de värsta 5% av fallen har rörelser ned till {worst_pct:.2f}% observerats.")
        
        return " ".join(lines)
    
    def _format_stability(self, pattern_eval: PatternEvaluation) -> str:
        """Formaterar stabilitetsinformation."""
        stability_pct = pattern_eval.stability_score * 100
        strength_pct = pattern_eval.statistical_strength * 100
        
        if stability_pct > 80:
            stability_desc = "mycket konsekvent"
        elif stability_pct > 60:
            stability_desc = "relativt stabilt"
        else:
            stability_desc = "varierande"
        
        lines = []
        lines.append(f"Mönstret har varit {stability_desc} över olika tidsperioder ")
        lines.append(f"(stabilitet: {stability_pct:.0f}%, historisk styrka: {strength_pct:.0f}%).")
        
        return " ".join(lines)
    
    def _format_negative_information(self, stats: OutcomeStatistics, pattern_eval: PatternEvaluation) -> str:
        """
        Formaterar NEGATIV information - när mönstret INTE fungerar.
        Detta bygger förtroende genom ärlighet.
        """
        lines = []
        
        # Worst case scenario
        worst_pct = abs(stats.percentile_5 * 100)
        lines.append(f"I de sämsta 5% av fallen (ungefär 1 gång av 20) har mönstret")
        lines.append(f"resulterat i förluster på upp till {worst_pct:.2f}%.")
        
        # Win rate transparency
        loss_rate = (1 - stats.win_rate) * 100
        lines.append(f"Mönstret har varit negativt i {loss_rate:.0f}% av observationerna.")
        
        # Temporal concern
        if pattern_eval.stability_score < 0.7:
            lines.append("Mönstrets prestanda har varierat över tid - det är inte konsekvent.")
        
        return " ".join(lines)
    
    def _format_limitations(self, stats: OutcomeStatistics) -> str:
        """Formaterar begränsningar och varningar."""
        lines = []
        
        lines.append("- Historiskt beteende är ingen garanti för framtida resultat")
        lines.append("- Detta mönster är svagt isolerat; värdet ligger i aggregation med andra mönster")
        
        if stats.sample_size < 50:
            lines.append("- Relativt få observationer innebär större osäkerhet")
        
        if abs(stats.skewness) > 1:
            lines.append("- Fördelningen av utfall är skev; extrema utfall kan förekomma")
        
        return "\n".join(lines)
    
    def _format_insignificant_pattern(
        self,
        situation: MarketSituation,
        pattern_eval: PatternEvaluation
    ) -> str:
        """Formaterar meddelande för icke-signifikanta mönster."""
        lines = []
        lines.append(f"## {situation.description}")
        lines.append("")
        
        if pattern_eval.occurrence_count < pattern_eval.occurrence_count:
            lines.append(f"Detta mönster har endast observerats {pattern_eval.occurrence_count} gånger, ")
            lines.append("vilket är för få observationer för att dra meningsfulla slutsatser.")
        else:
            lines.append("Detta mönster visar inte tillräcklig stabilitet över tid för att ")
            lines.append("vara användbart för analys.")
        
        return "\n".join(lines)


class ConsoleFormatter:
    """Formaterar output för konsolvisning."""
    
    @staticmethod
    def format_table(data: List[Dict], headers: List[str]) -> str:
        """
        Skapar en enkel textbaserad tabell.
        
        Args:
            data: Lista med dictionaries innehållande rad-data
            headers: Lista med kolumnrubriker
            
        Returns:
            Formaterad tabell som sträng
        """
        if not data or not headers:
            return ""
        
        # Beräkna kolumnbredder
        col_widths = {h: len(h) for h in headers}
        for row in data:
            for header in headers:
                value_len = len(str(row.get(header, "")))
                col_widths[header] = max(col_widths[header], value_len)
        
        # Skapa header
        lines = []
        header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        # Skapa rader
        for row in data:
            row_line = " | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers)
            lines.append(row_line)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """Formaterar ett tal som procent."""
        return f"{value * 100:.{decimals}f}%"
    
    @staticmethod
    def format_number(value: float, decimals: int = 2) -> str:
        """Formaterar ett tal."""
        return f"{value:.{decimals}f}"
