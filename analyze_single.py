"""
Quick Single Ticker Analysis
"""
import sys
from instrument_screener_v22 import InstrumentScreenerV22

def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BOL.ST"
    name = sys.argv[2] if len(sys.argv) > 2 else "Boliden"
    category = "Swedish"
    
    print(f"\n{'='*80}")
    print(f"ANALYZING: {name} ({ticker})")
    print(f"{'='*80}\n")
    
    screener = InstrumentScreenerV22(enable_v22_filters=True)
    result = screener._analyze_instrument_v22(ticker, name, category)
    
    if result:
        print(f"\n✅ ANALYSIS COMPLETE\n")
        print(f"Signal: {result.signal.name}")
        print(f"Final Score: {result.final_score:.1f}/100")
        print(f"Technical Edge: {result.best_edge:+.2f}%")
        print(f"Net Edge (after costs): {result.net_edge_after_costs:+.2f}%")
        print(f"Position Size: {result.final_allocation:.2f}%")
        print(f"Entry Recommendation: {result.entry_recommendation}")
        print(f"")
        print(f"V-Kelly Position: {result.v_kelly_position:.2f}%")
        print(f"Trend Aligned: {'✅' if result.trend_aligned else '❌'}")
        print(f"Volatility Regime: {result.volatility_regime}")
        print(f"Breakout Confidence: {result.breakout_confidence}")
        print(f"Cost Profitable: {'✅' if result.cost_profitable else '❌'}")
        print(f"")
        print(f"RVOL: {result.rvol:.2f}")
        print(f"RVOL Conviction: {result.rvol_conviction}")
        print(f"")
        print(f"Data Points: {result.data_points}")
        print(f"Period: {result.period_years:.1f} years")
        print(f"Avg Volume: {result.avg_volume:,.0f}")
        print(f"")
        print(f"Best Pattern: {result.best_pattern_name}")
        print(f"Significant Patterns: {result.significant_patterns}")
    else:
        print(f"\n❌ Analysis failed - criteria not met\n")

if __name__ == "__main__":
    main()
