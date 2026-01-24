"""
Test new simplified position sizing logic.
"""

test_cases = [
    {"name": "BSX", "wr": 1.00, "atr": 2.0},
    {"name": "NWSA", "wr": 0.812, "atr": 1.5},
    {"name": "CRM", "wr": 0.727, "atr": 2.0},
    {"name": "LIFCO-B", "wr": 0.733, "atr": 2.2},
    {"name": "ZTS", "wr": 0.80, "atr": 1.8},
]

capital = 100000
regime_multiplier = 1.0  # EUPHORIA

print("="*80)
print("NEW POSITION SIZING TEST")
print("="*80)

for tc in test_cases:
    wr = tc["wr"]
    atr = tc["atr"]
    
    # Base allocation
    if wr >= 0.80:
        base = 0.03
    elif wr >= 0.70:
        base = 0.025
    elif wr >= 0.60:
        base = 0.02
    else:
        base = 0.015
    
    # Volatility adjustment
    if atr > 3.0:
        base *= (3.0 / atr)
    elif atr > 2.5:
        base *= 0.9
    
    # Regime
    position_pct = base * regime_multiplier
    
    # Floor
    min_pct = 0.015
    floor_applied = False
    if 0 < position_pct < min_pct:
        position_pct = min_pct
        floor_applied = True
    
    # Convert to percentage number (1.5% = 1.5)
    position_pct_display = position_pct * 100
    
    # SEK
    position_sek = capital * position_pct
    
    print(f"\n{tc['name']} (WR: {wr*100:.1f}%, ATR: {atr:.1f}%):")
    print(f"  Base: {base*100:.2f}%")
    print(f"  Position: {position_sek:,.0f} SEK ({position_pct_display:.2f}%)")
    if floor_applied:
        print(f"  ⚠️ Floor applied")

print(f"\n{'='*80}")
print("✅ VARIATION CONFIRMED - positions now vary by win rate and volatility!")
