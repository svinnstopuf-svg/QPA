"""
HISTORICAL BACKFILL SIMULATION
Point-in-Time Analysis Engine

Kör dashboard-analys för varje dag i en historisk period med endast data 
som var tillgänglig vid den tidpunkten.

Usage:
    python historical_backfill.py --period "senaste veckan"
    python historical_backfill.py --period "senaste månaden"
    python historical_backfill.py --days 7
"""

import sys
import io
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict
import numpy as np

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from instrument_screener_v22 import InstrumentScreenerV22, Signal
from instruments_universe_800 import get_all_800_instruments
from src.risk.execution_guard import ExecutionGuard, AvanzaAccountType
from src.risk.isk_optimizer import CourtageTier
from src.risk.all_weather_config import is_all_weather, get_all_weather_category


class HistoricalBackfillSimulator:
    """
    Time-Slice Engine för point-in-time dashboard-analys.
    """
    
    def __init__(self, portfolio_value_sek: float = 100000, quick_mode: bool = False):
        self.portfolio_value_sek = portfolio_value_sek
        self.quick_mode = quick_mode
        self.execution_guard = ExecutionGuard(
            account_type=AvanzaAccountType.SMALL,
            portfolio_value_sek=portfolio_value_sek,
            use_isk_optimizer=True,
            isk_courtage_tier=CourtageTier.MINI
        )
        self.reports_dir = Path("reports/backfill")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_period(self, period_str: str) -> int:
        """
        Parsa period-string till antal dagar.
        
        Examples:
            "senaste veckan" -> 7
            "senaste månaden" -> 30
            "senaste 2 veckorna" -> 14
        """
        period_str = period_str.lower()
        
        if "vecka" in period_str or "week" in period_str:
            if "2" in period_str:
                return 14
            elif "3" in period_str:
                return 21
            return 7
        elif "månad" in period_str or "month" in period_str:
            if "2" in period_str:
                return 60
            elif "3" in period_str:
                return 90
            return 30
        elif "dag" in period_str or "day" in period_str:
            # Extract number
            import re
            match = re.search(r'\d+', period_str)
            if match:
                return int(match.group())
            return 1
        
        # Default
        return 7
    
    def generate_trading_days(self, days_back: int) -> List[datetime]:
        """
        Generera lista med handelsdagar (skip weekends).
        """
        trading_days = []
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        days_collected = 0
        days_checked = 0
        max_days_to_check = days_back * 2  # Safety margin
        
        while days_collected < days_back and days_checked < max_days_to_check:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                trading_days.append(current_date)
                days_collected += 1
            
            current_date -= timedelta(days=1)
            days_checked += 1
        
        # Reverse så äldsta är först
        trading_days.reverse()
        return trading_days
    
    def run_point_in_time_analysis(self, analysis_date: datetime) -> Dict:
        """
        Kör full dashboard-analys för en specifik dag med endast data 
        tillgänglig fram till den dagen.
        
        Returns:
            Dict med investable/watchlist instruments och market stats
        """
        print(f"\n📅 Analyserar {analysis_date.strftime('%Y-%m-%d')} (Point-in-Time)...")
        
        # Initialize screener med analysis_date för point-in-time constraint
        screener = InstrumentScreenerV22(
            enable_v22_filters=True,
            analysis_date=analysis_date
        )
        
        instruments = get_all_800_instruments()
        
        # Quick mode: endast 100 mest likvida instruments
        if self.quick_mode:
            instruments = instruments[:100]
            print(f"  ⚡ QUICK MODE: Analyserar endast {len(instruments)} instruments")
        
        try:
            # Kör screening med point-in-time data (endast fram till analysis_date)
            results = screener.screen_instruments(instruments)
        except Exception as e:
            print(f"⚠️  Error screening instruments: {e}")
            return None
        
        # Filter actionable signals (GREEN/YELLOW)
        actionable = [r for r in results if r.signal in [Signal.GREEN, Signal.YELLOW]]
        
        # Prioritize All-Weather i CRISIS
        if results and results[0].regime_multiplier <= 0.2:
            all_weather = [r for r in actionable if is_all_weather(r.ticker)]
            normal = [r for r in actionable if not is_all_weather(r.ticker)]
            actionable = all_weather + normal
        
        # Run through Execution Guard
        investable = []
        watchlist = []
        
        for r in actionable:
            if "BLOCK" in r.entry_recommendation or r.final_allocation == 0.0:
                watchlist.append(r)
                continue
            
            exec_result = self.execution_guard.analyze(
                ticker=r.ticker,
                category=r.category if hasattr(r, 'category') else 'default',
                position_size_pct=r.final_allocation,
                net_edge_pct=r.net_edge_after_costs,
                product_name=r.name,
                holding_period_days=5
            )
            
            r.exec_result = exec_result
            
            if exec_result.net_edge_after_execution > 0:
                investable.append(r)
            else:
                watchlist.append(r)
        
        # Market stats
        total_signals = len(results)
        green_signals = len([r for r in results if r.signal == Signal.GREEN])
        yellow_signals = len([r for r in results if r.signal == Signal.YELLOW])
        red_signals = len([r for r in results if r.signal == Signal.RED])
        
        # Determine regime from regime_multiplier
        regime_multiplier = results[0].regime_multiplier if results else 0
        if regime_multiplier <= 0.2:
            regime = "🔴 CRISIS"
        elif regime_multiplier <= 0.4:
            regime = "🟠 STRESSED"
        elif regime_multiplier <= 0.7:
            regime = "🟡 CAUTIOUS"
        else:
            regime = "🟢 HEALTHY"
        
        return {
            'date': analysis_date.strftime('%Y-%m-%d'),
            'regime': regime,
            'regime_multiplier': regime_multiplier,
            'investable': [self._serialize_result(r) for r in investable],
            'watchlist': [self._serialize_result(r) for r in watchlist],
            'market_stats': {
                'total_analyzed': total_signals,
                'green_signals': green_signals,
                'yellow_signals': yellow_signals,
                'red_signals': red_signals
            }
        }
    
    def _serialize_result(self, result) -> Dict:
        """Convert screening result to JSON-serializable dict."""
        exec_result = getattr(result, 'exec_result', None)
        
        return {
            'ticker': result.ticker,
            'name': result.name,
            'category': result.category if hasattr(result, 'category') else 'unknown',
            'signal': result.signal.name,
            'score': result.final_score,  # V22 uses final_score not score
            'technical_edge': result.net_edge_after_costs,  # Before execution costs
            'net_edge_after_execution': exec_result.net_edge_after_execution if exec_result else 0,
            'position': result.final_allocation,
            'execution_risk': exec_result.execution_risk_level if exec_result else 'UNKNOWN'
        }
    
    def run_backfill_simulation(self, days_back: int) -> List[Dict]:
        """
        Kör full backfill simulation för specified period.
        
        Returns:
            List of daily analysis results
        """
        print(f"\n🎯 HISTORICAL BACKFILL SIMULATION")
        print(f"Period: Senaste {days_back} handelsdagar")
        print(f"Portfolio: {self.portfolio_value_sek:,.0f} SEK")
        if self.quick_mode:
            print(f"Mode: ⚡ QUICK (100 instruments only)")
        else:
            print(f"Mode: 🔍 FULL (800 instruments)")
        print("=" * 80)
        
        trading_days = self.generate_trading_days(days_back)
        print(f"\n📊 Genererade {len(trading_days)} handelsdagar")
        print(f"Från: {trading_days[0].strftime('%Y-%m-%d')}")
        print(f"Till: {trading_days[-1].strftime('%Y-%m-%d')}")
        
        # Run point-in-time analysis för varje dag
        daily_results = []
        
        for i, analysis_date in enumerate(trading_days, 1):
            print(f"\n[{i}/{len(trading_days)}] ", end='')
            
            result = self.run_point_in_time_analysis(analysis_date)
            
            if result:
                daily_results.append(result)
                
                # Save individual day result
                date_str = result['date']
                output_file = self.reports_dir / f"actionable_{date_str}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"✅ {len(result['investable'])} investable, {len(result['watchlist'])} watchlist")
            else:
                print(f"⚠️  Skipped (no data)")
        
        print(f"\n✅ Backfill complete: {len(daily_results)} days analyzed")
        print(f"📁 Saved to: {self.reports_dir}")
        
        return daily_results
    
    def generate_backfill_summary(self, daily_results: List[Dict]) -> Dict:
        """
        Generera sammanfattning av backfill results.
        """
        if not daily_results:
            return {}
        
        total_days = len(daily_results)
        total_investable = sum(len(d['investable']) for d in daily_results)
        total_watchlist = sum(len(d['watchlist']) for d in daily_results)
        
        # Regime distribution
        regimes = [d['regime'] for d in daily_results]
        regime_counts = {}
        for regime in regimes:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        return {
            'period': {
                'start_date': daily_results[0]['date'],
                'end_date': daily_results[-1]['date'],
                'total_days': total_days
            },
            'signals': {
                'total_investable': total_investable,
                'total_watchlist': total_watchlist,
                'avg_investable_per_day': total_investable / total_days,
                'avg_watchlist_per_day': total_watchlist / total_days
            },
            'regime_distribution': regime_counts,
            'data_quality': 'HIGH (Backfilled Point-in-Time Analysis)'
        }


def main():
    parser = argparse.ArgumentParser(description='Historical Backfill Simulation')
    parser.add_argument('--period', type=str, help='Period string (e.g., "senaste veckan")')
    parser.add_argument('--days', type=int, help='Number of trading days')
    parser.add_argument('--portfolio', type=float, default=100000, help='Portfolio value in SEK')
    parser.add_argument('--quick', action='store_true', help='Quick mode: endast 100 instruments')
    
    args = parser.parse_args()
    
    # Determine days back
    if args.days:
        days_back = args.days
    elif args.period:
        simulator = HistoricalBackfillSimulator(
            portfolio_value_sek=args.portfolio,
            quick_mode=args.quick
        )
        days_back = simulator.parse_period(args.period)
    else:
        print("❌ Måste ange --period eller --days")
        return
    
    # Run simulation
    simulator = HistoricalBackfillSimulator(
        portfolio_value_sek=args.portfolio,
        quick_mode=args.quick
    )
    daily_results = simulator.run_backfill_simulation(days_back)
    
    if not daily_results:
        print("\n❌ Ingen data genererad")
        return
    
    # Generate summary
    summary = simulator.generate_backfill_summary(daily_results)
    
    print("\n" + "=" * 80)
    print("📊 BACKFILL SUMMARY")
    print("=" * 80)
    print(f"\nPeriod: {summary['period']['start_date']} → {summary['period']['end_date']}")
    print(f"Days Analyzed: {summary['period']['total_days']}")
    print(f"\nSignals:")
    print(f"  - Total Investable: {summary['signals']['total_investable']}")
    print(f"  - Total Watchlist: {summary['signals']['total_watchlist']}")
    print(f"  - Avg per Day: {summary['signals']['avg_investable_per_day']:.1f} investable")
    print(f"\nData Quality: {summary['data_quality']}")
    
    # Save summary
    summary_file = simulator.reports_dir / "backfill_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Summary saved: {summary_file}")
    
    # Prompt to run weekly analysis
    print("\n" + "=" * 80)
    print("🎯 NÄSTA STEG: Kör veckoanalys på backfilled data")
    print("=" * 80)
    print("\nKommando:")
    print("  python veckovis_analys.py --backfill")


if __name__ == "__main__":
    main()
