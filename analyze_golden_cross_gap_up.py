#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOLDEN CROSS & GAP UP PATTERN ANALYZER
=======================================
Empirical test: Do these patterns work for 21-63 day position trading?

Golden Cross:
- 50MA crosses above 200MA
- Traditional trend-following signal
- Question: Does it predict 21-63d returns?

Gap Up:
- Price gaps up >2%
- Momentum/breakout signal
- Question: Does it predict 21-63d returns?

Author: V4.0 Position Trading System
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

def detect_golden_cross(prices):
    """Detect Golden Cross (50MA crosses above 200MA)"""
    ma_50 = np.zeros(len(prices))
    ma_200 = np.zeros(len(prices))
    
    for i in range(50, len(prices)):
        ma_50[i] = np.mean(prices[i-50:i])
    
    for i in range(200, len(prices)):
        ma_200[i] = np.mean(prices[i-200:i])
    
    # Detect crosses
    diff = ma_50 - ma_200
    crosses = []
    
    for i in range(200, len(prices)-1):
        # Cross from below to above
        if diff[i-1] <= 0 and diff[i] > 0:
            crosses.append(i)
    
    return crosses

def detect_gap_up(open_prices, close_prices, threshold=0.02):
    """Detect Gap Up >2%"""
    gaps = []
    
    for i in range(1, len(open_prices)):
        prev_close = close_prices[i-1]
        curr_open = open_prices[i]
        gap = (curr_open - prev_close) / prev_close
        
        if gap > threshold:
            gaps.append(i)
    
    return gaps

def analyze_forward_returns(prices, indices, forward_days=[21, 42, 63]):
    """Calculate forward returns after signals"""
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
    """Analyze context: Are we at tops, bottoms, or random?"""
    contexts = {
        'at_52w_high': 0,
        'at_52w_low': 0,
        'in_uptrend': 0,
        'in_downtrend': 0,
        'neutral': 0,
        'after_decline': 0  # After -10%+ decline
    }
    
    for idx in indices:
        if idx < 252:
            continue
        
        # 52-week high/low check
        lookback_252 = prices[max(0, idx-252):idx+1]
        current_price = prices[idx]
        high_52w = np.max(lookback_252)
        low_52w = np.min(lookback_252)
        
        # Check decline from 90-day high
        lookback_90 = prices[max(0, idx-90):idx+1]
        high_90d = np.max(lookback_90)
        decline_pct = ((current_price - high_90d) / high_90d) * 100
        
        if decline_pct < -10:
            contexts['after_decline'] += 1
        
        # At 52-week high? (within 5%)
        if current_price >= high_52w * 0.95:
            contexts['at_52w_high'] += 1
        # At 52-week low? (within 5%)
        elif current_price <= low_52w * 1.05:
            contexts['at_52w_low'] += 1
        else:
            # Check trend (200-day SMA)
            if idx >= 200:
                sma_200 = np.mean(prices[idx-200:idx])
                if current_price > sma_200 * 1.05:
                    contexts['in_uptrend'] += 1
                elif current_price < sma_200 * 0.95:
                    contexts['in_downtrend'] += 1
                else:
                    contexts['neutral'] += 1
    
    return contexts

def run_analysis():
    """Main analysis"""
    print("="*80)
    print("GOLDEN CROSS & GAP UP PATTERN ANALYZER")
    print("="*80)
    print("\nQuestion: Do these patterns work for 21-63 day position trading?")
    print("Strategy: MEAN REVERSION / BOTTOM FISHING")
    print("\nTesting on historical data...\n")
    
    # Test tickers (diverse set)
    test_tickers = [
        "AAPL", "MSFT", "NVDA",  # Tech
        "WMT", "PG", "CALM",      # Staples
        "JPM", "BAC",             # Financials
        "XOM", "CVX",             # Energy
        "SPY", "QQQ"              # Indices
    ]
    
    gc_results = []
    gap_results = []
    
    for ticker in test_tickers:
        try:
            print(f"Analyzing {ticker}...")
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5y")
            
            if hist.empty or len(hist) < 300:
                print(f"  ⚠️  Insufficient data\n")
                continue
            
            prices = hist['Close'].values
            open_prices = hist['Open'].values
            
            # === GOLDEN CROSS ===
            gc_indices = detect_golden_cross(prices)
            
            if len(gc_indices) > 0:
                gc_forward = analyze_forward_returns(prices, gc_indices)
                gc_context = analyze_pattern_context(prices, gc_indices)
                
                stats_21d = np.array(gc_forward[21])
                stats_63d = np.array(gc_forward[63])
                
                wr_21d = np.mean(stats_21d > 0) * 100 if len(stats_21d) > 0 else 0
                wr_63d = np.mean(stats_63d > 0) * 100 if len(stats_63d) > 0 else 0
                avg_21d = np.mean(stats_21d) if len(stats_21d) > 0 else 0
                avg_63d = np.mean(stats_63d) if len(stats_63d) > 0 else 0
                
                print(f"  Golden Cross: {len(gc_indices)} signals")
                print(f"    Win Rate (21d): {wr_21d:.1f}% | Avg: {avg_21d:+.2f}%")
                print(f"    Win Rate (63d): {wr_63d:.1f}% | Avg: {avg_63d:+.2f}%")
                print(f"    Context: {gc_context['after_decline']}/{len(gc_indices)} after -10%+ decline")
                
                gc_results.append({
                    'ticker': ticker,
                    'signals': len(gc_indices),
                    'win_rate_21d': wr_21d,
                    'win_rate_63d': wr_63d,
                    'avg_ret_21d': avg_21d,
                    'avg_ret_63d': avg_63d,
                    'pct_after_decline': gc_context['after_decline']/len(gc_indices)*100 if len(gc_indices) > 0 else 0
                })
            
            # === GAP UP ===
            gap_indices = detect_gap_up(open_prices, prices)
            
            if len(gap_indices) > 0:
                gap_forward = analyze_forward_returns(prices, gap_indices)
                gap_context = analyze_pattern_context(prices, gap_indices)
                
                stats_21d = np.array(gap_forward[21])
                stats_63d = np.array(gap_forward[63])
                
                wr_21d = np.mean(stats_21d > 0) * 100 if len(stats_21d) > 0 else 0
                wr_63d = np.mean(stats_63d > 0) * 100 if len(stats_63d) > 0 else 0
                avg_21d = np.mean(stats_21d) if len(stats_21d) > 0 else 0
                avg_63d = np.mean(stats_63d) if len(stats_63d) > 0 else 0
                
                print(f"  Gap Up: {len(gap_indices)} signals")
                print(f"    Win Rate (21d): {wr_21d:.1f}% | Avg: {avg_21d:+.2f}%")
                print(f"    Win Rate (63d): {wr_63d:.1f}% | Avg: {avg_63d:+.2f}%")
                print(f"    Context: {gap_context['after_decline']}/{len(gap_indices)} after -10%+ decline")
                
                gap_results.append({
                    'ticker': ticker,
                    'signals': len(gap_indices),
                    'win_rate_21d': wr_21d,
                    'win_rate_63d': wr_63d,
                    'avg_ret_21d': avg_21d,
                    'avg_ret_63d': avg_63d,
                    'pct_after_decline': gap_context['after_decline']/len(gap_indices)*100 if len(gap_indices) > 0 else 0
                })
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}\n")
            continue
    
    # === SUMMARY ===
    print("\n" + "="*80)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    if len(gc_results) > 0:
        df_gc = pd.DataFrame(gc_results)
        print(f"\n📊 GOLDEN CROSS (n={len(gc_results)} tickers, {df_gc['signals'].sum():.0f} total signals):")
        print(f"  Avg Win Rate (21d): {df_gc['win_rate_21d'].mean():.1f}%")
        print(f"  Avg Win Rate (63d): {df_gc['win_rate_63d'].mean():.1f}%")
        print(f"  Avg Return (21d):   {df_gc['avg_ret_21d'].mean():+.2f}%")
        print(f"  Avg Return (63d):   {df_gc['avg_ret_63d'].mean():+.2f}%")
        print(f"  Avg % After Decline: {df_gc['pct_after_decline'].mean():.1f}%")
    
    if len(gap_results) > 0:
        df_gap = pd.DataFrame(gap_results)
        print(f"\n📊 GAP UP (n={len(gap_results)} tickers, {df_gap['signals'].sum():.0f} total signals):")
        print(f"  Avg Win Rate (21d): {df_gap['win_rate_21d'].mean():.1f}%")
        print(f"  Avg Win Rate (63d): {df_gap['win_rate_63d'].mean():.1f}%")
        print(f"  Avg Return (21d):   {df_gap['avg_ret_21d'].mean():+.2f}%")
        print(f"  Avg Return (63d):   {df_gap['avg_ret_63d'].mean():+.2f}%")
        print(f"  Avg % After Decline: {df_gap['pct_after_decline'].mean():.1f}%")
    
    # === VERDICT ===
    print("\n" + "="*80)
    print("🎯 VERDICT & RECOMMENDATION")
    print("="*80)
    
    if len(gc_results) > 0:
        gc_wr = df_gc['win_rate_63d'].mean()
        gc_ret = df_gc['avg_ret_63d'].mean()
        gc_decline = df_gc['pct_after_decline'].mean()
        
        print(f"\n{'='*80}")
        print("GOLDEN CROSS:")
        print("="*80)
        
        if gc_wr > 65 and gc_ret > 3:
            print("✅ KEEP - Shows decent edge for position trading")
            print(f"   Win Rate: {gc_wr:.1f}% | Avg Return: {gc_ret:+.2f}%")
            if gc_decline > 20:
                print(f"   {gc_decline:.1f}% occur after declines → Aligns with strategy!")
                print("\n   RECOMMENDATION: KEEP as SECONDARY pattern")
            else:
                print(f"   Only {gc_decline:.1f}% occur after declines")
                print("\n   RECOMMENDATION: KEEP but DEMOTE to low priority")
        elif gc_wr < 55 or gc_ret < 1:
            print("❌ REMOVE - Poor performance for position trading")
            print(f"   Win Rate: {gc_wr:.1f}% | Avg Return: {gc_ret:+.2f}%")
            print("\n   RECOMMENDATION: REMOVE entirely")
        else:
            print("⚠️  MIXED - Moderate performance")
            print(f"   Win Rate: {gc_wr:.1f}% | Avg Return: {gc_ret:+.2f}%")
            print("\n   RECOMMENDATION: DEMOTE to SECONDARY only")
    
    if len(gap_results) > 0:
        gap_wr = df_gap['win_rate_63d'].mean()
        gap_ret = df_gap['avg_ret_63d'].mean()
        gap_decline = df_gap['pct_after_decline'].mean()
        
        print(f"\n{'='*80}")
        print("GAP UP:")
        print("="*80)
        
        if gap_wr > 65 and gap_ret > 3:
            print("✅ KEEP - Shows decent edge for position trading")
            print(f"   Win Rate: {gap_wr:.1f}% | Avg Return: {gap_ret:+.2f}%")
            if gap_decline > 20:
                print(f"   {gap_decline:.1f}% occur after declines → Aligns with strategy!")
                print("\n   RECOMMENDATION: KEEP as SECONDARY pattern")
            else:
                print(f"   Only {gap_decline:.1f}% occur after declines")
                print("\n   RECOMMENDATION: KEEP but mark as 'momentum continuation' not reversal")
        elif gap_wr < 55 or gap_ret < 1:
            print("❌ REMOVE - Poor performance for position trading")
            print(f"   Win Rate: {gap_wr:.1f}% | Avg Return: {gap_ret:+.2f}%")
            print("\n   RECOMMENDATION: REMOVE entirely")
        else:
            print("⚠️  MIXED - Moderate performance")
            print(f"   Win Rate: {gap_wr:.1f}% | Avg Return: {gap_ret:+.2f}%")
            print("\n   RECOMMENDATION: DEMOTE to SECONDARY only")

if __name__ == "__main__":
    run_analysis()
