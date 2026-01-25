"""
Quick test to verify robust statistics are displayed correctly.
"""

from instrument_screener_v23_position import PositionTradingScreener

# Test with a few instruments
test_instruments = [
    ("CALM", "Cal-Maine Foods Inc."),
    ("KBH", "KB Home"),
]

screener = PositionTradingScreener(
    capital=100000.0,
    max_risk_per_trade=0.01,
    min_win_rate=0.60,
    min_rrr=3.0
)

results = screener.screen_instruments(test_instruments)

# Display results
print("\n" + "="*80)
print("ROBUST STATISTICS VERIFICATION")
print("="*80)

for i, result in enumerate(results, 1):
    print(f"\n[{i}] {result.name} ({result.ticker})")
    print(f"Status: {result.status}")
    print(f"Score: {result.score:.1f}/100")
    print(f"Sample Size: {result.sample_size}")
    
    print(f"\nRaw Metrics:")
    print(f"  Win Rate: {result.win_rate_63d*100:.1f}%")
    print(f"  Expected Value: {result.expected_value*100:+.2f}%")
    
    print(f"\nRobust Statistics:")
    print(f"  Adjusted WR: {result.adjusted_win_rate*100:.1f}%")
    print(f"  P-value: {result.p_value:.4f}")
    sig = "✓ YES" if result.p_value < 0.05 else "✗ NO"
    print(f"  Significant: {sig}")
    print(f"  Consistency: {result.return_consistency:.2f}")
    print(f"  Sample Factor: {result.sample_size_factor:.2f} ({result.sample_size_factor*100:.0f}%)")
    print(f"  Pessimistic EV: {result.pessimistic_ev*100:+.2f}%")
    print(f"  Robust Score: {result.robust_score:.1f}/100")
    
    print(f"\nConfidence Interval:")
    print(f"  95% CI: [{result.win_rate_ci_lower*100:.1f}%, {result.win_rate_ci_upper*100:.1f}%]")
    print(f"  Margin: ±{result.win_rate_ci_margin*100:.1f}%")

print("\n" + "="*80)
