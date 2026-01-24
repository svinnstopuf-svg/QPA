"""
Find Valid V4.0 Setups

Scans multiple instruments to find one that meets all criteria:
1. Market context valid (-15%+ decline AND below EMA200)
2. Volume confirmation (exhaustion + breakout)
3. EV > 0
4. RRR >= 3.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_fetcher import DataFetcher
from src.analyzer import QuantPatternAnalyzer


# Swedish small/mid caps that historically have had volatility
TEST_TICKERS = [
    "SINCH.ST",      # Sinch (tech, volatile)
    "ERIC-B.ST",     # Ericsson B
    "SBB-B.ST",      # Samhällsbyggnadsbolaget (real estate, declined 2023)
    "MYCR.ST",       # Mycronic
    "SECT.ST",       # Sectra
    "ESSITY-B.ST",   # Essity B
    "HUSQ-B.ST",     # Husqvarna B
    "ELECTA-B.ST",   # Electa
    "HTRO.ST",       # H&M
    "KINV-B.ST",     # Kinnevik B
]


def test_ticker(ticker: str, analyzer: QuantPatternAnalyzer, fetcher: DataFetcher):
    """Test if ticker meets V4.0 criteria."""
    print(f"\n{'='*80}")
    print(f"Testing: {ticker}")
    print('='*80)
    
    try:
        # Fetch data
        market_data = fetcher.fetch_stock_data(ticker, period="15y")
        
        if market_data is None:
            print(f"❌ Could not fetch data for {ticker}")
            return None
        
        # Add ticker for earnings check
        market_data.ticker = ticker
        
        # Run analysis
        print("\nRunning V4.0 analysis...")
        results = analyzer.analyze_market_data(market_data)
        
        # Check results
        total_patterns = results['total_patterns']
        significant_patterns = len(results['significant_patterns'])
        
        print(f"\nResults:")
        print(f"  Total patterns: {total_patterns}")
        print(f"  Passed all filters: {significant_patterns}")
        
        if significant_patterns > 0:
            print(f"\n✅ FOUND VALID SETUP: {ticker}")
            return results
        else:
            print(f"❌ No valid setups")
            return None
            
    except Exception as e:
        print(f"❌ Error testing {ticker}: {e}")
        return None


def main():
    print("="*80)
    print("V4.0 SETUP SCANNER")
    print("Searching for instruments that meet ALL criteria...")
    print("="*80)
    
    # Initialize
    fetcher = DataFetcher()
    analyzer = QuantPatternAnalyzer(
        min_occurrences=10,
        min_confidence=0.60,
        forward_periods=21
    )
    
    valid_setups = []
    
    # Scan tickers
    for ticker in TEST_TICKERS:
        result = test_ticker(ticker, analyzer, fetcher)
        if result is not None:
            valid_setups.append((ticker, result))
    
    # Summary
    print("\n" + "="*80)
    print("SCAN COMPLETE")
    print("="*80)
    print(f"\nScanned: {len(TEST_TICKERS)} instruments")
    print(f"Valid setups found: {len(valid_setups)}")
    
    if len(valid_setups) > 0:
        print("\n" + "="*80)
        print("DETAILED ANALYSIS OF VALID SETUPS")
        print("="*80)
        
        for ticker, results in valid_setups:
            print(f"\n{'#'*80}")
            print(f"TICKER: {ticker}")
            print('#'*80)
            
            for i, pattern in enumerate(results['significant_patterns'][:3], 1):
                print(f"\n{i}. {pattern['description']}")
                print(f"   Priority: {pattern['metadata'].get('priority', 'SECONDARY')}")
                print(f"   Sample size: {pattern['sample_size']}")
                
                # Multi-timeframe
                print(f"\n   MULTI-TIMEFRAME RETURNS:")
                print(f"     21-day: {pattern['mean_return_21d']*100:+.2f}% (WR: {pattern['win_rate_21d']*100:.1f}%)")
                print(f"     42-day: {pattern['mean_return_42d']*100:+.2f}% (WR: {pattern['win_rate_42d']*100:.1f}%)")
                print(f"     63-day: {pattern['mean_return_63d']*100:+.2f}% (WR: {pattern['win_rate_63d']*100:.1f}%)")
                
                # Risk metrics
                print(f"\n   RISK MANAGEMENT:")
                print(f"     Expected Value: {pattern['expected_value']*100:+.2f}% ✓")
                print(f"     Risk/Reward: {pattern['risk_reward_ratio']:.2f}:1 ✓")
                print(f"     Avg Win: +{pattern['avg_win']*100:.2f}%")
                print(f"     Avg Loss: -{pattern['avg_loss']*100:.2f}%")
                
                # Earnings
                earnings_risk = pattern.get('earnings_risk', 'UNKNOWN')
                earnings_msg = pattern.get('earnings_message', 'No data')
                print(f"\n   EARNINGS: {earnings_risk} - {earnings_msg}")
                
                # Bayesian
                print(f"\n   Bayesian edge: {pattern['bayesian_edge']*100:+.2f}%")
                print(f"   Uncertainty: {pattern['bayesian_uncertainty']}")
                
                # Volume (if PRIMARY pattern)
                if pattern['metadata'].get('priority') == 'PRIMARY':
                    print(f"\n   VOLUME CONFIRMATION:")
                    print(f"     Volume declining: {pattern['metadata'].get('volume_declining', 'N/A')}")
                    print(f"     High volume breakout: {pattern['metadata'].get('high_volume_breakout', 'N/A')}")
    else:
        print("\n❌ No instruments met ALL V4.0 criteria in this scan")
        print("\nTry:")
        print("  1. Scan during market corrections (more -15% declines)")
        print("  2. Add more volatile small/mid caps to TEST_TICKERS")
        print("  3. Lower context filter threshold temporarily for testing")


if __name__ == "__main__":
    main()
