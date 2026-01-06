"""
🎯 TRADING DASHBOARD - Allt du behöver veta på EN sida

Kör detta VARJE DAG för att få översikt.
"""

import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from instrument_screener_v22 import InstrumentScreenerV22, format_v22_report
# Switch to 800-ticker universe for expanded market coverage
from instruments_universe_800 import get_all_800_instruments
from src.risk.all_weather_config import (
    is_all_weather, get_all_weather_category, get_avanza_alternative,
    is_defensive_sector
)
from src.analysis.macro_indicators import MacroIndicators
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier
from datetime import datetime
import os

def print_section(title, emoji="📊"):
    """Print section header."""
    print("\n" + "="*80)
    print(f"{emoji} {title}")
    print("="*80)

def main():
    """Simple daily dashboard."""
    
    print("\n" + "🎯 "*20)
    print("          TRADING DASHBOARD - Dagens Översikt")
    print("🎯 "*20)
    print(f"\n📅 Datum: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Initialize Execution Guard with ISK optimization
    execution_guard = ExecutionGuard(
        account_type=AvanzaAccountType.SMALL,  # Legacy parameter
        portfolio_value_sek=100000,  # Change to your portfolio value
        use_isk_optimizer=True,  # Enable ISK-specific cost analysis
        isk_courtage_tier=CourtageTier.MINI  # Your Avanza courtage class
    )
    
    # Run screening
    print("\n⏳ Analyserar 800 instruments...")
    screener = InstrumentScreenerV22(enable_v22_filters=True)
    instruments = get_all_800_instruments()
    results = screener.screen_instruments(instruments)
    
    # Create reports dir
    os.makedirs("reports", exist_ok=True)
    
    # ========================================================================
    # 1. DAGENS ACTION ITEMS (Viktigast!)
    # ========================================================================
    print_section("DAGENS ACTION ITEMS", "🎯")
    
    # Include all GREEN/YELLOW signals, regardless of ENTER or BLOCK status
    # This ensures technically strong signals blocked by costs appear in watchlist
    from instrument_screener_v22 import Signal
    actionable = [r for r in results if r.signal in [Signal.GREEN, Signal.YELLOW]]
    
    # Prioritize All-Weather during CRISIS
    if results and results[0].regime_multiplier <= 0.2:  # CRISIS
        # Separate All-Weather from normal
        all_weather = [r for r in actionable if is_all_weather(r.ticker)]
        normal = [r for r in actionable if not is_all_weather(r.ticker)]
        actionable = all_weather + normal  # All-Weather first
    
    # ========================================================================
    # Analyze all actionable with Execution Guard and categorize
    # ========================================================================
    investable = []  # Net edge > 0 after ALL costs
    watchlist = []   # Technical signal but blocked by execution costs
    
    for r in actionable:
        # Check if signal was already blocked by screener (e.g., position too small)
        if "BLOCK" in r.entry_recommendation or r.final_allocation == 0.0:
            # Skip Execution Guard - already blocked, add directly to watchlist
            watchlist.append(r)
            continue
        
        # EXECUTION GUARD - Check execution costs (with ISK optimization)
        exec_result = execution_guard.analyze(
            ticker=r.ticker,
            category=r.category if hasattr(r, 'category') else 'default',
            position_size_pct=r.final_allocation,
            net_edge_pct=r.net_edge_after_costs,
            product_name=r.name,  # For ISK product classification
            holding_period_days=5  # Default 5-day holding period
        )
        
        # Store exec_result with the signal
        r.exec_result = exec_result
        
        # Categorize: INVESTABLE if net edge after execution costs > 0
        if exec_result.net_edge_after_execution > 0:
            investable.append(r)
        else:
            watchlist.append(r)
    
    # ========================================================================
    # Display header with counts
    # ========================================================================
    print(f"\n✅ {len(investable)} INVESTERBARA | 📋 {len(watchlist)} PÅ BEVAKNING\n")
    
    # ========================================================================
    # 🚀 INVESTERBARA - Full details (Net Edge > 0 efter alla kostnader)
    # ========================================================================
    if investable:
        print("\n" + "="*80)
        print("🚀 INVESTERBARA (Matematiskt lönsamma efter alla avgifter)")
        print("="*80 + "\n")
        
        for i, r in enumerate(investable, 1):
            # Mark All-Weather instruments
            aw_marker = " 🛡️ [ALL-WEATHER]" if is_all_weather(r.ticker) else ""
            print(f"{i}. {r.name} ({r.ticker}){aw_marker}")
            print(f"   Signal: {r.signal.name}")
            print(f"   Teknisk Edge: {r.net_edge_after_costs:+.2f}%")
            print(f"   Position: {r.final_allocation:.2f}%")
            
            # All-Weather marker
            if is_all_weather(r.ticker):
                category = get_all_weather_category(r.ticker)
                print(f"   Kategori: {category} (Crisis Protection)")
                # Avanza alternative
                avanza_alt = get_avanza_alternative(r.ticker)
                if avanza_alt:
                    print(f"   💡 Avanza: {avanza_alt}")
            
            # Defensive sector marker
            elif is_defensive_sector(r.ticker):
                print(f"   Kategori: Defensive Sector (0.5x allocation in CRISIS)")
            
            # Display execution analysis
            exec_result = r.exec_result
            
            if exec_result.execution_risk_level in ["HIGH", "EXTREME"]:
                print(f"   🛡️ EXECUTION GUARD: 🔴 {exec_result.execution_risk_level}")
                for warning in exec_result.warnings:
                    print(f"      • {warning}")
                print(f"      • Total kostnad: {exec_result.total_execution_cost_pct:.2f}%")
                print(f"      • Net Edge efter execution: {exec_result.net_edge_after_execution:+.2f}%")
                print(f"      • Rekommendation: {exec_result.avanza_recommendation}")
                # ISK-specific details
                if exec_result.isk_analysis:
                    isk = exec_result.isk_analysis
                    print(f"      🇸🇪 ISK: {isk.product_type.value} (Health: {isk.product_health_score}/100)")
                    print(f"         Net edge efter ISK: {isk.net_edge_after_isk:.2%}")
            elif exec_result.execution_risk_level == "MEDIUM":
                print(f"   🛡️ EXECUTION GUARD: 🟡 {exec_result.execution_risk_level}")
                print(f"      • Total kostnad: {exec_result.total_execution_cost_pct:.2f}%")
                print(f"      • Net Edge efter execution: {exec_result.net_edge_after_execution:+.2f}%")
                if exec_result.warnings:
                    print(f"      • {exec_result.warnings[0]}")
                # ISK-specific details
                if exec_result.isk_analysis:
                    isk = exec_result.isk_analysis
                    if isk.is_foreign:
                        print(f"      🇸🇪 ISK: FX-kostnad {isk.fx_conversion_cost_pct:.2%}")
            else:
                print(f"   🛡️ EXECUTION GUARD: 🟢 {exec_result.execution_risk_level}")
                print(f"      • Total kostnad: {exec_result.total_execution_cost_pct:.2f}%")
                print(f"      • Net Edge efter execution: {exec_result.net_edge_after_execution:+.2f}%")
                # ISK-specific details for GREEN signals
                if exec_result.isk_analysis:
                    isk = exec_result.isk_analysis
                    print(f"      🇸🇪 ISK: {isk.product_type.value} | Net edge: {isk.net_edge_after_isk:.2%}")
            
            print(f"   Entry: {r.entry_recommendation}")
            print()
    else:
        print("\n" + "="*80)
        print("🚀 INVESTERBARA")
        print("="*80)
        print("\n❌ Inga investerbara signaler idag.")
        print("   → Alla signaler blockerade av courtage/FX-kostnader.\n")
    
    # ========================================================================
    # 📋 BEVAKNINGSLISTA - Minimal info (Teknisk signal men blockerad)
    # ========================================================================
    if watchlist:
        print("\n" + "="*80)
        print("📋 BEVAKNINGSLISTA (Teknisk signal men blockerad av kostnader)")
        print("="*80 + "\n")
        
        for r in watchlist:
            # Get primary blocking reason
            # Check if signal was blocked before Execution Guard (by screener)
            if "BLOCK" in r.entry_recommendation:
                # Extract reason from entry_recommendation (e.g., "BLOCK - Position too small for viable courtage")
                block_reason = r.entry_recommendation.replace("BLOCK - ", "")
            elif hasattr(r, 'exec_result'):
                # Blocked by Execution Guard
                exec_result = r.exec_result
                if "AVSTÅ" in exec_result.avanza_recommendation:
                    block_reason = exec_result.warnings[0] if exec_result.warnings else "Courtage-spärr"
                else:
                    block_reason = "Negativ net edge efter kostnader"
            else:
                block_reason = "Blockerad av filter"
            
            print(f"• {r.ticker:10s} | {r.signal.name:6s} | Teknisk: {r.net_edge_after_costs:+.1f}% | {block_reason}")
        
        print(f"\n💡 Dessa instrument har tekniska köpsignaler men blir olönsamma på grund av")
        print(f"   Avanzas avgifter (courtage, FX, spread). Vänta på bättre entry eller högre position.\n")
    
    # ========================================================================
    # 2. MARKNADSLÄGE (Snabb överblick)
    # ========================================================================
    print_section("MARKNADSLÄGE", "🌡️")
    
    green = [r for r in results if r.signal.name == "GREEN"]
    yellow = [r for r in results if r.signal.name == "YELLOW"]
    red = [r for r in results if r.signal.name == "RED"]
    
    # All-Weather statistics
    all_weather_results = [r for r in results if is_all_weather(r.ticker)]
    aw_green = [r for r in all_weather_results if r.signal.name == "GREEN"]
    aw_yellow = [r for r in all_weather_results if r.signal.name == "YELLOW"]
    
    total = len(results)
    red_pct = (len(red) / total * 100) if total > 0 else 0
    
    print(f"\nSignaler: 🟢 {len(green)} | 🟡 {len(yellow)} | 🔴 {len(red)}")
    
    if results:
        regime_mult = results[0].regime_multiplier
        if regime_mult <= 0.2:
            regime = "🔴 CRISIS"
            advice = "Minimal exponering (10% max)"
        elif regime_mult <= 0.4:
            regime = "🟠 STRESSED"
            advice = "Försiktig (30% max)"
        elif regime_mult <= 0.7:
            regime = "🟡 CAUTIOUS"
            advice = "Måttlig (50% max)"
        else:
            regime = "🟢 HEALTHY"
            advice = "Normal exponering"
        
        print(f"Regim: {regime}")
        print(f"Rekommendation: {advice}")
        print(f"RED-signaler: {red_pct:.0f}%")
        print()
        print(f"🛡️ All-Weather: {len(all_weather_results)} analyserade")
        print(f"   GREEN/YELLOW: {len(aw_green) + len(aw_yellow)} (får 1.0x multiplier i CRISIS)")
        
        # Show All-Weather opportunities in CRISIS
        if regime_mult <= 0.2 and (aw_green or aw_yellow):
            print(f"\n   🎯 All-Weather opportunities (CRISIS protection):")
            for r in (aw_green + aw_yellow)[:3]:
                print(f"      • {r.ticker}: {r.signal.name} (+{r.net_edge_after_costs:.2f}%)")
    
    # ========================================================================
    # 3. SAFE HAVEN WATCH (Macro indicators)
    # ========================================================================
    print_section("SAFE HAVEN WATCH", "🛡️")
    
    # Initialize macro indicators
    macro = MacroIndicators()
    
    # Analyze yield curve
    yield_curve = macro.analyze_yield_curve()
    if yield_curve:
        print(f"\n📊 Räntekurva (Yield Curve):")
        print(f"   Kort ränta (^IRX): {yield_curve.short_rate:.2f}%")
        print(f"   Lång ränta (^TNX): {yield_curve.long_rate:.2f}%")
        print(f"   Spread: {yield_curve.spread:+.2f}%")
        print(f"   {yield_curve.message}")
    
    # Analyze credit spreads
    credit_spreads = macro.analyze_credit_spreads()
    if credit_spreads:
        print(f"\n💰 Kreditspreadar (Corporate vs Treasury):")
        print(f"   Treasury (TLT): {credit_spreads.treasury_return:+.2f}%")
        print(f"   Corporate (LQD): {credit_spreads.corporate_return:+.2f}%")
        print(f"   Spread: {credit_spreads.spread:+.2f}%")
        print(f"   {credit_spreads.message}")
    
    # Safe haven watch
    sp500_result = next((r for r in results if r.ticker == "^GSPC"), None)
    sp500_signal = sp500_result.signal.name if sp500_result else "RED"
    
    safe_haven_watch = macro.analyze_safe_haven_watch(all_weather_results, sp500_signal)
    print(f"\n🎯 Safe Haven Aktivitet:")
    print(f"   Analyserade: {safe_haven_watch.total_safe_havens}")
    print(f"   GREEN: {safe_haven_watch.green_count} | YELLOW: {safe_haven_watch.yellow_count} | RED: {safe_haven_watch.red_count}")
    print(f"   Styrka: {safe_haven_watch.safe_haven_strength:.0f}%")
    print(f"   {safe_haven_watch.message}")
    
    if safe_haven_watch.top_performers:
        print(f"\n   Top Safe Havens:")
        for ticker, name, edge in safe_haven_watch.top_performers[:3]:
            print(f"      • {ticker}: +{edge:.2f}%")
    
    # Systemic risk score
    if results:
        risk_score, risk_message = macro.get_systemic_risk_score(
            yield_curve, credit_spreads, safe_haven_watch, results[0].regime_multiplier
        )
        print(f"\n🚨 SYSTEMRISK-POIÄNG: {risk_score:.0f}/100")
        print(f"   {risk_message}")
    
    # ========================================================================
    # 4. TOP 3 OPPORTUNITIES (Om några finns)
    # ========================================================================
    if actionable:
        print_section("TOP 3 MÖJLIGHETER", "⭐")
        
        for i, r in enumerate(actionable[:3], 1):
            print(f"\n{i}. {r.name}")
            print(f"   Ticker: {r.ticker}")
            print(f"   Score: {r.final_score:.1f}/100")
            print(f"   Net Edge: {r.net_edge_after_costs:+.2f}%")
            print(f"   Allokering: {r.final_allocation:.2f}%")
            print(f"   Volatilitet: {r.volatility_regime}")
            
            # Execution Guard summary (with ISK optimization)
            exec_result = execution_guard.analyze(
                ticker=r.ticker,
                category=r.category if hasattr(r, 'category') else 'default',
                position_size_pct=r.final_allocation,
                net_edge_pct=r.net_edge_after_costs,
                product_name=r.name,
                holding_period_days=5
            )
            print(f"   Execution Risk: {exec_result.execution_risk_level}")
            if exec_result.warnings:
                print(f"   ⚠️ {exec_result.warnings[0]}")
    
    # ========================================================================
    # 5. VARNINGAR (Om något är viktigt)
    # ========================================================================
    print_section("VARNINGAR", "⚠️")
    
    warnings = []
    
    # Check if market is stressed
    if red_pct > 90:
        warnings.append("Marknad i CRISIS: 90%+ RED signaler")
    
    # Check cost issues
    blocked_by_cost = [r for r in results if "Negative net edge" in r.entry_recommendation]
    if len(blocked_by_cost) > 5:
        warnings.append(f"{len(blocked_by_cost)} signaler blockerade av höga kostnader")
    
    # Check trend issues
    blocked_by_trend = [r for r in results if "Below 200-day MA" in r.entry_recommendation]
    if len(blocked_by_trend) > 5:
        warnings.append(f"{len(blocked_by_trend)} signaler blockerade pga negativ trend")
    
    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")
    else:
        print("  ✅ Inga varningar")
    
    # ========================================================================
    # 6. NÄSTA STEG
    # ========================================================================
    print_section("NÄSTA STEG", "📋")
    
    if actionable:
        print("\n1. Granska top 3 opportunities ovan")
        print("2. Kör Monte Carlo för att validera risk:")
        print("   → python -c \"from src.analysis.monte_carlo import *; ...\"")
        print("3. Placera order för godkända positioner")
    else:
        print("\n1. Inget att göra idag - vänta")
        print("2. Kom tillbaka imorgon")
        print("3. Läs veckorapport på söndag")
    
    # ========================================================================
    # SAVE SUMMARY
    # ========================================================================
    today = datetime.now().strftime("%Y-%m-%d")
    summary_file = f"reports/dashboard_summary_{today}.txt"
    
    # Create simple summary
    summary = f"""
TRADING DASHBOARD - {today}
{'='*60}

ACTION ITEMS:
  Köpsignaler: {len(actionable)}
  Regime: {regime if results else 'N/A'}
  
MARKNADSLÄGE:
  GREEN: {len(green)} | YELLOW: {len(yellow)} | RED: {len(red)}
  RED%: {red_pct:.0f}%
  
TOP OPPORTUNITY:
  {actionable[0].name if actionable else 'Ingen'}
  
VARNINGAR:
  {len(warnings)} aktiva
"""
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\n💾 Dashboard sammanfattning sparad: {summary_file}")
    
    print("\n" + "🎯 "*20)
    print("          Dashboard klar!")
    print("🎯 "*20 + "\n")

if __name__ == "__main__":
    main()
