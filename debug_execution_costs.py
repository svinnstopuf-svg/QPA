"""
Debug execution cost calculation
"""

from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier

# Initialize Execution Guard
execution_guard = ExecutionGuard(
    account_type=AvanzaAccountType.SMALL,
    portfolio_value_sek=100000,
    use_isk_optimizer=True,
    isk_courtage_tier=CourtageTier.MINI
)

# Test case 1: BILI-A.ST (Swedish stock, 1.2% position, 2.5% edge)
print("\n" + "="*80)
print("🔍 DEBUG: BILI-A.ST (Swedish stock)")
print("="*80)
print(f"Portfolio: 100,000 SEK")
print(f"Position: 1.2% = 1,200 SEK")
print(f"Teknisk edge: 2.5%")
print()

result = execution_guard.analyze(
    ticker="BILI-A.ST",
    category="default",
    position_size_pct=1.2,
    net_edge_pct=2.5,
    product_name="Billerud",
    holding_period_days=5
)

print(f"Fee Analysis:")
print(f"  Courtage SEK: {result.fee_analysis.courtage_sek:.2f} SEK")
print(f"  Courtage %: {result.fee_analysis.courtage_pct:.2f}%")
print(f"  Spread cost: {result.fee_analysis.spread_cost_pct:.2f}%")
print(f"  Total fee cost: {result.fee_analysis.total_cost_pct:.2f}%")
print()

if result.isk_analysis:
    isk = result.isk_analysis
    print(f"ISK Analysis:")
    print(f"  Market type: {'Swedish' if not isk.is_foreign else 'Foreign'}")
    print(f"  FX cost: {isk.fx_conversion_cost_pct*100:.2f}%")
    print(f"  Courtage SEK: {isk.courtage_cost_sek:.2f} SEK")
    print(f"  Courtage %: {isk.courtage_pct*100:.2f}%")
    print(f"  Total ISK cost: {isk.total_isk_cost_pct*100:.2f}%")
    print(f"  Net edge after ISK: {isk.net_edge_after_isk*100:.2f}%")
    print()

print(f"Liquidity Analysis:")
print(f"  Estimated slippage: {result.liquidity.estimated_slippage_pct:.2f}%")
print()

print(f"TOTAL EXECUTION COST: {result.total_execution_cost_pct:.2f}%")
print(f"NET EDGE AFTER EXECUTION: {result.net_edge_after_execution:.2f}%")
print()

if result.warnings:
    print("Warnings:")
    for w in result.warnings:
        print(f"  - {w}")

print("\n" + "="*80)
print("🔍 DEBUG: NOBI.ST (Swedish stock, SMALL position)")
print("="*80)
print(f"Portfolio: 100,000 SEK")
print(f"Position: 0.5% = 500 SEK")
print(f"Teknisk edge: 0.8%")
print()

result2 = execution_guard.analyze(
    ticker="NOBI.ST",
    category="default",
    position_size_pct=0.5,
    net_edge_pct=0.8,
    product_name="Nobina",
    holding_period_days=5
)

print(f"Fee Analysis:")
print(f"  Courtage SEK: {result2.fee_analysis.courtage_sek:.2f} SEK")
print(f"  Courtage %: {result2.fee_analysis.courtage_pct:.2f}%")
print(f"  Spread cost: {result2.fee_analysis.spread_cost_pct:.2f}%")
print(f"  Total fee cost: {result2.fee_analysis.total_cost_pct:.2f}%")
print()

if result2.isk_analysis:
    isk = result2.isk_analysis
    print(f"ISK Analysis:")
    print(f"  Market type: {'Swedish' if not isk.is_foreign else 'Foreign'}")
    print(f"  Courtage SEK: {isk.courtage_cost_sek:.2f} SEK")
    print(f"  Courtage %: {isk.courtage_pct*100:.2f}%")
    print(f"  Total ISK cost: {isk.total_isk_cost_pct*100:.2f}%")
    print()

print(f"TOTAL EXECUTION COST: {result2.total_execution_cost_pct:.2f}%")
print(f"NET EDGE AFTER EXECUTION: {result2.net_edge_after_execution:.2f}%")
print()

print("="*80)
print("💡 FÖRKLARING:")
print("="*80)
print("För NOBI.ST (500 SEK position):")
print(f"  Courtage MINI på Avanza: 1 SEK minimum")
print(f"  1 SEK / 500 SEK = 0.2% courtage")
print(f"  + Spread ~0.1% = ~0.3% total execution cost")
print(f"  Men vi ser: {result2.total_execution_cost_pct:.2f}% - VARFÖR?")
print()
