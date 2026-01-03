"""Debug: Varför blir edge 0.00% i screenern?"""

from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher

# Test med OMX Stockholm 30
df = DataFetcher()
market_data = df.fetch_stock_data("^OMX", period="15y")

analyzer = QuantPatternAnalyzer(
    min_occurrences=5,
    min_confidence=0.40,
    forward_periods=1
)

print("Analyserar ^OMX...")
analysis_results = analyzer.analyze_market_data(market_data)

print(f"\nSignifikanta mönster: {len(analysis_results['significant_patterns'])}")
print("\nDetaljerad edge-info:")
print("-" * 80)

for i, pattern in enumerate(analysis_results['significant_patterns'][:5], 1):
    print(f"\n{i}. Pattern:")
    print(f"   Pattern type: {type(pattern)}")
    print(f"   Pattern keys: {list(pattern.keys()) if isinstance(pattern, dict) else 'N/A'}")
    
    # Situation
    situation = pattern.get('situation', {})
    print(f"   Situation type: {type(situation)}")
    if hasattr(situation, 'description'):
        print(f"   Beskrivning: {situation.description}")
    
    # Pattern eval
    eval_data = pattern.get('pattern_eval', {})
    print(f"   Eval data type: {type(eval_data)}")
    print(f"   Has outcome_stats key: {'outcome_stats' in eval_data}")
    
    if 'outcome_stats' in eval_data:
        outcome = eval_data['outcome_stats']
        print(f"   Outcome stats type: {type(outcome)}")
        print(f"   Mean return: {outcome.mean_return}")
        print(f"   Mean return * 100: {outcome.mean_return * 100}")
        edge = outcome.mean_return * 100
        print(f"   Edge (calculated): {edge:.4f}%")
    else:
        print("   ❌ SAKNAR outcome_stats!")
        print(f"   Eval_data keys: {list(eval_data.keys()) if isinstance(eval_data, dict) else 'N/A'}")
