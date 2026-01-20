"""
Full Step-by-Step Analysis - Complete Calculations
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
from src.decision import TrafficLightEvaluator, Signal
from src.analysis.signal_aggregator import SignalAggregator
from src import QuantPatternAnalyzer

def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NOLA-B.ST"
    name = sys.argv[2] if len(sys.argv) > 2 else "Nolato B"
    
    print("\n" + "="*80)
    print(f"FULL ANALYSIS: {name} ({ticker})")
    print("="*80 + "\n")
    
    # Initialize
    data_fetcher = DataFetcher()
    bayesian = BayesianEdgeEstimator()
    v_kelly = VolatilityPositionSizer()
    trend_filter = TrendFilter()
    breakout_filter = VolatilityBreakoutFilter()
    cost_filter = CostAwareFilter()
    rvol_filter = RVOLFilter()
    analyzer = QuantPatternAnalyzer(min_occurrences=5, min_confidence=0.40, forward_periods=1)
    traffic_light = TrafficLightEvaluator()
    
    # STEP 1: DATA
    print("STEG 1: DATA HAMTNING")
    print("-" * 80)
    market_data = data_fetcher.fetch_stock_data(ticker, period="15y")
    if not market_data:
        print("ERROR: Kunde inte hamta data")
        return
    
    print(f"Hamtade {len(market_data)} datapunkter ({len(market_data)/252:.1f} ar)")
    print(f"Period: {market_data.timestamps[0].strftime('%Y-%m-%d')} till {market_data.timestamps[-1].strftime('%Y-%m-%d')}")
    print(f"Senaste pris: {market_data.close_prices[-1]:.2f} SEK")
    print(f"Genomsnittlig volym: {market_data.volume.mean():,.0f}\n")
    
    # STEP 2: PATTERN ANALYSIS
    print("STEG 2: PATTERN DETECTION & BAYESIAN EDGE")
    print("-" * 80)
    analysis_results = analyzer.analyze_market_data(market_data)
    current_situation = analyzer.get_current_market_situation(market_data, lookback_window=50)
    
    all_results = analysis_results.get('results', [])
    significant_patterns = analysis_results.get('significant_patterns', [])
    print(f"Detekterade {len(all_results)} patterns totalt")
    print(f"Signifikanta patterns (min_confidence > 0.40): {len(significant_patterns)}\n")
    
    # Filter to only significant results
    significant_results = [r for r in all_results if r['pattern_eval'].is_significant]
    
    if significant_results:
        print("SIGNIFIKANTA MONSTER:\n")
        for i, result in enumerate(significant_results[:5], 1):
            situation = result['situation']
            outcome_stats = result['outcome_stats']
            pattern_eval = result['pattern_eval']
            bayesian_est = result.get('bayesian_estimate')
            
            desc = situation.description
            occ = outcome_stats.sample_size
            mean_ret = outcome_stats.mean_return * 100
            win_rate = outcome_stats.win_rate * 100
            conf = pattern_eval.statistical_strength
            
            print(f"{i}. {desc}")
            print(f"   Antal ganger sett: {occ}")
            print(f"   Genomsnittlig avkastning: {mean_ret:+.2f}%")
            print(f"   Win rate: {win_rate:.1f}%")
            print(f"   Statistical Strength: {conf:.2f}")
            
            if bayesian_est:
                print(f"   BAYESIAN EDGE ESTIMATION:")
                print(f"      Point Estimate: {bayesian_est.point_estimate*100:+.3f}%")
                print(f"      95% Credible Interval: [{bayesian_est.credible_interval_95[0]*100:+.2f}%, {bayesian_est.credible_interval_95[1]*100:+.2f}%]")
                print(f"      P(edge > 0): {bayesian_est.probability_positive*100:.1f}%")
                print(f"      Sample Size: {bayesian_est.sample_size}")
                print(f"      Uncertainty Level: {bayesian_est.uncertainty_level.upper()}")
                print(f"      Survivorship-Adjusted Edge: {bayesian_est.bias_adjusted_edge*100:+.3f}%")
                print(f"         (Original edge x 0.80 = {bayesian_est.point_estimate*100:+.3f}% x 0.80)")
            print()
    
    # Find best edge (using Bayesian-adjusted, like screener does)
    best_edge_raw = 0.0
    best_edge_bayesian = 0.0
    best_pattern_name = "Inget"
    for pattern in significant_patterns:
        # V3.0: Use Bayesian edge (survivorship-adjusted)
        if 'bayesian_edge' in pattern:
            edge = pattern['bayesian_edge'] * 100
        elif 'mean_return' in pattern:
            edge = pattern['mean_return'] * 100
        else:
            continue
        
        if abs(edge) > abs(best_edge_bayesian):
            best_edge_bayesian = edge
            best_edge_raw = pattern.get('mean_return', 0) * 100
            best_pattern_name = pattern.get('description', 'Inget')
    
    print(f">>> BASTA PATTERN: {best_pattern_name}")
    print(f">>> TECHNICAL EDGE (Raw): {best_edge_raw:+.2f}%")
    print(f">>> BAYESIAN EDGE (Survivorship-Adjusted): {best_edge_bayesian:+.2f}%")
    print(f"    (Used by screener - conservative, realistic)\n")
    
    # STEP 3: TRAFFIC LIGHT
    print("STEG 3: TRAFFIC LIGHT KATEGORISERING")
    print("-" * 80)
    
    aggregated = None
    if current_situation['active_situations']:
        aggregator = SignalAggregator()
        aggregated = aggregator.aggregate_signals(current_situation['active_situations'])
    
    aggregated_signal_data = {
        'bias': aggregated.direction if aggregated and hasattr(aggregated, 'direction') else 'NEUTRAL',
        'confidence': aggregated.confidence if aggregated else 'LAG',
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
    print(f"Bias: {aggregated_signal_data['bias']}\n")
    
    print("TRAFFIC LIGHT LOGIK:")
    if traffic_result.signal == Signal.GREEN:
        print("  GREEN: Edge > 1.0% AND Win rate > 55% AND High confidence")
        print("  Base Allocation: 4.0%")
        base_alloc = 4.0
    elif traffic_result.signal == Signal.YELLOW:
        print("  YELLOW: Edge 0.5-1.0% OR Win rate 50-55% OR Medium confidence")
        print("  Base Allocation: 2.0%")
        base_alloc = 2.0
    elif traffic_result.signal == Signal.ORANGE:
        print("  ORANGE: Edge 0-0.5% OR Win rate < 50% OR Low confidence")
        print("  Base Allocation: 0.5%")
        base_alloc = 0.5
    else:
        print("  RED: Edge < 0% - Negativ expected return")
        print("  Base Allocation: 0.0%")
        base_alloc = 0.0
    print()
    
    # STEP 4: V-KELLY
    print("STEG 4: V-KELLY POSITION SIZING (Volatilitet Adjustment)")
    print("-" * 80)
    
    atr = v_kelly.calculate_atr_percent(
        high=market_data.high_prices,
        low=market_data.low_prices,
        close=market_data.close_prices,
        period=14
    )
    
    print(f"ATR (14-day): {atr:.2f}%")
    print(f"  (Average True Range / Price)")
    print()
    
    pos_result = v_kelly.adjust_position_size(
        base_allocation=base_alloc,
        atr_percent=atr,
        signal_strength=traffic_result.signal.name
    )
    
    print(f"V-KELLY CALCULATION:")
    print(f"  Base Allocation: {base_alloc:.2f}%")
    print(f"  ATR: {atr:.2f}%")
    print(f"  Volatility-Adjusted Position: {pos_result.volatility_adjusted:.2f}%")
    print(f"  Logik: Hogre volatilitet = mindre position for samma risk")
    print()
    
    # STEP 5: TREND FILTER
    print("STEG 5: TREND FILTER (V3.0 Elastic Scoring)")
    print("-" * 80)
    
    trend_result = trend_filter.analyze_trend(
        prices=market_data.close_prices,
        current_signal=traffic_result.signal.name
    )
    
    current_price = market_data.close_prices[-1]
    ma_50 = np.mean(market_data.close_prices[-50:])
    ma_200 = np.mean(market_data.close_prices[-200:])
    
    print(f"Current Price: {current_price:.2f} SEK")
    print(f"50-day MA: {ma_50:.2f} SEK")
    print(f"200-day MA: {ma_200:.2f} SEK")
    print()
    print(f"Trend Aligned (price > 200MA): {trend_result.allow_long}")
    print(f"Trend Score (V3.0 Elastic 0-15): {trend_result.trend_score:.1f} points")
    print()
    
    if current_price > ma_200:
        print(f"  LOGIK: Price ({current_price:.2f}) > 200MA ({ma_200:.2f})")
        print(f"         -> Full strength (15 points)")
    elif current_price > ma_50:
        distance = (current_price - ma_50) / (ma_200 - ma_50)
        print(f"  LOGIK: Price between 50MA-200MA")
        print(f"         Distance: {distance*100:.1f}% up from 50MA toward 200MA")
        print(f"         Elastic Score: {distance:.3f} x 15 = {trend_result.trend_score:.1f} points")
    else:
        print(f"  LOGIK: Price below 50MA -> BLOCKED (0 points)")
    print()
    
    # STEP 6: VOLATILITY BREAKOUT
    print("STEG 6: VOLATILITY BREAKOUT TIMING")
    print("-" * 80)
    
    breakout = breakout_filter.analyze_breakout(
        high=market_data.high_prices,
        low=market_data.low_prices,
        close=market_data.close_prices,
        volume=market_data.volume,
        signal=traffic_result.signal.name
    )
    
    print(f"Volatility Regime: {breakout.regime.value}")
    print(f"Breakout Confidence: {breakout.confidence:.2f}")
    print(f"ATR Change: {breakout.atr_change_pct:+.2f}%")
    print(f"Volume Confirmation: {breakout.volume_confirmation}")
    print()
    print(f"LOGIK:")
    if breakout.regime.value == "EXPLOSIVE":
        print(f"  EXPLOSIVE: ATR > +20% - Very high volatility breakout")
    elif breakout.regime.value == "EXPANDING":
        print(f"  EXPANDING: ATR +5% to +20% - Strong breakout")
    elif breakout.regime.value == "STABLE":
        print(f"  STABLE: ATR -5% to +5% - Normal conditions")
    else:
        print(f"  CONTRACTING: ATR < -5% - Volatility contracting")
    print()
    
    # STEP 7: COST-AWARE FILTER
    print("STEG 7: COST-AWARE FILTER (Net Edge Calculation)")
    print("-" * 80)
    
    is_foreign = not ticker.endswith('.ST')
    cost_result = cost_filter.analyze_edge_after_costs(
        predicted_edge=best_edge_bayesian,
        ticker=ticker,
        category="Swedish",
        position_size=10000,
        is_foreign=is_foreign
    )
    
    print(f"Technical Edge (Raw mean): {best_edge_raw:+.2f}%")
    print(f"Bayesian Edge (Survivorship-Adjusted): {best_edge_bayesian:+.2f}%")
    print()
    print(f"KOSTNADER:")
    print(f"  Spread: {cost_result.trading_costs.spread_pct:.3f}%")
    print(f"  Courtage: {cost_result.trading_costs.courtage/10000*100:.3f}% (pa 10,000 SEK)")
    print(f"  FX Cost: {cost_result.trading_costs.fx_cost_pct:.3f}%")
    print(f"  -----------------------")
    print(f"  TOTAL COST: {cost_result.trading_costs.total_pct:.3f}%")
    print()
    print(f"NET EDGE (efter kostnader):")
    print(f"  Bayesian: {best_edge_bayesian:+.2f}% - Cost: {cost_result.trading_costs.total_pct:.3f}% = {cost_result.net_edge:+.2f}%")
    print(f"  Profitable: {cost_result.profitable}")
    print()
    
    # STEP 8: RVOL FILTER
    print("STEG 8: RVOL FILTER (V3.0 - Relative Volume)")
    print("-" * 80)
    
    rvol_result = rvol_filter.analyze_rvol(volume=market_data.volume)
    
    print(f"Current Volume: {market_data.volume[-1]:,.0f}")
    print(f"Average Volume (20d): {rvol_result.avg_volume_20d:,.0f}")
    print(f"RVOL Ratio: {rvol_result.rvol:.2f}x")
    print()
    print(f"Conviction Level: {rvol_result.conviction_level}")
    print(f"Score Multiplier: {rvol_result.score_multiplier:.2f}x")
    print()
    print(f"LOGIK:")
    if rvol_result.rvol < 0.5:
        print(f"  RVOL < 0.5: DEAD ZONE - Score x 0.0 (BLOCK)")
    elif rvol_result.rvol < 1.0:
        print(f"  RVOL 0.5-1.0: WEAK VOLUME - Score x 0.5")
    else:
        print(f"  RVOL >= 1.0: NORMAL/HIGH VOLUME - Score x 1.0")
    print()
    
    # STEP 9: FINAL SCORE
    print("STEG 9: FINAL SCORE CALCULATION (0-100)")
    print("-" * 80)
    
    # Traffic (30%)
    if traffic_result.signal == Signal.GREEN:
        traffic_pts = 30
    elif traffic_result.signal == Signal.YELLOW:
        traffic_pts = 20
    elif traffic_result.signal == Signal.ORANGE:
        traffic_pts = 10
    else:
        traffic_pts = 0
    
    print(f"1. Traffic Light (30%): {traffic_pts} points")
    print(f"   Signal: {traffic_result.signal.name}")
    print()
    
    # Net Edge (25%)
    if cost_result.net_edge > 0:
        edge_pts = min(25, (cost_result.net_edge / 0.50) * 25)
    else:
        edge_pts = max(-10, (cost_result.net_edge / 0.50) * 10)
    
    print(f"2. Net Edge (25%): {edge_pts:.1f} points")
    print(f"   Net Edge: {cost_result.net_edge:+.2f}%")
    print(f"   Formula: ({cost_result.net_edge:.2f} / 0.50) x 25 = {edge_pts:.1f}")
    print()
    
    # V-Kelly (15%)
    kelly_pts = min(15, (pos_result.volatility_adjusted / 5.0) * 15)
    print(f"3. V-Kelly Position (15%): {kelly_pts:.1f} points")
    print(f"   Position: {pos_result.volatility_adjusted:.2f}%")
    print(f"   Formula: ({pos_result.volatility_adjusted:.2f} / 5.0) x 15 = {kelly_pts:.1f}")
    print()
    
    # Trend (15%)
    trend_pts = trend_result.trend_score
    print(f"4. Trend Elasticity (15%): {trend_pts:.1f} points")
    print(f"   V3.0 Elastic Score (0-15)")
    print()
    
    # Breakout (10%)
    if breakout.regime.value == "EXPLOSIVE":
        breakout_pts = 10
    elif breakout.regime.value == "EXPANDING":
        breakout_pts = 8
    elif breakout.regime.value == "STABLE":
        breakout_pts = 5
    else:
        breakout_pts = 2
    
    print(f"5. Volatility Breakout (10%): {breakout_pts} points")
    print(f"   Regime: {breakout.regime.value} (Confidence: {breakout.confidence:.2f})")
    print()
    
    # Cost (5%)
    cost_pts = 5 if cost_result.profitable else 0
    print(f"6. Cost Profitable (5%): {cost_pts} points")
    print(f"   Profitable: {cost_result.profitable}")
    print()
    
    subtotal = traffic_pts + edge_pts + kelly_pts + trend_pts + breakout_pts + cost_pts
    print(f"SUBTOTAL: {subtotal:.1f} points")
    print()
    
    # RVOL multiplier
    final_score = subtotal * rvol_result.score_multiplier
    final_score = max(0, min(100, final_score))
    
    print(f"RVOL MULTIPLIER: x{rvol_result.score_multiplier:.2f}")
    print(f"  {subtotal:.1f} x {rvol_result.score_multiplier:.2f} = {final_score:.1f}")
    print()
    print(f">>> FINAL SCORE: {final_score:.1f}/100")
    print()
    
    # STEP 10: ENTRY DECISION
    print("STEG 10: ENTRY BESLUT")
    print("-" * 80)
    
    if not trend_result.allow_long:
        entry = "BLOCK - Below 200-day MA"
        final_alloc = 0.0
    elif not cost_result.profitable:
        entry = "BLOCK - Negative net edge after costs"
        final_alloc = 0.0
    elif breakout.regime.value == "CONTRACTING":
        entry = "WAIT - Volatility contracting"
        final_alloc = pos_result.volatility_adjusted * 0.5
    elif breakout.regime.value == "STABLE":
        entry = "CAUTIOUS - Stable regime"
        final_alloc = pos_result.volatility_adjusted * 0.7
    elif breakout.regime.value in ["EXPANDING", "EXPLOSIVE"]:
        entry = "ENTER - Strong entry conditions"
        final_alloc = pos_result.volatility_adjusted
    else:
        entry = "ENTER"
        final_alloc = pos_result.volatility_adjusted
    
    print(f"FINAL RECOMMENDATION:")
    print(f"  Signal: {traffic_result.signal.name}")
    print(f"  Score: {final_score:.1f}/100")
    print(f"  Position: {final_alloc:.2f}%")
    print(f"  Entry: {entry}")
    print(f"  Raw Edge: {best_edge_raw:+.2f}%")
    print(f"  Bayesian Edge (after survivorship bias): {best_edge_bayesian:+.2f}%")
    print(f"  Net Edge (after costs): {cost_result.net_edge:+.2f}%")
    print()
    
    if entry.startswith("ENTER"):
        print(f">>> KOP {name}")
        print(f"    Position: {final_alloc:.2f}% av portfölj")
        print(f"    Forvantat edge (Bayesian): {best_edge_bayesian:+.2f}%")
        print(f"    Forvantat edge (Net after costs): {cost_result.net_edge:+.2f}% per trade")
    elif entry.startswith("WAIT") or entry.startswith("CAUTIOUS"):
        print(f">>> WATCH {name}")
        print(f"    Vanta pa battre timing")
    else:
        print(f">>> AVSTA fran {name}")
        print(f"    Blockerad: {entry}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
