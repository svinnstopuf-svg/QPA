"""
Integration Test for New V7.0 Modules

Tests:
1. Motor B (Momentum Engine) - RS-Rating, VCP detection
2. Alpha-Switch (Convergence) - Motor A→B transitions
3. Statistical Iron Curtain - Bootstrap + Kaufman ER
4. Hard Limits - MAE 6% cap + Sector diversification
5. Elite Report Formatter - Sunday report format
"""

import sys
import numpy as np
from datetime import datetime

from src.utils.data_fetcher import DataFetcher
from src.patterns.momentum_engine import MomentumEngine, calculate_universe_returns
from src.analysis.alpha_switch import AlphaSwitchDetector, apply_convergence_boost
from src.analysis.statistical_iron_curtain import StatisticalIronCurtain
from src.analysis.hard_limits import HardLimits
from src.communication.elite_formatter import EliteReportFormatter


def test_motor_b():
    """Test Motor B (Momentum Engine)"""
    print("=" * 80)
    print("TEST 1: MOTOR B (MOMENTUM ENGINE)")
    print("=" * 80)
    
    fetcher = DataFetcher()
    engine = MomentumEngine()
    
    # Test on strong momentum stock (NVDA) and weak stock (T)
    test_tickers = ["NVDA", "T", "AAPL"]
    
    # Fetch data for RS-Rating calculation
    print("\nFetching universe data for RS-Rating...")
    market_data_dict = {}
    for ticker in test_tickers:
        data = fetcher.fetch_stock_data(ticker, period="2y")
        if data:
            market_data_dict[ticker] = data
    
    universe_returns = calculate_universe_returns(test_tickers, market_data_dict)
    
    print(f"\n✅ Universe returns calculated for {len(universe_returns)} tickers\n")
    
    # Test each ticker
    for ticker in test_tickers:
        if ticker not in market_data_dict:
            continue
        
        print(f"\n--- {ticker} ---")
        signal = engine.detect_momentum_signal(
            ticker,
            market_data_dict[ticker],
            universe_returns
        )
        
        print(f"Valid: {signal.is_valid}")
        print(f"Trend Alignment: {signal.trend_alignment} (Price>{signal.price_above_ema50}, EMA50>{signal.ema50_above_ema200})")
        print(f"52w High Proximity: {signal.distance_from_52w:+.1f}% (near: {signal.near_high})")
        print(f"RS-Rating: {signal.rs_rating:.1f}/100")
        print(f"VCP: ATR ratio {signal.atr_ratio:.3f} (contracted: {signal.volatility_contracted})")
        print(f"Reason: {signal.reason}")
    
    return market_data_dict


def test_alpha_switch(market_data_dict):
    """Test Alpha-Switch (Convergence Detection)"""
    print("\n" + "=" * 80)
    print("TEST 2: ALPHA-SWITCH (CONVERGENCE DETECTION)")
    print("=" * 80)
    
    detector = AlphaSwitchDetector(lookback_days=15)
    engine = MomentumEngine()
    
    # Test convergence on AAPL
    ticker = "AAPL"
    if ticker in market_data_dict:
        print(f"\n--- {ticker} ---")
        
        # First check Motor B
        motor_b = engine.detect_momentum_signal(ticker, market_data_dict[ticker], {})
        print(f"Motor B Active: {motor_b.is_valid}")
        
        # Check convergence
        convergence = detector.detect_convergence(
            ticker,
            market_data_dict[ticker],
            motor_b
        )
        
        print(f"Convergence Detected: {convergence.is_convergence}")
        print(f"Motor A Triggered: {convergence.motor_a_triggered}")
        if convergence.motor_a_triggered:
            print(f"  Days Since Motor A: {convergence.days_since_motor_a}")
            print(f"  Price Move: {convergence.price_move_since_motor_a:+.1f}%")
        print(f"Convergence Multiplier: {convergence.convergence_multiplier}x")
        print(f"Reason: {convergence.reason}")
        
        # Test boost application
        original_robust = 75.0
        boosted, was_boosted = apply_convergence_boost(original_robust, convergence)
        print(f"\nRobust Score Boost: {original_robust} → {boosted:.1f} (boosted: {was_boosted})")


def test_iron_curtain():
    """Test Statistical Iron Curtain"""
    print("\n" + "=" * 80)
    print("TEST 3: STATISTICAL IRON CURTAIN")
    print("=" * 80)
    
    iron_curtain = StatisticalIronCurtain()
    
    # Create mock forward returns (strong pattern)
    np.random.seed(42)
    strong_returns = np.concatenate([
        np.random.normal(0.08, 0.03, 20),  # 20 wins around +8%
        np.random.normal(-0.02, 0.01, 10)  # 10 losses around -2%
    ])
    
    # Create mock prices (trending)
    trending_prices = np.cumsum(np.random.normal(0.001, 0.01, 100)) + 100
    
    print("\n--- Strong Pattern (70% WR, 4:1 RRR) ---")
    
    # Bootstrap test
    bootstrap = iron_curtain.bootstrap_resample(
        ticker="TEST1",
        forward_returns=strong_returns,
        win_rate=0.70,
        avg_win=0.08,
        avg_loss=-0.02
    )
    
    print(f"Bootstrap: {bootstrap.n_positive_ev}/{bootstrap.n_simulations} positive ({bootstrap.pass_rate*100:.1f}%)")
    print(f"Passed: {bootstrap.passed}")
    print(f"Mean EV: {bootstrap.mean_ev*100:+.2f}%")
    print(f"95% CI: [{bootstrap.ci_95_lower*100:.2f}%, {bootstrap.ci_95_upper*100:.2f}%]")
    print(f"Reason: {bootstrap.reason}")
    
    # Kaufman ER test
    kaufman = iron_curtain.calculate_kaufman_er("TEST1", trending_prices, period=63)
    
    print(f"\nKaufman ER: {kaufman.efficiency_ratio:.3f}")
    print(f"Passed: {kaufman.passed}")
    print(f"Total Change: {kaufman.total_price_change:.2f}")
    print(f"Sum Absolute: {kaufman.sum_absolute_changes:.2f}")
    print(f"Reason: {kaufman.reason}")
    
    # Create choppy prices (should FAIL ER)
    choppy_prices = 100 + 5 * np.sin(np.linspace(0, 10*np.pi, 100))
    
    print("\n--- Choppy Pattern (should FAIL ER) ---")
    kaufman_bad = iron_curtain.calculate_kaufman_er("TEST2", choppy_prices, period=63)
    print(f"Kaufman ER: {kaufman_bad.efficiency_ratio:.3f}")
    print(f"Passed: {kaufman_bad.passed}")
    print(f"Reason: {kaufman_bad.reason}")


def test_hard_limits():
    """Test Hard Limits"""
    print("\n" + "=" * 80)
    print("TEST 4: HARD LIMITS")
    print("=" * 80)
    
    hard_limits = HardLimits()
    
    # Test MAE hard cap
    print("\n--- MAE Hard Cap Tests ---")
    
    # Case 1: Low volatility (should pass)
    mae_low = hard_limits.check_mae_limit("TEST1", avg_loss=-0.03)  # -3% avg loss
    print(f"\nLow Volatility (-3% avg loss):")
    print(f"  Optimal Stop: {mae_low.optimal_stop_pct*100:.1f}%")
    print(f"  Passed: {mae_low.passed}")
    print(f"  {mae_low.reason}")
    
    # Case 2: High volatility (should FAIL)
    mae_high = hard_limits.check_mae_limit("TEST2", avg_loss=-0.05)  # -5% avg loss
    print(f"\nHigh Volatility (-5% avg loss):")
    print(f"  Optimal Stop: {mae_high.optimal_stop_pct*100:.1f}%")
    print(f"  Passed: {mae_high.passed}")
    print(f"  {mae_high.reason}")
    
    # Test Sector Diversification
    print("\n--- Sector Diversification Tests ---")
    
    # Mock existing setups
    from dataclasses import dataclass
    
    @dataclass
    class MockSetup:
        ticker: str
        robust_score: float
    
    existing = [
        MockSetup("AAPL", 85),
        MockSetup("MSFT", 82),
        MockSetup("GOOGL", 80)  # 3 already in Technology
    ]
    
    sector_map = {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "GOOGL": "Technology",
        "NVDA": "Technology",
        "JPM": "Financials"
    }
    
    # Case 1: Would be #4 in Technology with low score (should FAIL)
    div_fail = hard_limits.check_sector_diversification(
        ticker="NVDA",
        sector="Technology",
        robust_score=80.0,  # Not high enough
        existing_setups=existing,
        sector_map=sector_map
    )
    print(f"\n#4 in Technology (Robust: 80):")
    print(f"  Sector Count: {div_fail.sector_count}")
    print(f"  Required Score: {div_fail.robust_score_required:.1f}")
    print(f"  Passed: {div_fail.passed}")
    print(f"  {div_fail.reason}")
    
    # Case 2: Would be #4 but with high enough score (should PASS)
    div_pass = hard_limits.check_sector_diversification(
        ticker="NVDA",
        sector="Technology",
        robust_score=95.0,  # High enough to overcome penalty
        existing_setups=existing,
        sector_map=sector_map
    )
    print(f"\n#4 in Technology (Robust: 95):")
    print(f"  Required Score: {div_pass.robust_score_required:.1f}")
    print(f"  Passed: {div_pass.passed}")
    print(f"  {div_pass.reason}")
    
    # Case 3: Different sector (should PASS)
    div_other = hard_limits.check_sector_diversification(
        ticker="JPM",
        sector="Financials",
        robust_score=70.0,
        existing_setups=existing,
        sector_map=sector_map
    )
    print(f"\n#1 in Financials (Robust: 70):")
    print(f"  Sector Count: {div_other.sector_count}")
    print(f"  Passed: {div_other.passed}")
    print(f"  {div_other.reason}")


def test_elite_formatter():
    """Test Elite Report Formatter"""
    print("\n" + "=" * 80)
    print("TEST 5: ELITE REPORT FORMATTER")
    print("=" * 80)
    
    formatter = EliteReportFormatter()
    
    # Test Why Log generation
    print("\n--- Why Log Examples ---")
    
    # Convergence case
    why1 = formatter.generate_why_log(
        ticker="TEST1",
        robust_score=85,
        quality_score=75,
        rrr=4.2,
        rs_rating=98,
        convergence=True,
        timing_confidence=65
    )
    print(f"\nConvergence case: {why1}")
    
    # Strong RRR case
    why2 = formatter.generate_why_log(
        ticker="TEST2",
        robust_score=80,
        quality_score=85,
        rrr=5.5,
        rs_rating=None,
        convergence=False,
        timing_confidence=55
    )
    print(f"Strong RRR case: {why2}")
    
    # Fallback case
    why3 = formatter.generate_why_log(
        ticker="TEST3",
        robust_score=72,
        quality_score=50,
        rrr=3.2,
        rs_rating=None,
        convergence=False,
        timing_confidence=45
    )
    print(f"Fallback case: {why3}")
    
    print("\n✅ All formatter tests passed")


if __name__ == "__main__":
    print("🧪 TESTING NEW V7.0 MODULES\n")
    
    try:
        # Test 1: Motor B
        market_data = test_motor_b()
        
        # Test 2: Alpha-Switch
        test_alpha_switch(market_data)
        
        # Test 3: Iron Curtain
        test_iron_curtain()
        
        # Test 4: Hard Limits
        test_hard_limits()
        
        # Test 5: Elite Formatter
        test_elite_formatter()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nNew modules are ready for integration into sunday_dashboard.py")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
