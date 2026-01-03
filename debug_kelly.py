"""Debug Kelly-beräkning"""

from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher

df = DataFetcher()

# Test Apple och Microsoft
tickers = [("AAPL", "Apple"), ("MSFT", "Microsoft")]

for ticker, name in tickers:
    print(f"\n{'='*60}")
    print(f"{name} ({ticker})")
    print('='*60)
    
    market_data = df.fetch_stock_data(ticker, period="15y")
    
    analyzer = QuantPatternAnalyzer(
        min_occurrences=5,
        min_confidence=0.40,
        forward_periods=1
    )
    
    results = analyzer.analyze_market_data(market_data)
    significant = results.get('significant_patterns', [])
    
    print(f"Signifikanta mönster: {len(significant)}")
    
    # Hitta bästa edge och win_rate
    best_edge = 0
    best_pattern = None
    
    for p in significant:
        if 'mean_return' in p:
            edge = p['mean_return'] * 100
            if abs(edge) > abs(best_edge):
                best_edge = edge
                best_pattern = p
    
    if best_pattern:
        print(f"\nBästa mönster:")
        print(f"  Beskrivning: {best_pattern.get('description', 'N/A')}")
        print(f"  Edge: {best_edge:.4f}%")
        print(f"  Win rate: {best_pattern.get('win_rate', 'N/A')}")
        print(f"  Sample size: {best_pattern.get('sample_size', 'N/A')}")
        
        # Beräkna Kelly
        win_rate = best_pattern.get('win_rate', 0.5)
        full_kelly = (best_edge / 100) * win_rate
        quarter_kelly = 0.25 * full_kelly
        
        print(f"\nKelly-beräkning:")
        print(f"  Full Kelly: {full_kelly:.6f} = {full_kelly*100:.4f}%")
        print(f"  Quarter Kelly (25%): {quarter_kelly:.6f} = {quarter_kelly*100:.4f}%")
        print(f"  Capped at 0.25 (25%): {min(quarter_kelly, 0.25):.6f} = {min(quarter_kelly, 0.25)*100:.4f}%")
