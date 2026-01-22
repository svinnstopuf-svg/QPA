"""
Test 1-day vs 21-day forward periods to validate Phase 1 changes.
"""
import numpy as np
from src.utils.data_fetcher import DataFetcher
from src import QuantPatternAnalyzer

def test_forward_periods():
    """Compare 1-day vs 21-day forward returns."""
    
    ticker = "NOLA-B.ST"
    
    print("\n" + "="*80)
    print(f"FORWARD PERIODS COMPARISON: {ticker}")
    print("="*80 + "\n")
    
    # Fetch data once
    data_fetcher = DataFetcher()
    market_data = data_fetcher.fetch_stock_data(ticker, period="15y")
    
    if not market_data:
        print("ERROR: Could not fetch data")
        return
    
    print(f"Data: {len(market_data)} days ({len(market_data)/252:.1f} years)")
    print(f"Period: {market_data.timestamps[0].strftime('%Y-%m-%d')} to {market_data.timestamps[-1].strftime('%Y-%m-%d')}")
    print()
    
    # Test 1-day forward (current system)
    print("TEST 1: CURRENT SYSTEM (1-DAY FORWARD)")
    print("-" * 80)
    
    analyzer_1d = QuantPatternAnalyzer(
        min_occurrences=5,
        min_confidence=0.40,
        forward_periods=1
    )
    
    results_1d = analyzer_1d.analyze_market_data(market_data)
    sig_patterns_1d = results_1d.get('significant_patterns', [])
    
    print(f"Significant patterns found: {len(sig_patterns_1d)}")
    
    if sig_patterns_1d:
        for i, pattern in enumerate(sig_patterns_1d[:3], 1):
            print(f"\n{i}. {pattern['description']}")
            print(f"   Sample size: {pattern['sample_size']}")
            print(f"   Mean return (1d): {pattern['mean_return']*100:+.2f}%")
            print(f"   Bayesian edge: {pattern.get('bayesian_edge', 0)*100:+.2f}%")
            print(f"   Win rate: {pattern['win_rate']*100:.1f}%")
    
    print("\n\n")
    
    # Test 21-day forward (position trading)
    print("TEST 2: POSITION TRADING (21-DAY FORWARD)")
    print("-" * 80)
    
    analyzer_21d = QuantPatternAnalyzer(
        min_occurrences=5,
        min_confidence=0.40,
        forward_periods=21
    )
    
    results_21d = analyzer_21d.analyze_market_data(market_data)
    sig_patterns_21d = results_21d.get('significant_patterns', [])
    
    print(f"Significant patterns found: {len(sig_patterns_21d)}")
    
    if sig_patterns_21d:
        for i, pattern in enumerate(sig_patterns_21d[:3], 1):
            print(f"\n{i}. {pattern['description']}")
            print(f"   Sample size: {pattern['sample_size']}")
            print(f"   Mean return (21d): {pattern['mean_return']*100:+.2f}%")
            print(f"   Bayesian edge: {pattern.get('bayesian_edge', 0)*100:+.2f}%")
            print(f"   Win rate: {pattern['win_rate']*100:.1f}%")
    
    # Compare specific pattern across timeframes
    print("\n\n")
    print("COMPARISON: EXTENDED RALLY PATTERN")
    print("-" * 80)
    
    # Find Extended Rally in both
    rally_1d = None
    rally_21d = None
    
    for p in sig_patterns_1d:
        if "Extended Rally" in p['description']:
            rally_1d = p
            break
    
    for p in sig_patterns_21d:
        if "Extended Rally" in p['description']:
            rally_21d = p
            break
    
    if rally_1d and rally_21d:
        print(f"\n1-DAY FORWARD:")
        print(f"  Sample size: {rally_1d['sample_size']}")
        print(f"  Mean return: {rally_1d['mean_return']*100:+.2f}%")
        print(f"  Bayesian edge: {rally_1d.get('bayesian_edge', 0)*100:+.2f}%")
        print(f"  Win rate: {rally_1d['win_rate']*100:.1f}%")
        
        print(f"\n21-DAY FORWARD:")
        print(f"  Sample size: {rally_21d['sample_size']}")
        print(f"  Mean return: {rally_21d['mean_return']*100:+.2f}%")
        print(f"  Bayesian edge: {rally_21d.get('bayesian_edge', 0)*100:+.2f}%")
        print(f"  Win rate: {rally_21d['win_rate']*100:.1f}%")
        
        print(f"\nCHANGE:")
        edge_change = (rally_21d.get('bayesian_edge', 0) - rally_1d.get('bayesian_edge', 0)) * 100
        print(f"  Edge difference: {edge_change:+.2f}% ({'+better' if edge_change > 0 else 'worse'})")
        print(f"  21-day edge is {abs(edge_change / rally_1d.get('bayesian_edge', 0.01)):+.1f}x the 1-day edge")
    else:
        if not rally_1d:
            print("Extended Rally not found in 1-day analysis")
        if not rally_21d:
            print("Extended Rally not found in 21-day analysis")
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("="*80)
    print(f"\n1-day forward: Good for swing trading (1-3 day holds)")
    print(f"21-day forward: Good for position trading (3-6 week holds)")
    print(f"\nFor position trading, we expect:")
    print(f"  - HIGHER absolute returns (longer hold = bigger moves)")
    print(f"  - FEWER patterns (need 21+ days forward data)")
    print(f"  - DIFFERENT patterns (structural bottoms, not momentum)")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_forward_periods()
