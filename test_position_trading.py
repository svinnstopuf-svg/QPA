"""
Test Position Trading System on NOLA-B

Tests:
1. Market Context Filter ("Vattenpasset")
2. Pivot-based Double Bottom detection
3. PRIMARY vs SECONDARY pattern classification
"""
import numpy as np
from src.utils.data_fetcher import DataFetcher
from src.filters.market_context_filter import MarketContextFilter, format_context_report
from src.patterns.position_trading_patterns import PositionTradingPatternDetector

def test_position_trading_nola_b():
    """Test full position trading system on NOLA-B."""
    
    ticker = "NOLA-B.ST"
    
    print("\n" + "="*80)
    print(f"POSITION TRADING SYSTEM TEST: {ticker}")
    print("="*80)
    
    # Fetch data
    data_fetcher = DataFetcher()
    market_data = data_fetcher.fetch_stock_data(ticker, period="15y")
    
    if not market_data:
        print("ERROR: Could not fetch data")
        return
    
    print(f"\nData: {len(market_data)} days")
    print(f"Period: {market_data.timestamps[0].strftime('%Y-%m-%d')} to {market_data.timestamps[-1].strftime('%Y-%m-%d')}")
    
    # STEP 1: Check Market Context (Vattenpasset)
    print("\n" + "="*80)
    print("STEP 1: MARKET CONTEXT CHECK ('VATTENPASSET')")
    print("="*80)
    
    context_filter = MarketContextFilter(
        min_decline_pct=15.0,
        lookback_high=90,
        ema_period=200
    )
    
    context = context_filter.check_market_context(market_data)
    print(format_context_report(context))
    
    if not context.is_valid_for_entry:
        print("\n" + "="*80)
        print("SYSTEM DECISION: NO SETUP")
        print("="*80)
        print("\nSkipping pattern detection - context requirements not met.")
        print("This instrument is NOT in a position trading setup zone.")
        print("\nFor position trading, we need:")
        print("  1. Decline of -15%+ from 90-day high")
        print("  2. Price below EMA 200")
        print("\nCurrent instrument does not meet these criteria.")
        return
    
    # STEP 2: Pattern Detection (only if context is valid)
    print("\n\n" + "="*80)
    print("STEP 2: PRIMARY PATTERN DETECTION")
    print("="*80)
    print("\nContext is VALID - proceeding with structural pattern detection...")
    
    pattern_detector = PositionTradingPatternDetector(
        min_decline_pct=10.0,  # Already validated 15% in context, use 10% here
        lookback_decline=60,
        min_stabilization_days=10
    )
    
    # Detect all position trading patterns
    patterns = pattern_detector.detect_all_position_patterns(market_data)
    
    print(f"\nDetected {len(patterns)} PRIMARY patterns:")
    
    if not patterns:
        print("  No PRIMARY patterns found.")
        print("\n  PRIMARY patterns include:")
        print("    - Double Bottom (W-pattern)")
        print("    - Inverse Head & Shoulders")
        print("    - Bull Flag after Decline")
        print("    - Higher Lows Reversal")
    else:
        for pattern_id, situation in patterns.items():
            print(f"\n  Pattern: {situation.description}")
            print(f"  Type: {situation.metadata.get('pattern', 'unknown')}")
            print(f"  Priority: {situation.metadata.get('priority', 'N/A')}")
            print(f"  Decline before pattern: {situation.metadata.get('decline_pct', 0):.1f}%")
            
            if 'bounce_height' in situation.metadata:
                print(f"  Bounce height: {situation.metadata['bounce_height']:.1f}%")
            
            if 'volume_declining' in situation.metadata:
                print(f"  Volume declining at Low 2: {situation.metadata['volume_declining']}")
            
            if 'triggered' in situation.metadata:
                print(f"  Breakout triggered: {situation.metadata['triggered']}")
                if situation.metadata['triggered']:
                    print(f"  High volume breakout: {situation.metadata.get('high_volume_breakout', False)}")
            
            print(f"  Occurrences: {len(situation.timestamp_indices)}")
    
    # STEP 3: Show current price action
    print("\n\n" + "="*80)
    print("STEP 3: CURRENT PRICE ACTION")
    print("="*80)
    
    prices = market_data.close_prices
    volume = market_data.volume
    
    print(f"\nLast 10 days:")
    for i in range(-10, 0):
        date = market_data.timestamps[i].strftime('%Y-%m-%d')
        price = prices[i]
        vol = volume[i]
        ret = ((prices[i] - prices[i-1]) / prices[i-1] * 100) if i > -len(prices) else 0
        print(f"  {date}: {price:.2f} SEK (Vol: {vol:>10,.0f}, Ret: {ret:>6.2f}%)")
    
    # STEP 4: Final Decision
    print("\n\n" + "="*80)
    print("POSITION TRADING DECISION")
    print("="*80)
    
    print(f"\nContext Valid: {context.is_valid_for_entry}")
    print(f"PRIMARY Patterns Found: {len(patterns)}")
    print(f"Decline from High: {context.decline_from_high:.1f}%")
    print(f"Price vs EMA200: {context.price_vs_ema200:.1f}%")
    
    if context.is_valid_for_entry and len(patterns) > 0:
        print("\n✓ POTENTIAL FOR SUNDAY REVIEW")
        print("\nThis instrument shows:")
        print("  1. Valid position trading context (declined, below EMA200)")
        print("  2. At least one PRIMARY structural reversal pattern")
        print("\nRECOMMENDATION:")
        print("  → Add to Sunday analysis watchlist")
        print("  → Review 21/42/63-day forward returns")
        print("  → Check for SECONDARY timing signals (RSI, volume, etc.)")
        print("  → Prepare position sizing (21-day hold minimum)")
    elif context.is_valid_for_entry:
        print("\n◐ CONTEXT VALID, WAITING FOR PATTERN")
        print("\nThis instrument shows:")
        print("  1. Valid decline and below EMA200")
        print("  2. No PRIMARY pattern yet formed")
        print("\nRECOMMENDATION:")
        print("  → Monitor for structural reversal formation")
        print("  → Wait for Double Bottom, IH&S, or Higher Lows")
    else:
        print("\n✗ NO SETUP")
        print("\nThis instrument is NOT in position trading zone.")
        print("Skip for now - not a structural bottom opportunity.")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_position_trading_nola_b()
