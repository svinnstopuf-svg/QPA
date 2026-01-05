"""
🎯 TRADING DASHBOARD - Allt du behöver veta på EN sida

Kör detta VARJE DAG för att få översikt.
"""

from instrument_screener_v22 import InstrumentScreenerV22, format_v22_report
from instruments_universe import get_all_instruments
from src.risk.all_weather_config import (
    is_all_weather, get_all_weather_category, get_avanza_alternative,
    is_defensive_sector
)
from src.analysis.macro_indicators import MacroIndicators
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
    
    # Run screening
    print("\n⏳ Analyserar 250 instruments...")
    screener = InstrumentScreenerV22(enable_v22_filters=True)
    instruments = get_all_instruments()
    results = screener.screen_instruments(instruments)
    
    # Create reports dir
    os.makedirs("reports", exist_ok=True)
    
    # ========================================================================
    # 1. DAGENS ACTION ITEMS (Viktigast!)
    # ========================================================================
    print_section("DAGENS ACTION ITEMS", "🎯")
    
    actionable = [r for r in results if r.entry_recommendation.startswith("ENTER")]
    
    # Prioritize All-Weather during CRISIS
    if results and results[0].regime_multiplier <= 0.2:  # CRISIS
        # Separate All-Weather from normal
        all_weather = [r for r in actionable if is_all_weather(r.ticker)]
        normal = [r for r in actionable if not is_all_weather(r.ticker)]
        actionable = all_weather + normal  # All-Weather first
    
    if actionable:
        print(f"\n✅ {len(actionable)} KÖPSIGNALER idag:\n")
        for i, r in enumerate(actionable[:5], 1):  # Max 5
            # Mark All-Weather instruments
            aw_marker = " 🛡️ [ALL-WEATHER]" if is_all_weather(r.ticker) else ""
            print(f"{i}. {r.name} ({r.ticker}){aw_marker}")
            print(f"   Signal: {r.signal.name}")
            print(f"   Net Edge: {r.net_edge_after_costs:+.2f}%")
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
            
            print(f"   Entry: {r.entry_recommendation}")
            print()
    else:
        print("\n❌ Inga köpsignaler idag.")
        print("   → Vänta. Marknad är i CRISIS-läge.\n")
    
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
