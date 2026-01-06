"""
Test edge cases för execution cost beräkning
"""

from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier

execution_guard = ExecutionGuard(
    account_type=AvanzaAccountType.SMALL,
    portfolio_value_sek=100000,
    use_isk_optimizer=True,
    isk_courtage_tier=CourtageTier.MINI
)

test_cases = [
    # (ticker, category, position_pct, edge_pct, name, description)
    ("BILI-A.ST", "default", 5.0, 3.0, "Billerud", "Large Swedish position"),
    ("NOBI.ST", "default", 0.1, 0.5, "Nobina", "Tiny position (100 SEK)"),
    ("AAPL", "stock_us", 2.0, 1.5, "Apple", "US stock with FX"),
    ("NOVO-B.CO", "default", 1.5, 1.2, "Novo Nordisk", "Danish stock (Nordic FX)"),
    ("SPY", "etf_liquid", 3.0, 0.8, "S&P 500 ETF", "US ETF"),
]

print("\n" + "="*80)
print("🧪 EDGE CASE TESTING - Execution Cost Beräkning")
print("="*80 + "\n")

for ticker, category, pos_pct, edge_pct, name, desc in test_cases:
    pos_sek = (pos_pct / 100) * 100000
    
    result = execution_guard.analyze(
        ticker=ticker,
        category=category,
        position_size_pct=pos_pct,
        net_edge_pct=edge_pct,
        product_name=name,
        holding_period_days=5
    )
    
    print(f"📊 {desc}")
    print(f"   Ticker: {ticker} | Position: {pos_sek:.0f} SEK ({pos_pct}%)")
    print(f"   Teknisk edge: {edge_pct:.2f}%")
    
    if result.isk_analysis:
        isk = result.isk_analysis
        print(f"   ISK courtage: {isk.courtage_cost_sek:.2f} SEK ({isk.courtage_pct*100:.2f}%)")
        print(f"   ISK FX cost: {isk.fx_conversion_cost_pct*100:.2f}%")
        print(f"   ISK total cost: {isk.total_isk_cost_pct*100:.2f}%")
    
    print(f"   Execution cost: {result.total_execution_cost_pct:.2f}%")
    print(f"   Net edge: {result.net_edge_after_execution:+.2f}%")
    
    # Sanity check
    expected_net = edge_pct - result.total_execution_cost_pct
    if abs(result.net_edge_after_execution - expected_net) > 0.01:
        print(f"   ⚠️ VARNING: Arithmetic mismatch!")
        print(f"      Expected: {expected_net:.2f}%")
        print(f"      Got: {result.net_edge_after_execution:.2f}%")
    
    # Investability check
    if result.net_edge_after_execution > 0:
        print(f"   ✅ INVESTERBAR")
    else:
        print(f"   ❌ BEVAKNINGSLISTA")
    
    print()

print("="*80)
print("✅ EDGE CASE TEST SLUTFÖRT")
print("="*80)
