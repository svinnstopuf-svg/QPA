"""
ULTRA-DEEP ANALYSIS - Mining & Metals Stocks

Shows COMPLETE analysis process with ALL patterns detected,
full Bayesian statistics, and detailed breakdown.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher
from src.decision import TrafficLightEvaluator, format_traffic_light_report
from src.analysis.signal_aggregator import SignalAggregator


def ultra_deep_analysis(ticker, name):
    """Run ultra-deep analysis showing ALL patterns"""
    
    print("\n" + "=" * 80)
    print(f"🔬 ULTRA-DEEP ANALYSIS: {name} ({ticker})")
    print("=" * 80)
    
    # Fetch data
    print(f"\nHämtar data för {ticker}...")
    fetcher = DataFetcher()
    market_data = fetcher.fetch_stock_data(ticker, period="15y")
    
    if market_data is None:
        print(f"❌ Kunde inte hämta data för {ticker}")
        return
    
    print(f"✅ Hämtade {len(market_data)} dagar data")
    print(f"Period: {market_data.timestamps[0].date()} till {market_data.timestamps[-1].date()}")
    
    # Initialize analyzer with sensitive parameters
    print("\n" + "=" * 80)
    print("INITIERAR MÖNSTERANALYSATOR")
    print("=" * 80)
    analyzer = QuantPatternAnalyzer(
        min_occurrences=5,
        min_confidence=0.40,
        forward_periods=1
    )
    print("Parameters:")
    print(f"  Min occurrences: 5")
    print(f"  Min confidence: 0.40")
    print(f"  Forward periods: 1")
    
    # Analyze
    print("\n" + "=" * 80)
    print("PATTERN DETECTION - FULLSTÄNDIG ANALYS")
    print("=" * 80)
    print("Söker efter alla 15+ tekniska och säsongsmässiga mönster...")
    print()
    
    analysis_results = analyzer.analyze_market_data(market_data)
    
    # Show ALL patterns found
    print("\n" + "=" * 80)
    print("ALLA HITTADE MÖNSTER (ALLA NIVÅER)")
    print("=" * 80)
    
    all_patterns = analysis_results.get('all_patterns', [])
    if all_patterns:
        print(f"\nTotalt {len(all_patterns)} mönster identifierade:\n")
        for i, pattern in enumerate(all_patterns, 1):
            print(f"{i}. {pattern['name']}")
            print(f"   Occurrences: {pattern['occurrences']}")
            print(f"   Win Rate: {pattern['win_rate']:.1%}")
            print(f"   Avg Return: {pattern['avg_return']:+.2%}")
            print(f"   P-value: {pattern.get('p_value', 0):.4f}")
            print(f"   Confidence: {pattern.get('confidence', 0):.1%}")
            print()
    else:
        print("Inga mönster hittade i datan.")
    
    # Show SIGNIFICANT patterns (above threshold)
    print("\n" + "=" * 80)
    print("SIGNIFIKANTA MÖNSTER (Över tröskelvärden)")
    print("=" * 80)
    
    sig_patterns = analysis_results.get('significant_patterns', [])
    if sig_patterns:
        print(f"\n{len(sig_patterns)} mönster klarar signifikanstesten:\n")
        for i, pattern in enumerate(sig_patterns, 1):
            print(f"{i}. {pattern['name']}")
            print(f"   Occurrences: {pattern['occurrences']}")
            print(f"   Win Rate: {pattern['win_rate']:.1%}")
            print(f"   Avg Return: {pattern['avg_return']:+.2%}")
            print(f"   Edge: {pattern.get('edge', 0):+.2%}")
            print(f"   P-value: {pattern.get('p_value', 0):.4f}")
            print(f"   Bayesian Confidence: {pattern.get('bayesian_confidence', 0):.1%}")
            print()
    else:
        print("\nInga signifikanta mönster (ingen edge över tröskelvärden).")
    
    # Summary table
    print("\n" + "=" * 80)
    print("SAMMANFATTNINGSTABELL")
    print("=" * 80)
    summary_table = analyzer.create_summary_table(analysis_results)
    print(summary_table)
    
    # Traffic Light Evaluation
    print("\n" + "=" * 80)
    print("TRAFFIC LIGHT EVALUATION")
    print("=" * 80)
    
    if sig_patterns:
        evaluator = TrafficLightEvaluator()
        
        for pattern in sig_patterns[:3]:  # Top 3
            result = evaluator.evaluate_pattern(pattern)
            print(f"\n{pattern['name']}:")
            print(f"  Signal: {result.signal.name}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Recommendation: {result.recommended_allocation}")
    
    # Current market situation
    print("\n" + "=" * 80)
    print("NUVARANDE MARKNADSSITUATION")
    print("=" * 80)
    
    current_situation = analyzer.get_current_market_situation(market_data, lookback_window=50)
    
    if current_situation['active_situations']:
        print(f"\nAktiva situationer (senaste {current_situation['lookback_window']} dagarna):\n")
        for i, sit in enumerate(current_situation['active_situations'], 1):
            print(f"{i}. {sit['description']}")
            print(f"   Confidence: {sit.get('confidence', 'N/A')}")
            print()
        
        # Aggregate signals
        aggregator = SignalAggregator()
        aggregated = aggregator.aggregate_signals(current_situation['active_situations'])
        
        print("\nAGGREGERAD SIGNAL:")
        print(aggregated.description)
        print(f"Konfidensgrad: {aggregated.confidence.upper()}")
        
        if aggregated.correlation_warning:
            print("\n⚠️ VARNING: Signalkorrelation detekterad")
            print("Dessa signaler är troligen inte oberoende.")
    else:
        print("\nInga speciella situationer identifierade för närvarande.")
    
    # Pattern health monitoring
    if sig_patterns:
        print("\n" + "=" * 80)
        print("PATTERN HEALTH MONITORING")
        print("=" * 80)
        pattern_statuses = analyzer.monitor_patterns(analysis_results)
        monitoring_report = analyzer.generate_monitoring_report(pattern_statuses)
        print(monitoring_report)
    
    # Bayesian uncertainty
    if sig_patterns:
        print("\n" + "=" * 80)
        print("BAYESIAN UNCERTAINTY QUANTIFICATION")
        print("=" * 80)
        bayesian_report = analyzer.show_bayesian_uncertainty(analysis_results)
        print(bayesian_report)
    
    print("\n" + "=" * 80)
    print(f"ANALYS KLAR FÖR {name}")
    print("=" * 80)


if __name__ == "__main__":
    print("🔬" * 40)
    print("     ULTRA-DEEP ANALYSIS - MINING & METALS STOCKS")
    print("     Visar ALLA patterns och fullständig statistik")
    print("🔬" * 40)
    
    stocks = [
        ("ERO.TO", "Ero Copper"),
        ("KNT.TO", "K92 Mining"),
        ("AA", "Alcoa"),
        ("BOL.ST", "Boliden"),
    ]
    
    for ticker, name in stocks:
        try:
            ultra_deep_analysis(ticker, name)
            input("\n[Tryck ENTER för nästa aktie...]")
        except Exception as e:
            print(f"\n❌ Fel vid analys av {ticker}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print("✅ ALLA ANALYSER KLARA")
    print("=" * 80)
