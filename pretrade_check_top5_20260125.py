#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRE-TRADE CHECKLIST - TOP 5 SETUPS (2026-01-25)
==============================================
Runs comprehensive 5-check analysis on all Top 5 Sunday Dashboard setups:
1. CALM - Score 98.4/100
2. AWK - Score 94.2/100
3. CEG - Score 90.8/100
4. KBH - Score 79.0/100
5. NEU - Score 68.9/100

Author: V4.0 Position Trading System
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from instruments_universe_1200 import (
    get_sector_for_ticker,
    get_geography_for_ticker,
    calculate_usd_sek_zscore,
    get_fx_adjustment_factor
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Top 5 Setups from Sunday Dashboard 2026-01-25 (After PRIMARY filtering)
# ZTS (Death Cross - SECONDARY) removed → NEU now #5
SETUPS = [
    {"ticker": "CALM", "score": 98.4, "position_sek": 3000, "expected_profit_sek": 181, "win_rate": 0.939, "ev_21d": 0.0602},
    {"ticker": "AWK", "score": 94.2, "position_sek": 3000, "expected_profit_sek": 304, "win_rate": 1.000, "ev_21d": 0.1014},
    {"ticker": "CEG", "score": 90.8, "position_sek": 2500, "expected_profit_sek": 353, "win_rate": 0.733, "ev_21d": 0.1412},
    {"ticker": "KBH", "score": 79.0, "position_sek": 2000, "expected_profit_sek": 185, "win_rate": 0.618, "ev_21d": 0.0926},
    {"ticker": "NEU", "score": 68.9, "position_sek": 3000, "expected_profit_sek": 215, "win_rate": 0.700, "ev_21d": 0.0850}  # New #5
]

# Portfolio settings
PORTFOLIO_VALUE_SEK = 100_000
ISK_ACCOUNT = True

# Cost structure (Avanza ISK)
COURTAGE_MIN_SEK = 1.0
COURTAGE_RATE = 0.0015  # 0.15%
SPREAD_ESTIMATE = 0.001  # 0.10%

# FX costs by geography
FX_COSTS = {
    "Sverige": 0.0000,
    "Norge": 0.0025,
    "Danmark": 0.0025,
    "Finland": 0.0025,
    "USA": 0.0050,
    "Tyskland": 0.0050,
    "Frankrike": 0.0050,
    "Storbritannien": 0.0050,
    "Schweiz": 0.0050,
    "Nederländerna": 0.0050,
    "Spanien": 0.0050
}

# Sector exposure limits
SECTOR_CAP = 0.40  # 40% max per sector

# FX exposure limits
FX_EXPOSURE_WARNING = 0.30  # 30% warning threshold
FX_EXPOSURE_MAX = 0.50  # 50% hard limit

# Data freshness
DATA_AGE_WARNING_DAYS = 3
DATA_AGE_MAX_DAYS = 7

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_courtage(position_sek):
    """Calculate Avanza courtage"""
    courtage = max(COURTAGE_MIN_SEK, position_sek * COURTAGE_RATE)
    return courtage

def calculate_total_costs(position_sek, geography):
    """Calculate total trading costs"""
    courtage = calculate_courtage(position_sek)
    spread_cost = position_sek * SPREAD_ESTIMATE
    fx_cost = position_sek * FX_COSTS.get(geography, 0.0050)
    
    total_cost = courtage + spread_cost + fx_cost
    total_cost_pct = (total_cost / position_sek) * 100
    
    return {
        "courtage": courtage,
        "spread": spread_cost,
        "fx": fx_cost,
        "total": total_cost,
        "total_pct": total_cost_pct
    }

def fetch_latest_data(ticker):
    """Fetch latest price data for sanity check"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        if hist.empty:
            return None
        
        latest_date = hist.index[-1]
        latest_close = hist['Close'].iloc[-1]
        latest_volume = hist['Volume'].iloc[-1]
        
        # Calculate average volume
        avg_volume = hist['Volume'].mean()
        
        # Make datetime timezone-aware for comparison
        latest_date_naive = latest_date.tz_localize(None) if latest_date.tzinfo else latest_date
        age_days = (datetime.now() - latest_date_naive).days
        
        return {
            "date": latest_date,
            "close": latest_close,
            "volume": latest_volume,
            "avg_volume": avg_volume,
            "age_days": age_days
        }
    except Exception as e:
        return None

# ============================================================================
# PRE-TRADE CHECKS
# ============================================================================

def check_1_execution_guard(setup, costs):
    """CHECK 1: Execution Guard - Är courtage rimligt?"""
    print(f"\n{'='*80}")
    print(f"CHECK 1: EXECUTION GUARD - {setup['ticker']}")
    print(f"{'='*80}")
    
    courtage_pct = (costs['courtage'] / setup['position_sek']) * 100
    
    print(f"Position Size:    {setup['position_sek']:,.0f} SEK")
    print(f"Courtage:         {costs['courtage']:.2f} SEK ({courtage_pct:.2f}%)")
    print(f"Courtage Min:     {COURTAGE_MIN_SEK:.2f} SEK")
    
    # Decision logic
    if courtage_pct > 1.0:
        print(f"\n❌ FAIL: Courtage {courtage_pct:.2f}% > 1.0% (inefficient)")
        return False
    elif courtage_pct > 0.5:
        print(f"\n⚠️  WARNING: Courtage {courtage_pct:.2f}% > 0.5% (acceptable but high)")
        return True
    else:
        print(f"\n✅ PASS: Courtage {courtage_pct:.2f}% is efficient")
        return True

def check_2_cost_aware_filter(setup, costs):
    """CHECK 2: Cost-Aware Filter - Är EV positivt efter kostnader?"""
    print(f"\n{'='*80}")
    print(f"CHECK 2: COST-AWARE FILTER - {setup['ticker']}")
    print(f"{'='*80}")
    
    gross_ev_pct = setup['ev_21d'] * 100
    total_costs_pct = costs['total_pct']
    net_ev_pct = gross_ev_pct - total_costs_pct
    
    # Calculate net profit in SEK
    gross_profit = setup['expected_profit_sek']
    net_profit = (net_ev_pct / 100) * setup['position_sek']
    
    print(f"Gross EV (21d):   +{gross_ev_pct:.2f}%")
    print(f"Total Costs:      -{total_costs_pct:.2f}%")
    print(f"  ├─ Courtage:    -{(costs['courtage']/setup['position_sek']*100):.2f}%")
    print(f"  ├─ Spread:      -{(costs['spread']/setup['position_sek']*100):.2f}%")
    print(f"  └─ FX:          -{(costs['fx']/setup['position_sek']*100):.2f}%")
    print(f"Net EV:           +{net_ev_pct:.2f}%")
    print(f"\nGross Profit:     +{gross_profit:.0f} SEK")
    print(f"Cost:             -{costs['total']:.2f} SEK")
    print(f"Net Profit:       +{net_profit:.0f} SEK")
    
    # Decision logic
    if net_ev_pct <= 0:
        print(f"\n❌ FAIL: Net EV {net_ev_pct:.2f}% ≤ 0 (unprofitable after costs)")
        return False
    elif net_ev_pct < 2.0:
        print(f"\n⚠️  WARNING: Net EV {net_ev_pct:.2f}% < 2.0% (marginal)")
        return True
    else:
        print(f"\n✅ PASS: Net EV {net_ev_pct:.2f}% is attractive after costs")
        return True

def check_3_sector_cap(setup, sector, existing_portfolio):
    """CHECK 3: Sector Cap - Skulle denna trade bryta sector cap?"""
    print(f"\n{'='*80}")
    print(f"CHECK 3: SECTOR CAP - {setup['ticker']}")
    print(f"{'='*80}")
    
    # Calculate current sector exposure
    current_sector_value = existing_portfolio.get(sector, 0)
    new_sector_value = current_sector_value + setup['position_sek']
    new_sector_pct = new_sector_value / PORTFOLIO_VALUE_SEK
    
    print(f"Sector:           {sector}")
    print(f"Current Exposure: {current_sector_value:,.0f} SEK ({current_sector_value/PORTFOLIO_VALUE_SEK*100:.1f}%)")
    print(f"After Trade:      {new_sector_value:,.0f} SEK ({new_sector_pct*100:.1f}%)")
    print(f"Sector Cap:       {SECTOR_CAP*100:.0f}%")
    
    # Decision logic
    if new_sector_pct > SECTOR_CAP:
        print(f"\n❌ FAIL: New exposure {new_sector_pct*100:.1f}% > {SECTOR_CAP*100:.0f}% cap")
        return False
    elif new_sector_pct > SECTOR_CAP * 0.8:
        print(f"\n⚠️  WARNING: New exposure {new_sector_pct*100:.1f}% > {SECTOR_CAP*0.8*100:.0f}% (approaching limit)")
        return True
    else:
        print(f"\n✅ PASS: Sector exposure {new_sector_pct*100:.1f}% well within {SECTOR_CAP*100:.0f}% limit")
        return True

def check_4_fx_guard(setup, geography, existing_portfolio):
    """CHECK 4: FX Guard - USD/SEK position och exposure"""
    print(f"\n{'='*80}")
    print(f"CHECK 4: FX GUARD - {setup['ticker']}")
    print(f"{'='*80}")
    
    # Calculate USD/SEK Z-score
    try:
        zscore = calculate_usd_sek_zscore()
        fx_adjustment = get_fx_adjustment_factor(zscore)
    except:
        zscore = None
        fx_adjustment = 1.0
    
    # Calculate USD exposure
    current_usd_value = existing_portfolio.get("USD", 0)
    is_usd = geography == "USA"
    
    if is_usd:
        new_usd_value = current_usd_value + setup['position_sek']
        new_usd_pct = new_usd_value / PORTFOLIO_VALUE_SEK
    else:
        new_usd_value = current_usd_value
        new_usd_pct = new_usd_value / PORTFOLIO_VALUE_SEK
    
    print(f"Geography:        {geography}")
    if is_usd:
        print(f"USD Exposure:     {current_usd_value:,.0f} SEK → {new_usd_value:,.0f} SEK ({new_usd_pct*100:.1f}%)")
        if zscore is not None:
            print(f"USD/SEK Z-score:  {zscore:.2f}")
            if zscore < -1.5:
                print(f"  → USD is CHEAP (favorable for US stocks)")
            elif zscore > 2.0:
                print(f"  → USD is EXPENSIVE (unfavorable for US stocks)")
            else:
                print(f"  → USD is NEUTRAL")
    else:
        print(f"No USD exposure (non-US stock)")
    
    # Decision logic
    if is_usd:
        if new_usd_pct > FX_EXPOSURE_MAX:
            print(f"\n❌ FAIL: USD exposure {new_usd_pct*100:.1f}% > {FX_EXPOSURE_MAX*100:.0f}% limit")
            return False
        elif new_usd_pct > FX_EXPOSURE_WARNING:
            print(f"\n⚠️  WARNING: USD exposure {new_usd_pct*100:.1f}% > {FX_EXPOSURE_WARNING*100:.0f}% threshold")
            if zscore is not None and zscore > 2.0:
                print(f"   Additional concern: USD is expensive (Z={zscore:.2f})")
            return True
        else:
            print(f"\n✅ PASS: USD exposure {new_usd_pct*100:.1f}% acceptable")
            if zscore is not None and zscore < -1.5:
                print(f"   Bonus: USD is cheap (Z={zscore:.2f}) - favorable timing!")
            return True
    else:
        print(f"\n✅ PASS: Non-USD stock, no FX exposure concern")
        return True

def check_5_data_sanity(ticker, data_info):
    """CHECK 5: Data Sanity - Är data färsk och trovärdig?"""
    print(f"\n{'='*80}")
    print(f"CHECK 5: DATA SANITY - {ticker}")
    print(f"{'='*80}")
    
    if data_info is None:
        print(f"❌ FAIL: Unable to fetch data for {ticker}")
        return False
    
    age_days = data_info['age_days']
    volume_ratio = data_info['volume'] / data_info['avg_volume'] if data_info['avg_volume'] > 0 else 0
    
    print(f"Latest Data:      {data_info['date'].strftime('%Y-%m-%d')} ({age_days} days old)")
    print(f"Latest Close:     ${data_info['close']:.2f}")
    print(f"Latest Volume:    {data_info['volume']:,.0f}")
    print(f"Avg Volume (5d):  {data_info['avg_volume']:,.0f}")
    print(f"Volume Ratio:     {volume_ratio:.2f}x")
    
    # Decision logic
    issues = []
    
    if age_days > DATA_AGE_MAX_DAYS:
        issues.append(f"Data too old ({age_days} > {DATA_AGE_MAX_DAYS} days)")
    elif age_days > DATA_AGE_WARNING_DAYS:
        print(f"\n⚠️  WARNING: Data is {age_days} days old (>{DATA_AGE_WARNING_DAYS} days)")
    
    if volume_ratio < 0.1:
        issues.append(f"Suspiciously low volume ({volume_ratio:.2f}x avg)")
    elif volume_ratio < 0.3:
        print(f"\n⚠️  WARNING: Below-average volume ({volume_ratio:.2f}x)")
    
    if issues:
        print(f"\n❌ FAIL: {', '.join(issues)}")
        return False
    else:
        print(f"\n✅ PASS: Data is fresh and volume is normal")
        return True

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_pretrade_checks():
    """Run all pre-trade checks on Top 5 setups"""
    
    print("="*80)
    print("PRE-TRADE CHECKLIST - TOP 5 SETUPS (2026-01-25)")
    print("="*80)
    print(f"\nPortfolio Value: {PORTFOLIO_VALUE_SEK:,.0f} SEK")
    print(f"Account Type: {'ISK' if ISK_ACCOUNT else 'KF'}")
    print(f"\nAnalyzing {len(SETUPS)} setups...")
    
    # Simulate existing portfolio (empty for now)
    # In production, this would load from portfolio tracker
    existing_sector_exposure = {}
    existing_fx_exposure = {"USD": 0}
    
    # Track results
    results = []
    
    for i, setup in enumerate(SETUPS, 1):
        ticker = setup['ticker']
        
        print(f"\n\n{'#'*80}")
        print(f"# SETUP {i}/5: {ticker} (Score: {setup['score']:.1f}/100)")
        print(f"{'#'*80}")
        
        # Lookup metadata
        sector = get_sector_for_ticker(ticker)
        geography = get_geography_for_ticker(ticker)
        
        print(f"\nSector:    {sector}")
        print(f"Geography: {geography}")
        print(f"Position:  {setup['position_sek']:,.0f} SEK ({setup['position_sek']/PORTFOLIO_VALUE_SEK*100:.1f}% of portfolio)")
        
        # Calculate costs
        costs = calculate_total_costs(setup['position_sek'], geography)
        
        # Fetch latest data
        data_info = fetch_latest_data(ticker)
        
        # Run 5 checks
        check1 = check_1_execution_guard(setup, costs)
        check2 = check_2_cost_aware_filter(setup, costs)
        check3 = check_3_sector_cap(setup, sector, existing_sector_exposure)
        check4 = check_4_fx_guard(setup, geography, existing_fx_exposure)
        check5 = check_5_data_sanity(ticker, data_info)
        
        all_passed = all([check1, check2, check3, check4, check5])
        
        # Summary
        print(f"\n{'='*80}")
        print(f"SUMMARY - {ticker}")
        print(f"{'='*80}")
        print(f"CHECK 1 (Execution Guard):  {'✅ PASS' if check1 else '❌ FAIL'}")
        print(f"CHECK 2 (Cost-Aware):       {'✅ PASS' if check2 else '❌ FAIL'}")
        print(f"CHECK 3 (Sector Cap):       {'✅ PASS' if check3 else '❌ FAIL'}")
        print(f"CHECK 4 (FX Guard):         {'✅ PASS' if check4 else '❌ FAIL'}")
        print(f"CHECK 5 (Data Sanity):      {'✅ PASS' if check5 else '❌ FAIL'}")
        
        if all_passed:
            print(f"\n🟢 FINAL DECISION: PROCEED WITH TRADE")
            recommendation = "PROCEED"
        else:
            print(f"\n🔴 FINAL DECISION: DO NOT TRADE")
            recommendation = "REJECT"
        
        results.append({
            "ticker": ticker,
            "score": setup['score'],
            "check1": check1,
            "check2": check2,
            "check3": check3,
            "check4": check4,
            "check5": check5,
            "recommendation": recommendation
        })
    
    # Final summary
    print(f"\n\n{'#'*80}")
    print(f"# FINAL SUMMARY - ALL 5 SETUPS")
    print(f"{'#'*80}\n")
    
    print(f"{'Ticker':<8} {'Score':<8} {'C1':<5} {'C2':<5} {'C3':<5} {'C4':<5} {'C5':<5} {'Decision':<10}")
    print(f"{'-'*80}")
    
    for r in results:
        c1 = '✅' if r['check1'] else '❌'
        c2 = '✅' if r['check2'] else '❌'
        c3 = '✅' if r['check3'] else '❌'
        c4 = '✅' if r['check4'] else '❌'
        c5 = '✅' if r['check5'] else '❌'
        
        print(f"{r['ticker']:<8} {r['score']:<8.1f} {c1:<5} {c2:<5} {c3:<5} {c4:<5} {c5:<5} {r['recommendation']:<10}")
    
    proceed_count = sum(1 for r in results if r['recommendation'] == 'PROCEED')
    print(f"\n{'-'*80}")
    print(f"TOTAL: {proceed_count}/{len(results)} setups cleared for trading")
    
    if proceed_count > 0:
        print(f"\n✅ You have {proceed_count} actionable setup(s) ready to trade!")
    else:
        print(f"\n⚠️  No setups passed all 5 checks. Review issues above.")

if __name__ == "__main__":
    run_pretrade_checks()
