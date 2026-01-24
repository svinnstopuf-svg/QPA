"""
Quick check of BSX pattern to verify 100% win rate claim.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_fetcher import DataFetcher
from src.analyzer import QuantPatternAnalyzer

def main():
    print("="*80)
    print("CHECKING BSX PATTERN DETAILS")
    print("="*80)
    
    # Fetch BSX data
    fetcher = DataFetcher()
    print("\nFetching BSX data...")
    market_data = fetcher.fetch_stock_data("BSX", period="15y")
    
    if market_data is None:
        print("❌ Failed to fetch BSX data")
        return
    
    market_data.ticker = "BSX"
    
    # Run analyzer
    analyzer = QuantPatternAnalyzer(
        min_occurrences=5,
        min_confidence=0.60,
        forward_periods=21
    )
    
    print("\nAnalyzing patterns...")
    results = analyzer.analyze_market_data(market_data)
    
    # Find the pattern with 100% win rate
    print("\n" + "="*80)
    print("SIGNIFICANT PATTERNS")
    print("="*80)
    
    for pattern in results['significant_patterns']:
        print(f"\n📊 {pattern['description']}")
        print(f"   Sample Size: {pattern['sample_size']}")
        print(f"   Win Rate (63d): {pattern['win_rate_63d']*100:.1f}%")
        print(f"   Mean Return (21d): {pattern['mean_return_21d']*100:+.2f}%")
        print(f"   Mean Return (63d): {pattern['mean_return_63d']*100:+.2f}%")
        print(f"   Expected Value: {pattern['expected_value']*100:+.2f}%")
        print(f"   RRR: 1:{pattern['risk_reward_ratio']:.2f}")
        print(f"   Priority: {pattern['metadata'].get('priority', 'N/A')}")
        
        # Show individual returns if sample size is small
        if pattern['sample_size'] <= 10:
            print(f"\n   ⚠️ SMALL SAMPLE SIZE ({pattern['sample_size']} occurrences)")
            print(f"   This may explain the 100% win rate")


if __name__ == "__main__":
    main()
