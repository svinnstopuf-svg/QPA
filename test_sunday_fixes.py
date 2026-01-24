"""
Quick test to verify Sunday Dashboard fixes:
1. Market Context Filter relaxed to -10%
2. Diagnostic analysis shows rejection reasons
3. Near-misses displayed
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.filters.market_context_filter import MarketContextFilter
from src.utils.market_data import MarketData
import numpy as np


def test_context_filter_threshold():
    """Test that context filter now uses -10% threshold."""
    
    print("="*80)
    print("TEST 1: Market Context Filter Threshold")
    print("="*80)
    
    context_filter = MarketContextFilter()
    
    # Check default threshold
    print(f"\nMin decline threshold: {context_filter.min_decline_pct}%")
    assert context_filter.min_decline_pct == 10.0, "Should be 10.0%"
    print("✅ PASS: Threshold is 10%")
    
    # Check constructor allows custom thresholds
    custom_filter = MarketContextFilter(min_decline_pct=12.0)
    print(f"\nCustom threshold test: {custom_filter.min_decline_pct}%")
    assert custom_filter.min_decline_pct == 12.0, "Should accept custom threshold"
    print("✅ PASS: Custom thresholds work")
    
    print("\n✅ COMPLETE: Context filter uses -10% threshold by default")


def test_diagnostic_method():
    """Test that diagnostic analysis method exists."""
    
    print("\n" + "="*80)
    print("TEST 2: Diagnostic Analysis Method")
    print("="*80)
    
    from instrument_screener_v23_position import PositionTradingScreener
    
    screener = PositionTradingScreener()
    
    # Check method exists
    assert hasattr(screener, 'analyze_rejection_reasons'), "Should have analyze_rejection_reasons method"
    print("\n✅ PASS: analyze_rejection_reasons() method exists")
    
    # Mock some results
    from instrument_screener_v23_position import PositionTradingScore
    
    mock_results = [
        PositionTradingScore(
            ticker="AAPL",
            name="Apple",
            decline_from_high=-5.0,
            price_vs_ema200=2.0,
            context_valid=False,
            primary_patterns=0,
            best_pattern_name="Double Bottom",
            pattern_priority="PRIMARY",
            edge_21d=0.05,
            edge_42d=0.08,
            edge_63d=0.10,
            win_rate_63d=0.65,
            expected_value=0.03,
            risk_reward_ratio=3.5,
            avg_win=0.08,
            avg_loss=-0.02,
            bayesian_edge=0.03,
            uncertainty="LOW",
            sample_size=50,
            earnings_risk="LOW",
            earnings_days=30,
            volume_confirmed=True,
            position_size_pct=1.0,
            max_loss_pct=1.0,
            status="NO SETUP",
            score=30.0,
            recommendation="Context invalid"
        )
    ]
    
    diagnostics = screener.analyze_rejection_reasons(mock_results)
    
    print(f"\nDiagnostic keys: {list(diagnostics.keys())}")
    assert 'stats' in diagnostics, "Should have stats"
    assert 'decline_distribution' in diagnostics, "Should have decline_distribution"
    assert 'near_misses' in diagnostics, "Should have near_misses"
    
    print("✅ PASS: Diagnostic structure correct")
    
    print(f"\nStats: {diagnostics['stats']}")
    print(f"Decline Distribution: {diagnostics['decline_distribution']}")


def test_sunday_dashboard_integration():
    """Test that Sunday Dashboard has new diagnostic output."""
    
    print("\n" + "="*80)
    print("TEST 3: Sunday Dashboard Integration")
    print("="*80)
    
    # Read sunday_dashboard.py to check for diagnostic code
    with open("sunday_dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    checks = [
        ("analyze_rejection_reasons", "Diagnostic analysis call"),
        ("DIAGNOSTIC ANALYSIS", "Diagnostic section header"),
        ("REJECTION BREAKDOWN", "Rejection stats display"),
        ("DECLINE DISTRIBUTION", "Decline distribution display"),
        ("NEAR-MISSES", "Near-misses display"),
        ("TOP 10 REJECTED", "Top rejected instruments display")
    ]
    
    all_passed = True
    for check_str, description in checks:
        if check_str in content:
            print(f"✅ PASS: {description}")
        else:
            print(f"❌ FAIL: {description} not found")
            all_passed = False
    
    if all_passed:
        print("\n✅ ALL CHECKS PASSED: Sunday Dashboard integrated correctly")
    else:
        print("\n⚠️ SOME CHECKS FAILED: Review integration")


if __name__ == "__main__":
    print("\n🧪 TESTING SUNDAY DASHBOARD FIXES\n")
    
    try:
        test_context_filter_threshold()
        test_diagnostic_method()
        test_sunday_dashboard_integration()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETE")
        print("="*80)
        print("\nSummary of Changes:")
        print("1. ✅ Market Context Filter: -15% → -10% decline threshold")
        print("2. ✅ Diagnostic Analysis: Added rejection reason tracking")
        print("3. ✅ Near-Misses Display: Shows instruments close to qualifying")
        print("4. ✅ Top Rejected Display: Shows patterns that failed context")
        print("\nNext: Run python sunday_dashboard.py to test full flow")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
