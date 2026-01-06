"""
Debug: Se faktiska positionsstorlekar från screener
"""

from instrument_screener_v22 import InstrumentScreenerV22
from instruments_universe_800 import get_all_800_instruments
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier

print("\n" + "="*80)
print("🔍 DEBUG: Faktiska Positionsstorlekar från Screener")
print("="*80 + "\n")

# Run screening (only first 50 to be quick)
screener = InstrumentScreenerV22(enable_v22_filters=True)
instruments = get_all_800_instruments()[:50]  # First 50 only
results = screener.screen_instruments(instruments)

# Initialize Execution Guard
execution_guard = ExecutionGuard(
    account_type=AvanzaAccountType.SMALL,
    portfolio_value_sek=100000,
    use_isk_optimizer=True,
    isk_courtage_tier=CourtageTier.MINI
)

# Find BILI-A.ST or similar signals
actionable = [r for r in results if r.entry_recommendation.startswith("ENTER")]

print(f"Found {len(actionable)} ENTER signals\n")

for r in actionable[:5]:  # First 5
    print(f"Ticker: {r.ticker}")
    print(f"  Signal: {r.signal.name}")
    print(f"  Teknisk Edge: {r.net_edge_after_costs:.2f}%")
    print(f"  Position Size: {r.final_allocation:.3f}%")
    print(f"  Regime Multiplier: {r.regime_multiplier:.2f}x")
    
    # Calculate position in SEK
    pos_sek = (r.final_allocation / 100) * 100000
    print(f"  Position SEK: {pos_sek:.0f} SEK")
    
    # Analyze with Execution Guard
    exec_result = execution_guard.analyze(
        ticker=r.ticker,
        category=r.category if hasattr(r, 'category') else 'default',
        position_size_pct=r.final_allocation,
        net_edge_pct=r.net_edge_after_costs,
        product_name=r.name,
        holding_period_days=5
    )
    
    if exec_result.isk_analysis:
        isk = exec_result.isk_analysis
        print(f"  ISK Courtage: {isk.courtage_cost_sek:.2f} SEK ({isk.courtage_pct*100:.2f}%)")
        print(f"  ISK Total Cost: {isk.total_isk_cost_pct*100:.2f}%")
    
    print(f"  Execution Cost: {exec_result.total_execution_cost_pct:.2f}%")
    print(f"  Net Edge: {exec_result.net_edge_after_execution:+.2f}%")
    print(f"  Status: {'✅ INVESTERBAR' if exec_result.net_edge_after_execution > 0 else '❌ BEVAKNINGSLISTA'}")
    print()

print("="*80)
