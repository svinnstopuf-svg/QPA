"""
Volume Diagnostic Tool

Analyzes why Enhanced Volume Check fails for specific tickers.
Shows detailed volume patterns and price action.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
from src.analysis.timing_score import TimingScoreCalculator


def diagnose_volume(ticker: str):
    """
    Diagnose volume pattern for a ticker
    
    Args:
        ticker: Stock ticker to analyze
    """
    
    print("="*80)
    print(f"VOLUME DIAGNOSTIC: {ticker}")
    print("="*80)
    
    # Fetch data
    print(f"\nFetching price data...")
    ticker_obj = yf.Ticker(ticker)
    hist = ticker_obj.history(period="1mo")
    
    if hist.empty or len(hist) < 6:
        print(f"❌ Insufficient data")
        return
    
    print(f"✅ Fetched {len(hist)} days of data\n")
    
    # Get last 6 days for analysis
    recent = hist.tail(6)
    
    # Current day metrics
    current = recent.iloc[-1]
    previous = recent.iloc[-2]
    
    current_close = current['Close']
    current_open = current['Open']
    current_volume = current['Volume']
    prev_close = previous['Close']
    
    # 5-day average volume (excluding current)
    avg_volume_5d = recent['Volume'].iloc[:-1].mean()
    
    # Calculate metrics
    is_declining = current_close < prev_close
    is_green = current_close > current_open
    volume_ratio = current_volume / avg_volume_5d
    volume_pct_change = (volume_ratio - 1) * 100
    
    print("CURRENT DAY METRICS:")
    print(f"  Close: {current_close:.2f} | Open: {current_open:.2f}")
    print(f"  Previous Close: {prev_close:.2f}")
    print(f"  Price Change: {((current_close / prev_close - 1) * 100):+.2f}%")
    print(f"  Day Type: {'🟢 GREEN' if is_green else '🔴 RED'}")
    
    print(f"\nVOLUME ANALYSIS:")
    print(f"  Current Volume: {current_volume:,.0f}")
    print(f"  5-Day Avg Volume: {avg_volume_5d:,.0f}")
    print(f"  Volume Ratio: {volume_ratio:.2f}x")
    print(f"  Volume Change: {volume_pct_change:+.1f}%")
    
    print(f"\nENHANCED VOLUME CHECK:")
    print(f"  Scenario A - Seller Exhaustion:")
    print(f"    Price Declining? {is_declining}")
    print(f"    Volume -15% below avg? {volume_ratio < 0.85} (need <0.85, got {volume_ratio:.2f})")
    scenario_a = is_declining and volume_ratio < 0.85
    print(f"    ✅ PASS" if scenario_a else f"    ❌ FAIL")
    
    print(f"\n  Scenario B - Buyer Entry:")
    print(f"    Green Day? {is_green}")
    print(f"    Volume +10% above avg? {volume_ratio > 1.10} (need >1.10, got {volume_ratio:.2f})")
    scenario_b = is_green and volume_ratio > 1.10
    print(f"    ✅ PASS" if scenario_b else f"    ❌ FAIL")
    
    confirmed = scenario_a or scenario_b
    print(f"\n  FINAL RESULT: {'✅ CONFIRMED' if confirmed else '❌ NOT CONFIRMED'}")
    
    if not confirmed:
        print(f"\n⚠️ WHY IT FAILED:")
        if is_declining and not (volume_ratio < 0.85):
            print(f"  • Declining price BUT volume not low enough (need -15%, got {volume_pct_change:+.1f}%)")
            print(f"  • Interpretation: Sellers still active, not exhausted yet")
        elif is_green and not (volume_ratio > 1.10):
            print(f"  • Green day BUT volume not high enough (need +10%, got {volume_pct_change:+.1f}%)")
            print(f"  • Interpretation: Weak buying interest, not enough conviction")
        else:
            print(f"  • Red day with normal/high volume = Active selling (bad for reversal)")
            print(f"  • Need to wait for either:")
            print(f"    1. Price continues down on drying volume (seller exhaustion)")
            print(f"    2. Green reversal day with volume spike (buyers stepping in)")
    
    # Show last 5 days volume pattern
    print(f"\n" + "-"*80)
    print("LAST 5 DAYS VOLUME PATTERN:")
    print("-"*80)
    print(f"{'Date':<12} {'Close':>10} {'Change':>8} {'Volume':>12} {'vs Avg':>8}")
    print("-"*80)
    
    for i in range(-5, 0):
        day = recent.iloc[i]
        date = day.name.strftime('%Y-%m-%d')
        close = day['Close']
        if i > -5:
            prev_day = recent.iloc[i-1]
            change = ((close / prev_day['Close']) - 1) * 100
        else:
            change = 0
        volume = day['Volume']
        vs_avg = ((volume / avg_volume_5d) - 1) * 100
        
        print(f"{date:<12} {close:>10.2f} {change:>7.1f}% {volume:>12,.0f} {vs_avg:>7.1f}%")
    
    print("="*80)
    print()


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("\nUsage: python diagnose_volume_issue.py TICKER [TICKER2 ...]")
        print("\nExample:")
        print("  python diagnose_volume_issue.py KBH LEVI SAP.DE")
        print()
        return
    
    tickers = sys.argv[1:]
    
    for ticker in tickers:
        try:
            diagnose_volume(ticker)
        except Exception as e:
            print(f"\n❌ Error analyzing {ticker}: {e}\n")


if __name__ == "__main__":
    main()
