"""
Quick Demo - Execution Guard

Testar olika scenarion för att visa hur systemet fungerar.
"""

from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType

def print_separator():
    print("\n" + "=" * 80)

def test_scenario(name, ticker, category, position_pct, net_edge_pct, guard):
    """Test a single scenario"""
    print(f"\n🎯 SCENARIO: {name}")
    print(f"Ticker: {ticker}")
    print(f"Position: {position_pct}% of portfolio")
    print(f"Net Edge: {net_edge_pct:+.2f}%")
    
    result = guard.analyze(
        ticker=ticker,
        category=category,
        position_size_pct=position_pct,
        net_edge_pct=net_edge_pct
    )
    
    print()
    if result.fx_risk:
        print(f"💱 FX Risk: {result.fx_risk.message}")
    print(f"💰 Fees: {result.fee_analysis.message}")
    print(f"📊 Liquidity: {result.liquidity.message}")
    print()
    print(f"📈 Total Execution Cost: {result.total_execution_cost_pct:.2f}%")
    print(f"🛡️ Execution Risk: {result.execution_risk_level}")
    
    if result.warnings:
        print(f"\n⚠️ WARNINGS:")
        for w in result.warnings:
            print(f"  • {w}")
    
    print(f"\n💡 Avanza Recommendation:")
    print(f"  → {result.avanza_recommendation}")


if __name__ == "__main__":
    print("🛡️" * 40)
    print("          EXECUTION GUARD - DEMO")
    print("🛡️" * 40)
    
    # Initialize guard
    guard = ExecutionGuard(
        account_type=AvanzaAccountType.SMALL,
        portfolio_value_sek=100000
    )
    
    print(f"\nConfiguration:")
    print(f"  Account Type: {guard.account_type.value}")
    print(f"  Portfolio Value: {guard.portfolio_value_sek:,} SEK")
    
    print_separator()
    
    # Scenario 1: Good execution (large position, good edge)
    test_scenario(
        name="Good Execution - Stor position med stark edge",
        ticker="AAPL",
        category="stock_us_liquid",
        position_pct=5.0,
        net_edge_pct=2.5,
        guard=guard
    )
    
    print_separator()
    
    # Scenario 2: Small position problem (fees eat edge)
    test_scenario(
        name="Fee Problem - Liten position med svag edge",
        ticker="XLU",
        category="etf_sector",
        position_pct=1.5,
        net_edge_pct=0.8,
        guard=guard
    )
    
    print_separator()
    
    # Scenario 3: Medium position (acceptable)
    test_scenario(
        name="Medium Position - Acceptabla kostnader",
        ticker="NVDA",
        category="stock_us_liquid",
        position_pct=3.0,
        net_edge_pct=1.5,
        guard=guard
    )
    
    print_separator()
    
    # Scenario 4: Inverse ETF warning
    test_scenario(
        name="Inverse ETF - Daily reset warning",
        ticker="SH",
        category="etf_inverse",
        position_pct=2.0,
        net_edge_pct=1.2,
        guard=guard
    )
    
    print_separator()
    
    # Scenario 5: Swedish stock (no FX risk)
    test_scenario(
        name="Swedish Stock - Inga FX-risker",
        ticker="VOLV-B.ST",
        category="stock_swedish",
        position_pct=4.0,
        net_edge_pct=2.0,
        guard=guard
    )
    
    print_separator()
    
    # Scenario 6: Commodity ETF
    test_scenario(
        name="Commodity ETF - Prioritera låga avgifter",
        ticker="GLD",
        category="etf_commodity",
        position_pct=3.5,
        net_edge_pct=1.8,
        guard=guard
    )
    
    print_separator()
    print("\n✅ DEMO COMPLETE")
    print()
    print("📋 SUMMARY:")
    print("  • Execution Guard hjälper dig minimera dolda kostnader")
    print("  • Varnar för FX-risk (USD topping)")
    print("  • Varnar för höga courtage (små positioner)")
    print("  • Varnar för låg likviditet (slippage risk)")
    print("  • Rekommenderar bästa produkttyp på Avanza")
    print()
    print("💡 TIP: Integrera i dashboard.py för automatisk analys!")
    print()
