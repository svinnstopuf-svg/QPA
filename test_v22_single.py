"""
Test V2.2 Screener på ett enskilt instrument först
"""

from instrument_screener_v22 import InstrumentScreenerV22, format_v22_report

def test_single_instrument():
    """Test på ett enskilt instrument."""
    
    print("Testing V2.2 Screener på AAPL...\n")
    
    # Initialize screener
    screener = InstrumentScreenerV22(
        min_data_years=5.0,
        min_avg_volume=50000,
        enable_v22_filters=True
    )
    
    # Test på AAPL
    test_instruments = [
        ("AAPL", "Apple Inc", "stock_us_tech")
    ]
    
    try:
        results = screener.screen_instruments(test_instruments)
        
        if results:
            print("\n✅ SUCCESS! Result:")
            print(f"  Ticker: {results[0].ticker}")
            print(f"  Signal: {results[0].signal.name}")
            print(f"  Best Edge: {results[0].best_edge:.2f}%")
            print(f"  Net Edge (after costs): {results[0].net_edge_after_costs:.2f}%")
            print(f"  V-Kelly Position: {results[0].v_kelly_position:.2f}%")
            print(f"  Trend Aligned: {results[0].trend_aligned}")
            print(f"  Breakout Confidence: {results[0].breakout_confidence}")
            print(f"  Volatility Regime: {results[0].volatility_regime}")
            print(f"  Cost Profitable: {results[0].cost_profitable}")
            print(f"  Final Allocation: {results[0].final_allocation:.2f}%")
            print(f"  Entry Recommendation: {results[0].entry_recommendation}")
            print(f"  Final Score: {results[0].final_score:.1f}/100")
            print("\n✅ All checks passed! Ready to run full analysis.")
        else:
            print("\n⚠️ No results returned")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_instrument()
