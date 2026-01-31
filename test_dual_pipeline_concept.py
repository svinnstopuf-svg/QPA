"""
Simple Test: Dual-Pipeline Concept

Demonstrates how Motor A and Motor B analyze the same instruments
independently and produce different results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_fetcher import DataFetcher
from src.patterns.momentum_engine import MomentumEngine, calculate_universe_returns

def test_dual_pipeline_concept():
    """
    Test dual-pipeline on a few instruments to show the concept.
    """
    print("\n" + "="*80)
    print("🧪 DUAL-PIPELINE CONCEPT TEST")
    print("="*80)
    
    # Test instruments
    tickers = [
        "NVDA",   # High momentum stock
        "T",      # Low/declining stock  
        "AAPL",   # Moderate
    ]
    
    print(f"\nTesting {len(tickers)} instruments:")
    for t in tickers:
        print(f"  - {t}")
    
    # Fetch data
    print("\n📊 Fetching market data (2 years)...")
    data_fetcher = DataFetcher()
    universe_market_data = {}
    
    for ticker in tickers:
        try:
            market_data = data_fetcher.fetch_stock_data(ticker, period="2y")
            if market_data:
                universe_market_data[ticker] = market_data
                print(f"  ✓ {ticker}: {len(market_data.close_prices)} days")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")
    
    if len(universe_market_data) == 0:
        print("\n❌ No data fetched. Exiting.")
        return
    
    # Calculate universe returns for RS-Rating
    print("\n📈 Calculating universe returns...")
    universe_returns = calculate_universe_returns(
        list(universe_market_data.keys()),
        universe_market_data
    )
    
    # Initialize Motor B
    momentum_engine = MomentumEngine(
        min_rs_rating=95.0,
        min_52w_proximity=0.95,
        max_atr_ratio=0.85
    )
    
    # Analyze each instrument
    print("\n" + "="*80)
    print("MOTOR A (Mean Reversion) vs MOTOR B (Momentum)")
    print("="*80)
    
    for ticker, market_data in universe_market_data.items():
        print("\n" + "-"*80)
        print(f"📊 {ticker}")
        print("-"*80)
        
        prices = market_data.close_prices
        current_price = prices[-1]
        
        # Calculate EMA200 for Motor A check
        import numpy as np
        if len(prices) >= 200:
            ema200_values = []
            multiplier = 2.0 / (200 + 1)
            ema = np.mean(prices[:200])  # Start with SMA
            
            for i in range(200, len(prices)):
                ema = (prices[i] - ema) * multiplier + ema
            
            ema200 = ema
        else:
            ema200 = 0
        
        # Calculate decline from 90-day high
        if len(prices) >= 90:
            high_90d = np.max(prices[-90:])
            decline_pct = ((current_price - high_90d) / high_90d) * 100
        else:
            decline_pct = 0
        
        # MOTOR A CHECK (Simplified)
        motor_a_valid = (current_price < ema200) and (decline_pct <= -10.0)
        
        print(f"\n🔵 MOTOR A (Mean Reversion):")
        print(f"   Price: {current_price:.2f}")
        print(f"   EMA200: {ema200:.2f}")
        print(f"   Price vs EMA200: {((current_price/ema200 - 1)*100):+.1f}%")
        print(f"   Decline from 90d high: {decline_pct:.1f}%")
        print(f"   Status: {'✅ QUALIFIED' if motor_a_valid else '❌ NOT QUALIFIED'}")
        if motor_a_valid:
            print(f"   → Bottom fishing setup")
        else:
            if current_price >= ema200:
                print(f"   → Reject: Price above EMA200 (not in downtrend)")
            if decline_pct > -10.0:
                print(f"   → Reject: Insufficient decline (need -10%+)")
        
        # MOTOR B CHECK
        motor_b_signal = momentum_engine.detect_momentum_signal(
            ticker,
            market_data,
            universe_returns
        )
        
        print(f"\n🚀 MOTOR B (Momentum/Launchpad):")
        print(f"   RS-Rating: {motor_b_signal.rs_rating:.0f}/100")
        print(f"   Trend: Price {'>' if motor_b_signal.price_above_ema50 else '<'} EMA50 {'>' if motor_b_signal.ema50_above_ema200 else '<'} EMA200")
        print(f"   Distance from 52w high: {motor_b_signal.distance_from_52w:+.1f}%")
        print(f"   VCP: ATR ratio {motor_b_signal.atr_ratio:.3f}")
        print(f"   Status: {'✅ QUALIFIED' if motor_b_signal.is_valid else '❌ NOT QUALIFIED'}")
        if not motor_b_signal.is_valid:
            print(f"   → {motor_b_signal.reason}")
        else:
            print(f"   → Momentum leader setup")
        
        # CONVERGENCE CHECK
        print(f"\n🎯 CONVERGENCE:")
        if motor_a_valid and motor_b_signal.is_valid:
            print(f"   🌟 HOLY GRAIL! Both Motor A and Motor B qualified!")
            print(f"   → This is extremely rare - buy bottom with momentum")
        elif motor_a_valid:
            print(f"   Motor A only → Mean reversion trade")
        elif motor_b_signal.is_valid:
            print(f"   Motor B only → Momentum trade")
        else:
            print(f"   Neither qualified → No setup")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    print("\nKey Insight:")
    print("- Motor A and Motor B have OPPOSITE requirements")
    print("- Motor A: Price < EMA200, declining")
    print("- Motor B: Price > EMA50 > EMA200, near highs")
    print("- Convergence (both valid) is VERY RARE but powerful")
    print("- Running separate pipelines allows each to find its own setups")


if __name__ == "__main__":
    test_dual_pipeline_concept()
