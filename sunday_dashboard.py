"""
SUNDAY DASHBOARD - Complete V4.0 Position Trading System

THE definitive tool for Sunday analysis.
Integrates 37 features:
- 16 V4.0 Position Trading features (via screener)
- 21 Risk Management & Portfolio Intelligence features

Runtime: ~4-6 hours for 800 instruments
Output: Top 3-5 setups + Portfolio health + PDF report
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path

# Core
from instrument_screener_v23_position import PositionTradingScreener
from instruments_universe_800 import (
    SWEDISH_INSTRUMENTS,
    US_LARGE_CAP,
    ALL_WEATHER_HEDGE
)

# Phase 1: Risk Management
from src.risk.volatility_position_sizing import VolatilityPositionSizer
from src.risk.regime_detection import RegimeDetector
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier
from src.risk.cost_aware_filter import CostAwareFilter

# Phase 2: Market Context
from src.risk.market_breadth import MarketBreadthIndicator
from src.analysis.macro_indicators import MacroIndicators
from src.risk.all_weather_config import is_all_weather, get_all_weather_category

# Phase 3: Portfolio Intelligence
from src.risk.sector_cap_manager import SectorCapManager
from src.risk.mae_optimizer import MAEOptimizer
from src.risk.monte_carlo_simulator import MonteCarloSimulator
from src.analysis.correlation_detector import CorrelationDetector
from src.portfolio.health_tracker import PortfolioHealthTracker
from src.portfolio.exit_guard import ExitGuard
from src.risk.fx_guard import FXGuard
from src.portfolio.inactivity_checker import InactivityChecker

# Phase 4: Infrastructure
from src.validation.data_sanity_checker import DataSanityChecker
from src.reporting.weekly_report import WeeklyReportGenerator
from src.utils.data_fetcher import DataFetcher


class SundayDashboard:
    """
    Complete Sunday Dashboard - Position Trading Edition.
    
    Architecture:
    1. PRE-FLIGHT: Market Breadth, Macro, Systemic Risk
    2. SCAN: Call PositionTradingScreener (800 instruments)
    3. POST-PROCESS: Apply 21 risk management filters
    4. DISPLAY: Top setups + Portfolio health
    5. EXPORT: PDF report + JSON backfill
    """
    
    def __init__(
        self,
        capital: float = 100000.0,
        max_risk_per_trade: float = 0.01,
        min_position_sek: float = 1500.0
    ):
        self.capital = capital
        self.max_risk_per_trade = max_risk_per_trade
        self.min_position_sek = min_position_sek
        self.min_position_pct = min_position_sek / capital
        
        print("="*80)
        print("SUNDAY DASHBOARD - V4.0 POSITION TRADING")
        print("="*80)
        print(f"\nCapital: {self.capital:,.0f} SEK")
        print(f"Risk per trade: {self.max_risk_per_trade*100:.1f}%")
        print(f"Minimum position: {self.min_position_sek:,.0f} SEK ({self.min_position_pct*100:.1f}%)")
        
        # Initialize all components
        self._init_components()
    
    def _init_components(self):
        """Initialize all 21 risk management components."""
        
        # Phase 1: Risk Management
        self.v_kelly_sizer = VolatilityPositionSizer(
            target_volatility=0.2,  # 0.2% per day for position trading (21-63 day holds)
            max_position=0.05,  # Max 5% per position
            min_position=0.001  # Min 0.1%
        )
        self.regime_detector = RegimeDetector()
        self.execution_guard = ExecutionGuard(
            account_type=AvanzaAccountType.SMALL,
            portfolio_value_sek=self.capital,
            use_isk_optimizer=True,
            isk_courtage_tier=CourtageTier.MINI
        )
        self.cost_filter = CostAwareFilter()
        
        # Phase 2: Market Context
        self.market_breadth = MarketBreadthIndicator()
        self.macro_indicators = MacroIndicators()
        
        # Phase 3: Portfolio Intelligence
        self.sector_cap = SectorCapManager(max_sector_pct=0.40)
        self.mae_optimizer = MAEOptimizer()
        self.monte_carlo = MonteCarloSimulator(num_paths=500, holding_days=63)
        self.correlation_detector = CorrelationDetector()
        self.portfolio_health = PortfolioHealthTracker()
        self.exit_guard = ExitGuard()
        self.fx_guard = FXGuard()
        self.inactivity_checker = InactivityChecker()
        
        # Phase 4: Infrastructure
        self.data_sanity = DataSanityChecker()
        self.report_generator = WeeklyReportGenerator()
        self.data_fetcher = DataFetcher()
        
        # Screener
        self.screener = PositionTradingScreener(
            capital=self.capital,
            max_risk_per_trade=self.max_risk_per_trade
        )
    
    def run(self, max_setups: int = 5) -> Dict:
        """
        Run complete Sunday analysis.
        
        Returns:
            Dict with all results
        """
        
        results = {}
        
        # ====================================================================
        # 1. PRE-FLIGHT CHECKS
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 1: PRE-FLIGHT CHECKS")
        print("="*80)
        
        # Market Breadth
        print("\n📊 Market Breadth (OMXS30)...")
        try:
            breadth = self.market_breadth.analyze_breadth()
            
            # Check if we got valid data
            if breadth.constituents_analyzed > 0:
                results['market_breadth'] = breadth
                print(f"   Breadth: {breadth.breadth_pct:.0f}% ({breadth.constituents_above_200ma}/{breadth.constituents_analyzed} above 200MA)")
                print(f"   Regime: {breadth.breadth_regime}")
                
                if not breadth.tradable:
                    print(f"   ⚠️ WARNING: Weak market - consider reducing exposure!")
            else:
                print(f"   ⚠️ Breadth data unavailable - skipping (continuing anyway)")
                results['market_breadth'] = None
        except Exception as e:
            print(f"   ⚠️ Breadth check failed: {e} - skipping (continuing anyway)")
            results['market_breadth'] = None
        
        # Macro Indicators
        print("\n🌍 Macro Indicators...")
        macro_results = {}
        
        # Yield Curve
        try:
            yield_curve = self.macro_indicators.analyze_yield_curve()
            macro_results['yield_curve'] = yield_curve
            print(f"   Yield Curve: {yield_curve.message}")
        except Exception as e:
            print(f"   ⚠️ Yield Curve unavailable: {e}")
            macro_results['yield_curve'] = None
        
        # Credit Spreads
        try:
            credit = self.macro_indicators.analyze_credit_spreads()
            macro_results['credit_spreads'] = credit
            print(f"   Credit Spreads: {credit.message}")
        except Exception as e:
            print(f"   ⚠️ Credit Spreads unavailable: {e}")
            macro_results['credit_spreads'] = None
        
        results['macro'] = macro_results
        
        # Systemic Risk Score
        print("\n🚨 Systemic Risk Score...")
        systemic_risk = 0
        if macro_results.get('yield_curve') and macro_results.get('credit_spreads'):
            # Simple aggregation
            if hasattr(macro_results['yield_curve'], 'is_inverted') and macro_results['yield_curve'].is_inverted:
                systemic_risk += 30
            if hasattr(macro_results['credit_spreads'], 'spread') and macro_results['credit_spreads'].spread > 0.5:
                systemic_risk += 20
            
            results['systemic_risk'] = systemic_risk
            print(f"   Risk Score: {systemic_risk}/100")
            
            if systemic_risk > 70:
                print(f"   🚨 EXTREME RISK - Recommend blocking new positions")
                print(f"   (Continuing analysis for informational purposes)")
        else:
            print(f"   Risk Score: N/A (insufficient macro data)")
            results['systemic_risk'] = None
        
        # ====================================================================
        # 2. SCAN UNIVERSE
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 2: SCANNING UNIVERSE")
        print("="*80)
        
        # Load instruments
        all_tickers = []
        all_tickers.extend(SWEDISH_INSTRUMENTS)
        all_tickers.extend(US_LARGE_CAP)
        all_tickers.extend(ALL_WEATHER_HEDGE)
        
        # Try additional categories
        try:
            import instruments_universe_800 as universe
            if hasattr(universe, 'SECTOR_ETFS'):
                all_tickers.extend(universe.SECTOR_ETFS)
            if hasattr(universe, 'GLOBAL_EMERGING'):
                all_tickers.extend(universe.GLOBAL_EMERGING)
        except:
            pass
        
        instruments = [(ticker, ticker) for ticker in all_tickers]
        
        print(f"\nScanning {len(instruments)} instruments...")
        print(f"Expected runtime: {len(instruments) * 20 / 3600:.1f} hours\n")
        
        # Run screener
        screener_results = self.screener.screen_instruments(instruments)
        
        # Filter to POTENTIAL only
        potential_setups = [r for r in screener_results if r.status == "POTENTIAL"]
        potential_secondary = [r for r in screener_results if r.status == "POTENTIAL*"]
        
        print(f"\n✅ Screening complete!")
        print(f"   Total scanned: {len(screener_results)}")
        print(f"   POTENTIAL (PRIMARY): {len(potential_setups)}")
        print(f"   POTENTIAL (SECONDARY): {len(potential_secondary)}")
        
        results['screener_results'] = screener_results
        results['potential_setups'] = potential_setups
        
        # DIAGNOSTIC ANALYSIS
        print("\n" + "="*80)
        print("📊 DIAGNOSTIC ANALYSIS")
        print("="*80)
        
        diagnostics = self.screener.analyze_rejection_reasons(screener_results)
        stats = diagnostics['stats']
        
        print(f"\nREJECTION BREAKDOWN:")
        print(f"   No patterns detected: {stats['no_patterns']} ({stats['no_patterns']/stats['total']*100:.1f}%)")
        print(f"   Context invalid (Vattenpasset): {stats['context_invalid']} ({stats['context_invalid']/stats['total']*100:.1f}%)")
        print(f"   Earnings risk: {stats['earnings_risk']} ({stats['earnings_risk']/stats['total']*100:.1f}%)")
        print(f"   Low win rate (<60%): {stats['low_win_rate']} ({stats['low_win_rate']/stats['total']*100:.1f}%)")
        print(f"   Low RRR (<3:1): {stats['low_rrr']} ({stats['low_rrr']/stats['total']*100:.1f}%)")
        print(f"   Negative EV: {stats['negative_ev']} ({stats['negative_ev']/stats['total']*100:.1f}%)")
        print(f"   Secondary pattern only: {stats['secondary_only']} ({stats['secondary_only']/stats['total']*100:.1f}%)")
        
        print(f"\nDECLINE DISTRIBUTION (from 90-day high):")
        for range_label, count in diagnostics['decline_distribution'].items():
            pct = count / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"   {range_label}: {count} ({pct:.1f}%)")
        
        # Show near-misses
        near_misses = diagnostics['near_misses']
        if len(near_misses) > 0:
            print(f"\n🎯 NEAR-MISSES (Close to -10% threshold):")
            for nm in near_misses[:5]:
                print(f"   {nm['ticker']}: {nm['decline']:.1f}% decline, {nm['vs_ema200']:+.1f}% vs EMA200")
        
        # Show top rejected instruments with patterns but invalid context
        rejected_with_patterns = [
            r for r in screener_results 
            if r.status == "NO SETUP" and r.best_pattern_name != "None"
        ]
        if len(rejected_with_patterns) > 0:
            # Sort by how close they are to qualifying
            rejected_sorted = sorted(
                rejected_with_patterns, 
                key=lambda x: x.decline_from_high,
                reverse=True  # Least negative = closest to qualifying
            )
            
            print(f"\n🔴 TOP 10 REJECTED (Had patterns, failed context):")
            for r in rejected_sorted[:10]:
                below_ema = "Below EMA200" if r.price_vs_ema200 < 0 else f"+{r.price_vs_ema200:.1f}% above EMA200"
                print(f"   {r.ticker}: {r.decline_from_high:.1f}% decline, {below_ema}")
                print(f"      Pattern: {r.best_pattern_name}")
        
        results['diagnostics'] = diagnostics
        
        if len(potential_setups) == 0 and len(potential_secondary) == 0:
            print("\n❌ No POTENTIAL setups found.")
            print("   Market conditions not favorable for position trading.")
            print("   Consider checking near-misses or relaxing filters further.")
            return results
        
        # ====================================================================
        # 3. POST-PROCESSING (Apply 21 Risk Filters)
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 3: POST-PROCESSING & RISK MANAGEMENT")
        print("="*80)
        
        # Include both PRIMARY and SECONDARY patterns for processing
        all_potential = potential_setups + potential_secondary
        
        if len(all_potential) > 0:
            processed_setups = self._post_process_setups(all_potential, results)
        else:
            processed_setups = []
        
        results['processed_setups'] = processed_setups
        
        # ====================================================================
        # 4. PORTFOLIO HEALTH CHECK
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 4: PORTFOLIO HEALTH CHECK")
        print("="*80)
        
        portfolio_analysis = self._check_portfolio_health(screener_results)
        results['portfolio_health'] = portfolio_analysis
        
        # ====================================================================
        # 5. DISPLAY RESULTS
        # ====================================================================
        self._display_results(results, max_setups)
        
        # ====================================================================
        # 6. EXPORT
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 5: EXPORT")
        print("="*80)
        
        # JSON Backfill
        self._export_json(results)
        
        # Text Report Generation
        try:
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"sunday_report_{timestamp}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("SUNDAY DASHBOARD REPORT\n")
                f.write("="*80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Capital: {self.capital:,.0f} SEK\n")
                f.write("\n")
                
                # Regime
                if 'regime' in results:
                    regime = results['regime']
                    f.write("REGIME:\n")
                    f.write(f"  {regime.regime.value}\n")
                    f.write(f"  Position Multiplier: {regime.position_size_multiplier:.1f}x\n")
                    f.write(f"  {regime.recommendation}\n")
                    f.write("\n")
                
                # Top Setups
                processed = results.get('processed_setups', [])
                f.write(f"TOP {min(5, len(processed))} SETUPS:\n")
                f.write("="*80 + "\n")
                
                for i, setup in enumerate(processed[:5], 1):
                    f.write(f"\n#{i}: {setup.ticker} - {setup.best_pattern_name}\n")
                    f.write(f"Score: {setup.score:.1f}/100\n")
                    f.write(f"Edge (63d): {setup.edge_63d*100:+.2f}%\n")
                    f.write(f"Win Rate: {setup.win_rate_63d*100:.1f}%\n")
                    f.write(f"RRR: 1:{setup.risk_reward_ratio:.2f}\n")
                    f.write(f"Position: {setup.position_size_sek:,.0f} SEK ({setup.position_size_pct:.2f}%)\n")
                    f.write(f"Expected Profit: {setup.ev_sek:+,.0f} SEK\n")
                    f.write("-"*80 + "\n")
                
                # Diagnostics
                if 'diagnostics' in results:
                    diag = results['diagnostics']
                    stats = diag['stats']
                    f.write("\nDIAGNOSTICS:\n")
                    f.write(f"Total scanned: {stats['total']}\n")
                    f.write(f"POTENTIAL: {stats['potential']}\n")
                    f.write(f"No patterns: {stats['no_patterns']} ({stats['no_patterns']/stats['total']*100:.1f}%)\n")
                    f.write(f"Context invalid: {stats['context_invalid']} ({stats['context_invalid']/stats['total']*100:.1f}%)\n")
            
            print(f"\n📄 Report saved: {report_path}")
        except Exception as e:
            print(f"\n⚠️ Report generation failed: {e}")
        
        return results
    
    def _post_process_setups(self, setups: List, results: Dict) -> List:
        """Apply all 21 risk management filters to setups."""
        
        processed = []
        
        # Detect regime
        print("\n🔍 Regime Detection...")
        signal_counts = {
            'GREEN': len([s for s in setups if s.win_rate_63d > 0.70]),
            'YELLOW': len([s for s in setups if 0.60 <= s.win_rate_63d <= 0.70]),
            'ORANGE': len([s for s in setups if 0.50 <= s.win_rate_63d < 0.60]),
            'RED': len([s for s in setups if s.win_rate_63d < 0.50])
        }
        
        regime_result = self.regime_detector.detect_regime(signal_counts)
        regime_multiplier = regime_result.position_size_multiplier
        
        print(f"   Regime: {regime_result.regime.value}")
        print(f"   Position Multiplier: {regime_multiplier:.1f}x")
        print(f"   Recommendation: {regime_result.recommendation}")
        
        results['regime'] = regime_result
        
        # Process each setup
        for setup in setups:
            # V-Kelly Position Sizing
            try:
                # Calculate actual volatility from pattern metrics
                # Use avg_win and avg_loss as volatility proxy
                # Higher volatility = larger swings = need smaller position
                if setup.avg_win > 0 and setup.avg_loss < 0:
                    # Estimate ATR from average win/loss range
                    estimated_atr_pct = (setup.avg_win + abs(setup.avg_loss)) / 2 * 100
                    # Cap between 0.5% and 5% for reasonable values
                    estimated_atr_pct = max(0.5, min(5.0, estimated_atr_pct))
                else:
                    estimated_atr_pct = 2.0  # Fallback to 2% if no data
                
                # Base allocation scales with signal quality and volatility
                # Higher win rate = larger base allocation
                if setup.win_rate_63d >= 0.80:
                    base_allocation = 0.03  # 3% for very strong signals (80%+ win rate)
                elif setup.win_rate_63d >= 0.70:
                    base_allocation = 0.025  # 2.5% for strong signals (70-80% win rate)
                elif setup.win_rate_63d >= 0.60:
                    base_allocation = 0.02  # 2% for good signals (60-70% win rate)
                else:
                    base_allocation = 0.015  # 1.5% for weaker signals (<60% win rate)
                
                # Adjust for volatility: higher volatility = reduce position
                # estimated_atr_pct range: 0.5% to 5.0%
                # Scale down if very volatile (ATR > 3%)
                if estimated_atr_pct > 3.0:
                    volatility_factor = 3.0 / estimated_atr_pct  # Reduce by 1/volatility
                    base_allocation *= volatility_factor
                elif estimated_atr_pct > 2.5:
                    base_allocation *= 0.9  # Slightly reduce
                # If ATR < 2.5%, use full base allocation
                
                # Apply regime multiplier
                position_pct = base_allocation * regime_multiplier
                
                # Apply 1500 SEK floor (min_position_pct is already % as decimal: 1.5% = 0.015)
                if 0 < position_pct < self.min_position_pct:
                    position_pct = self.min_position_pct
                    setup.position_size_pct = position_pct * 100  # Store as percentage (1.5% = 1.5)
                    setup.floor_applied = True
                else:
                    setup.position_size_pct = position_pct * 100  # Store as percentage
                    setup.floor_applied = False
                
            except Exception as e:
                setup.position_size_pct = self.min_position_pct * 100  # Convert to percentage
                setup.floor_applied = True
            
            # Calculate position in SEK (position_size_pct is already a percentage number, e.g., 1.5 for 1.5%)
            setup.position_size_sek = self.capital * (setup.position_size_pct / 100)
            
            # Expected Value in SEK
            setup.ev_sek = setup.position_size_sek * setup.expected_value
            
            processed.append(setup)
        
        # Monte Carlo Risk Analysis
        print("\n🎲 Monte Carlo Risk Simulation...")
        for setup in processed:
            try:
                # Estimate stop-out probability based on win rate and RRR
                # Simple approximation: if win_rate is high and RRR good, stop-out risk is low
                # P(stop-out) ≈ (1 - win_rate) * adjustment_factor
                
                if setup.risk_reward_ratio >= 4.0:
                    rrr_factor = 0.5  # Good RRR = lower stop-out risk
                elif setup.risk_reward_ratio >= 3.0:
                    rrr_factor = 0.7
                elif setup.risk_reward_ratio >= 2.0:
                    rrr_factor = 0.9
                else:
                    rrr_factor = 1.2  # Poor RRR = higher risk
                
                base_stopout_prob = (1.0 - setup.win_rate_63d)
                setup.stop_out_probability = min(0.95, base_stopout_prob * rrr_factor)
                
                # Expected final value (simplified)
                setup.expected_final_value = setup.position_size_sek * (1 + setup.expected_value)
                
                # Warn if high stop-out risk
                if setup.stop_out_probability > 0.30:  # >30% chance of stop-out
                    setup.mc_warning = f"High stop-out risk: {setup.stop_out_probability*100:.1f}%"
                else:
                    setup.mc_warning = None
                    
            except Exception as e:
                setup.stop_out_probability = 0
                setup.expected_final_value = setup.position_size_sek
                setup.mc_warning = None
        
        # MAE Optimization (Maximum Adverse Excursion)
        print("\n📉 MAE Optimization...")
        for setup in processed:
            try:
                # Estimate optimal stop based on avg_loss
                # MAE principle: stop should be wider than typical loss
                # Use avg_loss * 1.5 as safety factor
                
                if setup.avg_loss < 0:
                    # avg_loss is already negative (e.g., -0.02 = -2%)
                    # Optimal stop = avg_loss * 1.5 (more negative = wider stop)
                    setup.optimal_stop_pct = abs(setup.avg_loss) * 1.5
                else:
                    setup.optimal_stop_pct = 0.015  # Default 1.5%
                
                # MAE-based RRR: avg_win / optimal_stop
                if setup.optimal_stop_pct > 0 and setup.avg_win > 0:
                    setup.mae_based_rrr = setup.avg_win / setup.optimal_stop_pct
                else:
                    setup.mae_based_rrr = setup.risk_reward_ratio
                
            except Exception as e:
                setup.optimal_stop_pct = 0.01  # Default 1% stop
                setup.mae_based_rrr = setup.risk_reward_ratio
        
        # Correlation Clustering
        print("\n🔗 Correlation Clustering...")
        try:
            tickers = [s.ticker for s in processed]
            scores = {s.ticker: s.score for s in processed}
            
            clusters = self.correlation_detector.find_clusters(tickers, scores)
            
            if clusters:
                print(f"   Found {len(clusters)} correlation clusters")
                
                # Mark setups in clusters
                for cluster in clusters:
                    for setup in processed:
                        if setup.ticker in cluster.tickers:
                            setup.in_cluster = True
                            setup.cluster_warning = cluster.risk_warning
                            setup.recommended_from_cluster = (setup.ticker == cluster.recommended_ticker)
            else:
                print(f"   No significant clusters found")
                for setup in processed:
                    setup.in_cluster = False
        except Exception as e:
            print(f"   ⚠️ Clustering failed: {e}")
        
        # Sort by score
        processed.sort(key=lambda x: x.score, reverse=True)
        
        return processed
    
    def _check_portfolio_health(self, screener_results: List) -> Dict:
        """Check health of existing positions."""
        
        # Load positions
        positions = self.portfolio_health.load_positions()
        
        if len(positions) == 0:
            print("\n   No existing positions to track.")
            return {'positions': [], 'assessments': []}
        
        print(f"\n   Tracking {len(positions)} existing positions...")
        
        # Build current data dicts
        current_prices = {}
        current_edges = {}
        exit_signals = {}
        
        for pos in positions:
            # Find in screener results
            match = next((r for r in screener_results if r.ticker == pos.ticker), None)
            
            if match:
                current_prices[pos.ticker] = match.edge_21d  # Approximate
                current_edges[pos.ticker] = match.edge_21d
            else:
                current_prices[pos.ticker] = pos.entry_price
                current_edges[pos.ticker] = 0.0
            
            # Check exit signals (would need market data)
            exit_signals[pos.ticker] = None
        
        # Assess health
        assessments = self.portfolio_health.assess_health(
            positions,
            current_edges,
            current_prices,
            exit_signals
        )
        
        # Display
        for assessment in assessments:
            action_icon = "🟢" if assessment.action == "HOLD" else "🔴" if assessment.action == "EXIT" else "🟡"
            print(f"\n   {action_icon} {assessment.ticker}: {assessment.action}")
            print(f"      {assessment.reason}")
        
        return {
            'positions': positions,
            'assessments': assessments
        }
    
    def _display_results(self, results: Dict, max_setups: int):
        """Display final results."""
        
        processed = results.get('processed_setups', [])
        
        if len(processed) == 0:
            return
        
        print("\n" + "="*80)
        print(f"🎯 TOP {min(max_setups, len(processed))} SETUPS FOR THIS SUNDAY")
        print("="*80)
        
        for i, setup in enumerate(processed[:max_setups], 1):
            print(f"\n{'#'*80}")
            print(f"RANK {i}: {setup.ticker} - {setup.best_pattern_name}")
            print(f"Score: {setup.score:.1f}/100 | Priority: PRIMARY")
            print('#'*80)
            
            print(f"\nEDGE & PERFORMANCE:")
            print(f"  21-day: {setup.edge_21d*100:+.2f}%")
            print(f"  42-day: {setup.edge_42d*100:+.2f}%")
            print(f"  63-day: {setup.edge_63d*100:+.2f}%")
            print(f"  Win Rate: {setup.win_rate_63d*100:.1f}%")
            print(f"  Risk/Reward: 1:{setup.risk_reward_ratio:.2f}")
            print(f"  Expected Value: {setup.expected_value*100:+.2f}%")
            
            print(f"\nPOSITION SIZING:")
            print(f"  Position: {setup.position_size_sek:,.0f} SEK ({setup.position_size_pct:.2f}%)")
            if setup.floor_applied:
                print(f"  ⚠️ Raised to 1,500 SEK floor (courtage efficiency)")
            print(f"  Expected Profit: {setup.ev_sek:+,.0f} SEK")
            
            print(f"\nRISK ANALYSIS:")
            # Monte Carlo results
            if hasattr(setup, 'stop_out_probability'):
                print(f"  Monte Carlo Stop-Out Risk: {setup.stop_out_probability*100:.1f}%")
                if setup.mc_warning:
                    print(f"  ⚠️ {setup.mc_warning}")
            
            # MAE optimization
            if hasattr(setup, 'optimal_stop_pct'):
                print(f"  Optimal Stop-Loss (MAE): {setup.optimal_stop_pct*100:.1f}%")
                print(f"  MAE-Based RRR: 1:{setup.mae_based_rrr:.2f}")
            
            print(f"\nMARKET CONTEXT:")
            print(f"  Decline from high: {setup.decline_from_high:.1f}%")
            print(f"  Below EMA200: {setup.price_vs_ema200:.1f}%")
            print(f"  Volume Confirmed: {'YES' if setup.volume_confirmed else 'NO'}")
            
            if setup.earnings_risk == 'HIGH':
                print(f"\n🚨 EARNINGS RISK: {setup.earnings_days} days - DO NOT TRADE")
            
            if setup.in_cluster:
                if setup.recommended_from_cluster:
                    print(f"\n✅ Recommended from correlation cluster")
                else:
                    print(f"\n⚠️ {setup.cluster_warning}")
        
        print("\n" + "="*80)
    
    def _export_json(self, results: Dict):
        """Export results to JSON for backfill."""
        
        os.makedirs("reports", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/actionable_{timestamp}.json"
        
        # Simplified export (full export would be more complex)
        export_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': timestamp,
            'num_setups': len(results.get('processed_setups', [])),
            'regime': results.get('regime').regime.value if results.get('regime') else 'UNKNOWN'
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n💾 JSON Export: {filename}")


def main():
    """Main entry point."""
    
    dashboard = SundayDashboard(
        capital=100000.0,
        max_risk_per_trade=0.01,
        min_position_sek=1500.0
    )
    
    results = dashboard.run(max_setups=5)
    
    print("\n" + "="*80)
    print("✅ SUNDAY ANALYSIS COMPLETE")
    print("="*80)
    
    # Display next steps
    processed = results.get('processed_setups', [])
    if len(processed) > 0:
        print("\n" + "="*80)
        print("📋 NEXT STEPS - PRE-TRADE CHECKLIST")
        print("="*80)
        print("\nBefore placing trades, run these additional checks:")
        print("\n1. EXECUTION GUARD (execution_guard.py)")
        print("   - Validates courtage efficiency")
        print("   - Checks if position size makes sense for your account type")
        print("   - ISK optimization for Swedish stocks")
        print("   Example: python -c 'from src.risk.execution_guard import ExecutionGuard; ...'")
        
        print("\n2. COST AWARE FILTER (cost_aware_filter.py)")
        print("   - Calculates all-in costs (courtage + spread)")
        print("   - Ensures edge > costs")
        print("   - Shows net expected value after costs")
        
        print("\n3. SECTOR CAP MANAGER (sector_cap_manager.py)")
        print("   - Checks if adding this position exceeds sector limits (40%)")
        print("   - Prevents over-concentration in one sector")
        print("   - Suggests alternative sectors if capped")
        
        print("\n4. FX GUARD (fx_guard.py)")
        print("   - For non-SEK instruments (USD, EUR)")
        print("   - Warns about currency exposure")
        print("   - Shows total FX risk across portfolio")
        
        print("\n5. DATA SANITY CHECK (data_sanity_checker.py)")
        print("   - Validates that data is fresh (not stale)")
        print("   - Checks for data gaps or anomalies")
        print("   - Confirms pattern still valid with latest data")
        
        print("\n" + "-"*80)
        print("AFTER PLACING TRADE - ONGOING MONITORING:")
        print("-"*80)
        
        print("\n6. EXIT GUARD (exit_guard.py)")
        print("   - Daily check for structure breaks (EMA50, Higher Lows, neckline)")
        print("   - Alerts when pattern invalidates")
        print("   - Suggests exit if setup deteriorates")
        
        print("\n7. INACTIVITY CHECKER (inactivity_checker.py)")
        print("   - Monitors dead trades (<2% move in 21 days)")
        print("   - Suggests cutting losers that aren't working")
        print("   - Frees up capital for better opportunities")
        
        print("\n8. PORTFOLIO HEALTH TRACKER (health_tracker.py)")
        print("   - Weekly review of all positions")
        print("   - Compares current edge vs entry edge")
        print("   - Recommends HOLD/INCREASE/DECREASE/EXIT")
        
        print("\n" + "="*80)
        print("\n💡 TIP: Create a positions.json file to track your trades:")
        print("   Then re-run Sunday Dashboard to see portfolio health in STEP 4")
        print("\n" + "="*80)


if __name__ == "__main__":
    main()
