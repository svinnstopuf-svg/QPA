"""
Test Momentum Dashboard with Small Watchlist

Tests:
1. Basic functionality
2. RS-Rating calculation
3. Quality checks
4. Timing analysis
5. Position sizing
6. Exit strategy
"""

from sunday_dashboard_momentum import SundayDashboardMomentum

# Small test watchlist - mix of potential momentum candidates
TEST_WATCHLIST = [
    # US Tech Leaders (likely high RS)
    "NVDA",   # AI leader
    "MSFT",   # Cloud/AI
    "AAPL",   # Consumer tech
    "GOOGL",  # AI/Cloud
    "META",   # Social/AI
    
    # Growth stocks
    "TSLA",   # EV/Tech
    "AMD",    # Semiconductors
    "AVGO",   # Chips
    
    # Swedish stocks (lower RS expected)
    "ERIC-B.ST",  # Telecom
    "VOLV-B.ST",  # Automotive
    
    # Fallen angels (should NOT qualify - too weak)
    "T",      # Value trap
    "KO",     # Defensive
]

def main():
    print("="*80)
    print("TESTING MOMENTUM DASHBOARD")
    print("="*80)
    print(f"\nTest watchlist: {len(TEST_WATCHLIST)} stocks")
    print("Expected results:")
    print("  - NVDA, MSFT, META: Likely qualify (RS >=95)")
    print("  - TSLA, AMD: Possible (depends on recent performance)")
    print("  - T, KO: Should REJECT (defensive, low RS)")
    print("  - Swedish stocks: Should REJECT (lower RS)")
    print("\n" + "="*80)
    
    # Create dashboard
    dashboard = SundayDashboardMomentum(
        capital=100000.0,
        max_risk_per_trade=0.01,
        min_position_sek=1500.0
    )
    
    # Run analysis on test watchlist
    print("\nRunning momentum analysis...")
    print("(This will take ~2-3 minutes for 12 stocks)\n")
    
    try:
        results = dashboard.run(tickers=TEST_WATCHLIST, max_setups=5)
        
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"\nRaw candidates found: {len(results.get('raw_setups', []))}")
        print(f"After post-processing: {len(results.get('processed_setups', []))}")
        
        processed = results.get('processed_setups', [])
        
        if len(processed) > 0:
            print("\n✅ SUCCESS - Found momentum setups!")
            print("\nTop setups:")
            for i, setup in enumerate(processed[:5], 1):
                print(f"  {i}. {setup.ticker}: RS={setup.rs_rating:.0f}, "
                      f"Score={setup.momentum_score:.0f}, "
                      f"Position={setup.position_size_sek:,.0f} SEK")
        else:
            print("\n⚠️ NO SETUPS FOUND")
            print("Possible reasons:")
            print("  - Market not in momentum regime")
            print("  - Test stocks don't meet RS ≥95 threshold")
            print("  - Timing not confirmed (volume/acceleration)")
        
        # Check what was rejected
        raw = results.get('raw_setups', [])
        if len(raw) > len(processed):
            print(f"\nSetups rejected in post-processing: {len(raw) - len(processed)}")
            print("(Check console output above for rejection reasons)")
        
        print("\n" + "="*80)
        print("Test complete! Check reports/ folder for detailed output.")
        print("="*80)
        
        return results
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()
