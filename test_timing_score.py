"""
Test script for Timing Score module

Validates that timing score correctly identifies reversal signals:
- RSI(2) momentum flips
- Mean reversion distance (3+ std from EMA5)
- Volume exhaustion patterns
- Hammer/Bullish Engulfing candles
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.analysis.timing_score import TimingScoreCalculator, format_timing_summary
import yfinance as yf


def test_timing_score_on_ticker(ticker: str):
    """Test timing score calculation on a real ticker"""
    
    print("="*80)
    print(f"TESTING TIMING SCORE: {ticker}")
    print("="*80)
    
    # Initialize calculator
    calculator = TimingScoreCalculator()
    
    # Fetch recent price data
    print(f"\nFetching price data for {ticker}...")
    ticker_obj = yf.Ticker(ticker)
    hist = ticker_obj.history(period="1mo")
    
    if hist.empty or len(hist) < 20:
        print(f"❌ Insufficient data for {ticker}")
        return
    
    print(f"✅ Fetched {len(hist)} days of data")
    
    # Calculate timing score
    print(f"\nCalculating timing signals...")
    signals = calculator.calculate_timing_score(ticker, hist)
    
    if signals is None:
        print(f"❌ Failed to calculate timing score")
        return
    
    # Display results
    print("\n" + "="*80)
    print(format_timing_summary(signals))
    print("="*80)
    
    # Interpretation
    print("\nINTERPRETATION:")
    if signals.total_score >= 75:
        print("⭐ EXCELLENT - This is a prime candidate for immediate reversal")
        print("   Action: Consider entering position within 1-3 days")
    elif signals.total_score >= 50:
        print("✅ GOOD - Decent probability of near-term bounce")
        print("   Action: Monitor closely, enter on confirmation")
    elif signals.total_score >= 25:
        print("⚠️ WEAK - Setup needs more time to develop")
        print("   Action: Wait for stronger signals before entering")
    else:
        print("❌ POOR - High risk of further decline")
        print("   Action: Avoid or wait for improvement in timing signals")
    
    print("\n" + "="*80)
    print()


def main():
    """Test timing score on multiple tickers"""
    
    print("\n" + "="*80)
    print("TIMING SCORE MODULE - VALIDATION TEST")
    print("="*80)
    print("\nThis test validates the 4 timing signals:")
    print("1. RSI Momentum Flip (RSI(2) < 10 and rising)")
    print("2. Mean Reversion Distance (>3 std from EMA5)")
    print("3. Volume Exhaustion (3-day decline on decreasing volume)")
    print("4. Price Action Signal (Hammer/Bullish Engulfing)")
    print("\n" + "="*80)
    
    # Test on a few tickers - mix of US and Swedish
    test_tickers = [
        "AAPL",      # US large cap
        "CALM",      # From your Top 5
        "KBH",       # From your Top 5
        "VOLV-B.ST", # Swedish large cap
    ]
    
    for ticker in test_tickers:
        try:
            test_timing_score_on_ticker(ticker)
        except Exception as e:
            print(f"\n❌ Error testing {ticker}: {e}\n")
    
    print("="*80)
    print("✅ TIMING SCORE MODULE TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
