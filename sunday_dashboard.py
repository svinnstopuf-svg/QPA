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
        
        # Get FX adjustment from results
        usd_sek_zscore = results.get('usd_sek_zscore', 0.0)
        fx_adjustment = results.get('fx_adjustment', 1.0)
        
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
        
        # Sort by adjusted score
        processed.sort(key=lambda x: x.adjusted_score, reverse=True)
        
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
            # Determine pattern priority
            is_primary = any(keyword in setup.best_pattern_name.lower() for keyword in [
                'lägsta nivåer', 'double bottom', 'inverse', 'bull flag', 'higher lows',
                'ema20 reclaim', 'volatilitetökning'
            ])
            priority_tag = "PRIMARY" if is_primary else "SECONDARY"
            
            print(f"\n{'#'*80}")
            print(f"RANK {i}: {setup.ticker} - {setup.best_pattern_name}")
            print(f"Score: {setup.score:.1f}/100 | Priority: {priority_tag}")
            print('#'*80)
            
            # Strategic Context
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
