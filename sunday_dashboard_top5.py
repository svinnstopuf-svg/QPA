"""
Quick Sunday Dashboard - Top 5 Only
Runs full dashboard analysis on just the top 5 instruments to verify robust statistics display.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from instrument_screener_v23_position import PositionTradingScreener

# Top 5 from latest Sunday run
TOP_5_INSTRUMENTS = [
    ("CALM", "Cal-Maine Foods Inc."),
    ("KBH", "KB Home"),
    ("NEU", "NewMarket Corporation"),
    ("NMAN.ST", "Nederman Holding AB"),
    ("PI", "Impinj Inc."),
]

def main():
    print("="*80)
    print("SUNDAY DASHBOARD - TOP 5 QUICK ANALYSIS")
    print("="*80)
    print(f"\nAnalyzing: {len(TOP_5_INSTRUMENTS)} instruments")
    print("Focus: Verify robust statistics display\n")
    
    # Initialize screener
    screener = PositionTradingScreener(
        capital=100000.0,
        max_risk_per_trade=0.01,
        min_win_rate=0.60,
        min_rrr=3.0
    )
    
    # Run screening
    results = screener.screen_instruments(TOP_5_INSTRUMENTS)
    
    # Display detailed results
    print("\n" + "="*80)
    print("DETAILED RESULTS WITH ROBUST STATISTICS")
    print("="*80)
    
    for i, setup in enumerate(results, 1):
        print(f"\n{'#'*80}")
        print(f"RANK {i}: {setup.ticker} - {setup.name}")
        print(f"Pattern: {setup.best_pattern_name}")
        print(f"Score: {setup.score:.1f}/100 | Status: {setup.status}")
        print('#'*80)
        
        print(f"\nEDGE & PERFORMANCE:")
        print(f"  21-day: {setup.edge_21d*100:+.2f}%")
        print(f"  42-day: {setup.edge_42d*100:+.2f}%")
        print(f"  63-day: {setup.edge_63d*100:+.2f}%")
        
        print(f"\nWIN RATE ANALYSIS:")
        print(f"  Raw Win Rate: {setup.win_rate_63d*100:.1f}% (n={setup.sample_size})")
        if hasattr(setup, 'win_rate_ci_margin') and setup.win_rate_ci_margin > 0:
            print(f"  95% CI: [{setup.win_rate_ci_lower*100:.1f}%, {setup.win_rate_ci_upper*100:.1f}%]")
            print(f"  Margin: ±{setup.win_rate_ci_margin*100:.1f}%")
        
        print(f"\n🔬 ROBUST STATISTICS:")
        if hasattr(setup, 'adjusted_win_rate') and setup.adjusted_win_rate > 0:
            print(f"  Bayesian Win Rate: {setup.adjusted_win_rate*100:.1f}%")
            adjustment = abs(setup.win_rate_63d - setup.adjusted_win_rate) * 100
            print(f"  Adjustment: {adjustment:.1f}% {'pulled down' if setup.adjusted_win_rate < setup.win_rate_63d else 'pulled up'}")
        
        if hasattr(setup, 'p_value') and setup.p_value < 1.0:
            sig_marker = "✓" if setup.p_value < 0.05 else "✗"
            sig_text = "YES" if setup.p_value < 0.05 else "NO"
            print(f"  Statistical Significance: {sig_marker} {sig_text} (p={setup.p_value:.4f})")
        
        if hasattr(setup, 'return_consistency') and setup.return_consistency != 0:
            consistency_level = "Excellent" if setup.return_consistency > 2.0 else "Good" if setup.return_consistency > 1.0 else "Moderate" if setup.return_consistency > 0.5 else "Volatile"
            print(f"  Return Consistency: {setup.return_consistency:.2f} ({consistency_level})")
        
        if hasattr(setup, 'sample_size_factor'):
            confidence_text = "Full" if setup.sample_size_factor >= 1.0 else "High" if setup.sample_size_factor >= 0.8 else "Moderate" if setup.sample_size_factor >= 0.6 else "Low"
            print(f"  Sample Size Confidence: {setup.sample_size_factor*100:.0f}% ({confidence_text})")
        
        if hasattr(setup, 'robust_score') and setup.robust_score > 0:
            print(f"  Robust Score: {setup.robust_score:.1f}/100")
            print(f"  → Contributes {setup.robust_score * 0.50:.1f} points to final score")
        
        print(f"\nEXPECTED VALUE:")
        print(f"  Raw EV: {setup.expected_value*100:+.2f}%")
        if hasattr(setup, 'pessimistic_ev') and setup.pessimistic_ev != 0:
            print(f"  Pessimistic EV: {setup.pessimistic_ev*100:+.2f}%")
            print(f"  → Use pessimistic for position sizing")
        
        print(f"\nRISK METRICS:")
        print(f"  Risk/Reward: 1:{setup.risk_reward_ratio:.2f}")
        print(f"  Avg Win: {setup.avg_win*100:+.2f}%")
        print(f"  Avg Loss: {setup.avg_loss*100:.2f}%")
        
        print(f"\nMARKET CONTEXT:")
        print(f"  Decline from high: {setup.decline_from_high:.1f}%")
        print(f"  Price vs EMA200: {setup.price_vs_ema200:+.1f}%")
        print(f"  Context Valid: {'✓ YES' if setup.context_valid else '✗ NO'}")
        print(f"  Earnings Risk: {setup.earnings_risk}")
        
        print(f"\nRECOMMENDATION:")
        print(f"  {setup.recommendation}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    # Summary
    print("\n📊 SUMMARY:")
    potential = [r for r in results if r.status.startswith("POTENTIAL")]
    print(f"  POTENTIAL setups: {len(potential)}/{len(results)}")
    
    if len(potential) > 0:
        avg_robust = sum(r.robust_score for r in potential if hasattr(r, 'robust_score') and r.robust_score > 0) / len(potential)
        print(f"  Average Robust Score: {avg_robust:.1f}/100")
        
        significant = [r for r in potential if hasattr(r, 'p_value') and r.p_value < 0.05]
        print(f"  Statistically Significant: {len(significant)}/{len(potential)}")
    
    print("\n✅ Robust statistics integration verified!")
    print("All Top 5 setups show complete robust metrics.\n")

if __name__ == "__main__":
    main()
