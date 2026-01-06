"""
Deep Analysis of Mining & Metals Stocks

Analyzes: ERO Copper, K92 Mining, Alcoa, and Boliden
Shows complete analysis process for each stock
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from instrument_screener_v22 import InstrumentScreenerV22
from src.utils.data_fetcher import DataFetcher
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType

def analyze_stock(ticker, name, category):
    """Run deep analysis for a single stock"""
    print("\n" + "=" * 80)
    print(f"🔍 DEEP ANALYSIS: {name} ({ticker})")
    print("=" * 80)
    
    # Fetch data
    print(f"\nFetching data for {ticker}...")
    fetcher = DataFetcher()
    market_data = fetcher.fetch_stock_data(ticker, period="15y")
    
    if market_data is None:
        print(f"❌ Could not fetch data for {ticker}")
        return None
    
    print(f"✅ Loaded {len(market_data)} days of data")
    print(f"   Period: {market_data.timestamps[0].date()} to {market_data.timestamps[-1].date()}")
    
    # Initialize screener
    screener = InstrumentScreenerV22(enable_v22_filters=True)
    
    # Analyze
    print("\n📊 Analyzing market data...")
    result = screener._analyze_instrument_v22(ticker, name, category)
    
    if result is None:
        print(f"❌ Analysis failed for {ticker}")
        return None
    
    # Display results
    print("\n" + "-" * 80)
    print("PATTERN DETECTION:")
    print("-" * 80)
    print(f"Score: {result.final_score:.1f}/100")
    print(f"Signal: {result.signal.name}")
    print(f"Entry Recommendation: {result.entry_recommendation}")
    
    print("\n" + "-" * 80)
    print("EDGE CALCULATION:")
    print("-" * 80)
    print(f"Best Pattern Edge: {result.best_edge:+.2f}%")
    print(f"Pattern: {result.best_pattern_name}")
    print(f"Net Edge (after costs): {result.net_edge_after_costs:+.2f}%")
    print(f"Cost Profitable: {'YES' if result.cost_profitable else 'NO'}")
    
    print("\n" + "-" * 80)
    print("RISK FILTERS:")
    print("-" * 80)
    print(f"Volatility Regime: {result.volatility_regime}")
    print(f"Market Regime Multiplier: {result.regime_multiplier:.2f}x")
    print(f"Trend Status: {'Above 200-day MA' if 'Below' not in result.entry_recommendation else 'Below 200-day MA'}")
    
    print("\n" + "-" * 80)
    print("POSITION SIZING:")
    print("-" * 80)
    print(f"V-Kelly Position: {result.final_allocation:.2f}% of portfolio")
    print(f"Risk Level: {result.signal.name}")
    
    # EXECUTION GUARD
    print("\n" + "-" * 80)
    print("🛡️ EXECUTION COST GUARD:")
    print("-" * 80)
    
    guard = ExecutionGuard(
        account_type=AvanzaAccountType.SMALL,
        portfolio_value_sek=100000
    )
    
    exec_result = guard.analyze(
        ticker=ticker,
        category=category,
        position_size_pct=result.final_allocation,
        net_edge_pct=result.net_edge_after_costs
    )
    
    if exec_result.fx_risk:
        print(f"💱 FX Risk: {exec_result.fx_risk.message}")
    print(f"💰 Fees: {exec_result.fee_analysis.message}")
    print(f"📊 Liquidity: {exec_result.liquidity.message}")
    print(f"\n🛡️ Execution Risk: {exec_result.execution_risk_level}")
    print(f"💸 Total Execution Cost: {exec_result.total_execution_cost_pct:.2f}%")
    
    if exec_result.warnings:
        print(f"\n⚠️ WARNINGS:")
        for warning in exec_result.warnings:
            print(f"  • {warning}")
    
    print(f"\n💡 Avanza Recommendation:")
    print(f"  → {exec_result.avanza_recommendation}")
    
    print("\n" + "-" * 80)
    print("FINAL RECOMMENDATION:")
    print("-" * 80)
    
    if exec_result.execution_risk_level in ["HIGH", "EXTREME"]:
        print("❌ DO NOT BUY - Execution costs too high")
    elif result.signal.name == "GREEN":
        print("✅ BUY - Strong positive edge")
    elif result.signal.name == "YELLOW":
        print("🟡 MAYBE - Weak positive edge, watch closely")
    else:
        print("🔴 DO NOT BUY - Negative edge")
    
    return result


if __name__ == "__main__":
    print("🎯" * 40)
    print("          MINING & METALS STOCKS - DEEP ANALYSIS")
    print("🎯" * 40)
    
    # Define stocks to analyze
    stocks = [
        ("ERO.TO", "Ero Copper", "stock_us_energy"),  # Canadian copper - Toronto Stock Exchange
        ("KNT.TO", "K92 Mining", "stock_us_energy"),  # Canadian gold/copper - Toronto
        ("AA", "Alcoa", "stock_us_energy"),  # US aluminum - NYSE
        ("BOL.ST", "Boliden", "stock_swedish_mid"),  # Swedish metals - Stockholm
    ]
    
    results = {}
    
    # Analyze each stock
    for ticker, name, category in stocks:
        try:
            result = analyze_stock(ticker, name, category)
            if result:
                results[ticker] = result
        except Exception as e:
            print(f"\n❌ Error analyzing {ticker}: {e}")
            continue
    
    # Summary
    print("\n\n" + "=" * 80)
    print("📊 SUMMARY - ALL MINING & METALS STOCKS")
    print("=" * 80)
    
    if results:
        print(f"\nAnalyzed {len(results)} stocks successfully:\n")
        for ticker, result in results.items():
            signal_emoji = {"GREEN": "🟢", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}.get(result.signal.name, "⚪")
            print(f"{signal_emoji} {result.name} ({ticker})")
            print(f"   Signal: {result.signal.name}")
            print(f"   Score: {result.final_score:.1f}/100")
            print(f"   Net Edge: {result.net_edge_after_costs:+.2f}%")
            print(f"   Position: {result.final_allocation:.2f}%")
            print()
    else:
        print("\n❌ No successful analyses")
    
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)
