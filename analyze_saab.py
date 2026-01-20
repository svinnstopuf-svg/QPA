"""
Analyze SAAB-B.ST (Swedish defense company)
"""
from instrument_screener_v22 import InstrumentScreenerV22

def main():
    ticker = "SAAB-B.ST"
    name = "SAAB AB (B-share)"
    category = "stock_swedish"
    
    print(f"\nAnalyzing {name} ({ticker})...")
    print("=" * 80)
    
    # Initialize screener with V2.2 filters enabled
    screener = InstrumentScreenerV22(
        min_data_years=5.0,
        min_avg_volume=50000,
        enable_v22_filters=True
    )
    
    # Screen the single instrument
    results = screener.screen_instruments([(ticker, name, category)])
    
    if not results:
        print("\n❌ Could not analyze SAAB - insufficient data or quality criteria not met")
        return
    
    result = results[0]
    
    # Print detailed analysis
    print("\n" + "=" * 80)
    print("🎯 SAAB AB (B-share) - DETAILED ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 TECHNICAL SCORING:")
    print(f"  Final Score:          {result.final_score:.1f}/100")
    print(f"  Signal:               {result.signal.name}")
    print(f"  Entry Recommendation: {result.entry_recommendation}")
    
    print(f"\n💰 EDGE CALCULATION:")
    print(f"  Best Pattern:         {result.best_pattern_name}")
    print(f"  Raw Edge:             {result.best_edge:.2f}%")
    print(f"  Net Edge (costs):     {result.net_edge_after_costs:.2f}%")
    print(f"  Cost Profitable:      {'YES' if result.cost_profitable else 'NO'}")
    
    print(f"\n📈 POSITION SIZING:")
    print(f"  V-Kelly Position:     {result.v_kelly_position:.2f}%")
    print(f"  Regime Multiplier:    {result.regime_multiplier:.2f}x")
    print(f"  Final Allocation:     {result.final_allocation:.2f}%")
    
    print(f"\n🔍 RISK FILTERS:")
    print(f"  Trend Aligned:        {'YES' if result.trend_aligned else 'NO (Below 200-day MA)'}")
    print(f"  Volatility Regime:    {result.volatility_regime}")
    print(f"  Breakout Confidence:  {result.breakout_confidence}")
    
    print(f"\n🇸🇪 ISK OPTIMIZATION:")
    print(f"  Asset Type:           Swedish stock")
    print(f"  FX Cost:              0.00% (no currency exchange)")
    print(f"  Courtage:             ~0.15-0.25% (MINI/SMALL tier)")
    print(f"  Status:               Priority asset for ISK accounts")
    
    print(f"\n📊 DATA QUALITY:")
    print(f"  Data Points:          {result.data_points}")
    print(f"  Period:               {result.period_years:.1f} years")
    print(f"  Avg Daily Volume:     {result.avg_volume:,.0f}")
    print(f"  Patterns Detected:    {result.total_patterns}")
    print(f"  Significant Patterns: {result.significant_patterns}")
    
    print("\n" + "=" * 80)
    print("🎲 CASINO-STYLE RECOMMENDATION:")
    print("=" * 80)
    
    if result.entry_recommendation == "ENTER":
        print(f"✅ BUY SIGNAL - Position size: {result.final_allocation:.2f}%")
        print(f"   Edge after costs: +{result.net_edge_after_costs:.2f}%")
        print(f"   This is an INVESTABLE opportunity (positive net edge)")
    elif result.entry_recommendation == "WAIT":
        print(f"⏸️  WATCH LIST - Technical setup present but timing not optimal")
        print(f"   Monitor for better entry conditions")
    else:
        print(f"🚫 BLOCK - Do not trade")
        if not result.cost_profitable:
            print(f"   Reason: Costs eat the edge (Net edge: {result.net_edge_after_costs:.2f}%)")
        elif not result.trend_aligned:
            print(f"   Reason: Below 200-day MA (fighting the trend)")
        else:
            print(f"   Reason: Negative technical edge")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
