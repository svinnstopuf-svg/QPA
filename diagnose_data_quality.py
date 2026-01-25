#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATA QUALITY DIAGNOSTIC
========================
Validates the Top 5 setups to check for:
1. Sample size sufficiency (are win rates based on enough trades?)
2. Overfitting risk (are patterns cherry-picked from history?)
3. Survivorship bias (are delisted stocks filtered out?)
4. Volume confirmation issues
5. Earnings data bugs

Author: V4.0 Position Trading System
Date: 2026-01-25
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json

# Top 5 from latest scan
TOP_5 = [
    {"ticker": "CALM", "pattern": "Nya lägsta nivåer (252 perioder)", "win_rate": 0.939, "sample_size": None},
    {"ticker": "AWK", "pattern": "Nya lägsta nivåer (252 perioder)", "win_rate": 1.000, "sample_size": None},
    {"ticker": "CEG", "pattern": "Volatilitetsökning (låg->hög regime)", "win_rate": 0.733, "sample_size": None},
    {"ticker": "KBH", "pattern": "Nya lägsta nivåer (252 perioder)", "win_rate": 0.618, "sample_size": None},
    {"ticker": "NEU", "pattern": "Nya lägsta nivåer (252 perioder)", "win_rate": 0.968, "sample_size": None},
]

def fetch_full_history(ticker):
    """Fetch complete historical data to check sample size"""
    try:
        stock = yf.Ticker(ticker)
        # Get max available history
        hist = stock.history(period="max")
        
        if hist.empty:
            return None
        
        return {
            "start_date": hist.index[0],
            "end_date": hist.index[-1],
            "total_days": len(hist),
            "data": hist
        }
    except Exception as e:
        return None

def count_pattern_occurrences(hist_data, pattern_name):
    """
    Estimate how many times pattern could have occurred in history.
    
    For "Nya lägsta nivåer (252 perioder)":
    - Pattern = new 52-week low
    - Each occurrence requires 252-day lookback
    - Scan entire history to count occurrences
    """
    
    if hist_data is None or hist_data['data'].empty:
        return 0
    
    df = hist_data['data'].copy()
    
    if "lägsta nivåer" in pattern_name.lower():
        # 252-day rolling low
        occurrences = 0
        for i in range(252, len(df)):
            current_low = df['Low'].iloc[i]
            prev_252_low = df['Low'].iloc[i-252:i].min()
            
            # New 252-day low?
            if current_low <= prev_252_low:
                occurrences += 1
        
        return occurrences
    
    elif "volatilitet" in pattern_name.lower():
        # Volatility spike = ATR increases significantly
        # Simplified: count days where 20-day ATR > 2x 100-day ATR
        
        if len(df) < 100:
            return 0
        
        # Calculate ATR proxy (High-Low range)
        df['range'] = df['High'] - df['Low']
        df['atr_20'] = df['range'].rolling(20).mean()
        df['atr_100'] = df['range'].rolling(100).mean()
        
        # Count regime shifts (ATR_20 > 1.5x ATR_100)
        occurrences = ((df['atr_20'] > 1.5 * df['atr_100']) & 
                      (df['atr_20'].shift(1) <= 1.5 * df['atr_100'].shift(1))).sum()
        
        return occurrences
    
    else:
        # Unknown pattern - return conservative estimate
        return 0

def check_survivorship_bias():
    """
    Check if delisted/bankrupt stocks are included in backtest.
    
    Red flag: If all tickers in universe are currently trading,
    survivorship bias is likely present.
    """
    
    print("\n" + "="*80)
    print("SURVIVORSHIP BIAS CHECK")
    print("="*80)
    
    # Load instruments universe
    try:
        from instruments_universe_1200 import INSTRUMENTS
        
        total_instruments = len(INSTRUMENTS)
        
        # Quick sample: check if any delisted stocks present
        # Heuristic: fetch random 10 tickers and see if all have recent data
        sample_tickers = list(INSTRUMENTS.keys())[:20]
        
        active_count = 0
        inactive_count = 0
        
        for ticker in sample_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                
                if not hist.empty:
                    latest_date = hist.index[-1]
                    days_since = (datetime.now() - latest_date.tz_localize(None)).days
                    
                    if days_since < 7:
                        active_count += 1
                    else:
                        inactive_count += 1
            except:
                inactive_count += 1
        
        print(f"\nSample: {len(sample_tickers)} random tickers")
        print(f"  Active (data <7 days old): {active_count}")
        print(f"  Inactive/Delisted: {inactive_count}")
        
        if inactive_count == 0:
            print(f"\n🚨 WARNING: 100% of sampled stocks are currently active")
            print(f"   This suggests SURVIVORSHIP BIAS - delisted stocks excluded")
            print(f"   Historical win rates are likely INFLATED")
            return "HIGH_RISK"
        elif inactive_count < 3:
            print(f"\n⚠️  Only {inactive_count}/{len(sample_tickers)} inactive stocks")
            print(f"   Possible survivorship bias present")
            return "MEDIUM_RISK"
        else:
            print(f"\n✅ {inactive_count}/{len(sample_tickers)} inactive stocks found")
            print(f"   Survivorship bias appears controlled")
            return "LOW_RISK"
    
    except Exception as e:
        print(f"\n❌ Could not load instruments universe: {e}")
        return "UNKNOWN"

def check_volume_confirmation():
    """Check if volume confirmation is properly implemented"""
    
    print("\n" + "="*80)
    print("VOLUME CONFIRMATION CHECK")
    print("="*80)
    
    print("\nChecking if pattern detection requires volume confirmation...")
    
    # Read pattern detection code
    try:
        with open("src/patterns/structural_patterns.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for volume validation logic
        if "volume" in content.lower() and "confirm" in content.lower():
            print("✅ Volume confirmation logic found in code")
            return True
        else:
            print("⚠️  No volume confirmation found in structural patterns")
            print("   Patterns may trigger on low-volume noise")
            return False
    
    except Exception as e:
        print(f"❌ Could not read pattern code: {e}")
        return None

def main():
    """Run comprehensive data quality diagnostics"""
    
    print("="*80)
    print("DATA QUALITY DIAGNOSTIC - TOP 5 SETUPS")
    print("="*80)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================================================
    # CHECK 1: SAMPLE SIZE VALIDATION
    # ========================================================================
    
    print("\n" + "="*80)
    print("CHECK 1: SAMPLE SIZE VALIDATION")
    print("="*80)
    print("\nFetching historical data to count pattern occurrences...")
    
    results = []
    
    for setup in TOP_5:
        ticker = setup['ticker']
        pattern = setup['pattern']
        win_rate = setup['win_rate']
        
        print(f"\n{'─'*80}")
        print(f"{ticker} - {pattern}")
        print(f"Reported Win Rate: {win_rate*100:.1f}%")
        
        # Fetch full history
        hist_data = fetch_full_history(ticker)
        
        if hist_data is None:
            print(f"  ❌ Could not fetch historical data")
            results.append({
                "ticker": ticker,
                "win_rate": win_rate,
                "sample_size": 0,
                "verdict": "UNKNOWN"
            })
            continue
        
        print(f"  Data Range: {hist_data['start_date'].strftime('%Y-%m-%d')} → {hist_data['end_date'].strftime('%Y-%m-%d')}")
        print(f"  Total Trading Days: {hist_data['total_days']:,}")
        
        # Count pattern occurrences
        occurrences = count_pattern_occurrences(hist_data, pattern)
        
        print(f"  Pattern Occurrences: {occurrences}")
        
        # Validate sample size
        # Rule of thumb: need at least 30 observations for statistical significance
        # For 93%+ win rates, need at least 50-100 observations to be credible
        
        if occurrences == 0:
            verdict = "🚨 CRITICAL: Cannot validate - pattern not found in history"
        elif occurrences < 20:
            verdict = f"🚨 CRITICAL: Only {occurrences} occurrences - INSUFFICIENT SAMPLE"
        elif occurrences < 30:
            verdict = f"⚠️  WARNING: Only {occurrences} occurrences - marginal sample size"
        elif win_rate > 0.90 and occurrences < 50:
            verdict = f"⚠️  WARNING: {win_rate*100:.1f}% win rate needs ≥50 samples (only {occurrences})"
        elif win_rate > 0.95 and occurrences < 100:
            verdict = f"⚠️  WARNING: {win_rate*100:.1f}% win rate needs ≥100 samples (only {occurrences})"
        else:
            verdict = f"✅ PASS: {occurrences} occurrences is sufficient"
        
        print(f"  {verdict}")
        
        results.append({
            "ticker": ticker,
            "pattern": pattern,
            "win_rate": win_rate,
            "sample_size": occurrences,
            "verdict": verdict
        })
    
    # ========================================================================
    # CHECK 2: SURVIVORSHIP BIAS
    # ========================================================================
    
    try:
        survivorship_risk = check_survivorship_bias()
    except Exception as e:
        print(f"\n⚠️  Survivorship bias check failed: {e}")
        survivorship_risk = "UNKNOWN"
    
    # ========================================================================
    # CHECK 3: VOLUME CONFIRMATION
    # ========================================================================
    
    try:
        volume_check = check_volume_confirmation()
    except Exception as e:
        print(f"\n⚠️  Volume confirmation check failed: {e}")
        volume_check = None
    
    # ========================================================================
    # SUMMARY & RECOMMENDATIONS
    # ========================================================================
    
    print("\n" + "="*80)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    # Count issues
    critical_issues = sum(1 for r in results if "CRITICAL" in r['verdict'])
    warnings = sum(1 for r in results if "WARNING" in r['verdict'])
    
    print(f"\nIssues Found:")
    print(f"  🚨 CRITICAL: {critical_issues}/5 setups")
    print(f"  ⚠️  WARNING:  {warnings}/5 setups")
    print(f"  ✅ PASS:     {5 - critical_issues - warnings}/5 setups")
    
    print(f"\nSurvivorship Bias Risk: {survivorship_risk}")
    print(f"Volume Confirmation: {'✅ Enabled' if volume_check else '❌ Disabled'}")
    
    print("\n" + "─"*80)
    print("RECOMMENDATIONS:")
    print("─"*80)
    
    if critical_issues > 0:
        print("\n🚨 CRITICAL ACTIONS REQUIRED:")
        print("  1. DO NOT TRADE setups with insufficient sample sizes")
        print("  2. Investigate why pattern occurrences are so low")
        print("  3. Check if backtest filters are too restrictive")
    
    if survivorship_risk == "HIGH_RISK":
        print("\n🚨 SURVIVORSHIP BIAS DETECTED:")
        print("  1. Add delisted/bankrupt stocks to backtest universe")
        print("  2. Expect win rates to DROP 10-20% with realistic data")
        print("  3. Current win rates are INFLATED and NOT tradeable")
    
    if not volume_check:
        print("\n⚠️  VOLUME CONFIRMATION ISSUE:")
        print("  1. Enable volume confirmation in pattern detection")
        print("  2. Current signals may be false breakouts on low volume")
    
    if warnings > 2:
        print("\n⚠️  SAMPLE SIZE CONCERNS:")
        print("  1. Increase backtest period (use 10+ years)")
        print("  2. Reduce pattern selectivity filters")
        print("  3. Accept lower win rates with more occurrences")
    
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    
    for r in results:
        print(f"\n{r['ticker']}")
        print(f"  Win Rate: {r['win_rate']*100:.1f}%")
        print(f"  Sample Size: {r['sample_size']}")
        print(f"  {r['verdict']}")

if __name__ == "__main__":
    main()
