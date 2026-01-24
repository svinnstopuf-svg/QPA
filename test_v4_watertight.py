"""
Test V4.0 "Watertight" System

Tests all new filters:
1. Volume confirmation (Low 2 < Low 1, breakout > 1.5x avg)
2. Expected Value (EV > 0)
3. Risk/Reward Ratio (RRR >= 1:3 = 3.0+)
4. Earnings risk (flag if < 10 days)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_fetcher import DataFetcher
from src.analyzer import QuantPatternAnalyzer


def test_watertight_system():
    """Test complete V4.0 system with all filters."""
    
    print("=" * 80)
    print("V4.0 WATERTIGHT SYSTEM TEST")
    print("Testing: Volume + EV + RRR + Earnings")
    print("=" * 80)
    
    # Test on NOLA-B
    ticker = "NOLA-B.ST"
    print(f"\nTicker: {ticker}")
    print("-" * 80)
    
    # Fetch data
    fetcher = DataFetcher()
    market_data = fetcher.fetch_stock_data(ticker, period="15y")
    
    if market_data is None:
        print("ERROR: Could not fetch data")
        return
    
    # Add ticker to market_data for earnings check
    market_data.ticker = ticker
    
    print(f"Hämtade {len(market_data.close_prices)} datapunkter")
    print(f"Period: {market_data.timestamps[0].date()} till {market_data.timestamps[-1].date()}")
    
    # Initialize analyzer with V4.0 filters
    print("\nInitializing QuantPatternAnalyzer with V4.0 filters...")
    analyzer = QuantPatternAnalyzer(
        min_occurrences=10,
        min_confidence=0.60,
        forward_periods=21  # Position trading
    )
    
    # Run analysis
    print("\nRunning analysis with all V4.0 filters active...\n")
    print("-" * 80)
    results = analyzer.analyze_market_data(market_data)
    print("-" * 80)
    
    # Display results
    print(f"\nRESULTS:")
    print(f"Total patterns detected: {results['total_patterns']}")
    print(f"Significant patterns (passed ALL filters): {len(results['significant_patterns'])}")
    
    if len(results['significant_patterns']) > 0:
        print(f"\nPATTERNS THAT PASSED V4.0 FILTERS:")
        print("=" * 80)
        
        for i, pattern in enumerate(results['significant_patterns'][:5], 1):
            print(f"\n{i}. {pattern['description']}")
            print(f"   Priority: {pattern['metadata'].get('priority', 'SECONDARY')}")
            print(f"   Sample size: {pattern['sample_size']}")
            
            # Multi-timeframe returns
            print(f"\n   MULTI-TIMEFRAME RETURNS:")
            print(f"     21-day: {pattern['mean_return_21d']*100:+.2f}% (Win rate: {pattern['win_rate_21d']*100:.1f}%)")
            print(f"     42-day: {pattern['mean_return_42d']*100:+.2f}% (Win rate: {pattern['win_rate_42d']*100:.1f}%)")
            print(f"     63-day: {pattern['mean_return_63d']*100:+.2f}% (Win rate: {pattern['win_rate_63d']*100:.1f}%)")
            
            # Risk management metrics
            print(f"\n   RISK MANAGEMENT (V4.0):")
            print(f"     Expected Value: {pattern['expected_value']*100:+.2f}% {'✓ POSITIVE' if pattern['expected_value'] > 0 else '✗ NEGATIVE'}")
            print(f"     Risk/Reward Ratio: {pattern['risk_reward_ratio']:.2f}:1 {'✓ >= 3.0' if pattern['risk_reward_ratio'] >= 3.0 else '✗ < 3.0'}")
            print(f"     Avg Win: +{pattern['avg_win']*100:.2f}%")
            print(f"     Avg Loss: -{pattern['avg_loss']*100:.2f}%")
            
            # Earnings risk
            print(f"\n   EARNINGS RISK:")
            earnings_risk = pattern.get('earnings_risk', 'UNKNOWN')
            earnings_msg = pattern.get('earnings_message', 'No data')
            if earnings_risk == 'HIGH':
                print(f"     ⚠️ {earnings_risk}: {earnings_msg}")
            elif earnings_risk == 'WARNING':
                print(f"     ⚠️ {earnings_risk}: {earnings_msg}")
            else:
                print(f"     ✓ {earnings_risk}: {earnings_msg}")
            
            # Bayesian edge
            print(f"\n   Bayesian edge: {pattern['bayesian_edge']*100:+.2f}%")
            print(f"   Uncertainty: {pattern['bayesian_uncertainty']}")
    else:
        print("\n⚠️ NO PATTERNS PASSED ALL V4.0 FILTERS")
        print("\nPossible reasons:")
        print("  - Market context not valid (no -15% decline or above EMA200)")
        print("  - Volume confirmation failed (no exhaustion or weak breakout)")
        print("  - Expected Value <= 0 (loses money on average)")
        print("  - Risk/Reward < 3.0 (worse than 1:3 ratio)")
    
    print("\n" + "=" * 80)
    print("V4.0 FILTER SUMMARY:")
    print("=" * 80)
    print("✓ Volume Analysis: Low 2 < Low 1, Breakout > 1.5x avg")
    print("✓ Expected Value: EV = (WR × AvgWin) - (LR × AvgLoss) > 0")
    print("✓ Risk/Reward: RRR = AvgWin / AvgLoss >= 3.0")
    print("✓ Earnings Risk: Flag if < 10 days to earnings")
    print("=" * 80)


if __name__ == "__main__":
    test_watertight_system()
