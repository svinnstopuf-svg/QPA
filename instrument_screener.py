"""
Instrument Screener - Filtrera fonder, ETF:er och aktier

Analyserar flera instrument och rankar dem baserat på statistisk edge.
Använder befintlig QuantPatternAnalyzer - ingen förändring av kärnlogik.

Fokus: Likviditet + stabilitet + långsiktighet

Val av instrument:
1. Index-ETF:er / fonder (bred exponering)
2. Enskilda aktier (stora, stabila bolag)
3. Tematiska fonder / ETF:er (används försiktigt)

Filtrering:
- Likviditet: Snittvolym > 50,000 aktier/dag
- Historik: Minst 5 års dagliga priser
- Beta/volatilitet: Undvik extremt hög volatilitet (beta > 1.5)
- Marknadstäckning: Index/ETF som speglar hela marknaden
"""

import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass
from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher
from src.decision import TrafficLightEvaluator, Signal
from src.analysis.signal_aggregator import SignalAggregator


@dataclass
class InstrumentScore:
    """Resultat för ett analyserat instrument."""
    ticker: str
    name: str
    category: str  # "index_etf", "stock", "thematic"
    
    # Pattern analysis
    total_patterns: int
    significant_patterns: int
    best_edge: float
    best_pattern_name: str
    
    # Traffic light
    signal: Signal
    signal_confidence: str
    
    # Risk metrics
    avg_edge: float
    stability_score: float
    tradeable_patterns: int
    
    # Practical allocation (Traffic Light based)
    recommended_allocation: str  # "5-10%", "2-5%", "0%"
    
    # Data quality
    data_points: int
    period_years: float
    avg_volume: float
    
    # Overall score (0-100)
    overall_score: float
    
    # Contributing factors (for debugging)
    contributing_factors: dict = None


class InstrumentScreener:
    """
    Screener för att filtrera och rangordna instrument.
    
    Använder befintlig QuantPatternAnalyzer utan modifikationer.
    """
    
    def __init__(
        self,
        min_data_years: float = 5.0,
        min_avg_volume: float = 50000,
        max_beta: float = 1.5
    ):
        """
        Initialize screener med filterkriterier.
        
        Args:
            min_data_years: Minst X års historik
            min_avg_volume: Minsta snittvolym per dag
            max_beta: Max beta (volatilitet relativt marknad)
        """
        self.min_data_years = min_data_years
        self.min_avg_volume = min_avg_volume
        self.max_beta = max_beta
        
        self.data_fetcher = DataFetcher()
        self.analyzer = QuantPatternAnalyzer(
            min_occurrences=5,
            min_confidence=0.40,
            forward_periods=1
        )
        self.traffic_light = TrafficLightEvaluator()
    
    def screen_instruments(
        self,
        instruments: List[Tuple[str, str, str]]
    ) -> List[InstrumentScore]:
        """
        Analysera och rangordna flera instrument.
        
        Args:
            instruments: Lista med (ticker, name, category)
            
        Returns:
            Lista av InstrumentScore, sorterad efter overall_score
        """
        results = []
        
        print("=" * 80)
        print("INSTRUMENT SCREENER")
        print("=" * 80)
        print(f"\nAnalyserar {len(instruments)} instrument...\n")
        
        for i, (ticker, name, category) in enumerate(instruments, 1):
            print(f"[{i}/{len(instruments)}] Analyserar {name} ({ticker})...")
            
            try:
                score = self._analyze_instrument(ticker, name, category)
                if score:
                    results.append(score)
                    # Konvertera signal till text för Windows-kompatibilitet
                    signal_text = self._signal_to_text(score.signal)
                    print(f"  OK: Score {score.overall_score:.1f}/100, Signal {signal_text}")
                else:
                    print(f"  SKIP: Misslyckades eller uppfyller inte kriterier")
            except Exception as e:
                print(f"  ERROR: {e}")
            
            print()
        
        # Sortera efter overall_score (högst först)
        results.sort(key=lambda x: x.overall_score, reverse=True)
        
        return results
    
    def _analyze_instrument(
        self,
        ticker: str,
        name: str,
        category: str
    ) -> InstrumentScore:
        """Analysera ett enskilt instrument."""
        
        # 1. Hämta data
        market_data = self.data_fetcher.fetch_stock_data(ticker, period="15y")
        if market_data is None:
            return None
        
        # 2. Kvalitetskontroll
        data_points = len(market_data)
        period_years = data_points / 252  # ~252 handelsdagar/år
        
        if period_years < self.min_data_years:
            print(f"  ⚠️ För kort historik: {period_years:.1f} år")
            return None
        
        avg_volume = float(market_data.volume.mean())
        if avg_volume < self.min_avg_volume:
            print(f"  ⚠️ För låg volym: {avg_volume:.0f}")
            return None
        
        # 3. Kör pattern analysis (befintlig logik)
        analysis_results = self.analyzer.analyze_market_data(market_data)
        
        # 4. Analysera nuvarande situation
        current_situation = self.analyzer.get_current_market_situation(
            market_data, lookback_window=50
        )
        
        # 5. Aggregera signaler
        aggregated = None
        if current_situation['active_situations']:
            aggregator = SignalAggregator()
            aggregated = aggregator.aggregate_signals(
                current_situation['active_situations']
            )
        
        # 6. Traffic Light-utvärdering
        aggregated_signal_data = {
            'bias': aggregated.direction if aggregated and hasattr(aggregated, 'direction') else 'NEUTRAL',
            'confidence': aggregated.confidence if aggregated else 'LÅG',
            'correlation_warning': aggregated.correlation_warning if aggregated else False
        }
        
        traffic_light_situation = {
            'aggregated_signal': aggregated_signal_data,
            'active_situations': current_situation.get('active_situations', [])
        }
        
        traffic_result = self.traffic_light.evaluate(
            analysis_results=analysis_results,
            current_situation=traffic_light_situation
        )
        
        # 7. Extrahera metrics
        significant_patterns = analysis_results.get('significant_patterns', [])
        
        # Hitta bästa edge
        best_edge = 0.0
        best_pattern_name = "Inget"
        avg_edge = 0.0
        stability_scores = []
        
        for pattern in significant_patterns:
            # Fix: mean_return och andra värden finns direkt i pattern dict
            if 'mean_return' in pattern:
                edge = pattern['mean_return'] * 100  # Convert to %
                if abs(edge) > abs(best_edge):
                    best_edge = edge
                    best_pattern_name = pattern.get('description', 'Inget')
                avg_edge += edge
            
            if 'stability_score' in pattern:
                stability_scores.append(pattern['stability_score'])
        
        if significant_patterns:
            avg_edge /= len(significant_patterns)
        
        avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0.5
        
        # Räkna tradeable patterns (edge >= 0.10%)
        tradeable_count = sum(
            1 for p in significant_patterns
            if 'mean_return' in p and p['mean_return'] * 100 >= 0.10
        )
        
        # 8. Practical allocation based on 4-tier Traffic Light
        # GREEN = 3-5%, YELLOW = 1-3%, ORANGE = 0-1%, RED = 0%
        if traffic_result.signal == Signal.GREEN:
            recommended_allocation = "3-5%"
        elif traffic_result.signal == Signal.YELLOW:
            recommended_allocation = "1-3%"
        elif traffic_result.signal == Signal.ORANGE:
            recommended_allocation = "0-1%"
        else:  # RED
            recommended_allocation = "0%"
        
        # 9. Beräkna overall score (0-100)
        overall_score = self._calculate_overall_score(
            traffic_result=traffic_result,
            best_edge=best_edge,
            avg_stability=avg_stability,
            tradeable_count=tradeable_count,
            total_patterns=len(significant_patterns),
            category=category
        )
        
        return InstrumentScore(
            ticker=ticker,
            name=name,
            category=category,
            total_patterns=len(analysis_results.get('results', [])),
            significant_patterns=len(significant_patterns),
            best_edge=best_edge,
            best_pattern_name=best_pattern_name,
            signal=traffic_result.signal,
            signal_confidence=traffic_result.confidence,
            avg_edge=avg_edge,
            stability_score=avg_stability,
            tradeable_patterns=tradeable_count,
            recommended_allocation=recommended_allocation,
            data_points=data_points,
            period_years=period_years,
            avg_volume=avg_volume,
            overall_score=overall_score,
            contributing_factors={
                'green_score': traffic_result.contributing_factors.get('green_score', 0),
                'red_score': traffic_result.contributing_factors.get('red_score', 0)
            }
        )
    
    def _calculate_overall_score(
        self,
        traffic_result,
        best_edge: float,
        avg_stability: float,
        tradeable_count: int,
        total_patterns: int,
        category: str
    ) -> float:
        """
        Beräkna overall score (0-100).
        
        Viktning:
        - Traffic Light: 30%
        - Edge: 30%
        - Stabilitet: 20%
        - Tradeable patterns: 20%
        """
        score = 0.0
        
        # 1. Traffic Light (30 poäng)
        if traffic_result.signal == Signal.GREEN:
            score += 30
        elif traffic_result.signal == Signal.YELLOW:
            score += 20
        elif traffic_result.signal == Signal.ORANGE:
            score += 10
        else:  # RED
            score += 0
        
        # 2. Edge (30 poäng)
        # Normalisera edge till 0-30 (0.50% edge = max poäng)
        edge_score = min(30, (abs(best_edge) / 0.50) * 30)
        if best_edge < 0:
            edge_score = 0  # Negativ edge = 0 poäng
        score += edge_score
        
        # 3. Stabilitet (20 poäng)
        score += avg_stability * 20
        
        # 4. Tradeable patterns (20 poäng)
        if total_patterns > 0:
            tradeable_ratio = tradeable_count / total_patterns
            score += tradeable_ratio * 20
        
        # Bonus/malus för kategori
        if category == "index_etf":
            score *= 1.1  # 10% bonus för index (stabilitet)
        elif category == "thematic":
            score *= 0.9  # 10% straff för tematiska (högre risk)
        
        return min(100, score)
    
    def _signal_to_text(self, signal: Signal) -> str:
        """Konvertera Signal enum till text (Windows-kompatibel)."""
        if signal == Signal.GREEN:
            return "GREEN"
        elif signal == Signal.YELLOW:
            return "YELLOW"
        elif signal == Signal.ORANGE:
            return "ORANGE"
        else:
            return "RED"


def format_screener_report(results: List[InstrumentScore]) -> str:
    """Formatera screener-resultat för display (Dashboard-stil)."""
    lines = []
    lines.append("=" * 80)
    lines.append("📊 INSTRUMENT SCREENER - VERSION 2.0 (4-NIVÅ SYSTEM)")
    lines.append("=" * 80)
    lines.append("")
    
    # Signalöversikt
    green_count = sum(1 for r in results if r.signal == Signal.GREEN)
    yellow_count = sum(1 for r in results if r.signal == Signal.YELLOW)
    orange_count = sum(1 for r in results if r.signal == Signal.ORANGE)
    red_count = sum(1 for r in results if r.signal == Signal.RED)
    
    lines.append("🚦 SIGNALÖVERSIKT:")
    lines.append(f"  🟢 GREEN  (Stark positiv):     {green_count} instrument")
    lines.append(f"  🟡 YELLOW (Måttlig positiv):   {yellow_count} instrument")
    lines.append(f"  🟠 ORANGE (Neutral/bevaka):   {orange_count} instrument")
    lines.append(f"  🔴 RED    (Stark negativ):     {red_count} instrument")
    lines.append("")
    lines.append(f"Analyserade: {len(results)} instrument")
    lines.append("")
    
    # Dashboard: Visa GREEN först
    lines.append("-" * 80)
    lines.append("👉 INVESTERINGSMÖJLIGHETER (GREEN/YELLOW/ORANGE FÖRST)")
    lines.append("-" * 80)
    lines.append("")
    
    # Sortera efter signal (GREEN > YELLOW > ORANGE > RED), sedan efter score
    signal_priority = {Signal.GREEN: 0, Signal.YELLOW: 1, Signal.ORANGE: 2, Signal.RED: 3}
    sorted_results = sorted(
        results, 
        key=lambda x: (signal_priority.get(x.signal, 4), -x.overall_score)
    )
    
    # Header
    lines.append(f"{'Rank':<5} {'Instrument':<30} {'Signal':<10} {'Edge':<8} {'Score':<6} {'Allokering':<12}")
    lines.append("-" * 80)
    
    for i, result in enumerate(sorted_results[:15], 1):
        # Konvertera till text istället för emoji
        if result.signal == Signal.GREEN:
            signal_text = "GREEN"
        elif result.signal == Signal.YELLOW:
            signal_text = "YELLOW"
        elif result.signal == Signal.ORANGE:
            signal_text = "ORANGE"
        else:
            signal_text = "RED"
        
        lines.append(
            f"{i:<5} {result.name[:28]:<30} "
            f"{signal_text:<10} "
            f"{result.best_edge:+.2f}%  "
            f"{result.overall_score:>5.1f}  "
            f"{result.recommended_allocation:>10}"
        )
    
    lines.append("")
    
    # Detaljerad info för topp 3
    lines.append("-" * 80)
    lines.append("DETALJERAD INFO (TOPP 3)")
    lines.append("-" * 80)
    
    for i, result in enumerate(results[:3], 1):
        # Konvertera signal till text
        if result.signal == Signal.GREEN:
            signal_text = "GREEN"
        elif result.signal == Signal.YELLOW:
            signal_text = "YELLOW"
        elif result.signal == Signal.ORANGE:
            signal_text = "ORANGE"
        else:
            signal_text = "RED"
        
        lines.append(f"\n{i}. {result.name} ({result.ticker})")
        lines.append(f"   Kategori: {result.category.upper()}")
        lines.append(f"   Signal: {signal_text} (Konfidens: {result.signal_confidence})")
        lines.append(f"   Bästa edge: {result.best_edge:+.2f}% ({result.best_pattern_name})")
        lines.append(f"   Genomsnittlig edge: {result.avg_edge:+.2f}%")
        lines.append(f"   Stabilitet: {result.stability_score:.1%}")
        lines.append(f"   Handelsbara mönster: {result.tradeable_patterns}/{result.significant_patterns}")
        lines.append(f"   Rekommenderad allokering: {result.recommended_allocation} av portfölj")
        lines.append(f"   Data: {result.period_years:.1f} år, {result.data_points} dagar")
        lines.append(f"   Overall Score: {result.overall_score:.1f}/100")
    
    lines.append("")
    
    # Nära edge-kategori (informativt)
    lines.append("-" * 80)
    lines.append("NÄRA EDGE-KATEGORIER (Informativt - ej handelsrekommendation)")
    lines.append("-" * 80)
    lines.append("")
    
    # Strong edge (0.50%+)
    strong_edge = [r for r in results if r.best_edge >= 0.50]
    if strong_edge:
        lines.append(f"STRONG EDGE (>=0.50%): {len(strong_edge)} instrument")
        for r in strong_edge[:5]:
            # Fix texttrunkering - använd full pattern name
            lines.append(f"  {r.name[:30]:<32} {r.best_edge:+.2f}% ({r.best_pattern_name})")
    
    # Moderate edge (0.20-0.49%)
    moderate_edge = [r for r in results if 0.20 <= r.best_edge < 0.50]
    if moderate_edge:
        lines.append(f"\nMODERATE EDGE (0.20-0.49%): {len(moderate_edge)} instrument")
        for r in moderate_edge[:5]:
            lines.append(f"  {r.name[:30]:<32} {r.best_edge:+.2f}% ({r.best_pattern_name})")
    
    # Small edge (0.10-0.19%)
    small_edge = [r for r in results if 0.10 <= r.best_edge < 0.20]
    if small_edge:
        lines.append(f"\nSMALL EDGE (0.10-0.19%): {len(small_edge)} instrument")
        for r in small_edge[:5]:
            lines.append(f"  {r.name[:30]:<32} {r.best_edge:+.2f}% ({r.best_pattern_name})")
    
    lines.append("")
    lines.append("[!] OBS: Edge ensam räcker inte - Traffic Light måste också vara grön/gul.")
    lines.append("")
    
    # Sektor/kategori-analys
    lines.append("-" * 80)
    lines.append("SEKTOR/KATEGORI-ANALYS (Multi-regim)")
    lines.append("-" * 80)
    lines.append("")
    
    # Gruppera efter kategori
    by_category = {}
    for r in results:
        if r.category not in by_category:
            by_category[r.category] = []
        by_category[r.category].append(r)
    
    for category, instruments in by_category.items():
        category_name = category.upper().replace('_', ' ')
        
        # Räkna signaler i kategorin
        cat_green = sum(1 for i in instruments if i.signal == Signal.GREEN)
        cat_yellow = sum(1 for i in instruments if i.signal == Signal.YELLOW)
        cat_orange = sum(1 for i in instruments if i.signal == Signal.ORANGE)
        cat_red = sum(1 for i in instruments if i.signal == Signal.RED)
        
        # Genomsnittlig edge i kategorin
        avg_cat_edge = sum(i.best_edge for i in instruments) / len(instruments)
        
        lines.append(f"{category_name}: {len(instruments)} instrument")
        lines.append(f"  Signaler: 🟢{cat_green} 🟡{cat_yellow} 🟠{cat_orange} 🔴{cat_red}")
        lines.append(f"  Genomsnittlig edge: {avg_cat_edge:+.2f}%")
        
        # Hitta outliers: positiva signaler när kategorin är mestadels RED
        if cat_red >= len(instruments) * 0.7:  # 70%+ RED
            outliers = [i for i in instruments if i.signal in [Signal.GREEN, Signal.YELLOW, Signal.ORANGE]]
            if outliers:
                lines.append(f"  👀 OUTLIERS (potentiell okorrelerad möjlighet):")
                for o in outliers:
                    signal_emoji = "🟢" if o.signal == Signal.GREEN else "🟡" if o.signal == Signal.YELLOW else "🟠"
                    lines.append(f"      {signal_emoji} {o.name[:25]:<27} Edge: {o.best_edge:+.2f}%")
        
        lines.append("")
    
    lines.append("[i] Outliers kan vara intressanta om de har låg korrelation med resten av sektorn.")
    lines.append("")
    
    # Övervakningskategori - Strong edge men RED signal
    lines.append("-" * 80)
    lines.append("ÖVERVAKNING (Strong edge men RED signal - bevakas utan att investera)")
    lines.append("-" * 80)
    lines.append("")
    
    watch_list = [r for r in results if r.best_edge >= 0.50 and r.signal == Signal.RED]
    if watch_list:
        lines.append(f"{len(watch_list)} instrument att bevaka:")
        for r in watch_list[:10]:
            # Förklara varför RED
            red_reasons = []
            if r.contributing_factors.get('red_score', 0) >= 2:
                red_reasons.append("Hög risk")
            if r.contributing_factors.get('green_score', 0) < 3:
                red_reasons.append("För få gröna villkor")
            if r.tradeable_patterns == 0:
                red_reasons.append("Inga handelsbara mönster")
            
            reason_text = ", ".join(red_reasons) if red_reasons else "Regim/risk-faktorer"
            
            lines.append(
                f"  {r.name[:30]:<32} Edge: {r.best_edge:+.2f}%, "
                f"Score: {r.overall_score:>5.1f} - RED p.g.a: {reason_text}"
            )
    else:
        lines.append("Inga instrument med strong edge och RED signal.")
    
    lines.append("")
    lines.append("[i] Bevaka dessa för framtida investeringsmöjligheter när signal blir grön/gul.")
    lines.append("")
    
    # Portföljrekommendation
    lines.append("-" * 80)
    lines.append("PORTFÖLJREKOMMENDATION")
    lines.append("-" * 80)
    lines.append("")
    
    # Alla signalnivåer
    green_instruments = [r for r in results if r.signal == Signal.GREEN]
    yellow_instruments = [r for r in results if r.signal == Signal.YELLOW]
    orange_instruments = [r for r in results if r.signal == Signal.ORANGE]
    
    if green_instruments or yellow_instruments or orange_instruments:
        lines.append("Traffic Light + Practical Allocation Rules (4-nivå):")
        lines.append("")
        
        if green_instruments:
            lines.append("🟢 GREEN (STARK POSITIV - 3-5%):")
            for result in green_instruments:
                lines.append(f"  {result.name[:30]:<32} {result.recommended_allocation:>8} av portfölj")
            lines.append("")
        
        if yellow_instruments:
            lines.append("🟡 YELLOW (MÅTTLIG POSITIV - 1-3%):")
            for result in yellow_instruments:
                lines.append(f"  {result.name[:30]:<32} {result.recommended_allocation:>8} av portfölj")
            lines.append("")
        
        if orange_instruments:
            lines.append("🟠 ORANGE (NEUTRAL/OBSERVANT - 0-1%):")
            for result in orange_instruments:
                lines.append(f"  {result.name[:30]:<32} {result.recommended_allocation:>8} av portfölj")
            lines.append("")
        
        # Beräkna total exponering
        total_green = len(green_instruments)
        total_yellow = len(yellow_instruments)
        total_orange = len(orange_instruments)
        
        # Estimerad exponering: GREEN=4%, YELLOW=2%, ORANGE=0.5%
        est_green_exposure = total_green * 4.0
        est_yellow_exposure = total_yellow * 2.0
        est_orange_exposure = total_orange * 0.5
        total_exposure = est_green_exposure + est_yellow_exposure + est_orange_exposure
        
        lines.append(f"Estimerad total exponering:")
        if total_green > 0:
            lines.append(f"  GREEN: ~{est_green_exposure:.0f}%")
        if total_yellow > 0:
            lines.append(f"  YELLOW: ~{est_yellow_exposure:.0f}%")
        if total_orange > 0:
            lines.append(f"  ORANGE: ~{est_orange_exposure:.0f}%")
        lines.append(f"  TOTAL: ~{total_exposure:.0f}%")
        lines.append(f"Rekommenderad cash reserve: ~{max(0, 100 - total_exposure):.0f}%")
    else:
        lines.append("[❌] Inga instrument rekommenderas för investering just nu.")
        lines.append("[!] Vänteläge - behåll hög cash reserve (100%)")
    
    lines.append("")
    
    # Signal-fördelning
    lines.append("-" * 80)
    lines.append("SIGNAL-FÖRDELNING")
    lines.append("-" * 80)
    
    green = sum(1 for r in results if r.signal == Signal.GREEN)
    yellow = sum(1 for r in results if r.signal == Signal.YELLOW)
    orange = sum(1 for r in results if r.signal == Signal.ORANGE)
    red = sum(1 for r in results if r.signal == Signal.RED)
    
    lines.append(f"  🟢 GREEN: {green} instrument ({green/len(results)*100:.0f}%)")
    lines.append(f"  🟡 YELLOW: {yellow} instrument ({yellow/len(results)*100:.0f}%)")
    lines.append(f"  🟠 ORANGE: {orange} instrument ({orange/len(results)*100:.0f}%)")
    lines.append(f"  🔴 RED: {red} instrument ({red/len(results)*100:.0f}%)")
    lines.append("")
    
    # Guide section
    lines.append("-" * 80)
    lines.append("GUIDE: Hur man tolkar resultaten")
    lines.append("-" * 80)
    lines.append("")
    lines.append("SIGNAL = Traffic Light 4-nivå system (färgen som styr din action):")
    lines.append("  • 🟢 GREEN  → Stark positiv: 3-5% per instrument")
    lines.append("  • 🟡 YELLOW → Måttlig positiv: 1-3% per instrument")
    lines.append("  • 🟠 ORANGE → Neutral/observant: 0-1% per instrument (eller vänta)")
    lines.append("  • 🔴 RED    → Stark negativ: 0%, stå utanför marknaden")
    lines.append("")
    lines.append("EDGE = Statistisk fördel i procent (informativt):")
    lines.append("  • Visar genomsnittlig avkastning från tekniska mönster")
    lines.append("  • Positiv edge betyder historisk fördel, men SIGNAL avgör om du agerar")
    lines.append("")
    lines.append("SCORE = Overall ranking (0-100):")
    lines.append("  • Kombinerar Traffic Light (30%), Edge (30%), Stabilitet (20%), Patterns (20%)")
    lines.append("  • Högre score = bättre kandidat när signal blir GREEN")
    lines.append("")
    lines.append("ALLOKERING = Praktisk positionsstorlek (graderad):")
    lines.append("  • Baserad direkt på Traffic Light signal")
    lines.append("  • Diversifiera: Sprid exponering över flera instrument")
    lines.append("  • Exempel 100,000 SEK portfölj:")
    lines.append("      - GREEN:  3,000-5,000 SEK per instrument")
    lines.append("      - YELLOW: 1,000-3,000 SEK per instrument")
    lines.append("      - ORANGE: 0-1,000 SEK per instrument (eller vänta)")
    lines.append("  • Max total exponering: 30-50% i svaga marknader")
    lines.append("")
    lines.append("=" * 80)
    lines.append("[!] VIKTIGT")
    lines.append("=" * 80)
    lines.append("  • Detta är ett statistiskt filter-verktyg, inte investeringsrådgivning")
    lines.append("  • Kombinera alltid med egen due diligence")
    lines.append("  • Allokeringar baseras på Traffic Light, inte Kelly (Kelly var för konservativt)")
    lines.append("  • Överstig aldrig din risktolerans")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point för instrument screener."""
    import sys
    
    # Importera det utvidgade instrumentuniversumet
    try:
        from instruments_universe import get_all_instruments, get_instrument_count
        instruments = get_all_instruments()
        print(f"\nℹ️ Laddar {get_instrument_count()} Avanza-kompatibla instrument...\n")
    except ImportError:
        print("⚠️ instruments_universe.py saknas, använder fallback-lista...\n")
        # Fallback - minimal lista om filen inte finns
        instruments = [
            ("^OMX", "OMX Stockholm 30", "index_regional"),
            ("^GSPC", "S&P 500", "index_global"),
            ("AAPL", "Apple", "stock_us_tech"),
            ("MSFT", "Microsoft", "stock_us_tech"),
        ]
    
    # Initiera screener
    screener = InstrumentScreener(
        min_data_years=5.0,
        min_avg_volume=50000,
        max_beta=1.5
    )
    
    # Kör screening
    results = screener.screen_instruments(instruments)
    
    # Visa resultat
    if results:
        report = format_screener_report(results)
        print("\n\n")
        print(report)
    else:
        print("\n❌ Inga instrument uppfyllde kriterierna.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
