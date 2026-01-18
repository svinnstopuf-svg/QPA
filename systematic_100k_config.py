"""
100K SYSTEMATIC OVERLAY CONFIGURATION
=====================================

Portfolio: 100,000 SEK
Strategy: Systematic growth with cost-efficient position sizing
Broker: Avanza (ISK account with MINI courtage: 1 SEK min)

POSITION SIZING RULES:
"""

# Portfolio parameters
PORTFOLIO_VALUE_SEK = 100000
BASE_UNIT_SEK = 1500  # 1.5% risk unit
MIN_POSITION_SEK = 1500  # Floor for cost efficiency
MIN_POSITION_PCT = 1.5  # As percentage

# Courtage analysis at 1500 SEK position
COURTAGE_PER_TRADE = 1  # Avanza MINI
ROUNDTRIP_COST = 2  # Buy + Sell
COURTAGE_PCT_AT_FLOOR = 0.13  # 2 SEK / 1500 SEK = 0.13%

# Regime-specific rules
REGIME_RULES = {
    'CRISIS': {
        'max_position_sek': 1500,  # Keep at floor in crisis
        'max_position_pct': 1.5,
        'allow_vkelly_scaling': False,  # Do NOT scale above floor
        'description': 'Minimal exposure - hold 1500 SEK floor only'
    },
    'STRESSED': {
        'max_position_sek': 2500,  # Allow some scaling
        'max_position_pct': 2.5,
        'allow_vkelly_scaling': True,  # Limited scaling
        'description': 'Conservative scaling - up to 2500 SEK'
    },
    'CAUTIOUS': {
        'max_position_sek': 3500,
        'max_position_pct': 3.5,
        'allow_vkelly_scaling': True,
        'description': 'Moderate scaling - up to 3500 SEK'
    },
    'HEALTHY': {
        'max_position_sek': 5000,  # Max individual position
        'max_position_pct': 5.0,
        'allow_vkelly_scaling': True,  # Full V-Kelly
        'description': 'Full V-Kelly scaling - up to 5000 SEK (5%)'
    }
}

# Diversification limits
MAX_SIMULTANEOUS_POSITIONS = 30  # Never more than 30 positions
IDEAL_POSITIONS = 20  # Target 20 positions for focus
MIN_POSITIONS_FOR_DIVERSIFICATION = 5  # At least 5 for risk spread

# Breakeven thresholds (adjusted for 1500 SEK floor)
BREAKEVEN_THRESHOLDS = {
    'swedish_stock': 0.13,  # Must beat 0.13% courtage cost
    'foreign_stock': 0.63,  # 0.13% courtage + 0.5% FX
    'all_weather': 0.63,   # Higher due to FX + ISK routing
}

# Position sizing logic
def calculate_position_size(
    v_kelly_position_pct: float,
    regime: str,
    portfolio_value: float = PORTFOLIO_VALUE_SEK
) -> tuple[float, str]:
    """
    Calculate actual position size with 100k Systematic rules.
    
    Args:
        v_kelly_position_pct: V-Kelly suggested position %
        regime: Current market regime (CRISIS/STRESSED/CAUTIOUS/HEALTHY)
        portfolio_value: Portfolio value in SEK
        
    Returns:
        (position_sek, reasoning)
    """
    regime_config = REGIME_RULES.get(regime, REGIME_RULES['CRISIS'])
    v_kelly_sek = (v_kelly_position_pct / 100) * portfolio_value
    
    # Rule 1: Enforce floor
    if v_kelly_sek < MIN_POSITION_SEK:
        position_sek = MIN_POSITION_SEK
        reasoning = f"V-Kelly {v_kelly_sek:.0f} SEK < floor → using {MIN_POSITION_SEK} SEK (0.13% courtage)"
    
    # Rule 2: Check regime ceiling
    elif regime_config['allow_vkelly_scaling']:
        position_sek = min(v_kelly_sek, regime_config['max_position_sek'])
        if position_sek == regime_config['max_position_sek']:
            reasoning = f"V-Kelly {v_kelly_sek:.0f} SEK capped at {regime} ceiling: {position_sek:.0f} SEK"
        else:
            reasoning = f"V-Kelly {v_kelly_sek:.0f} SEK → using full V-Kelly in {regime}"
    
    # Rule 3: CRISIS locks at floor
    else:
        position_sek = MIN_POSITION_SEK
        reasoning = f"{regime}: locked at floor {MIN_POSITION_SEK} SEK (minimal exposure)"
    
    return position_sek, reasoning


# Position acceptance criteria
def is_position_acceptable(
    net_edge_pct: float,
    instrument_type: str,
    conviction_score: float,
    days_investable: int,
    total_positions: int
) -> tuple[bool, str]:
    """
    Determine if position meets 100k Systematic criteria.
    
    Returns:
        (accept: bool, reason: str)
    """
    # Check 1: Diversification limit
    if total_positions >= MAX_SIMULTANEOUS_POSITIONS:
        return False, f"Portfolio full ({total_positions}/{MAX_SIMULTANEOUS_POSITIONS} positions)"
    
    # Check 2: Cost breakeven
    breakeven = BREAKEVEN_THRESHOLDS.get(instrument_type, BREAKEVEN_THRESHOLDS['foreign_stock'])
    if net_edge_pct < breakeven:
        return False, f"Net edge {net_edge_pct:.2f}% < breakeven {breakeven:.2f}%"
    
    # Check 3: Conviction threshold (with 1500 SEK floor, we can be selective)
    # BUY requires: Score >= 50 AND days_investable >= 5
    # STRONG BUY requires: Score >= 70 AND days_investable >= 10
    if conviction_score < 50:
        return False, f"Conviction {conviction_score:.1f}/100 < 50 (minimum for BUY)"
    
    if conviction_score >= 70 and days_investable >= 10:
        return True, "STRONG BUY: High conviction + consistent performance"
    elif conviction_score >= 50 and days_investable >= 5:
        return True, "BUY: Good conviction + reasonable consistency"
    else:
        return False, f"Consistency too low ({days_investable} days investable, need ≥5)"


# Example usage
if __name__ == "__main__":
    print("100K SYSTEMATIC OVERLAY - Configuration")
    print("=" * 60)
    print(f"Portfolio: {PORTFOLIO_VALUE_SEK:,} SEK")
    print(f"Base Unit: {BASE_UNIT_SEK} SEK (1.5%)")
    print(f"Min Position: {MIN_POSITION_SEK} SEK (0.13% courtage)")
    print(f"Max Positions: {MAX_SIMULTANEOUS_POSITIONS}")
    print()
    
    print("REGIME-SPECIFIC RULES:")
    for regime, config in REGIME_RULES.items():
        print(f"\n{regime}:")
        print(f"  Max Position: {config['max_position_sek']} SEK ({config['max_position_pct']}%)")
        print(f"  V-Kelly Scaling: {'Enabled' if config['allow_vkelly_scaling'] else 'Disabled'}")
        print(f"  {config['description']}")
    
    print("\n" + "=" * 60)
    print("BREAKEVEN THRESHOLDS:")
    for inst_type, threshold in BREAKEVEN_THRESHOLDS.items():
        print(f"  {inst_type}: {threshold:.2f}%")
    
    print("\n" + "=" * 60)
    print("EXAMPLE CALCULATIONS:")
    
    # Test cases
    test_cases = [
        (0.5, 'CRISIS', "Small V-Kelly in CRISIS"),
        (2.0, 'CRISIS', "Medium V-Kelly in CRISIS"),
        (3.0, 'HEALTHY', "Medium V-Kelly in HEALTHY"),
        (6.0, 'HEALTHY', "Large V-Kelly in HEALTHY (capped)"),
    ]
    
    for v_kelly_pct, regime, description in test_cases:
        position_sek, reasoning = calculate_position_size(v_kelly_pct, regime)
        print(f"\n{description}:")
        print(f"  Input: {v_kelly_pct}% V-Kelly, {regime} regime")
        print(f"  Output: {position_sek:.0f} SEK ({position_sek/PORTFOLIO_VALUE_SEK*100:.2f}%)")
        print(f"  {reasoning}")
