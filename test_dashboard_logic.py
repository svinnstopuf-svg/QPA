"""
Quick test of new dashboard INVESTERBARA vs BEVAKNINGSLISTA logic
"""

from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier
from dataclasses import dataclass
from enum import Enum

class Signal(Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"

@dataclass
class MockResult:
    ticker: str
    name: str
    signal: Signal
    net_edge_after_costs: float
    final_allocation: float
    entry_recommendation: str
    category: str = "default"

# Initialize Execution Guard
execution_guard = ExecutionGuard(
    account_type=AvanzaAccountType.SMALL,
    portfolio_value_sek=100000,
    use_isk_optimizer=True,
    isk_courtage_tier=CourtageTier.MINI
)

# Create mock signals (simulating actionable results)
actionable = [
    MockResult(
        ticker="BILI-A.ST",
        name="Billerud",
        signal=Signal.GREEN,
        net_edge_after_costs=2.5,  # 2.5% teknisk edge
        final_allocation=1.2,
        entry_recommendation="ENTER"
    ),
    MockResult(
        ticker="TGT",
        name="Target",
        signal=Signal.YELLOW,
        net_edge_after_costs=1.2,  # 1.2% teknisk edge
        final_allocation=0.8,
        entry_recommendation="ENTER",
        category="stock_us"
    ),
    MockResult(
        ticker="NOBI.ST",
        name="Nobina",
        signal=Signal.YELLOW,
        net_edge_after_costs=0.8,  # 0.8% teknisk edge
        final_allocation=0.5,  # Liten position
        entry_recommendation="ENTER"
    ),
]

print("\n" + "="*80)
print("🧪 TESTAR INVESTERBARA vs BEVAKNINGSLISTA LOGIK")
print("="*80 + "\n")

# Analyze all actionable with Execution Guard and categorize
investable = []  # Net edge > 0 after ALL costs
watchlist = []   # Technical signal but blocked by execution costs

for r in actionable:
    print(f"Analyserar: {r.ticker} (Teknisk edge: {r.net_edge_after_costs:+.2f}%)")
    
    # EXECUTION GUARD - Check execution costs (with ISK optimization)
    exec_result = execution_guard.analyze(
        ticker=r.ticker,
        category=r.category if hasattr(r, 'category') else 'default',
        position_size_pct=r.final_allocation,
        net_edge_pct=r.net_edge_after_costs,
        product_name=r.name,
        holding_period_days=5
    )
    
    # Store exec_result with the signal
    r.exec_result = exec_result
    
    print(f"  Total execution cost: {exec_result.total_execution_cost_pct:.2f}%")
    print(f"  Net edge efter execution: {exec_result.net_edge_after_execution:+.2f}%")
    
    # Categorize: INVESTABLE if net edge after execution costs > 0
    if exec_result.net_edge_after_execution > 0:
        investable.append(r)
        print(f"  ✅ INVESTERBAR\n")
    else:
        watchlist.append(r)
        print(f"  📋 BEVAKNINGSLISTA\n")

# Display results
print("\n" + "="*80)
print(f"✅ {len(investable)} INVESTERBARA | 📋 {len(watchlist)} PÅ BEVAKNING")
print("="*80 + "\n")

if investable:
    print("🚀 INVESTERBARA:")
    for r in investable:
        print(f"  • {r.ticker} - {r.signal.name} - Net edge: {r.exec_result.net_edge_after_execution:+.2f}%")
else:
    print("🚀 INVESTERBARA: Ingen")

print()

if watchlist:
    print("📋 BEVAKNINGSLISTA:")
    for r in watchlist:
        block_reason = r.exec_result.warnings[0] if r.exec_result.warnings else "Negativ net edge efter kostnader"
        print(f"  • {r.ticker:10s} | {r.signal.name:6s} | Teknisk: {r.net_edge_after_costs:+.1f}% | {block_reason}")
else:
    print("📋 BEVAKNINGSLISTA: Ingen")

print("\n" + "="*80)
print("✅ TEST SLUTFÖRT")
print("="*80 + "\n")
