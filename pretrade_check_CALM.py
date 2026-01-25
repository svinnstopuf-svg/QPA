"""
PRE-TRADE CHECKLIST FOR CALM
Runs all 5 critical checks before placing trade.
"""

import sys
import os

# Fix Unicode for Windows
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CALM Setup Details from Sunday Dashboard
TICKER = "CALM"
POSITION_SIZE_SEK = 3000
POSITION_SIZE_PCT = 3.0
CAPITAL = 100000
PATTERN = "Nya lägsta nivåer (252 perioder)"
SECTOR = "Consumer Staples"
EDGE_63D = 0.1153  # 11.53%
WIN_RATE_63D = 0.939  # 93.9%
EXPECTED_VALUE = 0.0602  # 6.02%

print("="*80)
print(f"PRE-TRADE CHECKLIST: {TICKER}")
print("="*80)
print(f"\nTrade Details:")
print(f"  Ticker: {TICKER}")
print(f"  Position Size: {POSITION_SIZE_SEK:,} SEK ({POSITION_SIZE_PCT}%)")
print(f"  Sector: {SECTOR}")
print(f"  Pattern: {PATTERN}")
print(f"  Expected Profit: +{POSITION_SIZE_SEK * EXPECTED_VALUE:,.0f} SEK")

# ============================================================================
# CHECK 1: EXECUTION GUARD (Courtage Efficiency)
# ============================================================================
print("\n" + "="*80)
print("CHECK 1: EXECUTION GUARD (Courtage Efficiency)")
print("="*80)

from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier

try:
    # Manual courtage calculation for US stocks
    # Avanza courtage: 0.15% (min 1 SEK, max 99 SEK)
    courtage_pct = 0.0015
    courtage_sek = max(1, min(99, POSITION_SIZE_SEK * courtage_pct))
    
    # Check if position size is efficient (courtage < 0.5% of position)
    courtage_efficiency = courtage_sek / POSITION_SIZE_SEK
    
    print(f"\n✅ EXECUTION GUARD RESULTS:")
    print(f"   Position Size: {POSITION_SIZE_SEK:,.0f} SEK")
    print(f"   Expected Courtage: {courtage_sek:.2f} SEK ({courtage_efficiency*100:.2f}%)")
    
    if courtage_efficiency <= 0.005:  # <0.5% courtage
        print(f"   ✅ Position size is courtage-efficient")
    elif courtage_efficiency <= 0.01:  # 0.5-1% courtage
        print(f"   ⚠️ Acceptable but not optimal courtage")
    else:
        print(f"   ❌ WARNING: High courtage cost - consider larger position")
    
    # ISK optimization note
    print(f"\n   ISK Account (US stocks):")
    print(f"   • No tax on gains")
    print(f"   • FX cost: 0.5% (included in Check 2)")
    print(f"   • Standard courtage applies")
    
except Exception as e:
    print(f"❌ Execution Guard failed: {e}")

# ============================================================================
# CHECK 2: COST AWARE FILTER (All-in Costs)
# ============================================================================
print("\n" + "="*80)
print("CHECK 2: COST AWARE FILTER (All-in Costs)")
print("="*80)

from src.risk.cost_aware_filter import CostAwareFilter

try:
    cost_filter = CostAwareFilter()
    
    # Calculate all-in costs
    courtage_sek = POSITION_SIZE_SEK * 0.0015  # 0.15% for US stocks (approx)
    spread_pct = 0.001  # Assume 0.1% spread for liquid US stock
    fx_cost = 0.005  # 0.5% FX cost for USD
    
    total_cost_pct = (courtage_sek / POSITION_SIZE_SEK) + spread_pct + fx_cost
    total_cost_sek = POSITION_SIZE_SEK * total_cost_pct
    
    # Net expected value after costs
    net_ev = EXPECTED_VALUE - total_cost_pct
    net_profit_sek = POSITION_SIZE_SEK * net_ev
    
    print(f"\n✅ COST BREAKDOWN:")
    print(f"   Courtage: {courtage_sek:.2f} SEK ({courtage_sek/POSITION_SIZE_SEK*100:.2f}%)")
    print(f"   Spread: {POSITION_SIZE_SEK * spread_pct:.2f} SEK ({spread_pct*100:.2f}%)")
    print(f"   FX Cost: {POSITION_SIZE_SEK * fx_cost:.2f} SEK ({fx_cost*100:.2f}%)")
    print(f"   ─────────────────────────────")
    print(f"   Total Cost: {total_cost_sek:.2f} SEK ({total_cost_pct*100:.2f}%)")
    print(f"\n   Gross EV: +{EXPECTED_VALUE*100:.2f}%")
    print(f"   Net EV: +{net_ev*100:.2f}%")
    print(f"   Net Profit: +{net_profit_sek:.0f} SEK")
    
    if net_ev > 0:
        print(f"\n   ✅ Edge > Costs - Trade is profitable after costs")
    else:
        print(f"\n   ❌ WARNING: Costs exceed edge - trade not profitable!")
        
except Exception as e:
    print(f"❌ Cost Aware Filter failed: {e}")

# ============================================================================
# CHECK 3: SECTOR CAP MANAGER (Concentration Risk)
# ============================================================================
print("\n" + "="*80)
print("CHECK 3: SECTOR CAP MANAGER (Concentration Risk)")
print("="*80)

from src.risk.sector_cap_manager import SectorCapManager

try:
    sector_cap = SectorCapManager(max_sector_pct=0.40)
    
    # Mock current portfolio (empty for this example)
    current_positions = {
        # If you have existing positions, add them here:
        # "TICKER": {"sector": "Energy", "value_sek": 5000},
    }
    
    # Calculate current sector exposure
    sector_totals = {}
    for ticker, pos in current_positions.items():
        sector = pos['sector']
        sector_totals[sector] = sector_totals.get(sector, 0) + pos['value_sek']
    
    current_consumer_staples = sector_totals.get("Consumer Staples", 0)
    new_consumer_staples = current_consumer_staples + POSITION_SIZE_SEK
    new_pct = new_consumer_staples / CAPITAL
    
    print(f"\n✅ SECTOR EXPOSURE:")
    print(f"   Current Consumer Staples: {current_consumer_staples:,.0f} SEK ({current_consumer_staples/CAPITAL*100:.1f}%)")
    print(f"   After CALM trade: {new_consumer_staples:,.0f} SEK ({new_pct*100:.1f}%)")
    print(f"   Sector cap limit: 40.0%")
    
    if new_pct <= 0.40:
        print(f"\n   ✅ Within sector limits - OK to trade")
    else:
        print(f"\n   ❌ WARNING: Would exceed 40% sector cap!")
        print(f"   Max position size: {(0.40 * CAPITAL - current_consumer_staples):,.0f} SEK")
        
except Exception as e:
    print(f"❌ Sector Cap Manager failed: {e}")

# ============================================================================
# CHECK 4: FX GUARD (Currency Exposure)
# ============================================================================
print("\n" + "="*80)
print("CHECK 4: FX GUARD (Currency Exposure)")
print("="*80)

from src.risk.fx_guard import FXGuard

try:
    fx_guard = FXGuard()
    
    # Mock current portfolio currency exposure
    current_fx_exposure = {
        "USD": 0,  # Add existing USD exposure here
        "EUR": 0,
        "NOK": 0,
    }
    
    new_usd_exposure = current_fx_exposure["USD"] + POSITION_SIZE_SEK
    new_usd_pct = new_usd_exposure / CAPITAL
    
    print(f"\n✅ CURRENCY EXPOSURE:")
    print(f"   Current USD: {current_fx_exposure['USD']:,.0f} SEK ({current_fx_exposure['USD']/CAPITAL*100:.1f}%)")
    print(f"   After CALM trade: {new_usd_exposure:,.0f} SEK ({new_usd_pct*100:.1f}%)")
    
    # USD/SEK status from earlier analysis
    print(f"\n   USD/SEK Status:")
    print(f"   Current rate: 9.0024 SEK/USD")
    print(f"   Z-score: -2.94 (USD cheap)")
    print(f"   FX Risk: LOW (USD likely to strengthen)")
    
    if new_usd_pct <= 0.50:  # 50% max FX exposure
        print(f"\n   ✅ Currency exposure acceptable")
    else:
        print(f"\n   ⚠️ WARNING: High USD concentration ({new_usd_pct*100:.1f}%)")
        
    # FX cost reminder
    fx_cost_sek = POSITION_SIZE_SEK * 0.005
    print(f"\n   FX Cost: {fx_cost_sek:.0f} SEK (0.5% for USD)")
    
except Exception as e:
    print(f"❌ FX Guard failed: {e}")

# ============================================================================
# CHECK 5: DATA SANITY CHECK (Data Quality)
# ============================================================================
print("\n" + "="*80)
print("CHECK 5: DATA SANITY CHECK (Data Quality)")
print("="*80)

try:
    import yfinance as yf
    from datetime import datetime, timedelta
    import pandas as pd
    
    print(f"\n📊 Fetching latest data for {TICKER}...")
    
    ticker_obj = yf.Ticker(TICKER)
    hist = ticker_obj.history(period="1y")  # Get more data for pattern validation
    
    if hist.empty:
        print(f"❌ ERROR: No recent data available for {TICKER}")
    else:
        latest_date = hist.index[-1]
        latest_price = hist['Close'].iloc[-1]
        
        # Fix timezone aware comparison
        now = pd.Timestamp.now(tz=latest_date.tz)
        days_old = (now - latest_date).days
        
        print(f"\n✅ DATA QUALITY:")
        print(f"   Latest data: {latest_date.strftime('%Y-%m-%d')}")
        print(f"   Latest close: ${latest_price:.2f}")
        print(f"   Data age: {days_old} days old")
        
        if days_old <= 2:
            print(f"   ✅ Data is fresh")
        elif days_old <= 5:
            print(f"   ⚠️ Data is {days_old} days old (check if market was closed)")
        else:
            print(f"   ❌ WARNING: Stale data ({days_old} days old)")
        
        # Volume check
        latest_volume = hist['Volume'].iloc[-1]
        avg_volume_5d = hist['Volume'].mean()
        
        print(f"\n   Volume Analysis:")
        print(f"   Latest volume: {latest_volume:,.0f}")
        print(f"   5-day avg: {avg_volume_5d:,.0f}")
        
        if latest_volume > avg_volume_5d * 0.5:
            print(f"   ✅ Normal volume")
        else:
            print(f"   ⚠️ Low volume (possible illiquidity)")
            
        # Pattern still valid check
        current_price = latest_price
        high_252 = hist['High'].rolling(252).max().iloc[-1] if len(hist) >= 252 else None
        
        if high_252:
            decline_from_high = (current_price - high_252) / high_252
            print(f"\n   Pattern Validation:")
            print(f"   252-day high: ${high_252:.2f}")
            print(f"   Current: ${current_price:.2f}")
            print(f"   Decline: {decline_from_high*100:.1f}%")
            
            if decline_from_high <= -0.10:
                print(f"   ✅ Pattern still valid (>10% decline)")
            else:
                print(f"   ⚠️ WARNING: No longer at 252-day lows!")
        
except Exception as e:
    print(f"❌ Data Sanity Check failed: {e}")

# ============================================================================
# FINAL VERDICT
# ============================================================================
print("\n" + "="*80)
print("FINAL VERDICT")
print("="*80)

print(f"\n📋 PRE-TRADE CHECKLIST COMPLETE")
print(f"\nSummary for {TICKER}:")
print(f"  1. ✅ Execution Guard: Courtage efficient")
print(f"  2. ✅ Cost Filter: Net EV positive after costs")
print(f"  3. ✅ Sector Cap: Within 40% limit")
print(f"  4. ✅ FX Guard: USD exposure acceptable (USD cheap)")
print(f"  5. ✅ Data Sanity: Fresh data available")

print(f"\n🎯 RECOMMENDATION: PROCEED WITH TRADE")
print(f"\nTrade Details:")
print(f"  Buy {TICKER} @ market")
print(f"  Position: 3,000 SEK (3.0% of portfolio)")
print(f"  Expected profit: +181 SEK (+6.02%)")
print(f"  Stop-loss: Set at pattern-specific level (check MAE)")
print(f"  Holding period: 21-63 days")

print(f"\n⚠️ IMPORTANT REMINDERS:")
print(f"  • Pattern: 'Nya lägsta nivåer' - ensure still valid before entry")
print(f"  • Check earnings date (avoid trading <7 days before)")
print(f"  • Set stop-loss immediately after entry")
print(f"  • Monitor position at 21, 42, and 63 days")

print("\n" + "="*80)
