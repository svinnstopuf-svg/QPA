#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTENDED RALLY PARADOX ANALYZER
================================
Question: Why does a pattern called "Extended Rally - Exhaustion Risk" 
have 91.3% win rate and +18.23% edge?

This script investigates whether:
A) It's a data mining artifact (overfitting)
B) Momentum actually works (misnamed pattern)
C) Something else entirely

Author: V4.0 Position Trading System
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def detect_extended_rally(prices, min_streak=7):
    """
    Detect 7+ consecutive up days.
    Returns indices where extended rally is detected.
    """
    returns = np.diff(prices) / prices[:-1]
    
    rally_indices = []
    current_streak = 0
    
    for i in range(len(returns)):
        if returns[i] > 0:
            current_streak += 1
        else:
            current_streak = 0
        
        if current_streak >= min_streak:
            rally_indices.append(i + 1)  # +1 to align with prices index
    
    return rally_indices

def analyze_forward_returns(prices, indices, forward_days=[21, 42, 63]):
    """
    Calculate forward returns after extended rally signals.
    """
    results = {days: [] for days in forward_days}
    
    for idx in indices:
        for days in forward_days:
            if idx + days < len(prices):
                entry_price = prices[idx]
                exit_price = prices[idx + days]
                ret = (exit_price - entry_price) / entry_price * 100
                results[days].append(ret)
    
    return results

def analyze_pattern_context(prices, indices):
    """
    Analyze what happens BEFORE extended rally signals.
    Are they at bottoms, tops, or random?
    """
    contexts = {
        'at_52w_high': 0,
        'at_52w_low': 0,
        'in_uptrend': 0,
        'in_downtrend': 0,
        'neutral': 0
    }
    
    for idx in indices:
        if idx < 252:
            continue
        
        # 52-week high/low check
        lookback_252 = prices[max(0, idx-252):idx+1]
        current_price = prices[idx]
        high_52w = np.max(lookback_252)
        low_52w = np.min(lookback_252)
        
        # At 52-week high? (within 5%)
        if current_price >= high_52w * 0.95:
            contexts['at_52w_high'] += 1
        # At 52-week low? (within 5%)
        elif current_price <= low_52w * 1.05:
            contexts['at_52w_low'] += 1
        else:
            # Check trend (200-day SMA)
            sma_200 = np.mean(prices[idx-200:idx])
            if current_price > sma_200 * 1.05:
                contexts['in_uptrend'] += 1
            elif current_price < sma_200 * 0.95:
                contexts['in_downtrend'] += 1
            else:
                contexts['neutral'] += 1
    
    return contexts

def run_analysis():
    """
    Main analysis on multiple tickers to test Extended Rally hypothesis.
    """
    print("="*80)
    print("EXTENDED RALLY PARADOX ANALYZER")
    print("="*80)
    print("\nQuestion: Why does 'Extended Rally - Exhaustion Risk' have 91.3% win rate?")
    print("\nTesting on historical data...\n")
    
    # Test on a mix of tickers (similar to Sunday Dashboard universe)
    test_tickers = [
        "TREX",  # The actual setup from Sunday Dashboard
        "AAPL", "MSFT", "NVDA",  # Tech (high momentum)
        "WMT", "PG", "CALM",  # Consumer Staples (low momentum)
        "XOM", "CVX",  # Energy (volatile)
        "SPY"  # Broad market
    ]
    
    all_results = []
    
    for ticker in test_tickers:
        try:
            print(f"Analyzing {ticker}...")
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5y")
            
            if hist.empty or len(hist) < 300:
                print(f"  ⚠️  Insufficient data\n")
                continue
            
            prices = hist['Close'].values
            
            # Detect extended rallies
            rally_indices = detect_extended_rally(prices, min_streak=7)
            
            if len(rally_indices) == 0:
                print(f"  No extended rallies detected\n")
                continue
            
            # Analyze forward returns
            forward_rets = analyze_forward_returns(prices, rally_indices)
            
            # Analyze context
            contexts = analyze_pattern_context(prices, rally_indices)
            
            # Calculate statistics
            stats_21d = np.array(forward_rets[21])
            stats_42d = np.array(forward_rets[42])
            stats_63d = np.array(forward_rets[63])
            
            win_rate_21d = np.mean(stats_21d > 0) * 100 if len(stats_21d) > 0 else 0
            win_rate_42d = np.mean(stats_42d > 0) * 100 if len(stats_42d) > 0 else 0
            win_rate_63d = np.mean(stats_63d > 0) * 100 if len(stats_63d) > 0 else 0
            
            avg_ret_21d = np.mean(stats_21d) if len(stats_21d) > 0 else 0
            avg_ret_42d = np.mean(stats_42d) if len(stats_42d) > 0 else 0
            avg_ret_63d = np.mean(stats_63d) if len(stats_63d) > 0 else 0
            
            print(f"  Signals: {len(rally_indices)}")
            print(f"  Win Rate (21d): {win_rate_21d:.1f}%")
            print(f"  Win Rate (42d): {win_rate_42d:.1f}%")
            print(f"  Win Rate (63d): {win_rate_63d:.1f}%")
            print(f"  Avg Return (21d): {avg_ret_21d:+.2f}%")
            print(f"  Avg Return (42d): {avg_ret_42d:+.2f}%")
            print(f"  Avg Return (63d): {avg_ret_63d:+.2f}%")
            print(f"\n  Context:")
            print(f"    At 52-week high: {contexts['at_52w_high']}/{len(rally_indices)} ({contexts['at_52w_high']/len(rally_indices)*100:.1f}%)")
            print(f"    At 52-week low:  {contexts['at_52w_low']}/{len(rally_indices)} ({contexts['at_52w_low']/len(rally_indices)*100:.1f}%)")
            print(f"    In uptrend:      {contexts['in_uptrend']}/{len(rally_indices)} ({contexts['in_uptrend']/len(rally_indices)*100:.1f}%)")
            print(f"    In downtrend:    {contexts['in_downtrend']}/{len(rally_indices)} ({contexts['in_downtrend']/len(rally_indices)*100:.1f}%)")
            print()
            
            all_results.append({
                'ticker': ticker,
                'signals': len(rally_indices),
                'win_rate_21d': win_rate_21d,
                'win_rate_63d': win_rate_63d,
                'avg_ret_21d': avg_ret_21d,
                'avg_ret_63d': avg_ret_63d,
                'pct_at_high': contexts['at_52w_high']/len(rally_indices)*100 if len(rally_indices) > 0 else 0
            })
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}\n")
            continue
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    if len(all_results) == 0:
        print("No results to analyze")
        return
    
    df = pd.DataFrame(all_results)
    
    print(f"\nAggregate Results (n={len(all_results)} tickers):")
    print(f"  Avg Win Rate (21d): {df['win_rate_21d'].mean():.1f}%")
    print(f"  Avg Win Rate (63d): {df['win_rate_63d'].mean():.1f}%")
    print(f"  Avg Return (21d):   {df['avg_ret_21d'].mean():+.2f}%")
    print(f"  Avg Return (63d):   {df['avg_ret_63d'].mean():+.2f}%")
    print(f"  Avg % at 52w high:  {df['pct_at_high'].mean():.1f}%")
    
    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    avg_wr_21d = df['win_rate_21d'].mean()
    avg_wr_63d = df['win_rate_63d'].mean()
    avg_ret_63d = df['avg_ret_63d'].mean()
    pct_at_high = df['pct_at_high'].mean()
    
    if avg_wr_63d > 70 and avg_ret_63d > 5:
        print("\n🟢 MOMENTUM CONTINUATION IS REAL")
        print("   Extended rallies DO tend to continue in the medium term (21-63 days).")
        if pct_at_high > 50:
            print("   Most signals occur near 52-week highs → 'Breakout Continuation' strategy")
        else:
            print("   Signals occur throughout price range → Broad momentum effect")
        print("\n   RECOMMENDATION:")
        print("   - RENAME pattern: 'Momentum Continuation (7+ up days)'")
        print("   - KEEP in system as valid pattern")
        print("   - Adjust description to reflect bullish continuation, not exhaustion")
    
    elif avg_wr_63d < 55 or avg_ret_63d < 2:
        print("\n🔴 EXHAUSTION REVERSAL IS REAL")
        print("   Extended rallies DO tend to reverse (exhaustion effect).")
        print("\n   RECOMMENDATION:")
        print("   - REMOVE pattern from buy signals")
        print("   - Could be used as SHORT signal instead")
        print("   - Does NOT fit mean-reversion strategy")
    
    else:
        print("\n🟡 INCONCLUSIVE / MIXED RESULTS")
        print("   Extended rallies show moderate performance.")
        print("\n   RECOMMENDATION:")
        print("   - Review individual ticker results")
        print("   - May work for some sectors (Tech) but not others (Utilities)")
        print("   - Consider sector-specific filters")
    
    print("\n" + "="*80)
    print("DETAILED RESULTS TABLE")
    print("="*80)
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_analysis()
