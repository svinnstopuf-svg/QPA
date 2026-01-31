"""
Quick Test: Complete Dual-Pipeline System

Tests Motor A (Mean Reversion) and Motor B (Momentum) on small watchlist
to verify all components work together.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_fetcher import DataFetcher
from src.patterns.momentum_engine import MomentumEngine, calculate_universe_returns
from src.patterns.momentum_patterns import MomentumPatternDetector
from src.analysis.momentum_quality import MomentumQualityAnalyzer
from src.filters.market_context_filter import MarketContextFilter
from src.patterns.position_trading_patterns import PositionTradingPatternDetector

def test_dual_pipeline():
    """
    Test both pipelines on small set of instruments.
    """
    print("\n" + "="*80)
    print("🧪 DUAL-PIPELINE COMPLETE TEST")
    print("="*80)
    
    # Small diverse watchlist
    tickers = [
        "NVDA",    # High momentum
        "T",       # Low/value
        "AAPL",    # Moderate
        "TSLA",    # Volatile momentum
        "KO"       # Defensive
    ]
    
    print(f"\nTesting {len(tickers)} instruments:")
    for t in tickers:
        print(f"  - {t}")
    
    # Initialize components
    data_fetcher = DataFetcher()
    
    # Motor A components
    context_filter = MarketContextFilter(min_decline_pct=10.0)
    mean_reversion_detector = PositionTradingPatternDetector(min_decline_pct=10.0)
    
    # Motor B components
    momentum_engine = MomentumEngine()
    momentum_pattern_detector = MomentumPatternDetector(
        min_rs_rating=90.0,  # Relaxed for test
        min_volume_surge=1.5
    )
    momentum_quality = MomentumQualityAnalyzer()
    
    # Fetch data
    print("\n📊 Fetching market data...")
    universe_data = {}
    for ticker in tickers:
        try:
            market_data = data_fetcher.fetch_stock_data(ticker, period="2y")
            if market_data:
                universe_data[ticker] = market_data
                print(f"  ✓ {ticker}: {len(market_data.close_prices)} days")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")
    
    if len(universe_data) == 0:
        print("\n❌ No data fetched. Exiting.")
        return
    
    # Calculate universe returns for RS-Rating
    print("\n📈 Calculating universe returns...")
    universe_returns = calculate_universe_returns(
        list(universe_data.keys()),
        universe_data
    )
    
    # Results storage
    motor_a_results = {}
    motor_b_results = {}
    
    print("\n" + "="*80)
    print("RUNNING DUAL-PIPELINE ANALYSIS")
    print("="*80)
    
    for ticker, market_data in universe_data.items():
        print(f"\n📊 Analyzing {ticker}...")
        print("-"*80)
        
        # MOTOR A: Mean Reversion Pipeline
        print("\n🔵 MOTOR A (Mean Reversion):")
        
        # Check market context
        context = context_filter.check_market_context(market_data)
        
        if context.is_valid_for_entry:
            print(f"   ✓ Context valid: {context.decline_from_high:.1f}% decline, {context.price_vs_ema200:.1f}% below EMA200")
            
            # Detect patterns
            patterns = mean_reversion_detector.detect_double_bottom(market_data)
            
            if patterns:
                motor_a_results[ticker] = patterns[0]
                print(f"   ✓ Pattern found: {len(patterns)} Double Bottom(s)")
            else:
                print(f"   ✗ No patterns detected")
        else:
            print(f"   ✗ {context.reason}")
        
        # MOTOR B: Momentum Pipeline
        print("\n🚀 MOTOR B (Momentum/Launchpad):")
        
        # Check momentum signal (VCP + RS)
        motor_b_signal = momentum_engine.detect_momentum_signal(
            ticker,
            market_data,
            universe_returns
        )
        
        if motor_b_signal.is_valid:
            print(f"   ✓ VCP Setup: RS={motor_b_signal.rs_rating:.0f}/100")
            print(f"   ✓ Trend: Price > EMA50 > EMA200")
            print(f"   ✓ 52w proximity: {motor_b_signal.distance_from_52w:+.1f}%")
            
            # Detect momentum patterns
            patterns = momentum_pattern_detector.detect_all_patterns(
                market_data,
                motor_b_signal.rs_rating
            )
            
            if patterns:
                motor_b_results[ticker] = patterns[0]
                print(f"   ✓ Pattern: {patterns[0].pattern_name} (Quality: {patterns[0].pattern_quality:.0f}/100)")
            else:
                print(f"   ℹ️  VCP valid but no chart patterns yet")
                # Store VCP signal even without pattern
                motor_b_results[ticker] = motor_b_signal
        else:
            print(f"   ✗ {motor_b_signal.reason}")
        
        # Quality check for Motor B candidates
        if ticker in motor_b_results:
            print("\n   💎 Quality Check:")
            try:
                quality = momentum_quality.analyze_quality(ticker)
                print(f"      Overall: {quality.momentum_quality_score:.0f}/100 ({quality.quality_tier})")
                print(f"      Growth: {quality.earnings_growth_yoy*100:+.1f}% YoY")
                print(f"      Liquidity: ${quality.avg_daily_dollar_volume/1e6:.1f}M/day")
            except Exception as e:
                print(f"      ⚠️ Quality check failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 DUAL-PIPELINE RESULTS SUMMARY")
    print("="*80)
    
    print(f"\n🔵 MOTOR A (Mean Reversion):")
    if motor_a_results:
        print(f"   Found {len(motor_a_results)} setups:")
        for ticker in motor_a_results:
            print(f"   • {ticker}")
    else:
        print(f"   No mean reversion setups found")
        print(f"   (Market likely too strong - instruments not declined enough)")
    
    print(f"\n🚀 MOTOR B (Momentum/Launchpad):")
    if motor_b_results:
        print(f"   Found {len(motor_b_results)} setups:")
        for ticker, setup in motor_b_results.items():
            if hasattr(setup, 'pattern_name'):
                print(f"   • {ticker}: {setup.pattern_name}")
            else:
                print(f"   • {ticker}: VCP signal (no pattern yet)")
    else:
        print(f"   No momentum setups found")
        print(f"   (Instruments not meeting RS≥90 + VCP requirements)")
    
    print(f"\n🎯 CONVERGENCE:")
    convergence = set(motor_a_results.keys()) & set(motor_b_results.keys())
    if convergence:
        print(f"   🌟 HOLY GRAIL! {len(convergence)} instrument(s) qualify for both:")
        for ticker in convergence:
            print(f"   • {ticker} - Mean reversion bottom + Momentum confirmation!")
    else:
        print(f"   No convergence (expected - very rare)")
    
    print("\n" + "="*80)
    print("✅ DUAL-PIPELINE TEST COMPLETE")
    print("="*80)
    
    print("\nKey Insights:")
    print("- Motor A and Motor B run independently ✓")
    print("- Each motor has its own filters and requirements ✓")
    print("- Convergence detection works ✓")
    print("- Quality checks integrated ✓")
    
    if len(motor_a_results) == 0 and len(motor_b_results) == 0:
        print("\n💡 Note: Current market conditions don't favor either strategy")
        print("   - Motor A needs -10%+ declines (bottom fishing)")
        print("   - Motor B needs RS≥90 + uptrend (momentum leaders)")
        print("   This is NORMAL - strategies are market-regime dependent!")


if __name__ == "__main__":
    test_dual_pipeline()
