"""
🎯 TRADING DASHBOARD - Allt du behöver veta på EN sida

Kör detta VARJE DAG för att få översikt.
"""

from instrument_screener_v22 import InstrumentScreenerV22, format_v22_report
from instruments_universe import get_all_instruments
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
    
    if actionable:
        print(f"\n✅ {len(actionable)} KÖPSIGNALER idag:\n")
        for i, r in enumerate(actionable[:5], 1):  # Max 5
            print(f"{i}. {r.name} ({r.ticker})")
            print(f"   Signal: {r.signal.name}")
            print(f"   Net Edge: {r.net_edge_after_costs:+.2f}%")
            print(f"   Position: {r.final_allocation:.2f}%")
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
    
    # ========================================================================
    # 3. TOP 3 OPPORTUNITIES (Om några finns)
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
    # 4. VARNINGAR (Om något är viktigt)
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
    # 5. NÄSTA STEG
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
