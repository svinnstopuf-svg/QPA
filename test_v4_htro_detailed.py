"""
Detailed V4.0 Analysis: HTRO.ST (H&M)

Full analysis of a valid setup that passes all filters.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_fetcher import DataFetcher
from src.analyzer import QuantPatternAnalyzer


def main():
    ticker = "HTRO.ST"
    
    print("="*80)
    print(f"V4.0 DETAILED ANALYSIS: {ticker} (H&M)")
    print("="*80)
    
    # Fetch data
    print(f"\nFetching data...")
    fetcher = DataFetcher()
    market_data = fetcher.fetch_stock_data(ticker, period="15y")
    
    if market_data is None:
        print("ERROR: Could not fetch data")
        return
    
    market_data.ticker = ticker
    
    # Initialize analyzer
    print("\nInitializing V4.0 analyzer...")
    analyzer = QuantPatternAnalyzer(
        min_occurrences=10,
        min_confidence=0.60,
        forward_periods=21
    )
    
    # Run analysis
    print("\nRunning complete analysis with all V4.0 filters...\n")
    print("-"*80)
    results = analyzer.analyze_market_data(market_data)
    print("-"*80)
    
    # Results
    print(f"\nTOTAL PATTERNS DETECTED: {results['total_patterns']}")
    print(f"PASSED ALL V4.0 FILTERS: {len(results['significant_patterns'])}")
    
    if len(results['significant_patterns']) == 0:
        print("\n❌ No patterns passed filters")
        return
    
    # Detailed breakdown
    print("\n" + "="*80)
    print("PATTERNS THAT PASSED ALL V4.0 FILTERS")
    print("="*80)
    
    for i, pattern in enumerate(results['significant_patterns'], 1):
        print(f"\n{'#'*80}")
        print(f"PATTERN {i}: {pattern['description']}")
        print('#'*80)
        
        # Basic info
        print(f"\nPriority: {pattern['metadata'].get('priority', 'SECONDARY')}")
        print(f"Sample size: {pattern['sample_size']} observations")
        print(f"Statistical strength: {pattern['statistical_strength']:.2f}")
        print(f"Stability score: {pattern['stability_score']:.2f}")
        
        # Multi-timeframe returns
        print(f"\n{'─'*80}")
        print("MULTI-TIMEFRAME FORWARD RETURNS (Position Trading)")
        print('─'*80)
        print(f"\n21-day (1 month):")
        print(f"  Return: {pattern['mean_return_21d']*100:+.2f}%")
        print(f"  Win Rate: {pattern['win_rate_21d']*100:.1f}%")
        
        print(f"\n42-day (2 months):")
        print(f"  Return: {pattern['mean_return_42d']*100:+.2f}%")
        print(f"  Win Rate: {pattern['win_rate_42d']*100:.1f}%")
        
        print(f"\n63-day (3 months):")
        print(f"  Return: {pattern['mean_return_63d']*100:+.2f}%")
        print(f"  Win Rate: {pattern['win_rate_63d']*100:.1f}%")
        
        # Risk management metrics
        print(f"\n{'─'*80}")
        print("RISK MANAGEMENT (V4.0 Filters)")
        print('─'*80)
        
        ev = pattern['expected_value']
        rrr = pattern['risk_reward_ratio']
        avg_win = pattern['avg_win']
        avg_loss = pattern['avg_loss']
        
        print(f"\nExpected Value (EV):")
        print(f"  {ev*100:+.2f}% {'✅ PASS' if ev > 0 else '❌ FAIL'}")
        print(f"  Formula: (Win Rate × Avg Win) - (Loss Rate × Avg Loss)")
        
        print(f"\nRisk/Reward Ratio (RRR):")
        print(f"  {rrr:.2f}:1 {'✅ PASS' if rrr >= 3.0 else '❌ FAIL'}")
        print(f"  Target: >= 3.0 (1:3 minimum)")
        
        print(f"\nWin/Loss Breakdown:")
        print(f"  Average Win: +{avg_win*100:.2f}%")
        print(f"  Average Loss: -{avg_loss*100:.2f}%")
        print(f"  Win Rate: {pattern['win_rate']*100:.1f}%")
        
        # Bayesian adjustment
        print(f"\n{'─'*80}")
        print("BAYESIAN SURVIVORSHIP ADJUSTMENT")
        print('─'*80)
        print(f"\nRaw mean return: {pattern['mean_return']*100:+.2f}%")
        print(f"Bayesian adjusted edge: {pattern['bayesian_edge']*100:+.2f}%")
        print(f"Uncertainty level: {pattern['bayesian_uncertainty']}")
        
        # Earnings risk
        print(f"\n{'─'*80}")
        print("EARNINGS RISK CHECK")
        print('─'*80)
        earnings_risk = pattern.get('earnings_risk', 'UNKNOWN')
        earnings_msg = pattern.get('earnings_message', 'No data')
        days_until = pattern.get('earnings_days_until', None)
        
        if earnings_risk == 'HIGH':
            print(f"\n⚠️ HIGH RISK: {earnings_msg}")
            print(f"   DO NOT TRADE")
        elif earnings_risk == 'WARNING':
            print(f"\n⚠️ WARNING: {earnings_msg}")
            print(f"   Days until earnings: {days_until}")
        else:
            print(f"\n✅ {earnings_risk}: {earnings_msg}")
        
        # Volume (if PRIMARY pattern)
        if pattern['metadata'].get('priority') == 'PRIMARY':
            print(f"\n{'─'*80}")
            print("VOLUME CONFIRMATION (PRIMARY Pattern)")
            print('─'*80)
            
            vol_declining = pattern['metadata'].get('volume_declining', None)
            high_vol_breakout = pattern['metadata'].get('high_volume_breakout', None)
            
            print(f"\nVolume exhaustion (Low 2 < Low 1): {vol_declining}")
            print(f"Breakout volume (> 1.5x avg): {high_vol_breakout}")
            
            if vol_declining and high_vol_breakout:
                print("\n✅ STRONG VOLUME CONFIRMATION")
            elif vol_declining:
                print("\n⚠️ Exhaustion confirmed, waiting for breakout")
            else:
                print("\n❌ No volume confirmation (shouldn't happen)")
    
    # Summary
    print("\n" + "="*80)
    print("V4.0 FILTER SUMMARY")
    print("="*80)
    print("\n✅ All filters passed:")
    print("  1. Market Context: -15%+ decline AND below EMA200")
    print("  2. Volume Analysis: Exhaustion + breakout confirmation")
    print("  3. Expected Value: EV > 0 (profitable on average)")
    print("  4. Risk/Reward: RRR >= 3.0 (minimum 1:3 ratio)")
    print("  5. Earnings Risk: Flagged if < 10 days")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
