"""
Instrument Screener V2.2 - Med Casino-Style Risk Improvements

Integrerar alla V2.0, V2.1 och V2.2 features i ett unified workflow:
- V2.0: Traffic Light (4 nivåer), Bayesian edge, 250 instruments
- V2.1: V-Kelly sizing, Trend Filter, Regime Detection
- V2.2: Volatility Breakout, Cost-Aware Filter, Monte Carlo, Profit Targeting

Workflow:
1. Screen alla 250 instruments med Traffic Light
2. Filtrera med Volatility Breakout (timing check)
3. Validera med Cost-Aware Filter (net edge > 0)
4. Generera actionable report
"""

import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass
from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher
from src.decision import TrafficLightEvaluator, Signal
from src.analysis.signal_aggregator import SignalAggregator

# V2.1 imports
from src.risk.volatility_position_sizing import VolatilityPositionSizer
from src.risk.trend_filter import TrendFilter
from src.risk.regime_detection import RegimeDetector

# V2.2 imports
from src.entry.volatility_breakout import VolatilityBreakoutFilter
from src.risk.cost_aware_filter import CostAwareFilter


@dataclass
class InstrumentScoreV22:
    """Enhanced score med V2.2 features."""
    ticker: str
    name: str
    category: str
    
    # Pattern analysis (V2.0)
    total_patterns: int
    significant_patterns: int
    best_edge: float
    best_pattern_name: str
    
    # Traffic light (V2.0)
    signal: Signal
    signal_confidence: str
    recommended_allocation: str
    
    # V2.1 Risk Controls
    v_kelly_position: float  # % of portfolio (ATR-adjusted)
    trend_aligned: bool  # Above 200-day MA?
    regime_multiplier: float  # 0.2 - 1.0x based on market regime
    
    # V2.2 Features
    breakout_confidence: str  # LOW, MEDIUM, HIGH, EXTREME
    volatility_regime: str  # CONTRACTING, STABLE, EXPANDING, EXPLOSIVE
    net_edge_after_costs: float  # Edge - costs
    cost_profitable: bool  # Net edge > 0?
    
    # Combined metrics
    final_allocation: float  # Final position size (%) after all filters
    final_score: float  # 0-100 score
    entry_recommendation: str  # ENTER, WAIT, BLOCK
    
    # Data quality
    data_points: int
    period_years: float
    avg_volume: float


class InstrumentScreenerV22:
    """
    Unified screener med alla V2.0, V2.1, V2.2 features.
    
    Workflow:
    1. Pattern analysis + Traffic Light (V2.0)
    2. V-Kelly position sizing (V2.1)
    3. Trend filter check (V2.1)
    4. Regime detection (V2.1)
    5. Volatility breakout check (V2.2)
    6. Cost-aware validation (V2.2)
    7. Generate final recommendation
    """
    
    def __init__(
        self,
        min_data_years: float = 5.0,
        min_avg_volume: float = 50000,
        enable_v22_filters: bool = True
    ):
        """
        Initialize unified screener.
        
        Args:
            min_data_years: Minst X års historik
            min_avg_volume: Minsta snittvolym per dag
            enable_v22_filters: Enable V2.2 filters (volatility + cost)
        """
        self.min_data_years = min_data_years
        self.min_avg_volume = min_avg_volume
        self.enable_v22_filters = enable_v22_filters
        
        # Core components (V2.0)
        self.data_fetcher = DataFetcher()
        self.analyzer = QuantPatternAnalyzer(
            min_occurrences=5,
            min_confidence=0.40,
            forward_periods=1
        )
        self.traffic_light = TrafficLightEvaluator()
        
        # V2.1 components
        self.v_kelly_sizer = VolatilityPositionSizer()
        self.trend_filter = TrendFilter()
        self.regime_detector = RegimeDetector()
        
        # V2.2 components
        if enable_v22_filters:
            self.breakout_filter = VolatilityBreakoutFilter()
            self.cost_filter = CostAwareFilter()
    
    def screen_instruments(
        self,
        instruments: List[Tuple[str, str, str]]
    ) -> List[InstrumentScoreV22]:
        """
        Analysera alla instrument med unified V2.2 workflow.
        
        Args:
            instruments: Lista med (ticker, name, category)
            
        Returns:
            Lista av InstrumentScoreV22
        """
        results = []
        
        print("=" * 80)
        print("📊 INSTRUMENT SCREENER V2.2 - CASINO-STYLE RISK IMPROVEMENTS")
        print("=" * 80)
        print(f"\nAnalyserar {len(instruments)} instrument...")
        print(f"V2.2 Filters: {'Enabled' if self.enable_v22_filters else 'Disabled'}")
        print()
        
        for i, (ticker, name, category) in enumerate(instruments, 1):
            print(f"[{i}/{len(instruments)}] {name} ({ticker})...")
            
            try:
                score = self._analyze_instrument_v22(ticker, name, category)
                if score:
                    results.append(score)
                    print(f"  ✅ Score: {score.final_score:.1f}/100 | "
                          f"Signal: {self._signal_to_text(score.signal)} | "
                          f"Entry: {score.entry_recommendation}")
                else:
                    print(f"  ⚠️ Skipped (criteria not met)")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            print()
        
        # Sort by final_score
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Calculate regime multiplier for all
        if results:
            self._apply_regime_multiplier(results)
        
        return results
    
    def _analyze_instrument_v22(
        self,
        ticker: str,
        name: str,
        category: str
    ) -> InstrumentScoreV22:
        """Analyze single instrument with V2.2 workflow."""
        
        # 1. Fetch data
        market_data = self.data_fetcher.fetch_stock_data(ticker, period="15y")
        if market_data is None:
            return None
        
        # 2. Quality check
        data_points = len(market_data)
        period_years = data_points / 252
        
        if period_years < self.min_data_years:
            return None
        
        avg_volume = float(market_data.volume.mean())
        if avg_volume < self.min_avg_volume:
            return None
        
        # 3. Pattern analysis (V2.0)
        analysis_results = self.analyzer.analyze_market_data(market_data)
        current_situation = self.analyzer.get_current_market_situation(
            market_data, lookback_window=50
        )
        
        # 4. Aggregate signals
        aggregated = None
        if current_situation['active_situations']:
            aggregator = SignalAggregator()
            aggregated = aggregator.aggregate_signals(
                current_situation['active_situations']
            )
        
        # 5. Traffic Light (V2.0)
        aggregated_signal_data = {
            'bias': aggregated.direction if aggregated and hasattr(aggregated, 'direction') else 'NEUTRAL',
            'confidence': aggregated.confidence if aggregated else 'LÅG',
            'correlation_warning': aggregated.correlation_warning if aggregated else False
        }
        
        traffic_light_situation = {
            'aggregated_signal': aggregated_signal_data,
            'active_situations': current_situation.get('active_situations', [])
        }
        
        traffic_result = self.traffic_light.evaluate(
            analysis_results=analysis_results,
            current_situation=traffic_light_situation
        )
        
        # Extract edge metrics
        significant_patterns = analysis_results.get('significant_patterns', [])
        best_edge = 0.0
        best_pattern_name = "Inget"
        
        for pattern in significant_patterns:
            if 'mean_return' in pattern:
                edge = pattern['mean_return'] * 100
                if abs(edge) > abs(best_edge):
                    best_edge = edge
                    best_pattern_name = pattern.get('description', 'Inget')
        
        # 6. V-Kelly position sizing (V2.1)
        # Calculate ATR and adjust position
        try:
            atr_percent = self.v_kelly_sizer.calculate_atr_percent(
                high=market_data.high_prices,
                low=market_data.low_prices,
                close=market_data.close_prices,
                period=14
            )
            
            # Get base allocation from traffic light
            if traffic_result.signal == Signal.GREEN:
                base_alloc = 4.0
            elif traffic_result.signal == Signal.YELLOW:
                base_alloc = 2.0
            elif traffic_result.signal == Signal.ORANGE:
                base_alloc = 0.5
            else:
                base_alloc = 0.0
            
            position_result = self.v_kelly_sizer.adjust_position_size(
                base_allocation=base_alloc,
                atr_percent=atr_percent,
                signal_strength=traffic_result.signal.name
            )
            v_kelly_position = position_result.volatility_adjusted
        except Exception as e:
            print(f"    ⚠️ V-Kelly sizing failed: {e}")
            v_kelly_position = 1.0  # Default
        
        # 7. Trend filter (V2.1)
        trend_analysis = self.trend_filter.analyze_trend(
            prices=market_data.close_prices,
            current_signal=traffic_result.signal.name
        )
        trend_aligned = trend_analysis.allow_long
        
        # Initialize V2.2 defaults
        breakout_confidence = "N/A"
        volatility_regime = "N/A"
        net_edge_after_costs = best_edge
        cost_profitable = True
        
        # 8. Volatility Breakout Filter (V2.2)
        if self.enable_v22_filters:
            try:
                breakout_analysis = self.breakout_filter.analyze_breakout(
                    high=market_data.high_prices,
                    low=market_data.low_prices,
                    close=market_data.close_prices,
                    volume=market_data.volume,
                    signal=traffic_result.signal.name
                )
                breakout_confidence = breakout_analysis.confidence
                volatility_regime = breakout_analysis.regime.value
            except Exception as e:
                print(f"    ⚠️ Breakout filter failed: {e}")
        
        # 9. Cost-Aware Filter (V2.2)
        if self.enable_v22_filters and best_edge > 0:
            try:
                is_foreign = not ticker.endswith('.ST')
                cost_analysis = self.cost_filter.analyze_edge_after_costs(
                    predicted_edge=best_edge,
                    ticker=ticker,
                    category=category,
                    position_size=10000,
                    is_foreign=is_foreign
                )
                net_edge_after_costs = cost_analysis.net_edge
                cost_profitable = cost_analysis.profitable
            except Exception as e:
                print(f"    ⚠️ Cost filter failed: {e}")
        
        # 10. Calculate final allocation and recommendation
        final_allocation, entry_recommendation = self._calculate_final_allocation(
            traffic_signal=traffic_result.signal,
            v_kelly_position=v_kelly_position,
            trend_aligned=trend_aligned,
            breakout_confidence=breakout_confidence,
            cost_profitable=cost_profitable
        )
        
        # 11. Calculate final score
        final_score = self._calculate_final_score(
            traffic_result=traffic_result,
            best_edge=best_edge,
            net_edge=net_edge_after_costs,
            v_kelly_position=v_kelly_position,
            trend_aligned=trend_aligned,
            breakout_confidence=breakout_confidence,
            cost_profitable=cost_profitable
        )
        
        # 12. Recommended allocation based on signal
        if traffic_result.signal == Signal.GREEN:
            recommended_allocation = "3-5%"
        elif traffic_result.signal == Signal.YELLOW:
            recommended_allocation = "1-3%"
        elif traffic_result.signal == Signal.ORANGE:
            recommended_allocation = "0-1%"
        else:
            recommended_allocation = "0%"
        
        return InstrumentScoreV22(
            ticker=ticker,
            name=name,
            category=category,
            total_patterns=len(analysis_results.get('results', [])),
            significant_patterns=len(significant_patterns),
            best_edge=best_edge,
            best_pattern_name=best_pattern_name,
            signal=traffic_result.signal,
            signal_confidence=traffic_result.confidence,
            recommended_allocation=recommended_allocation,
            v_kelly_position=v_kelly_position,
            trend_aligned=trend_aligned,
            regime_multiplier=1.0,  # Will be set later
            breakout_confidence=breakout_confidence,
            volatility_regime=volatility_regime,
            net_edge_after_costs=net_edge_after_costs,
            cost_profitable=cost_profitable,
            final_allocation=final_allocation,
            final_score=final_score,
            entry_recommendation=entry_recommendation,
            data_points=data_points,
            period_years=period_years,
            avg_volume=avg_volume
        )
    
    def _calculate_final_allocation(
        self,
        traffic_signal: Signal,
        v_kelly_position: float,
        trend_aligned: bool,
        breakout_confidence: str,
        cost_profitable: bool
    ) -> Tuple[float, str]:
        """Calculate final allocation % and entry recommendation."""
        
        # Start with traffic light base
        if traffic_signal == Signal.GREEN:
            base_allocation = 4.0  # 4%
        elif traffic_signal == Signal.YELLOW:
            base_allocation = 2.0  # 2%
        elif traffic_signal == Signal.ORANGE:
            base_allocation = 0.5  # 0.5%
        else:  # RED
            return 0.0, "BLOCK"
        
        # Apply V-Kelly adjustment (ATR-based risk parity)
        allocation = v_kelly_position
        
        # Trend filter: block if not aligned
        if not trend_aligned:
            return 0.0, "BLOCK - Below 200-day MA"
        
        # Cost filter: block if not profitable
        if not cost_profitable:
            return 0.0, "BLOCK - Negative net edge after costs"
        
        # Volatility breakout: adjust timing
        if breakout_confidence == "LOW":
            return allocation * 0.5, "WAIT - Low breakout confidence"
        elif breakout_confidence == "MEDIUM":
            return allocation * 0.7, "CAUTIOUS - Medium breakout"
        elif breakout_confidence in ["HIGH", "EXTREME"]:
            return allocation, "ENTER - Strong entry conditions"
        
        # Default
        return allocation, "ENTER"
    
    def _calculate_final_score(
        self,
        traffic_result,
        best_edge: float,
        net_edge: float,
        v_kelly_position: float,
        trend_aligned: bool,
        breakout_confidence: str,
        cost_profitable: bool
    ) -> float:
        """Calculate final score (0-100) incorporating all filters."""
        
        score = 0.0
        
        # 1. Traffic Light (30%) - More granular
        if traffic_result.signal == Signal.GREEN:
            score += 30
        elif traffic_result.signal == Signal.YELLOW:
            score += 20
        elif traffic_result.signal == Signal.ORANGE:
            score += 10
        # RED = 0
        
        # 2. Net Edge after costs (25%) - Granular scale
        if net_edge > 0:
            # Scale: 0.1% = 5 points, 0.5% = 25 points (max)
            edge_score = min(25, (net_edge / 0.50) * 25)
            score += edge_score
        elif net_edge < 0:
            # Penalize negative edge
            score += max(-10, (net_edge / 0.50) * 10)
        
        # 3. V-Kelly Position Size (15%) - Reward lower volatility
        # Higher v-kelly position = lower volatility = better
        kelly_score = min(15, (v_kelly_position / 5.0) * 15)
        score += kelly_score
        
        # 4. Trend alignment (15%)
        if trend_aligned:
            score += 15
        
        # 5. Volatility breakout (10%)
        if breakout_confidence == "EXTREME":
            score += 10
        elif breakout_confidence == "HIGH":
            score += 8
        elif breakout_confidence == "MEDIUM":
            score += 5
        elif breakout_confidence == "LOW":
            score += 2
        
        # 6. Cost profitability (5%)
        if cost_profitable:
            score += 5
        
        return max(0, min(100, score))
    
    def _apply_regime_multiplier(self, results: List[InstrumentScoreV22]):
        """Apply regime multiplier to all results based on market conditions."""
        
        # Collect all signals for regime detection
        signal_counts = {
            Signal.GREEN: sum(1 for r in results if r.signal == Signal.GREEN),
            Signal.YELLOW: sum(1 for r in results if r.signal == Signal.YELLOW),
            Signal.ORANGE: sum(1 for r in results if r.signal == Signal.ORANGE),
            Signal.RED: sum(1 for r in results if r.signal == Signal.RED)
        }
        
        regime_result = self.regime_detector.detect_regime(signal_counts)
        
        # Apply multiplier to all
        for result in results:
            result.regime_multiplier = regime_result.position_size_multiplier
            result.final_allocation *= regime_result.position_size_multiplier
    
    def _signal_to_text(self, signal: Signal) -> str:
        """Convert Signal enum to text."""
        if signal == Signal.GREEN:
            return "GREEN"
        elif signal == Signal.YELLOW:
            return "YELLOW"
        elif signal == Signal.ORANGE:
            return "ORANGE"
        else:
            return "RED"


def format_v22_report(results: List[InstrumentScoreV22]) -> str:
    """Format V2.2 screener report."""
    lines = []
    lines.append("=" * 100)
    lines.append("📊 INSTRUMENT SCREENER V2.2 - CASINO-STYLE RISK IMPROVEMENTS")
    lines.append("=" * 100)
    lines.append("")
    
    # Signal overview
    green = [r for r in results if r.signal == Signal.GREEN]
    yellow = [r for r in results if r.signal == Signal.YELLOW]
    orange = [r for r in results if r.signal == Signal.ORANGE]
    red = [r for r in results if r.signal == Signal.RED]
    
    lines.append("🚦 SIGNAL DISTRIBUTION")
    lines.append("-" * 100)
    lines.append(f"GREEN  (Strong Buy):  {len(green)} | YELLOW (Cautious):  {len(yellow)} | "
                f"ORANGE (Neutral): {len(orange)} | RED (Avoid): {len(red)}")
    lines.append("")
    
    # Market regime
    if results:
        regime_mult = results[0].regime_multiplier
        if regime_mult <= 0.2:
            regime_text = "CRISIS (0.2x positions)"
        elif regime_mult <= 0.4:
            regime_text = "STRESSED (0.4x positions)"
        elif regime_mult <= 0.7:
            regime_text = "CAUTIOUS (0.7x positions)"
        else:
            regime_text = "HEALTHY (1.0x positions)"
        
        lines.append(f"📈 MARKET REGIME: {regime_text}")
        lines.append("")
    
    # Top opportunities
    actionable = [r for r in results if r.entry_recommendation.startswith("ENTER")]
    
    if actionable:
        lines.append("✅ TOP OPPORTUNITIES (ENTER SIGNALS)")
        lines.append("-" * 100)
        lines.append(f"{'Rank':<5} {'Instrument':<25} {'Signal':<8} {'Net Edge':<10} "
                    f"{'Alloc%':<8} {'Breakout':<12} {'Entry':<20}")
        lines.append("-" * 100)
        
        for i, r in enumerate(actionable[:10], 1):
            signal_text = "GREEN" if r.signal == Signal.GREEN else "YELLOW" if r.signal == Signal.YELLOW else "ORANGE"
            lines.append(
                f"{i:<5} {r.name[:23]:<25} {signal_text:<8} "
                f"{r.net_edge_after_costs:>7.2f}%  "
                f"{r.final_allocation:>6.2f}%  "
                f"{r.volatility_regime[:10]:<12} "
                f"{r.entry_recommendation[:18]:<20}"
            )
        lines.append("")
    
    # Wait signals
    wait_signals = [r for r in results if "WAIT" in r.entry_recommendation or "CAUTIOUS" in r.entry_recommendation]
    
    if wait_signals:
        lines.append("⏳ WAIT FOR BETTER TIMING")
        lines.append("-" * 100)
        for r in wait_signals[:5]:
            lines.append(f"  {r.name}: {r.entry_recommendation}")
        lines.append("")
    
    # Blocked
    blocked = [r for r in results if "BLOCK" in r.entry_recommendation]
    
    if blocked:
        lines.append(f"🚫 BLOCKED: {len(blocked)} instruments")
        lines.append("  Reasons: Below 200-day MA, negative net edge, contracting volatility")
        lines.append("")
    
    # Summary
    lines.append("=" * 100)
    lines.append("SUMMARY")
    lines.append(f"Total Analyzed: {len(results)} | Actionable: {len(actionable)} | "
                f"Wait: {len(wait_signals)} | Blocked: {len(blocked)}")
    
    if actionable:
        total_allocation = sum(r.final_allocation for r in actionable)
        lines.append(f"Recommended Total Allocation: {total_allocation:.1f}%")
    
    lines.append("=" * 100)
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Instrument Screener V2.2")
    print("\nRun with:")
    print("  from instrument_screener_v22 import InstrumentScreenerV22")
    print("  from instruments_universe import get_instruments_universe")
    print("  ")
    print("  screener = InstrumentScreenerV22(enable_v22_filters=True)")
    print("  instruments = get_instruments_universe()")
    print("  results = screener.screen_instruments(instruments)")
    print("  print(format_v22_report(results))")
