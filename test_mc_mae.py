"""
Quick test of Monte Carlo and MAE calculations.
"""

# Mock setup data
class MockSetup:
    def __init__(self, ticker, win_rate, rrr, avg_win, avg_loss, ev, position_size_sek):
        self.ticker = ticker
        self.win_rate_63d = win_rate
        self.risk_reward_ratio = rrr
        self.avg_win = avg_win
        self.avg_loss = avg_loss
        self.expected_value = ev
        self.position_size_sek = position_size_sek

# Test cases from actual Sunday Dashboard results
test_setups = [
    MockSetup("BSX", 1.00, 10.94, 0.14, -0.01, 0.14, 3000),  # 100% WR, great RRR
    MockSetup("NMAN", 0.917, 5.33, 0.0826, -0.015, 0.0826, 3000),  # 91.7% WR
    MockSetup("CRM", 0.727, 6.71, 0.0705, -0.01, 0.0705, 2500),  # 72.7% WR
    MockSetup("LOW_WR", 0.55, 2.5, 0.05, -0.02, 0.01, 2000),  # Low win rate
]

print("="*80)
print("MONTE CARLO & MAE TEST")
print("="*80)

for setup in test_setups:
    print(f"\n{'-'*80}")
    print(f"Testing: {setup.ticker}")
    print(f"  Win Rate: {setup.win_rate_63d*100:.1f}%")
    print(f"  RRR: 1:{setup.risk_reward_ratio:.2f}")
    print(f"  Avg Win: {setup.avg_win*100:+.2f}%")
    print(f"  Avg Loss: {setup.avg_loss*100:+.2f}%")
    
    # MONTE CARLO CALCULATION
    if setup.risk_reward_ratio >= 4.0:
        rrr_factor = 0.5
    elif setup.risk_reward_ratio >= 3.0:
        rrr_factor = 0.7
    elif setup.risk_reward_ratio >= 2.0:
        rrr_factor = 0.9
    else:
        rrr_factor = 1.2
    
    base_stopout_prob = (1.0 - setup.win_rate_63d)
    stop_out_probability = min(0.95, base_stopout_prob * rrr_factor)
    
    expected_final_value = setup.position_size_sek * (1 + setup.expected_value)
    
    print(f"\n  Monte Carlo Results:")
    print(f"    Stop-Out Probability: {stop_out_probability*100:.1f}%")
    print(f"    Expected Final Value: {expected_final_value:,.0f} SEK")
    
    if stop_out_probability > 0.30:
        print(f"    ⚠️ High stop-out risk!")
    else:
        print(f"    ✓ Acceptable risk")
    
    # MAE CALCULATION
    if setup.avg_loss < 0:
        optimal_stop_pct = abs(setup.avg_loss) * 1.5
    else:
        optimal_stop_pct = 0.015
    
    if optimal_stop_pct > 0 and setup.avg_win > 0:
        mae_based_rrr = setup.avg_win / optimal_stop_pct
    else:
        mae_based_rrr = setup.risk_reward_ratio
    
    print(f"\n  MAE Results:")
    print(f"    Optimal Stop-Loss: {optimal_stop_pct*100:.1f}%")
    print(f"    MAE-Based RRR: 1:{mae_based_rrr:.2f}")

print(f"\n{'='*80}")
print("\nEXPECTED BEHAVIOR:")
print("- BSX (100% WR, RRR 10.94): Stop-out ~0%, MAE stop ~1.5%")
print("- NMAN (91.7% WR, RRR 5.33): Stop-out ~4.2%, MAE stop ~2.3%")
print("- CRM (72.7% WR, RRR 6.71): Stop-out ~13.6%, MAE stop ~1.5%")
print("- LOW_WR (55% WR, RRR 2.5): Stop-out ~40.5%, MAE stop ~3.0%")
print("\n✓ Values should now VARY based on win rate and RRR!")
print("="*80)
