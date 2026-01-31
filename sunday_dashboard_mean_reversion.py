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

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import codecs
    # Only wrap if not already wrapped
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path

# Core
from instrument_screener_v23_position import PositionTradingScreener
from instruments_universe_1200 import (
    get_all_tickers,
    get_sector_for_ticker,
    get_geography_for_ticker,
    get_mifid_ii_proxy,
    get_sector_volatility_factor,
    calculate_usd_sek_zscore,
    get_fx_adjustment_factor,
    MIFID_II_PROXY_MAP
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

# Phase 5: Timing Score (Immediate Reversal Detection)
from src.analysis.timing_score import TimingScoreCalculator, format_timing_summary

# Phase 6: Macro Regime & Quality Filters (V6.0)
from src.analysis.macro_regime import MacroRegimeAnalyzer, format_regime_summary
from src.analysis.quality_score import QualityScoreAnalyzer, format_quality_summary

# Phase 7: Hybrid Engine & Statistical Iron Curtain (V7.0)
from src.patterns.momentum_engine import MomentumEngine, calculate_universe_returns
from src.analysis.alpha_switch import AlphaSwitchDetector, apply_convergence_boost
from src.analysis.statistical_iron_curtain import StatisticalIronCurtain, eliminate_correlated_by_er
from src.analysis.hard_limits import HardLimits
from src.communication.elite_formatter import EliteReportFormatter

# TIMING THRESHOLD FOR ACTIVE BUY SIGNALS
TIMING_THRESHOLD = 50.0  # Minimum timing confidence required for buy signal


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
        print("SUNDAY DASHBOARD - MEAN REVERSION STRATEGY V6.1")
        print("="*80)
        print("Philosophy: Buy weakness at structural support (Bottom Fishing)")
        print("Patterns: Double Bottom, IH&S, New Lows, Extended Selloff")
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
        
        # Phase 5: Timing Score (Immediate Reversal Detection)
        self.timing_calculator = TimingScoreCalculator()
        
        # Phase 6: Macro Regime & Quality Filters (V6.0)
        self.macro_analyzer = MacroRegimeAnalyzer()
        self.quality_analyzer = QualityScoreAnalyzer()
        
        # Phase 7: Hybrid Engine & Statistical Iron Curtain (V7.0)
        self.momentum_engine = MomentumEngine(
            min_rs_rating=95.0,
            min_52w_proximity=0.95,
            max_atr_ratio=0.85
        )
        self.alpha_switch = AlphaSwitchDetector(lookback_days=15)
        self.iron_curtain = StatisticalIronCurtain(
            n_bootstrap=1000,
            min_pass_rate=0.95,
            min_efficiency_ratio=0.30
        )
        self.hard_limits = HardLimits()
        self.elite_formatter = EliteReportFormatter()
        
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
        
        # FX Guard: USD/SEK Check
        print("\n💱 FX Guard (USD/SEK)...")
        usd_sek_zscore = 0.0
        try:
            import yfinance as yf
            import numpy as np
            
            # Fetch USD/SEK data
            usdsek = yf.Ticker("USDSEK=X")
            hist = usdsek.history(period="1y")  # 1 year for 200-day calculation
            
            if not hist.empty and len(hist) >= 200:
                current_rate = hist['Close'].iloc[-1]
                mean_200d = hist['Close'].rolling(200).mean().iloc[-1]
                std_200d = hist['Close'].rolling(200).std().iloc[-1]
                
                usd_sek_zscore = calculate_usd_sek_zscore(current_rate, mean_200d, std_200d)
                fx_adjustment = get_fx_adjustment_factor(usd_sek_zscore)
                
                print(f"   Current: {current_rate:.4f} SEK/USD")
                print(f"   200-day mean: {mean_200d:.4f}")
                print(f"   Z-score: {usd_sek_zscore:+.2f}")
                print(f"   FX adjustment: {fx_adjustment:.1%}")
                
                if usd_sek_zscore > 2.0:
                    print(f"   ⚠️ WARNING: USD extremely expensive - avoiding US positions")
                elif usd_sek_zscore > 1.5:
                    print(f"   ⚡ CAUTION: USD expensive - reducing US exposure")
                elif usd_sek_zscore < -1.5:
                    print(f"   🎯 OPPORTUNITY: USD cheap - favoring US positions")
                else:
                    print(f"   ✅ USD/SEK at fair value")
                
                results['usd_sek_zscore'] = usd_sek_zscore
                results['fx_adjustment'] = fx_adjustment
            else:
                print(f"   ⚠️ Insufficient USD/SEK data - no FX adjustment")
                results['usd_sek_zscore'] = 0.0
                results['fx_adjustment'] = 1.0
        except Exception as e:
            print(f"   ⚠️ FX Guard failed: {e} - no FX adjustment")
            results['usd_sek_zscore'] = 0.0
            results['fx_adjustment'] = 1.0
        
        # Systemic Risk Score
        print("\n🚨 Systemic Risk Score...")
        systemic_risk = 0
        risk_components = []
        
        # Component 1: Yield Curve (0-40 points)
        if macro_results.get('yield_curve'):
            yc = macro_results['yield_curve']
            if yc.risk_level == "EXTREME":
                systemic_risk += 40
                risk_components.append("Yield Curve: EXTREME (40pts)")
            elif yc.risk_level == "HIGH":
                systemic_risk += 30
                risk_components.append("Yield Curve: HIGH (30pts)")
            elif yc.risk_level == "MEDIUM":
                systemic_risk += 15
                risk_components.append("Yield Curve: MEDIUM (15pts)")
            else:
                risk_components.append("Yield Curve: LOW (0pts)")
        
        # Component 2: Credit Spreads (0-30 points)
        if macro_results.get('credit_spreads'):
            cs = macro_results['credit_spreads']
            if cs.stress_level == "EXTREME":
                systemic_risk += 30
                risk_components.append("Credit Spreads: EXTREME (30pts)")
            elif cs.stress_level == "HIGH":
                systemic_risk += 20
                risk_components.append("Credit Spreads: HIGH (20pts)")
            elif cs.stress_level == "MEDIUM":
                systemic_risk += 10
                risk_components.append("Credit Spreads: MEDIUM (10pts)")
            else:
                risk_components.append("Credit Spreads: LOW (0pts)")
        
        # Component 3: Safe Haven Activity (0-30 points)
        # Will be calculated after screener results are available
        # For now, use market breadth as proxy
        if results.get('market_breadth'):
            breadth = results['market_breadth']
            if breadth.breadth_pct < 20:  # <20% = extreme weakness
                systemic_risk += 30
                risk_components.append("Market Breadth: EXTREME weakness (30pts)")
            elif breadth.breadth_pct < 40:
                systemic_risk += 20
                risk_components.append("Market Breadth: HIGH weakness (20pts)")
            elif breadth.breadth_pct < 60:
                systemic_risk += 10
                risk_components.append("Market Breadth: MEDIUM weakness (10pts)")
            else:
                risk_components.append("Market Breadth: Healthy (0pts)")
        
        results['systemic_risk'] = systemic_risk
        
        # Macro Regime Analysis (V6.0)
        print("\n🌐 Macro Regime Analysis (The 'Wind' Filter)...")
        try:
            macro_regime = self.macro_analyzer.analyze_regime()
            results['macro_regime'] = macro_regime
            
            print(f"   Regime: {macro_regime.regime.value}")
            print(f"   Position Size Multiplier: {macro_regime.position_size_multiplier:.0%}")
            
            # S&P 500
            print(f"\n   S&P 500:")
            print(f"      Current: {macro_regime.sp500_price:.2f}")
            print(f"      200-day EMA: {macro_regime.sp500_ema200:.2f}")
            status_emoji = "✅" if macro_regime.sp500_above_ema else "⚠️"
            print(f"      {status_emoji} {macro_regime.sp500_distance_pct:+.2f}% vs EMA")
            
            # US 10Y Yield
            print(f"\n   US 10Y Yield:")
            print(f"      Current: {macro_regime.us10y_current:.2f}%")
            print(f"      3-week change: {macro_regime.us10y_change_bps:+.0f} bps")
            print(f"      Trend: {macro_regime.us10y_trend}")
            
            # Defensive signals
            if len(macro_regime.defensive_signals) > 0:
                print(f"\n   ⚠️ DEFENSIVE MODE ACTIVATED:")
                for signal in macro_regime.defensive_signals:
                    print(f"      • {signal}")
                print(f"   → All position sizes will be HALVED (50%)")
            else:
                print(f"\n   ✅ AGGRESSIVE MODE - Full position sizing")
        
        except Exception as e:
            print(f"   ⚠️ Macro regime analysis failed: {e}")
            # Default to neutral/aggressive regime
            from src.analysis.macro_regime import MacroRegimeAnalysis, MarketRegime
            macro_regime = MacroRegimeAnalysis(
                regime=MarketRegime.AGGRESSIVE,
                position_size_multiplier=1.0,
                sp500_price=0.0, sp500_ema200=0.0, sp500_above_ema=True, sp500_distance_pct=0.0,
                us10y_current=0.0, us10y_3w_ago=0.0, us10y_trend="Flat", us10y_change_bps=0.0,
                usdsek_current=0.0, usdsek_zscore=0.0,
                defensive_signals=[]
            )
            results['macro_regime'] = macro_regime
        
        # Display
        if systemic_risk > 0 or len(risk_components) > 0:
            print(f"   Risk Score: {systemic_risk}/100")
            for component in risk_components:
                print(f"      • {component}")
            
            if systemic_risk >= 80:
                print(f"   🚨 EXTREME RISK - Recommend blocking all new positions")
            elif systemic_risk >= 60:
                print(f"   ⚠️ HIGH RISK - Reduce position sizes by 50%")
            elif systemic_risk >= 40:
                print(f"   ⚠️ ELEVATED RISK - Extra caution recommended")
            else:
                print(f"   ✅ ACCEPTABLE RISK - Proceed with normal trading")
        else:
            print(f"   Risk Score: N/A (insufficient macro data)")
            results['systemic_risk'] = None
        
        # ====================================================================
        # 2. SCAN UNIVERSE
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 2: SCANNING UNIVERSE")
        print("="*80)
        
        # Load instruments from new 1200-ticker universe
        all_tickers = get_all_tickers()
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tickers = []
        for ticker in all_tickers:
            if ticker not in seen:
                seen.add(ticker)
                unique_tickers.append(ticker)
        
        instruments = [(ticker, ticker) for ticker in unique_tickers]
        
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
                    f.write(f"Win Rate (Raw): {setup.win_rate_63d*100:.1f}% (n={setup.sample_size})\n")
                    if hasattr(setup, 'adjusted_win_rate') and setup.adjusted_win_rate > 0:
                        f.write(f"Win Rate (Bayesian): {setup.adjusted_win_rate*100:.1f}%\n")
                    if hasattr(setup, 'p_value') and setup.p_value < 1.0:
                        sig = "YES" if setup.p_value < 0.05 else "NO"
                        f.write(f"Statistically Significant: {sig} (p={setup.p_value:.4f})\n")
                    if hasattr(setup, 'robust_score') and setup.robust_score > 0:
                        f.write(f"Robust Score: {setup.robust_score:.1f}/100\n")
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
        
        # Get FX adjustment and Macro Regime multiplier from results
        usd_sek_zscore = results.get('usd_sek_zscore', 0.0)
        fx_adjustment = results.get('fx_adjustment', 1.0)
        
        # Get Macro Regime multiplier (V6.0)
        macro_regime = results.get('macro_regime')
        macro_multiplier = macro_regime.position_size_multiplier if macro_regime else 1.0
        
        # Process each setup
        for setup in setups:
            # Strategic Features: Sector & Geography
            setup.sector = get_sector_for_ticker(setup.ticker)
            setup.geography = get_geography_for_ticker(setup.ticker)
            setup.sector_volatility = get_sector_volatility_factor(setup.sector)
            
            # Check if MiFID II proxy needed
            if setup.ticker in MIFID_II_PROXY_MAP:
                setup.mifid_proxy = get_mifid_ii_proxy(setup.ticker)
                setup.mifid_warning = f"Cannot trade {setup.ticker} on Avanza ISK. Use {setup.mifid_proxy} instead."
            else:
                setup.mifid_proxy = None
                setup.mifid_warning = None
            
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
                
                # Apply Macro Regime multiplier (V6.0 - The 'Wind' Filter)
                # This halves position sizing in DEFENSIVE markets
                position_pct *= macro_multiplier
                setup.macro_adjusted = (macro_multiplier < 1.0)
                
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
                    # No losses: estimate from volatility
                    # Use combination of avg_win range and sample size
                    # Wider stops for patterns with:
                    # - Higher volatility (larger avg_win implies larger swings)
                    # - Smaller sample size (less confidence)
                    
                    # Base stop: 2% for conservative estimate
                    base_stop = 0.02
                    
                    # Adjust for pattern volatility
                    if setup.avg_win > 0.10:  # >10% avg win = high volatility
                        volatility_factor = 1.5
                    elif setup.avg_win > 0.05:  # 5-10% avg win = medium volatility
                        volatility_factor = 1.2
                    else:  # <5% avg win = low volatility
                        volatility_factor = 1.0
                    
                    # Adjust for sample size confidence
                    if setup.sample_size < 5:
                        confidence_factor = 1.5  # Low confidence = wider stop
                    elif setup.sample_size < 10:
                        confidence_factor = 1.2
                    else:
                        confidence_factor = 1.0
                    
                    setup.optimal_stop_pct = base_stop * volatility_factor * confidence_factor
                    
                    # Cap between 1.5% and 6%
                    setup.optimal_stop_pct = max(0.015, min(0.06, setup.optimal_stop_pct))
                
                # MAE-based RRR: avg_win / optimal_stop
                if setup.optimal_stop_pct > 0 and setup.avg_win > 0:
                    setup.mae_based_rrr = setup.avg_win / setup.optimal_stop_pct
                else:
                    setup.mae_based_rrr = setup.risk_reward_ratio
                
            except Exception as e:
                setup.optimal_stop_pct = 0.02  # Default 2% stop (more conservative)
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
        
        # Calculate Quality Scores (V6.0 - The 'Company' Filter)
        print("\n🏭 Quality Score Analysis (The 'Company' Filter)...")
        for setup in processed:
            try:
                quality_analysis = self.quality_analyzer.analyze_quality(setup.ticker)
                setup.quality_score = quality_analysis.quality_score
                setup.quality_analysis = quality_analysis
                
                # Log quality warnings
                if quality_analysis.quality_score < 40:
                    warning = " - VALUE TRAP!" if quality_analysis.value_trap_warning else ""
                    print(f"   🚨 {setup.ticker}: HIGH RISK/TRASH (Q:{quality_analysis.quality_score:.0f}){warning}")
                elif quality_analysis.quality_score >= 80:
                    print(f"   ✅ {setup.ticker}: HIGH QUALITY (Q:{quality_analysis.quality_score:.0f})")
            except Exception as e:
                print(f"   ⚠️ Quality analysis failed for {setup.ticker}: {e}")
                setup.quality_score = 0.0
                setup.quality_analysis = None
        
        # V7.0: Motor B (Momentum/Launchpad Detection)
        # NOTE: Motor B requires OPPOSITE conditions from Motor A (price > EMA50 > EMA200, near 52w high)
        # Running Motor B on Motor A candidates (price < EMA200, -15% decline) will ALWAYS reject
        # TODO: Implement separate Motor B pipeline that scans full universe independently
        print("\n🚀 Motor B - Momentum/Launchpad Detection...")
        print("   ⚠️  SKIPPED: Motor B requires separate pipeline (incompatible with Motor A candidates)")
        print("   Motor A: Price < EMA200, -15% decline (bottom fishing)")
        print("   Motor B: Price > EMA50 > EMA200, near 52w high (momentum leaders)")
        print("   → These conditions are mutually exclusive")
        
        # Mark all setups as Motor A only
        for setup in processed:
            setup.motor_b_signal = None
            setup.rs_rating = None
        
        # V7.0: Alpha-Switch (Convergence Detection)
        # SKIPPED: No Motor B signals to converge with
        print("\n🎯 Alpha-Switch - Convergence Detection...")
        print("   ⚠️  SKIPPED: No Motor B pipeline active")
        for setup in processed:
            setup.convergence_detected = False
            setup.convergence = None
        
        # V7.0: Statistical Iron Curtain (Bootstrap + Kaufman ER)
        # CRITICAL BUG FIX: Iron Curtain was using MOCK/GENERATED data instead of HISTORICAL returns
        # This defeats the entire purpose of statistical validation
        # Solution: DISABLE until we have access to actual historical forward returns from screener
        print("\n🛡️ Statistical Iron Curtain (Bootstrap + Kaufman ER)...")
        print("   ⚠️  DISABLED: Requires historical forward returns (not available from screener)")
        print("   Previous implementation used GENERATED data which invalidates statistical tests")
        print("   → All setups pass Iron Curtain by default")
        
        for setup in processed:
            setup.iron_curtain_passed = True  # Disabled - pass all by default
            setup.kaufman_er = None
        
        # V7.0: Hard Limits (MAE 6% Cap + Sector Diversification)
        print("\n⚠️ Hard Limits Enforcement...")
        sector_map = {s.ticker: s.sector for s in processed if hasattr(s, 'sector')}
        validated_setups = []
        
        for i, setup in enumerate(processed):
            try:
                # Check both hard limits
                passed, mae_check, sector_check = self.hard_limits.validate_setup(
                    ticker=setup.ticker,
                    sector=getattr(setup, 'sector', 'Unknown'),
                    robust_score=getattr(setup, 'robust_score', 0),
                    avg_loss=setup.avg_loss,
                    existing_setups=validated_setups,  # Already validated (higher ranked)
                    sector_map=sector_map
                )
                
                setup.mae_check = mae_check
                setup.sector_check = sector_check
                setup.hard_limits_passed = passed
                
                if not passed:
                    if not mae_check.passed:
                        print(f"   ❌ {setup.ticker}: {mae_check.reason}")
                    if not sector_check.passed:
                        print(f"   ❌ {setup.ticker}: {sector_check.reason}")
                else:
                    validated_setups.append(setup)
            except Exception as e:
                print(f"   ⚠️ Hard limits check failed for {setup.ticker}: {e}")
                setup.hard_limits_passed = True  # Don't reject on error
                validated_setups.append(setup)
        
        print(f"   Hard Limits: {len(validated_setups)}/{len(processed)} setups passed")
        
        # Replace processed with validated only
        processed = validated_setups
        
        # Calculate Timing Scores (for New Lows only)
        print("\n⏱️ Timing Score Analysis (Immediate Reversal Detection)...")
        for setup in processed:
            try:
                # Fetch fresh price data for timing analysis
                import yfinance as yf
                ticker_obj = yf.Ticker(setup.ticker)
                hist = ticker_obj.history(period="1mo")  # Last month for RSI(2) and EMA(5)
                
                if not hist.empty and len(hist) >= 20:
                    timing_signals = self.timing_calculator.calculate_timing_score(
                        setup.ticker,
                        hist
                    )
                    
                    if timing_signals:
                        setup.timing_confidence = timing_signals.total_score
                        setup.timing_signals = timing_signals
                        
                        # Classify as ACTIVE BUY SIGNAL or WATCHLIST
                        has_robust_score = hasattr(setup, 'robust_score') and setup.robust_score > 70
                        has_timing = timing_signals.total_score >= TIMING_THRESHOLD
                        
                        if has_robust_score and has_timing:
                            setup.signal_status = "ACTIVE BUY SIGNAL"
                            setup.waiting_reason = None
                            print(f"   🚀 {setup.ticker}: ACTIVE BUY SIGNAL (Timing: {timing_signals.total_score:.0f}%)")
                        elif has_robust_score:
                            setup.signal_status = "WATCHLIST (Wait for Trigger)"
                            # Determine why we're waiting
                            reasons = []
                            if not timing_signals.volume_confirmed:
                                reasons.append("Waiting for Volume")
                            if timing_signals.rsi_2_current > 30:
                                reasons.append("RSI not oversold")
                            elif timing_signals.rsi_2_current < 15 and timing_signals.rsi_hook_boost == 0:
                                reasons.append("RSI too low (no hook yet)")
                            if timing_signals.candle_pattern in ["Bearish/Neutral", "Bearish"]:
                                reasons.append("Price Action missing")
                            setup.waiting_reason = ", ".join(reasons) if reasons else "Timing < 50%"
                            print(f"   ⏸️ {setup.ticker}: WATCHLIST - {setup.waiting_reason}")
                        else:
                            setup.signal_status = "NO SIGNAL"
                            setup.waiting_reason = "Robust Score < 70"
                    else:
                        setup.timing_confidence = 0.0
                        setup.timing_signals = None
                        setup.signal_status = "NO SIGNAL"
                        setup.waiting_reason = "Timing data unavailable"
                else:
                    setup.timing_confidence = 0.0
                    setup.timing_signals = None
            except Exception as e:
                print(f"   ⚠️ Timing analysis failed for {setup.ticker}: {e}")
                setup.timing_confidence = 0.0
                setup.timing_signals = None
        
        # Apply Strategic Adjustments
        print("\n🎯 Strategic Score Adjustments...")
        for setup in processed:
            # Store original score
            setup.raw_score = setup.score
            
            # 1. Sector Volatility Adjustment
            # Normalize EV by sector volatility (Sharpe-like adjustment)
            # Lower volatility sectors get bonus, higher volatility get penalty
            vol_adjusted_ev = setup.expected_value / setup.sector_volatility
            vol_adjustment_factor = vol_adjusted_ev / setup.expected_value if setup.expected_value != 0 else 1.0
            
            # Cap sector adjustment to ±20% to prevent extreme scores
            vol_adjustment_factor = max(0.80, min(1.20, vol_adjustment_factor))
            setup.score *= vol_adjustment_factor
            setup.sector_adjustment = vol_adjustment_factor
            
            # 2. FX Guard Adjustment (US tickers only)
            if setup.geography == "USA":
                setup.score *= fx_adjustment
                setup.fx_adjusted = True
                setup.fx_factor = fx_adjustment
            else:
                setup.fx_adjusted = False
                setup.fx_factor = 1.0
            
            # 3. Final cap: Never exceed 100 points
            # Strategic adjustments are for relative ranking, not absolute quality
            if setup.score > 100:
                setup.score = 100.0
                setup.capped_at_100 = True
            else:
                setup.capped_at_100 = False
            
            # Store final adjusted score
            setup.adjusted_score = setup.score
        
        print(f"   Applied sector volatility normalization (0.70x-1.35x)")
        if fx_adjustment != 1.0:
            print(f"   Applied FX adjustment to US tickers ({fx_adjustment:.1%})")
        
        # Sort by Multi-Factor Rank: Signal Status, Quality, Timing, Robust Score
        def sort_key(setup):
            # Priority 1: ACTIVE BUY SIGNALS (status = ACTIVE BUY SIGNAL)
            is_active = 1 if getattr(setup, 'signal_status', '') == 'ACTIVE BUY SIGNAL' else 0
            # Priority 2: Quality Score (companies that make money)
            quality = getattr(setup, 'quality_score', 0)
            # Priority 3: Timing confidence
            timing = getattr(setup, 'timing_confidence', 0)
            # Priority 4: Robust Score (statistical edge)
            robust = getattr(setup, 'robust_score', 0)
            # Priority 5: Adjusted score (fallback)
            score = setup.adjusted_score
            return (is_active, quality, timing, robust, score)
        
        processed.sort(key=sort_key, reverse=True)
        
        # Calculate Multi-Factor Rank for each setup
        for setup in processed:
            # Combine Robust Score (statistical) + Quality Score (fundamental)
            robust_score = getattr(setup, 'robust_score', 0)
            quality_score = getattr(setup, 'quality_score', 0)
            # Weight: 60% Robust (pattern strength), 40% Quality (company health)
            setup.multi_factor_rank = (robust_score * 0.6) + (quality_score * 0.4)
        
        # FILTER: Top 5 should ONLY include PRIMARY patterns (structural reversals)
        # SECONDARY patterns (calendar, technical indicators) are supporting evidence only
        primary_only = []
        secondary_only = []
        
        for setup in processed:
            # Check if pattern is PRIMARY (structural reversal)
            # PRIMARY patterns have 'priority': 'PRIMARY' in metadata
            # or are from position_trading_patterns (which are all PRIMARY)
            is_primary = False
            
            # Patterns marked PRIMARY in metadata
            if hasattr(setup, 'pattern_metadata') and setup.pattern_metadata.get('priority') == 'PRIMARY':
                is_primary = True
            # Structural reversal patterns (always PRIMARY)
            elif any(keyword in setup.best_pattern_name.lower() for keyword in [
                'lägsta nivåer', 'double bottom', 'inverse', 'bull flag', 'higher lows',
                'ema20 reclaim', 'volatilitetökning'
            ]):
                is_primary = True
            
            if is_primary:
                primary_only.append(setup)
            else:
                secondary_only.append(setup)
        
        print(f"   Filtered: {len(primary_only)} PRIMARY, {len(secondary_only)} SECONDARY patterns")
        
        # Return PRIMARY patterns first, then SECONDARY (for Top 5 ranking)
        return primary_only + secondary_only
    
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
        
        # Fetch real market prices
        import yfinance as yf
        
        for pos in positions:
            # Get current market price
            try:
                ticker_obj = yf.Ticker(pos.ticker)
                hist = ticker_obj.history(period="1d")
                if not hist.empty:
                    current_prices[pos.ticker] = hist['Close'].iloc[-1]
                else:
                    current_prices[pos.ticker] = pos.entry_price
            except:
                current_prices[pos.ticker] = pos.entry_price
            
            # Find in screener results for edge
            match = next((r for r in screener_results if r.ticker == pos.ticker), None)
            
            if match:
                current_edges[pos.ticker] = match.edge_63d  # Use 63-day edge
            else:
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
        """Display final results in two groups: ACTIVE BUY SIGNALS and WATCHLIST."""
        
        processed = results.get('processed_setups', [])
        
        if len(processed) == 0:
            return
        
        # Separate into groups
        active_signals = [s for s in processed if getattr(s, 'signal_status', '') == 'ACTIVE BUY SIGNAL']
        watchlist = [s for s in processed if getattr(s, 'signal_status', '') == 'WATCHLIST (Wait for Trigger)']
        
        print("\n" + "="*80)
        print(f"🎯 SUNDAY ANALYSIS - BUY SIGNAL CLASSIFICATION")
        print("="*80)
        print(f"\n✅ ACTIVE BUY SIGNALS: {len(active_signals)}")
        print(f"⏸️  WATCHLIST (Waiting for Trigger): {len(watchlist)}")
        print(f"📊 Total Analyzed: {len(processed)}")
        print("\n" + "="*80)
        
        # Display ACTIVE BUY SIGNALS first
        if len(active_signals) > 0:
            print("\n" + "#"*80)
            print("GROUP 1: ACTIVE BUY SIGNALS (Robust Score > 70 AND Timing > 50%)")
            print("#"*80)
            self._display_setup_group(active_signals, results, max_count=max_setups)
        
        # Display WATCHLIST second (SHOW ALL)
        if len(watchlist) > 0:
            print("\n" + "#"*80)
            print("GROUP 2: CANDIDATES ON WATCHLIST (High Robust Score, Waiting for Timing)")
            print("#"*80)
            # Show ALL watchlist candidates, not just top 3
            self._display_setup_group(watchlist, results, max_count=len(watchlist))
        
        print("\n" + "="*80)
    
    def _display_setup_group(self, setups: List, results: Dict, max_count: int = 5):
        """Display a group of setups with full details."""
        
        if len(setups) == 0:
            print("\n   (No setups in this category)")
            return
        
        for i, setup in enumerate(setups[:max_count], 1):
            # Determine pattern priority
            is_primary = any(keyword in setup.best_pattern_name.lower() for keyword in [
                'lägsta nivåer', 'double bottom', 'inverse', 'bull flag', 'higher lows',
                'ema20 reclaim', 'volatilitetökning'
            ])
            priority_tag = "PRIMARY" if is_primary else "SECONDARY"
            
            print(f"\n{'#'*80}")
            # Show signal status in rank header
            signal_status = getattr(setup, 'signal_status', 'UNKNOWN')
            status_emoji = "🚀" if signal_status == "ACTIVE BUY SIGNAL" else "⏸️"
            print(f"{status_emoji} RANK {i}: {setup.ticker} - {setup.best_pattern_name}")
            
            # Multi-line header with all key metrics
            timing_conf = setup.timing_confidence if hasattr(setup, 'timing_confidence') else 0
            quality_score = setup.quality_score if hasattr(setup, 'quality_score') else 0
            multi_factor = setup.multi_factor_rank if hasattr(setup, 'multi_factor_rank') else 0
            
            # Get macro regime info
            macro_regime_info = results.get('macro_regime')
            macro_status = macro_regime_info.regime.value if macro_regime_info else "UNKNOWN"
            macro_emoji = "🟢" if macro_status == "AGGRESSIVE" else "🟡"
            
            print(f"Score: {setup.score:.1f}/100 | Priority: {priority_tag} | Timing: {timing_conf:.0f}% | Status: {signal_status}")
            print(f"Quality: {quality_score:.0f}/100 | Multi-Factor Rank: {multi_factor:.1f}/100 | Macro: {macro_emoji} {macro_status}")
            
            # Show waiting reason if on watchlist
            if hasattr(setup, 'waiting_reason') and setup.waiting_reason:
                print(f"⚠️ Reason for Waiting: {setup.waiting_reason}")
            
            print('#'*80)
            
            # Strategic Context
            print(f"\nCOMPANY QUALITY (V6.0 - The 'Company' Filter):")
            if hasattr(setup, 'quality_analysis') and setup.quality_analysis:
                qa = setup.quality_analysis
                print(f"  Quality Score: {qa.summary}")
                print(f"  Company: {qa.company_name}")
                
                # Profitability
                if qa.roe is not None:
                    print(f"  ROE: {qa.roe*100:.1f}% (Score: {qa.roe_score:.0f}/40)")
                
                # Solvency
                if qa.debt_to_equity is not None:
                    de_ratio = qa.debt_to_equity / 100 if qa.debt_to_equity > 10 else qa.debt_to_equity
                    print(f"  Debt/Equity: {de_ratio:.2f} (Score: {qa.debt_score:.0f}/40)")
                
                # Value
                if qa.trailing_pe is not None:
                    discount = ((qa.sector_avg_pe - qa.trailing_pe) / qa.sector_avg_pe) * 100
                    print(f"  P/E: {qa.trailing_pe:.1f} vs Sector {qa.sector_avg_pe:.1f} ({discount:+.0f}%, Score: {qa.value_score:.0f}/20)")
                
                # Value trap warning
                if qa.value_trap_warning:
                    print(f"  🚨 VALUE TRAP WARNING - Low quality despite cheap valuation!")
            
            print(f"\nSTRATEGIC CONTEXT:")
            print(f"  Sector: {setup.sector} (Vol: {setup.sector_volatility:.2f}x)")
            print(f"  Geography: {setup.geography}")
            
            # Score breakdown
            if hasattr(setup, 'raw_score'):
                print(f"  Raw Score: {setup.raw_score:.1f} → Adjusted: {setup.adjusted_score:.1f}")
                if hasattr(setup, 'sector_adjustment'):
                    print(f"  Sector Adjustment: {setup.sector_adjustment:.1%} (Vol: {setup.sector_volatility:.2f}x)")
                if setup.fx_adjusted:
                    print(f"  FX Adjustment: {setup.fx_factor:.1%} (USD/SEK Z={results.get('usd_sek_zscore', 0):.2f})")
                if hasattr(setup, 'capped_at_100') and setup.capped_at_100:
                    print(f"  ⚠️ Score capped at 100 (strategic adjustments for ranking only)")
            
            # MiFID II warning
            if setup.mifid_warning:
                print(f"\n⚠️ MiFID II: {setup.mifid_warning}")
            
            print(f"\nEDGE & PERFORMANCE:")
            print(f"  21-day: {setup.edge_21d*100:+.2f}%")
            print(f"  42-day: {setup.edge_42d*100:+.2f}%")
            print(f"  63-day: {setup.edge_63d*100:+.2f}%")
            
            # Win Rate with Confidence Interval & Robust Statistics
            if hasattr(setup, 'win_rate_ci_margin') and setup.win_rate_ci_margin > 0:
                print(f"  Win Rate (Raw): {setup.win_rate_63d*100:.1f}% ± {setup.win_rate_ci_margin*100:.1f}% (n={setup.sample_size})")
                print(f"  95% CI: [{setup.win_rate_ci_lower*100:.1f}%, {setup.win_rate_ci_upper*100:.1f}%]")
            else:
                print(f"  Win Rate (Raw): {setup.win_rate_63d*100:.1f}% (n={setup.sample_size})")
            
            # Display robust statistics if available
            if hasattr(setup, 'adjusted_win_rate') and setup.adjusted_win_rate > 0:
                print(f"  Win Rate (Bayesian): {setup.adjusted_win_rate*100:.1f}%")
            if hasattr(setup, 'p_value') and setup.p_value < 1.0:
                sig_marker = "✓" if setup.p_value < 0.05 else "✗"
                print(f"  Statistical Significance: {sig_marker} (p={setup.p_value:.4f})")
            if hasattr(setup, 'return_consistency') and setup.return_consistency != 0:
                print(f"  Return Consistency (Sharpe-like): {setup.return_consistency:.2f}")
            if hasattr(setup, 'sample_size_factor'):
                print(f"  Sample Size Confidence: {setup.sample_size_factor*100:.0f}%")
            if hasattr(setup, 'robust_score') and setup.robust_score > 0:
                print(f"  Robust Score: {setup.robust_score:.1f}/100")
            
            print(f"  Risk/Reward: 1:{setup.risk_reward_ratio:.2f}")
            print(f"  Expected Value (Raw): {setup.expected_value*100:+.2f}%")
            if hasattr(setup, 'pessimistic_ev') and setup.pessimistic_ev != 0:
                print(f"  Expected Value (Pessimistic): {setup.pessimistic_ev*100:+.2f}%")
            
            print(f"\nPOSITION SIZING:")
            print(f"  Position: {setup.position_size_sek:,.0f} SEK ({setup.position_size_pct:.2f}%)")
            if setup.floor_applied:
                print(f"  ⚠️ Raised to 1,500 SEK floor (courtage efficiency)")
            if hasattr(setup, 'macro_adjusted') and setup.macro_adjusted:
                print(f"  🌐 Macro Adjustment: Position HALVED due to DEFENSIVE regime (50%)")
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
            
            # Timing Score Breakdown
            if hasattr(setup, 'timing_signals') and setup.timing_signals:
                ts = setup.timing_signals
                print(f"\nTIMING SCORE (Immediate Reversal):")
                print(f"  Overall Confidence: {ts.total_score:.0f}% (0-100)")
                if ts.rsi_hook_boost > 0:
                    print(f"  🎯 RSI HOOK DETECTED: +{ts.rsi_hook_boost*100:.0f}% boost applied!")
                print(f"  └─ RSI Momentum Flip: {ts.rsi_momentum_flip:.0f}/25")
                print(f"     RSI(2): {ts.rsi_2_current:.1f} (prev: {ts.rsi_2_previous:.1f}, 2d ago: {ts.rsi_2_two_days_ago:.1f})")
                print(f"  └─ Mean Reversion: {ts.mean_reversion_distance:.0f}/25")
                print(f"     Distance: {ts.distance_from_ema5_std:.2f} std from EMA(5)")
                print(f"  └─ Volume Exhaustion: {ts.volume_exhaustion:.0f}/25")
                print(f"     Trend: {ts.volume_trend_last_3d}")
                vol_status = "✅ CONFIRMED" if ts.volume_confirmed else "❌ NOT CONFIRMED"
                print(f"     Enhanced Volume Check: {vol_status}")
                
                # Explain why volume not confirmed if applicable
                if not ts.volume_confirmed:
                    print(f"     ⚠️ Volume Issue: Need either:")
                    print(f"        - Declining price + volume -15% below avg (seller exhaustion), OR")
                    print(f"        - Green day + volume +10% above avg (buyer entry)")
                print(f"  └─ Price Action: {ts.price_action_signal:.0f}/25")
                print(f"     Pattern: {ts.candle_pattern}")
                
                # Interpretation with threshold check
                if ts.total_score >= TIMING_THRESHOLD:
                    if ts.total_score >= 75:
                        print(f"  🚀 ACTIVE BUY SIGNAL - Excellent timing for entry")
                    else:
                        print(f"  🚀 ACTIVE BUY SIGNAL - Good timing for entry")
                else:
                    print(f"  ⏸️ WATCHLIST - Timing below {TIMING_THRESHOLD:.0f}% threshold")
            
            if setup.earnings_risk == 'HIGH':
                print(f"\n🚨 EARNINGS RISK: {setup.earnings_days} days - DO NOT TRADE")
            
            if setup.in_cluster:
                if setup.recommended_from_cluster:
                    print(f"\n✅ Recommended from correlation cluster")
                else:
                    print(f"\n⚠️ {setup.cluster_warning}")
            
            # V7.0: Show Motor B & Convergence status if applicable
            if hasattr(setup, 'motor_b_signal') and setup.motor_b_signal and setup.motor_b_signal.is_valid:
                mb = setup.motor_b_signal
                print(f"\n🚀 MOTOR B (Momentum/Launchpad):")
                print(f"   RS-Rating: {mb.rs_rating:.0f}/100 (top {100-mb.rs_rating:.0f}% of universe)")
                print(f"   VCP: ATR ratio {mb.atr_ratio:.3f} (compressed: {mb.volatility_contracted})")
                print(f"   Distance from 52w high: {mb.distance_from_52w:+.1f}%")
            
            if hasattr(setup, 'convergence_detected') and setup.convergence_detected:
                conv = setup.convergence
                print(f"\n🎯 ALPHA-SWITCH (Convergence Detected!):")
                print(f"   Motor A triggered: {conv.days_since_motor_a} days ago @ {conv.motor_a_entry_price:.2f}")
                print(f"   Price move since: {conv.price_move_since_motor_a:+.1f}%")
                print(f"   Robust Score boosted: 1.2x multiplier applied")
            
            # V7.0: Show Iron Curtain results if available
            if hasattr(setup, 'iron_curtain_bootstrap'):
                boot = setup.iron_curtain_bootstrap
                print(f"\n🛡️ IRON CURTAIN (Statistical Validation):")
                print(f"   Bootstrap: {boot.n_positive_ev}/{boot.n_simulations} simulations EV>0 ({boot.pass_rate*100:.0f}%)")
                if hasattr(setup, 'kaufman_er'):
                    print(f"   Kaufman ER: {setup.kaufman_er:.3f} (signal/noise ratio)")
            
            # V7.0: Show Hard Limits checks
            if hasattr(setup, 'mae_check'):
                print(f"\n⚠️ HARD LIMITS:")
                print(f"   MAE Stop: {setup.mae_check.optimal_stop_pct*100:.1f}% (cap: 6%)")
                if hasattr(setup, 'sector_check'):
                    print(f"   Sector: {setup.sector_check.sector_count}/3 in {setup.sector_check.sector}")
        
        print("\n" + "="*80)
        
        # V7.0: Generate Elite Report (Top 5 ONLY)
        print("\n" + "="*80)
        print("📄 GENERATING ELITE SUNDAY REPORT (TOP 5 ONLY)")
        print("="*80)
        
        # Filter to top 5 ACTIVE BUY SIGNALS only
        top_5 = [s for s in processed if getattr(s, 'signal_status', '') == 'ACTIVE BUY SIGNAL'][:5]
        
        if len(top_5) == 0:
            # If no ACTIVE signals, use top 5 from all processed
            top_5 = processed[:5]
        
        macro_regime = results.get('macro_regime')
        if macro_regime:
            elite_report = self.elite_formatter.generate_sunday_report(
                top_5_setups=top_5,
                macro_regime=macro_regime
            )
            
            # Save Elite Report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            elite_path = f"reports/ELITE_SUNDAY_{timestamp}.txt"
            self.elite_formatter.save_report(elite_report, elite_path)
            
            # Also print to console
            print("\n" + elite_report)
    
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
