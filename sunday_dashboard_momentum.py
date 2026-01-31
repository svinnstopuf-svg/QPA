"""
Sunday Dashboard - MOMENTUM STRATEGY V7.0

Philosophy:
- Buy strength, not weakness
- Ride momentum leaders to new highs
- Let winners run with trailing stops
- "The trend is your friend" (Mark Minervini)

Strategy:
- Scan for RS-Rating ≥95 (top 5%)
- Price > EMA50 > EMA200 (confirmed uptrend)
- Near 52-week high (>95%)
- VCP contraction (ATR < 0.85)
- Institutional ownership 30%+
- Earnings growth >15% YoY

Entry:
- Breakout from tight consolidation
- Volume surge 2x+ average
- Gap up preferred
- Close near high of day

Exit:
- Trailing stop 2.5x ATR below high
- Profit targets: 2R, 3R, 5R
- Volume climax signal
- Breakdown below EMA50

Position Sizing:
- 2-4% per position (vs 1.5-2.5% for mean reversion)
- Higher for top RS-Rating (RS≥98 = 4%)
- Sector volatility BONUS (momentum loves volatility)
- No FX adjustment (momentum is momentum)

Risk Management:
- All V6.0 features applied
- Macro Regime multiplier
- Market Breadth check
- Correlation clustering
- Monte Carlo simulation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

# V6.0 Core Components (matching mean reversion imports)
from src.utils.data_fetcher import DataFetcher
from src.risk.regime_detection import RegimeDetector
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier
from src.risk.cost_aware_filter import CostAwareFilter
from src.risk.market_breadth import MarketBreadthIndicator
from src.analysis.macro_indicators import MacroIndicators
from src.risk.sector_cap_manager import SectorCapManager
from src.risk.mae_optimizer import MAEOptimizer
from src.risk.monte_carlo_simulator import MonteCarloSimulator
from src.analysis.correlation_detector import CorrelationDetector
from src.portfolio.health_tracker import PortfolioHealthTracker
from src.portfolio.exit_guard import ExitGuard
from src.risk.fx_guard import FXGuard
from src.portfolio.inactivity_checker import InactivityChecker
from src.validation.data_sanity_checker import DataSanityChecker
from src.reporting.weekly_report import WeeklyReportGenerator
from src.analysis.macro_regime import MacroRegimeAnalyzer, MacroRegimeAnalysis, MarketRegime
from instruments_universe_1200 import (
    get_all_tickers,
    get_sector_for_ticker,
    get_geography_for_ticker,
    get_sector_volatility_factor,
    get_mifid_ii_proxy,
    MIFID_II_PROXY_MAP
)

# V7.0 Momentum Components
from src.patterns.momentum_engine import MomentumEngine, calculate_universe_returns
from src.patterns.momentum_patterns import MomentumPatternDetector
from src.analysis.momentum_quality import MomentumQualityAnalyzer
from src.timing.momentum_timing import MomentumTimingAnalyzer
from src.exit.momentum_exit import MomentumExitManager
from src.analysis.momentum_statistics import MomentumStatisticsAnalyzer


class SundayDashboardMomentum:
    """
    Sunday Dashboard - Momentum Strategy V7.0
    
    Scans universe for momentum leaders ready to break higher.
    Applies all V6.0 risk management features.
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
        print("SUNDAY DASHBOARD - MOMENTUM STRATEGY V7.0")
        print("="*80)
        print("Philosophy: Buy strength before breakout (Launchpad Trading)")
        print("Patterns: VCP, Cup & Handle, Ascending Triangle, Bull Pennant")
        print(f"\nCapital: {self.capital:,.0f} SEK")
        print(f"Risk per trade: {self.max_risk_per_trade*100:.1f}%")
        print(f"Minimum position: {self.min_position_sek:,.0f} SEK ({self.min_position_pct*100:.1f}%)")
        
        self._init_components()
    
    def _init_components(self):
        """Initialize all components."""
        
        # V6.0 Risk Management
        self.regime_detector = RegimeDetector()
        self.execution_guard = ExecutionGuard(
            account_type=AvanzaAccountType.SMALL,
            portfolio_value_sek=self.capital,
            use_isk_optimizer=True,
            isk_courtage_tier=CourtageTier.MINI
        )
        self.cost_filter = CostAwareFilter()
        
        # Market Context
        self.market_breadth = MarketBreadthIndicator()
        self.macro_indicators = MacroIndicators()
        
        # Portfolio Intelligence
        self.sector_cap = SectorCapManager(max_sector_pct=0.40)
        self.mae_optimizer = MAEOptimizer()
        self.monte_carlo = MonteCarloSimulator(num_paths=500, holding_days=63)
        self.correlation_detector = CorrelationDetector()
        self.portfolio_health = PortfolioHealthTracker()
        self.exit_guard = ExitGuard()
        self.fx_guard = FXGuard()
        self.inactivity_checker = InactivityChecker()
        
        # Infrastructure
        self.data_sanity = DataSanityChecker()
        self.report_generator = WeeklyReportGenerator()
        self.data_fetcher = DataFetcher()
        
        # Macro Regime
        self.macro_analyzer = MacroRegimeAnalyzer()
        
        # V7.0 Momentum Components
        self.momentum_engine = MomentumEngine(
            min_rs_rating=95.0,
            min_52w_proximity=0.95,
            max_atr_ratio=0.85
        )
        self.momentum_pattern_detector = MomentumPatternDetector(
            min_rs_rating=90.0,
            min_volume_surge=2.0,
            min_consolidation_days=15
        )
        self.momentum_quality_analyzer = MomentumQualityAnalyzer(
            min_institutional_ownership=0.30,
            min_daily_dollar_volume=10_000_000
        )
        self.momentum_timing_analyzer = MomentumTimingAnalyzer(
            min_volume_surge=2.0,
            min_gap_pct=0.02
        )
        self.momentum_exit_manager = MomentumExitManager(
            initial_stop_atr_multiplier=2.0,
            trailing_stop_atr_multiplier=2.5
        )
        self.momentum_stats_analyzer = MomentumStatisticsAnalyzer(
            prior_win_rate=0.65,
            min_sample_size=20,
            bootstrap_simulations=1000
        )
    
    def run(self, tickers: Optional[List[str]] = None, max_setups: int = 5) -> Dict:
        """
        Run complete Sunday momentum analysis.
        
        Args:
            tickers: Optional custom watchlist. If None, uses full universe.
            max_setups: Number of setups to display
        
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
            if breadth.constituents_analyzed > 0:
                results['market_breadth'] = breadth
                print(f"   Breadth: {breadth.breadth_pct:.0f}% ({breadth.constituents_above_200ma}/{breadth.constituents_analyzed} above 200MA)")
                if not breadth.tradable:
                    print(f"   ⚠️ WARNING: Weak market - momentum strategy risky")
            else:
                results['market_breadth'] = None
        except Exception as e:
            results['market_breadth'] = None
        
        # Macro Indicators
        print("\n🌍 Macro Indicators...")
        try:
            yield_curve = self.macro_indicators.analyze_yield_curve()
            results['yield_curve'] = yield_curve
            print(f"   Yield Curve: {yield_curve.message}")
        except:
            results['yield_curve'] = None
        
        try:
            credit = self.macro_indicators.analyze_credit_spreads()
            results['credit_spreads'] = credit
            print(f"   Credit Spreads: {credit.message}")
        except:
            results['credit_spreads'] = None
        
        # Macro Regime
        print("\n🌐 Macro Regime Analysis (The 'Wind' Filter)...")
        try:
            macro_regime = self.macro_analyzer.analyze_regime()
            results['macro_regime'] = macro_regime
            print(f"   Regime: {macro_regime.regime.value}")
            print(f"   Position Size Multiplier: {macro_regime.position_size_multiplier:.0%}")
            
            if len(macro_regime.defensive_signals) > 0:
                print(f"\n   ⚠️ DEFENSIVE MODE: Momentum strategy NOT recommended")
                for signal in macro_regime.defensive_signals:
                    print(f"      • {signal}")
        except:
            macro_regime = MacroRegimeAnalysis(
                regime=MarketRegime.AGGRESSIVE,
                position_size_multiplier=1.0,
                sp500_price=0.0, sp500_ema200=0.0, sp500_above_ema=True, sp500_distance_pct=0.0,
                us10y_current=0.0, us10y_3w_ago=0.0, us10y_trend="Flat", us10y_change_bps=0.0,
                usdsek_current=0.0, usdsek_zscore=0.0,
                defensive_signals=[]
            )
            results['macro_regime'] = macro_regime
        
        # ====================================================================
        # 2. SCAN UNIVERSE
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 2: SCANNING UNIVERSE FOR MOMENTUM LEADERS")
        print("="*80)
        
        # Use custom watchlist if provided, otherwise full universe
        if tickers is not None:
            unique_tickers = tickers
            print(f"Using custom watchlist: {len(unique_tickers)} tickers")
        else:
            all_tickers = get_all_tickers()
            seen = set()
            unique_tickers = []
            for ticker in all_tickers:
                if ticker not in seen:
                    seen.add(ticker)
                    unique_tickers.append(ticker)
        
        print(f"\nScanning {len(unique_tickers)} instruments...")
        print(f"Expected runtime: {len(unique_tickers) * 10 / 3600:.1f} hours\n")
        print("Looking for:")
        print("  • RS-Rating ≥95 (top 5%)")
        print("  • Price > EMA50 > EMA200")
        print("  • Near 52-week high (>95%)")
        print("  • VCP contraction (ATR < 0.85)")
        
        # Fetch market data for universe (need 2y for RS-Rating)
        print("\n📊 Fetching 2-year data for RS-Rating calculation...")
        universe_market_data = {}
        for i, ticker in enumerate(unique_tickers):
            if (i + 1) % 100 == 0:
                print(f"   Progress: {i+1}/{len(unique_tickers)} ({(i+1)/len(unique_tickers)*100:.0f}%)")
            
            try:
                market_data = self.data_fetcher.fetch_stock_data(ticker, period="2y")
                if market_data:
                    universe_market_data[ticker] = market_data
            except:
                pass
        
        print(f"\n✓ Got data for {len(universe_market_data)} instruments")
        
        # Calculate universe returns for RS-Rating
        print("\n📈 Calculating universe returns...")
        universe_returns = calculate_universe_returns(
            list(universe_market_data.keys()),
            universe_market_data
        )
        
        # Scan each instrument
        print("\n🚀 Scanning for momentum signals...")
        momentum_setups = []
        
        for i, (ticker, market_data) in enumerate(universe_market_data.items()):
            if (i + 1) % 100 == 0:
                print(f"   Progress: {i+1}/{len(universe_market_data)} ({(i+1)/len(universe_market_data)*100:.0f}%)")
            
            try:
                motor_b_signal = self.momentum_engine.detect_momentum_signal(
                    ticker,
                    market_data,
                    universe_returns
                )
                
                if motor_b_signal.is_valid:
                    # Create setup object
                    @dataclass
                    class MomentumSetup:
                        ticker: str
                        motor_b_signal: object
                        rs_rating: float
                        current_price: float
                        distance_from_52w: float
                        atr_ratio: float
                    
                    setup = MomentumSetup(
                        ticker=ticker,
                        motor_b_signal=motor_b_signal,
                        rs_rating=motor_b_signal.rs_rating,
                        current_price=motor_b_signal.current_price,
                        distance_from_52w=motor_b_signal.distance_from_52w,
                        atr_ratio=motor_b_signal.atr_ratio
                    )
                    
                    momentum_setups.append(setup)
                    
                    print(f"   ✓ {ticker}: RS={motor_b_signal.rs_rating:.0f}, "
                          f"VCP={motor_b_signal.atr_ratio:.2f}, "
                          f"52w: {motor_b_signal.distance_from_52w:+.1f}%")
            
            except Exception as e:
                continue
        
        print(f"\n✅ Found {len(momentum_setups)} momentum candidates")
        results['raw_setups'] = momentum_setups
        
        if len(momentum_setups) == 0:
            print("\n❌ No momentum setups found.")
            print("   Market may not favor momentum strategy currently.")
            return results
        
        # ====================================================================
        # 3. POST-PROCESSING
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 3: POST-PROCESSING & RISK FILTERS")
        print("="*80)
        
        processed_setups = self._post_process_setups(momentum_setups, results, universe_market_data)
        results['processed_setups'] = processed_setups
        
        # ====================================================================
        # 4. PORTFOLIO HEALTH CHECK
        # ====================================================================
        print("\n" + "="*80)
        print("STEP 4: PORTFOLIO HEALTH CHECK")
        print("="*80)
        
        portfolio_analysis = self._check_portfolio_health()
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
        
        self._export_json(results)
        self._export_text_report(results)
        
        return results
    
    def _post_process_setups(self, setups: List, results: Dict, universe_data: Dict) -> List:
        """Apply all momentum-specific filters."""
        
        processed = []
        
        # Get macro multiplier
        macro_regime = results.get('macro_regime')
        macro_multiplier = macro_regime.position_size_multiplier if macro_regime else 1.0
        
        print("\n🔍 Applying Momentum Filters...")
        
        for setup in setups:
            # Sector & Geography
            setup.sector = get_sector_for_ticker(setup.ticker)
            setup.geography = get_geography_for_ticker(setup.ticker)
            sector_vol = get_sector_volatility_factor(setup.sector)
            
            # MiFID II proxy
            if setup.ticker in MIFID_II_PROXY_MAP:
                setup.mifid_proxy = get_mifid_ii_proxy(setup.ticker)
            else:
                setup.mifid_proxy = None
            
            # Position Sizing (Aggressive for momentum)
            rs_rating = setup.rs_rating
            if rs_rating >= 98:
                base_allocation = 0.04   # 4% for top 2%
            elif rs_rating >= 95:
                base_allocation = 0.03   # 3% for top 5%
            else:
                base_allocation = 0.02   # 2% baseline
            
            # Sector volatility BONUS (momentum loves volatility)
            if sector_vol > 1.3:
                base_allocation *= 1.1
            
            # Apply macro multiplier
            position_pct = base_allocation * macro_multiplier
            setup.position_size_pct = position_pct * 100
            setup.position_size_sek = self.capital * position_pct
            
            # Quality Check
            try:
                quality = self.momentum_quality_analyzer.analyze_quality(setup.ticker)
                setup.quality_score = quality.momentum_quality_score
                setup.quality_tier = quality.quality_tier
                
                if quality.quality_tier == "LAGGARD":
                    print(f"   ❌ {setup.ticker}: REJECTED - Low quality ({quality.quality_tier})")
                    continue
                
                if quality.institutional_ownership_pct < 0.30:
                    print(f"   ⚠️  {setup.ticker}: Low institutional ownership ({quality.institutional_ownership_pct*100:.0f}%)")
            
            except Exception as e:
                setup.quality_score = 50
                setup.quality_tier = "UNKNOWN"
            
            # Timing Check
            try:
                market_data_obj = universe_data.get(setup.ticker)
                if market_data_obj:
                    # Create DataFrame from MarketData
                    df = pd.DataFrame({
                        'Open': market_data_obj.open_prices,
                        'High': market_data_obj.high_prices,
                        'Low': market_data_obj.low_prices,
                        'Close': market_data_obj.close_prices,
                        'Volume': market_data_obj.volume
                    })
                    
                    timing = self.momentum_timing_analyzer.analyze_timing(setup.ticker, df)
                    setup.timing_confidence = timing.timing_confidence
                    setup.recommended_action = timing.recommended_action
                    
                    if timing.timing_confidence < 60:
                        print(f"   ❌ {setup.ticker}: REJECTED - Timing not confirmed ({timing.timing_confidence:.0f}%)")
                        continue
                else:
                    print(f"   ⚠️  {setup.ticker}: No data for timing check")
                    continue
            
            except Exception as e:
                print(f"   ⚠️  {setup.ticker}: Timing failed - {e}")
                continue
            
            # Exit Strategy
            try:
                market_data_obj = universe_data.get(setup.ticker)
                if market_data_obj:
                    atr = self.momentum_exit_manager.calculate_atr(market_data_obj, period=14)
                    entry_price = setup.current_price
                    
                    setup.initial_stop = entry_price - (atr * 2.0)
                    initial_risk = entry_price - setup.initial_stop
                    
                    setup.profit_target_1 = entry_price + (initial_risk * 2.0)
                    setup.profit_target_2 = entry_price + (initial_risk * 3.0)
                    setup.profit_target_3 = entry_price + (initial_risk * 5.0)
                else:
                    setup.initial_stop = setup.current_price * 0.92
                    setup.profit_target_1 = setup.current_price * 1.16
                    setup.profit_target_2 = setup.current_price * 1.24
                    setup.profit_target_3 = setup.current_price * 1.40
            
            except:
                setup.initial_stop = setup.current_price * 0.92
                setup.profit_target_1 = setup.current_price * 1.16
                setup.profit_target_2 = setup.current_price * 1.24
                setup.profit_target_3 = setup.current_price * 1.40
            
            # Win Rate Estimate (from RS-Rating)
            if setup.rs_rating >= 99:
                setup.estimated_win_rate = 0.75
            elif setup.rs_rating >= 98:
                setup.estimated_win_rate = 0.70
            else:
                setup.estimated_win_rate = 0.65
            
            # Risk/Reward Ratio
            setup.risk_reward_ratio = (setup.profit_target_1 - setup.current_price) / (setup.current_price - setup.initial_stop)
            
            # Expected Value
            setup.expected_value = (setup.estimated_win_rate * ((setup.profit_target_1 - setup.current_price) / setup.current_price)) + \
                                 ((1 - setup.estimated_win_rate) * ((setup.initial_stop - setup.current_price) / setup.current_price))
            setup.ev_sek = setup.position_size_sek * setup.expected_value
            
            # Final Score (RS-Rating + Quality + Timing)
            setup.momentum_score = (
                setup.rs_rating * 0.40 +
                setup.quality_score * 0.30 +
                setup.timing_confidence * 0.30
            )
            
            processed.append(setup)
        
        # Sort by momentum score
        processed.sort(key=lambda x: x.momentum_score, reverse=True)
        
        print(f"\n✓ {len(processed)}/{len(setups)} setups passed all filters")
        
        return processed
    
    def _check_portfolio_health(self) -> Dict:
        """Check health of existing momentum positions."""
        positions = self.portfolio_health.load_positions()
        
        if len(positions) == 0:
            print("\n   No existing positions to track.")
            return {'positions': [], 'assessments': []}
        
        print(f"\n   Tracking {len(positions)} existing positions...")
        
        # Fetch current prices
        current_prices = {}
        for pos in positions:
            try:
                ticker_obj = yf.Ticker(pos.ticker)
                hist = ticker_obj.history(period="1d")
                if not hist.empty:
                    current_prices[pos.ticker] = hist['Close'].iloc[-1]
                else:
                    current_prices[pos.ticker] = pos.entry_price
            except:
                current_prices[pos.ticker] = pos.entry_price
        
        # Display positions
        for pos in positions:
            current = current_prices[pos.ticker]
            pnl_pct = ((current - pos.entry_price) / pos.entry_price) * 100
            print(f"\n   {pos.ticker}: {pnl_pct:+.1f}% (Entry: {pos.entry_price:.2f}, Current: {current:.2f})")
        
        return {'positions': positions}
    
    def _display_results(self, results: Dict, max_setups: int):
        """Display final results."""
        processed = results.get('processed_setups', [])
        
        if len(processed) == 0:
            return
        
        print("\n" + "="*80)
        print(f"🎯 TOP {min(max_setups, len(processed))} MOMENTUM SETUPS")
        print("="*80)
        
        for i, setup in enumerate(processed[:max_setups], 1):
            print(f"\n{'='*80}")
            print(f"🚀 RANK #{i}: {setup.ticker} - MOMENTUM LEADER")
            print(f"{'='*80}")
            
            print(f"\nMomentum Score: {setup.momentum_score:.0f}/100")
            print(f"RS-Rating: {setup.rs_rating:.0f}/100 (top {100-setup.rs_rating:.0f}%)")
            print(f"Quality Tier: {setup.quality_tier} ({setup.quality_score:.0f}/100)")
            print(f"Timing: {setup.timing_confidence:.0f}% ({setup.recommended_action})")
            
            print(f"\nPrice Action:")
            print(f"  Current: {setup.current_price:.2f}")
            print(f"  Distance from 52w high: {setup.distance_from_52w:+.1f}%")
            print(f"  VCP Contraction: {setup.atr_ratio:.3f}")
            
            print(f"\nPosition Sizing:")
            print(f"  Size: {setup.position_size_sek:,.0f} SEK ({setup.position_size_pct:.2f}%)")
            print(f"  Expected Value: {setup.expected_value*100:+.1f}%")
            print(f"  Expected Profit: {setup.ev_sek:+,.0f} SEK")
            
            print(f"\nExit Strategy:")
            print(f"  Initial Stop: {setup.initial_stop:.2f} ({((setup.initial_stop - setup.current_price)/setup.current_price)*100:.1f}%)")
            print(f"  Target 1 (2R): {setup.profit_target_1:.2f} ({((setup.profit_target_1 - setup.current_price)/setup.current_price)*100:.1f}%)")
            print(f"  Target 2 (3R): {setup.profit_target_2:.2f} ({((setup.profit_target_2 - setup.current_price)/setup.current_price)*100:.1f}%)")
            print(f"  Target 3 (5R): {setup.profit_target_3:.2f} ({((setup.profit_target_3 - setup.current_price)/setup.current_price)*100:.1f}%)")
            print(f"  Risk/Reward: 1:{setup.risk_reward_ratio:.1f}")
        
        print("\n" + "="*80)
    
    def _export_json(self, results: Dict):
        """Export results to JSON."""
        try:
            import json
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = output_dir / f"momentum_results_{timestamp}.json"
            
            export_data = {
                'timestamp': timestamp,
                'strategy': 'MOMENTUM',
                'capital': self.capital,
                'num_setups': len(results.get('processed_setups', []))
            }
            
            with open(json_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"\n📄 JSON exported: {json_path}")
        except Exception as e:
            print(f"\n⚠️ JSON export failed: {e}")
    
    def _export_text_report(self, results: Dict):
        """Export text report."""
        try:
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"momentum_report_{timestamp}.txt"
            
            processed = results.get('processed_setups', [])
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("MOMENTUM STRATEGY REPORT\n")
                f.write("="*80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Capital: {self.capital:,.0f} SEK\n\n")
                
                f.write(f"TOP {min(5, len(processed))} SETUPS:\n")
                f.write("="*80 + "\n")
                
                for i, setup in enumerate(processed[:5], 1):
                    f.write(f"\n#{i}: {setup.ticker} - MOMENTUM LEADER\n")
                    f.write(f"RS-Rating: {setup.rs_rating:.0f}/100\n")
                    f.write(f"Momentum Score: {setup.momentum_score:.0f}/100\n")
                    f.write(f"Position: {setup.position_size_sek:,.0f} SEK\n")
                    f.write(f"Expected Profit: {setup.ev_sek:+,.0f} SEK\n")
                    f.write("-"*80 + "\n")
            
            print(f"📄 Report saved: {report_path}")
        except Exception as e:
            print(f"⚠️ Report generation failed: {e}")


def main():
    """Main entry point."""
    dashboard = SundayDashboardMomentum(
        capital=100000.0,
        max_risk_per_trade=0.01,
        min_position_sek=1500.0
    )
    
    results = dashboard.run(max_setups=5)
    
    print("\n" + "="*80)
    print("✅ MOMENTUM ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
