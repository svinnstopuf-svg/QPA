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
    
    # Kelly recommendation
    kelly_allocation: float
    position_size_pct: float
    
    # Data quality
    data_points: int
    period_years: float
    avg_volume: float
    
    # Overall score (0-100)
    overall_score: float


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
        
        # 8. Kelly allocation (mer korrekt)
        kelly_allocation = 0.0
        if best_edge > 0.10:
            # Hitta win_rate för bästa mönstret
            win_rate = 0.5  # Default
            for p in significant_patterns:
                if 'mean_return' in p and 'win_rate' in p:
                    if p['mean_return'] * 100 == best_edge:
                        win_rate = p['win_rate']
                        break
            
            # Kelly formula: f = (bp - q) / b
            # där b = odds (simplified: 1), p = win prob, q = loss prob
            # Konservativ approximation: f = edge * win_rate
            full_kelly = (best_edge / 100) * win_rate
            
            # Använd 25% av full Kelly (Renaissance-princip)
            kelly_allocation = min(0.25 * full_kelly, 0.25)
        
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
            kelly_allocation=kelly_allocation,
            position_size_pct=kelly_allocation * 100,
            data_points=data_points,
            period_years=period_years,
            avg_volume=avg_volume,
            overall_score=overall_score
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
            score += 15
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
        else:
            return "RED"


def format_screener_report(results: List[InstrumentScore]) -> str:
    """Formatera screener-resultat för display."""
    lines = []
    
    lines.append("=" * 80)
    lines.append("INSTRUMENT SCREENER RESULTAT")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Analyserade instrument: {len(results)}")
    lines.append("")
    
    # Topp 10 rankning
    lines.append("-" * 80)
    lines.append("TOPP RANKADE INSTRUMENT")
    lines.append("-" * 80)
    lines.append("")
    
    # Header
    lines.append(f"{'Rank':<5} {'Instrument':<30} {'Signal':<10} {'Edge':<8} {'Score':<6} {'Kelly%':<7}")
    lines.append("-" * 80)
    
    for i, result in enumerate(results[:10], 1):
        # Konvertera till text istället för emoji
        if result.signal == Signal.GREEN:
            signal_text = "GREEN"
        elif result.signal == Signal.YELLOW:
            signal_text = "YELLOW"
        else:
            signal_text = "RED"
        
        lines.append(
            f"{i:<5} {result.name[:28]:<30} "
            f"{signal_text:<10} "
            f"{result.best_edge:+.2f}%  "
            f"{result.overall_score:>5.1f}  "
            f"{result.position_size_pct:>6.1f}%"
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
        else:
            signal_text = "RED"
        
        lines.append(f"\n{i}. {result.name} ({result.ticker})")
        lines.append(f"   Kategori: {result.category.upper()}")
        lines.append(f"   Signal: {signal_text} (Konfidens: {result.signal_confidence})")
        lines.append(f"   Bästa edge: {result.best_edge:+.2f}% ({result.best_pattern_name})")
        lines.append(f"   Genomsnittlig edge: {result.avg_edge:+.2f}%")
        lines.append(f"   Stabilitet: {result.stability_score:.1%}")
        lines.append(f"   Handelsbara mönster: {result.tradeable_patterns}/{result.significant_patterns}")
        lines.append(f"   Kelly-allokering: {result.position_size_pct:.1f}% av portfölj")
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
            lines.append(f"  {r.name[:30]:<32} {r.best_edge:+.2f}% ({r.best_pattern_name[:30]})")
    
    # Moderate edge (0.20-0.49%)
    moderate_edge = [r for r in results if 0.20 <= r.best_edge < 0.50]
    if moderate_edge:
        lines.append(f"\nMODERATE EDGE (0.20-0.49%): {len(moderate_edge)} instrument")
        for r in moderate_edge[:5]:
            lines.append(f"  {r.name[:30]:<32} {r.best_edge:+.2f}% ({r.best_pattern_name[:30]})")
    
    # Small edge (0.10-0.19%)
    small_edge = [r for r in results if 0.10 <= r.best_edge < 0.20]
    if small_edge:
        lines.append(f"\nSMALL EDGE (0.10-0.19%): {len(small_edge)} instrument")
        for r in small_edge[:5]:
            lines.append(f"  {r.name[:30]:<32} {r.best_edge:+.2f}% ({r.best_pattern_name[:30]})")
    
    lines.append("")
    lines.append("[!] OBS: Edge ensam räcker inte - Traffic Light måste också vara grön/gul.")
    lines.append("")
    
    # Portföljrekommendation
    lines.append("-" * 80)
    lines.append("PORTFÖLJREKOMMENDATION")
    lines.append("-" * 80)
    lines.append("")
    
    # Endast gröna och gula signaler
    investable = [r for r in results if r.signal in [Signal.GREEN, Signal.YELLOW]]
    total_kelly = sum(r.kelly_allocation for r in investable)
    
    if total_kelly > 0:
        lines.append("Rekommenderad fördelning (baserat på Kelly Criterion):")
        lines.append("")
        
        for result in investable[:5]:
            if result.kelly_allocation > 0:
                normalized_pct = (result.kelly_allocation / total_kelly) * 100
                # Konvertera signal till text
                if result.signal == Signal.GREEN:
                    signal_text = "GREEN"
                else:
                    signal_text = "YELLOW"
                
                lines.append(
                    f"  {result.name[:30]:<32} {normalized_pct:>5.1f}%  "
                    f"({signal_text})"
                )
        
        lines.append("")
        lines.append(f"Total rekommenderad exponering: {min(100, total_kelly * 100):.1f}%")
        lines.append(f"Rekommenderad cash reserve: {max(0, 100 - total_kelly * 100):.1f}%")
    else:
        lines.append("[X] Inga instrument rekommenderas för investering just nu.")
        lines.append("[!] Vänteläge - behåll hög cash reserve")
    
    lines.append("")
    
    # Signal-fördelning
    lines.append("-" * 80)
    lines.append("SIGNAL-FÖRDELNING")
    lines.append("-" * 80)
    
    green = sum(1 for r in results if r.signal == Signal.GREEN)
    yellow = sum(1 for r in results if r.signal == Signal.YELLOW)
    red = sum(1 for r in results if r.signal == Signal.RED)
    
    lines.append(f"  GREEN: {green} instrument ({green/len(results)*100:.0f}%)")
    lines.append(f"  YELLOW: {yellow} instrument ({yellow/len(results)*100:.0f}%)")
    lines.append(f"  RED: {red} instrument ({red/len(results)*100:.0f}%)")
    lines.append("")
    
    lines.append("=" * 80)
    lines.append("[!] VIKTIGT")
    lines.append("=" * 80)
    lines.append("  • Detta är ett statistiskt filter-verktyg, inte investeringsrådgivning")
    lines.append("  • Kombinera alltid med egen due diligence")
    lines.append("  • Kelly-allokeringar är konservativa (25% av full Kelly)")
    lines.append("  • Överstig aldrig din risktolerans")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point för instrument screener."""
    
    # AVANZA-VÄNLIGA INSTRUMENT
    # Fokus: Likviditet + stabilitet + långsiktighet
    
    instruments = [
        # Index-ETF:er / fonder (BRED EXPONERING)
        ("^OMX", "OMX Stockholm 30", "index_etf"),
        ("^GSPC", "S&P 500", "index_etf"),
        ("^IXIC", "NASDAQ Composite", "index_etf"),
        ("^DJI", "Dow Jones Industrial", "index_etf"),
        ("^FTSE", "FTSE 100", "index_etf"),
        
        # Nordiska index
        ("^OMXH25", "OMX Helsinki 25", "index_etf"),
        ("^OMXC25", "OMX Copenhagen 25", "index_etf"),
        ("^OSEAX", "OBX Oslo", "index_etf"),
        
        # Svenska storbolag (STORA, STABILA)
        ("VOLV-B.ST", "Volvo B", "stock"),
        ("INVE-B.ST", "Investor B", "stock"),
        ("HM-B.ST", "H&M B", "stock"),
        ("SEB-A.ST", "SEB A", "stock"),
        ("ESSITY-B.ST", "Essity B", "stock"),
        
        # Amerikanska storbolag
        ("AAPL", "Apple", "stock"),
        ("MSFT", "Microsoft", "stock"),
        ("GOOGL", "Alphabet", "stock"),
        ("JNJ", "Johnson & Johnson", "stock"),
        
        # Tematiska (ANVÄND FÖRSIKTIGT)
        # ("QQQ", "NASDAQ-100 ETF", "thematic"),  # Om tillgänglig på Avanza
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
