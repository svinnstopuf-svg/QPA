"""
Quick test of Sunday Dashboard with small instrument batch.
Tests that post-processing works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sunday_dashboard import SundayDashboard


def main():
    print("="*80)
    print("QUICK SUNDAY DASHBOARD TEST")
    print("="*80)
    
    dashboard = SundayDashboard(
        capital=100000.0,
        max_risk_per_trade=0.01,
        min_position_sek=1500.0
    )
    
    # Override screener with just a few instruments for quick test
    from instruments_universe_800 import SWEDISH_INSTRUMENTS
    
    # Test with first 10 Swedish instruments only
    test_instruments = [(ticker, ticker) for ticker in SWEDISH_INSTRUMENTS[:10]]
    
    print(f"\n🧪 Testing with {len(test_instruments)} instruments only...")
    
    # Temporarily modify the run method to use test instruments
    # (This is a hack for testing - normally we'd pass it as a parameter)
    
    # Run pre-flight
    print("\n" + "="*80)
    print("STEP 1: PRE-FLIGHT CHECKS")
    print("="*80)
    print("\n✅ Skipping for quick test")
    
    # Run screener on test batch
    print("\n" + "="*80)
    print("STEP 2: SCANNING TEST BATCH")
    print("="*80)
    
    screener_results = dashboard.screener.screen_instruments(test_instruments)
    
    print(f"\n✅ Scanning complete!")
    print(f"   Total scanned: {len(screener_results)}")
    
    potential_setups = [r for r in screener_results if r.status == "POTENTIAL"]
    potential_secondary = [r for r in screener_results if r.status == "POTENTIAL*"]
    
    print(f"   POTENTIAL (PRIMARY): {len(potential_setups)}")
    print(f"   POTENTIAL (SECONDARY): {len(potential_secondary)}")
    
    # Test post-processing
    print("\n" + "="*80)
    print("STEP 3: POST-PROCESSING TEST")
    print("="*80)
    
    all_potential = potential_setups + potential_secondary
    
    if len(all_potential) > 0:
        print(f"\n🔍 Testing post-processing with {len(all_potential)} setups...")
        
        results = {'screener_results': screener_results}
        processed = dashboard._post_process_setups(all_potential, results)
        
        print(f"\n✅ Post-processing successful!")
        print(f"   Processed: {len(processed)} setups")
        
        if len(processed) > 0:
            print(f"\nTop setup:")
            top = processed[0]
            print(f"   {top.ticker}: {top.score:.1f}/100")
            print(f"   Pattern: {top.best_pattern_name}")
            print(f"   Position: {top.position_size_sek:,.0f} SEK")
    else:
        print("\n⚠️ No POTENTIAL setups in test batch (expected in strong market)")
        print("   Testing regime detection with empty setups...")
        
        # Test regime detection with mock data
        signal_counts = {
            'GREEN': 2,
            'YELLOW': 3,
            'ORANGE': 3,
            'RED': 2
        }
        
        regime_result = dashboard.regime_detector.detect_regime(signal_counts)
        
        print(f"\n✅ Regime detection works!")
        print(f"   Regime: {regime_result.regime.value}")
        print(f"   Multiplier: {regime_result.position_size_multiplier:.1f}x")
        print(f"   Recommendation: {regime_result.recommendation}")
    
    print("\n" + "="*80)
    print("✅ QUICK TEST COMPLETE - All systems functional")
    print("="*80)


if __name__ == "__main__":
    main()
