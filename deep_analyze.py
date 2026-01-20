"""
Deep Comprehensive Analysis - Shows All Calculations
"""
import sys
import numpy as np
from instrument_screener_v22 import InstrumentScreenerV22
from src.utils.data_fetcher import DataFetcher
from src.analysis.bayesian_estimator import BayesianEdgeEstimator
from src.risk.volatility_position_sizing import VolatilityPositionSizer
from src.risk.trend_filter import TrendFilter
from src.entry.volatility_breakout import VolatilityBreakoutFilter
from src.risk.cost_aware_filter import CostAwareFilter
from src.filters.rvol_filter import RVOLFilter

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NOLA-B.ST"
    name = sys.argv[2] if len(sys.argv) > 2 else "Nolato B"
    
    print(f"\n{'#'*80}")
    print(f"#  COMPREHENSIVE DEEP ANALYSIS: {name} ({ticker})")
    print(f"{'#'*80}\n")
    
    # Initialize components
    data_fetcher = DataFetcher()
    screener = InstrumentScreenerV22(enable_v22_filters=True)
    bayesian = BayesianEdgeEstimator()
    v_kelly = VolatilityPositionSizer()
    trend_filter = TrendFilter()
    breakout_filter = VolatilityBreakoutFilter()
    cost_filter = CostAwareFilter()
    rvol_filter = RVOLFilter()
    
    # 1. FETCH DATA
    print_section("1️⃣ DATA HÄMTNING")
    market_data = data_fetcher.fetch_stock_data(ticker, period="15y")
    
    if market_data is None:
        print("❌ Kunde inte hämta data")
        return
    
    print(f"✅ Hämtade data för {ticker}")
    print(f"   Datapunkter: {len(market_data)}")
    print(f"   Period: {len(market_data) / 252:.1f} år")
    print(f"   Från: {market_data.timestamps[0].strftime('%Y-%m-%d')}")
    print(f"   Till: {market_data.timestamps[-1].strftime('%Y-%m-%d')}")
    print(f"   Senaste pris: {market_data.close_prices[-1]:.2f} SEK")
    print(f"   Genomsnittlig volym: {market_data.volume.mean():,.0f}")
    
    # 2. PATTERN ANALYSIS
    print_section("2️⃣ PATTERN DETECTION & EDGE BERÄKNING")
    
    from src import QuantPatternAnalyzer
    analyzer = QuantPatternAnalyzer(min_occurrences=5, min_confidence=0.40, forward_periods=1)
    analysis_results = analyzer.analyze_market_data(market_data)
    current_situation = analyzer.get_current_market_situation(market_data, lookback_window=50)
    
    significant_patterns = analysis_results.get('significant_patterns', [])
    print(f"Totalt patterns detekterade: {len(analysis_results.get('results', []))}")
    print(f"Signifikanta patterns: {len(significant_patterns)}\n")
    
    if significant_patterns:
        print("📊 SIGNIFIKANTA MÖNSTER:\n")
        for i, pattern in enumerate(significant_patterns[:5], 1):
            print(f"{i}. {pattern.get('description', 'N/A')}")
            print(f"   Occurrences: {pattern.get('occurrences', 0)}")
            print(f"   Mean Return: {pattern.get('mean_return', 0)*100:+.2f}%")
            print(f"   Win Rate: {pattern.get('win_rate', 0)*100:.1f}%")
            print(f"   Confidence: {pattern.get('confidence', 0):.2f}")
            
            # Bayesian Analysis for this pattern
            if 'forward_returns' in pattern:
                returns = np.array(pattern['forward_returns'])
                bayesian_est = bayesian.estimate_edge(returns)
                print(f"   📈 BAYESIAN EDGE:")
                print(f"      Point Estimate: {bayesian_est.point_estimate:+.3%}")
                print(f"      95% CI: [{bayesian_est.credible_interval_95[0]:+.3%}, {bayesian_est.credible_interval_95[1]:+.3%}]")
                print(f"      P(edge > 0): {bayesian_est.probability_positive:.1%}")
                print(f"      Survivorship-Adjusted: {bayesian_est.bias_adjusted_edge:+.3%}")
                print(f"      Sample Size: {bayesian_est.sample_size}")
                print(f"      Uncertainty: {bayesian_est.uncertainty_level.upper()}")
            print()
    
    # Find best edge
    best_edge = 0.0
    best_pattern_name = "Inget"
    for pattern in significant_patterns:
        if 'mean_return' in pattern:
            edge = pattern['mean_return'] * 100
            if abs(edge) > abs(best_edge):
                best_edge = edge
                best_pattern_name = pattern.get('description', 'Inget')
    
    print(f"🎯 BÄSTA PATTERN: {best_pattern_name}")
    print(f"   Technical Edge: {best_edge:+.2f}%\n")
    
    # 3. TRAFFIC LIGHT
    print_section("3️⃣ TRAFFIC LIGHT EVALUATION")
    
    from src.decision import TrafficLightEvaluator, Signal
    from src.analysis.signal_aggregator import SignalAggregator
    
    traffic_light = TrafficLightEvaluator()
    
    aggregated = None
    if current_situation['active_situations']:
        aggregator = SignalAggregator()
        aggregated = aggregator.aggregate_signals(current_situation['active_situations'])
    
    aggregated_signal_data = {
        'bias': aggregated.direction if aggregated and hasattr(aggregated, 'direction') else 'NEUTRAL',
        'confidence': aggregated.confidence if aggregated else 'LÅG',
        'correlation_warning': aggregated.correlation_warning if aggregated else False
    }
    
    traffic_light_situation = {
        'aggregated_signal': aggregated_signal_data,
        'active_situations': current_situation.get('active_situations', [])
    }
    
    traffic_result = traffic_light.evaluate(
        analysis_results=analysis_results,
        current_situation=traffic_light_situation
    )
    
    print(f"Signal: {traffic_result.signal.name}")
    print(f"Confidence: {traffic_result.confidence}")
    print(f"Bias: {aggregated_signal_data['bias']}")
    
    # Traffic Light Thresholds
    if traffic_result.signal == Signal.GREEN:
        print(f"✅ GREEN: Edge > 1.0%, Win rate > 55%, High confidence")
        base_alloc = 4.0
    elif traffic_result.signal == Signal.YELLOW:
        print(f"🟡 YELLOW: Edge 0.5-1.0%, Win rate 50-55%, Medium confidence")
        base_alloc = 2.0
    elif traffic_result.signal == Signal.ORANGE:
        print(f"🟠 ORANGE: Edge 0-0.5%, Win rate < 50%, Low confidence")
        base_alloc = 0.5
    else:
        print(f"🔴 RED: Edge < 0%, Negative expected return")
        base_alloc = 0.0
    
    print(f"Base Allocation: {base_alloc}%")
    
    # 4. V-KELLY POSITION SIZING
    print_section("4️⃣ V-KELLY POSITION SIZING (Volatility Adjustment)")
    
    atr_percent = v_kelly.calculate_atr_percent(
        high=market_data.high_prices,
        low=market_data.low_prices,
        close=market_data.close_prices,
        period=14
    )
    
    print(f"ATR (14-day): {atr_percent:.2f}%")
    
    position_result = v_kelly.adjust_position_size(
        base_allocation=base_alloc,
        atr_percent=atr_percent,
        signal_strength=traffic_result.signal.name
    )
    
    print(f"Base Allocation: {base_alloc:.2f}%")
    print(f"Final V-Kelly Position: {position_result.volatility_adjusted:.2f}%")
    
    # 5. TREND FILTER
    print_section("5️⃣ TREND FILTER (V3.0 Elastic Scoring)")
    
    trend_analysis = trend_filter.analyze_trend(
        prices=market_data.close_prices,
        current_signal=traffic_result.signal.name
    )
    
    current_price = market_data.close_prices[-1]
    ma_50 = np.mean(market_data.close_prices[-50:])
    ma_200 = np.mean(market_data.close_prices[-200:])
    
    print(f"Current Price: {current_price:.2f} SEK")
    print(f"50-day MA: {ma_50:.2f} SEK")
    print(f"200-day MA: {ma_200:.2f} SEK")
    print(f"")
    print(f"Trend Aligned (above 200MA): {'✅ YES' if trend_analysis.allow_long else '❌ NO'}")
    print(f"Trend Score (V3.0 Elastic): {trend_analysis.trend_score:.1f}/15 points")
    print(f"")
    
    if current_price > ma_200:
        print(f"✅ Price above 200MA → Full strength (15 points)")
    elif current_price > ma_50:
        distance_pct = (current_price - ma_50) / (ma_200 - ma_50)
        print(f"⚠️ Price between 50MA-200MA → Elastic scoring ({distance_pct*100:.1f}% up)")
        print(f"   Trend Score: {trend_analysis.trend_score:.1f}/15")
    else:
        print(f"❌ Price below 50MA → BLOCKED")
    
    # 6. VOLATILITY BREAKOUT
    print_section("6️⃣ VOLATILITY BREAKOUT FILTER")
    
    breakout_analysis = breakout_filter.analyze_breakout(
        high=market_data.high_prices,
        low=market_data.low_prices,
        close=market_data.close_prices,
        volume=market_data.volume,
        signal=traffic_result.signal.name
    )
    
    print(f"Volatility Regime: {breakout_analysis.regime.value}")
    print(f"Breakout Confidence: {breakout_analysis.confidence}")
    print(f"Current ATR Ratio: {breakout_analysis.current_atr_ratio:.2f}x")
    print(f"Volume Ratio: {breakout_analysis.volume_ratio:.2f}x")
    print(f"")
    print(f"Recommendation: {breakout_analysis.recommendation}")
    
    # 7. COST-AWARE FILTER
    print_section("7️⃣ COST-AWARE FILTER (Net Edge Calculation)")
    
    is_foreign = not ticker.endswith('.ST')
    cost_analysis = cost_filter.analyze_edge_after_costs(
        predicted_edge=best_edge,
        ticker=ticker,
        category="Swedish",
        position_size=10000,
        is_foreign=is_foreign
    )
    
    print(f"Technical Edge (Before Costs): {best_edge:+.2f}%")
    print(f"")
    print(f"KOSTNADER:")
    print(f"  Spread: {cost_analysis.spread_cost:.2f}%")
    print(f"  Courtage: {cost_analysis.courtage_cost:.2f}%")
    print(f"  FX Cost: {cost_analysis.fx_cost:.2f}%")
    print(f"  Slippage: {cost_analysis.slippage_cost:.2f}%")
    print(f"  ────────────────────")
    print(f"  Total Cost: {cost_analysis.total_cost:.2f}%")
    print(f"")
    print(f"Net Edge (After Costs): {cost_analysis.net_edge:+.2f}%")
    print(f"Profitable: {'✅ YES' if cost_analysis.profitable else '❌ NO'}")
    
    # 8. RVOL FILTER
    print_section("8️⃣ RVOL FILTER (V3.0 - Relative Volume)")
    
    rvol_analysis = rvol_filter.analyze_rvol(volume=market_data.volume)
    
    print(f"Current Volume: {market_data.volume[-1]:,.0f}")
    print(f"Avg Volume (20d): {rvol_analysis.avg_volume_20d:,.0f}")
    print(f"RVOL Ratio: {rvol_analysis.rvol:.2f}x")
    print(f"")
    print(f"Conviction Level: {rvol_analysis.conviction_level}")
    print(f"Score Multiplier: {rvol_analysis.score_multiplier:.2f}x")
    print(f"")
    
    if rvol_analysis.rvol < 0.5:
        print(f"❌ DEAD ZONE: RVOL < 0.5 → Score × 0.0 (BLOCK)")
    elif rvol_analysis.rvol < 1.0:
        print(f"⚠️ WEAK VOLUME: RVOL < 1.0 → Score × 0.5")
    else:
        print(f"✅ NORMAL/HIGH VOLUME: RVOL ≥ 1.0 → Score × 1.0")
    
    print(f"")
    print(f"Recommendation: {rvol_analysis.recommendation}")
    
    # 9. FINAL SCORE CALCULATION
    print_section("9️⃣ FINAL SCORE CALCULATION (0-100)")
    
    print("WEIGHTED COMPONENTS:\n")
    
    # Traffic Light (30%)
    if traffic_result.signal == Signal.GREEN:
        traffic_points = 30
    elif traffic_result.signal == Signal.YELLOW:
        traffic_points = 20
    elif traffic_result.signal == Signal.ORANGE:
        traffic_points = 10
    else:
        traffic_points = 0
    print(f"1. Traffic Light (30%): {traffic_points} points")
    print(f"   Signal: {traffic_result.signal.name}")
    
    # Net Edge (25%)
    if cost_analysis.net_edge > 0:
        edge_score = min(25, (cost_analysis.net_edge / 0.50) * 25)
    else:
        edge_score = max(-10, (cost_analysis.net_edge / 0.50) * 10)
    print(f"")
    print(f"2. Net Edge after costs (25%): {edge_score:.1f} points")
    print(f"   Net Edge: {cost_analysis.net_edge:+.2f}%")
    print(f"   Formula: (net_edge / 0.50%) × 25 (capped at 25)")
    
    # V-Kelly (15%)
    kelly_score = min(15, (position_result.volatility_adjusted / 5.0) * 15)
    print(f"")
    print(f"3. V-Kelly Position (15%): {kelly_score:.1f} points")
    print(f"   Position: {position_result.volatility_adjusted:.2f}%")
    print(f"   Formula: (position / 5.0%) × 15 (capped at 15)")
    
    # Trend (15%)
    trend_score = trend_analysis.trend_score
    print(f"")
    print(f"4. Trend Elasticity (15%): {trend_score:.1f} points")
    print(f"   V3.0 Elastic Scoring (0-15 based on MA position)")
    
    # Volatility Breakout (10%)
    if breakout_analysis.confidence == "EXTREME":
        breakout_points = 10
    elif breakout_analysis.confidence == "HIGH":
        breakout_points = 8
    elif breakout_analysis.confidence == "MEDIUM":
        breakout_points = 5
    elif breakout_analysis.confidence == "LOW":
        breakout_points = 2
    else:
        breakout_points = 0
    print(f"")
    print(f"5. Volatility Breakout (10%): {breakout_points} points")
    print(f"   Confidence: {breakout_analysis.confidence}")
    
    # Cost Profitable (5%)
    cost_points = 5 if cost_analysis.profitable else 0
    print(f"")
    print(f"6. Cost Profitable (5%): {cost_points} points")
    print(f"   Profitable: {'✅' if cost_analysis.profitable else '❌'}")
    
    # Subtotal
    subtotal = traffic_points + edge_score + kelly_score + trend_score + breakout_points + cost_points
    print(f"")
    print(f"─────────────────────────────────────")
    print(f"SUBTOTAL: {subtotal:.1f} points")
    
    # RVOL Multiplier
    final_score = subtotal * rvol_analysis.score_multiplier
    final_score = max(0, min(100, final_score))
    
    print(f"")
    print(f"RVOL Multiplier: ×{rvol_analysis.score_multiplier:.2f}")
    print(f"")
    print(f"═════════════════════════════════════")
    print(f"FINAL SCORE: {final_score:.1f}/100")
    print(f"═════════════════════════════════════")
    
    # 10. ENTRY DECISION
    print_section("🎯 FINAL RECOMMENDATION")
    
    if not trend_analysis.allow_long:
        entry = "BLOCK - Below 200-day MA"
        final_allocation = 0.0
    elif not cost_analysis.profitable:
        entry = "BLOCK - Negative net edge after costs"
        final_allocation = 0.0
    elif breakout_analysis.confidence == "LOW":
        entry = "WAIT - Low breakout confidence"
        final_allocation = position_result.volatility_adjusted * 0.5
    elif breakout_analysis.confidence == "MEDIUM":
        entry = "CAUTIOUS - Medium breakout"
        final_allocation = position_result.volatility_adjusted * 0.7
    elif breakout_analysis.confidence in ["HIGH", "EXTREME"]:
        entry = "ENTER - Strong entry conditions"
        final_allocation = position_result.volatility_adjusted
    else:
        entry = "ENTER"
        final_allocation = position_result.volatility_adjusted
    
    print(f"Signal: {traffic_result.signal.name}")
    print(f"Final Score: {final_score:.1f}/100")
    print(f"Position Size: {final_allocation:.2f}%")
    print(f"Entry Recommendation: {entry}")
    print(f"")
    print(f"Technical Edge: {best_edge:+.2f}%")
    print(f"Net Edge (after costs): {cost_analysis.net_edge:+.2f}%")
    print(f"")
    
    if entry.startswith("ENTER"):
        print(f"✅ REKOMMENDATION: KÖP {name}")
        print(f"   Position: {final_allocation:.2f}% av portfölj")
        print(f"   Förväntat edge: {cost_analysis.net_edge:+.2f}% per trade")
    elif entry.startswith("WAIT") or entry.startswith("CAUTIOUS"):
        print(f"⚠️ REKOMMENDATION: WATCH {name}")
        print(f"   Vänta på bättre entry timing eller högre conviction")
    else:
        print(f"❌ REKOMMENDATION: AVSTÅ från {name}")
        print(f"   Blockerad av: {entry}")
    
    print(f"\n{'#'*80}\n")

if __name__ == "__main__":
    main()
