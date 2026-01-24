"""
Debug V-Kelly position sizing to understand why all positions are 5,000 SEK.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.risk.volatility_position_sizing import VolatilityPositionSizer


def main():
    print("="*80)
    print("V-KELLY DEBUG TEST")
    print("="*80)
    
    sizer = VolatilityPositionSizer()
    
    # Test different scenarios
    test_cases = [
        {
            "name": "BSX (100% WR, high quality)",
            "base_allocation": 3.0,  # 3% for 80%+ win rate
            "atr_percent": 2.0,  # Estimated from avg_win/avg_loss
            "signal_strength": "GREEN"
        },
        {
            "name": "NWSA (81% WR, strong)",
            "base_allocation": 3.0,
            "atr_percent": 1.5,
            "signal_strength": "GREEN"
        },
        {
            "name": "CRM (73% WR, good)",
            "base_allocation": 2.5,
            "atr_percent": 2.0,
            "signal_strength": "YELLOW"
        },
        {
            "name": "LIFCO-B (73% WR, good)",
            "base_allocation": 2.5,
            "atr_percent": 2.2,
            "signal_strength": "YELLOW"
        },
        {
            "name": "ZTS (80% WR, strong)",
            "base_allocation": 3.0,
            "atr_percent": 1.8,
            "signal_strength": "GREEN"
        }
    ]
    
    for tc in test_cases:
        print(f"\n{'-'*80}")
        print(f"Test: {tc['name']}")
        print(f"  Base Allocation: {tc['base_allocation']}%")
        print(f"  ATR: {tc['atr_percent']}%")
        print(f"  Signal Strength: {tc['signal_strength']}")
        
        result = sizer.adjust_position_size(
            base_allocation=tc['base_allocation'],
            atr_percent=tc['atr_percent'],
            signal_strength=tc['signal_strength']
        )
        
        print(f"\n  → Volatility Adjusted: {result.volatility_adjusted:.4f}% (as decimal)")
        print(f"  → Risk Units: {result.risk_units:.4f}")
        print(f"  → Recommendation: {result.recommendation}")
        
        # Simulate regime multiplier (EUPHORIA = 1.0x)
        regime_multiplier = 1.0
        final_position_pct = result.volatility_adjusted * regime_multiplier
        
        print(f"\n  After Regime (1.0x): {final_position_pct:.4f}%")
        
        # Check floor (1.5% = 0.015)
        min_position_pct = 0.015
        if 0 < final_position_pct < min_position_pct:
            final_position_pct = min_position_pct
            print(f"  ⚠️ FLOOR APPLIED: Raised to {min_position_pct*100:.2f}%")
        
        # Calculate SEK
        capital = 100000
        position_sek = capital * final_position_pct
        
        print(f"\n  FINAL: {position_sek:,.0f} SEK ({final_position_pct*100:.2f}%)")
    
    print(f"\n{'='*80}")
    print("\nCONCLUSION:")
    print("If all positions are 5,000 SEK (5%), then V-Kelly is hitting max_position cap")
    print("This means target_volatility / atr_percent is always >= 5%")
    print(f"\nWith target_volatility = {sizer.target_volatility}%:")
    print(f"  ATR 1.0% → {sizer.target_volatility / 1.0 * 100:.1f}% position (capped at 5%)")
    print(f"  ATR 1.5% → {sizer.target_volatility / 1.5 * 100:.1f}% position (capped at 5%)")
    print(f"  ATR 2.0% → {sizer.target_volatility / 2.0 * 100:.1f}% position (capped at 5%)")
    print(f"  ATR 3.0% → {sizer.target_volatility / 3.0 * 100:.1f}% position")
    print("\nNEED ATR > 1% to get positions < 5%!")


if __name__ == "__main__":
    main()
