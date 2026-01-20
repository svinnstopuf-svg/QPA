"""
Find BILI-A.ST and see why it's blocked
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from instrument_screener_v22 import InstrumentScreenerV22
from instruments_universe_800 import get_all_800_instruments
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier

print("\n" + "="*80)
print("🔍 Letar efter BILI-A.ST")
print("="*80 + "\n")

# Run screening
screener = InstrumentScreenerV22(enable_v22_filters=True)
instruments = get_all_800_instruments()

# Find BILI-A.ST
bili_instrument = None
for inst in instruments:
    # inst is a tuple: (ticker, name, category)
    if inst[0] == 'BILI-A.ST':
        bili_instrument = {'ticker': inst[0], 'name': inst[1], 'category': inst[2]}
        break

if not bili_instrument:
    print("❌ BILI-A.ST finns inte i 800-ticker universe!")
    exit(1)

print(f"✅ Hittade: {bili_instrument['ticker']} - {bili_instrument['name']}")
print(f"   Kategori: {bili_instrument['category']}")
print()

# Screen just this one
print("Analyserar BILI-A.ST...")
results = screener.screen_instruments([(bili_instrument['ticker'], bili_instrument['name'], bili_instrument['category'])])

if not results:
    print("❌ Ingen resultat från screener!")
    exit(1)

r = results[0]

print(f"\nScreener Resultat:")
print(f"  Signal: {r.signal.name}")
print(f"  Score: {r.final_score}/100")
print(f"  Teknisk Edge: {r.net_edge_after_costs:.2f}%")
print(f"  Base Allocation: {r.v_kelly_position:.2f}%")
print(f"  Regime Multiplier: {r.regime_multiplier:.2f}x")
print(f"  Final Allocation: {r.final_allocation:.2f}%")
print(f"  Entry Recommendation: {r.entry_recommendation}")
print()

# Check if it passes minimum position size
MIN_POSITION_PCT = 0.05
if r.final_allocation < MIN_POSITION_PCT:
    print(f"❌ BLOCKERAD: Position {r.final_allocation:.4f}% < minimum {MIN_POSITION_PCT}%")
    print(f"   Position skulle vara: {r.final_allocation * 1000:.0f} SEK på 100k portfölj")
else:
    print(f"✅ Passerar minimum position size")
    
    # Now check execution guard
    execution_guard = ExecutionGuard(
        account_type=AvanzaAccountType.SMALL,
        portfolio_value_sek=100000,
        use_isk_optimizer=True,
        isk_courtage_tier=CourtageTier.MINI
    )
    
    exec_result = execution_guard.analyze(
        ticker=r.ticker,
        category=r.category,
        position_size_pct=r.final_allocation,
        net_edge_pct=r.net_edge_after_costs,
        product_name=r.name,
        holding_period_days=5
    )
    
    print(f"\nExecution Guard:")
    print(f"  Total cost: {exec_result.total_execution_cost_pct:.2f}%")
    print(f"  Net edge after execution: {exec_result.net_edge_after_execution:+.2f}%")
    print(f"  Status: {'✅ INVESTERBAR' if exec_result.net_edge_after_execution > 0 else '❌ BEVAKNINGSLISTA'}")

print("\n" + "="*80)
