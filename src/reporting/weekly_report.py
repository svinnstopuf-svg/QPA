"""
Weekly Report Module - Delta Analysis

Jämför marknadens temperatur vecka för vecka:
- Signal distribution changes (RED/YELLOW/GREEN shifts)
- Confidence changes per instrument
- New opportunities (RED → YELLOW/GREEN transitions)
- Market temperature trends
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class WeeklySnapshot:
    """Snapshot of market state for a given week."""
    week_start: str
    week_end: str
    timestamp: str
    total_instruments: int
    signal_distribution: Dict[str, int]  # GREEN/YELLOW/ORANGE/RED counts
    top_opportunities: List[Dict]  # Top 10 by score
    avg_edge: float
    avg_confidence: float
    market_temperature: str  # "FROZEN", "COLD", "COOL", "WARM", "HOT"


@dataclass
class InstrumentDelta:
    """Change in an instrument's status week-over-week."""
    ticker: str
    name: str
    signal_change: str  # e.g. "RED → YELLOW"
    confidence_change: float  # e.g. +12%
    score_change: float
    edge_change: float
    decision: str  # "HOLD", "INCREASE", "DECREASE", "NEW"


class WeeklyReportGenerator:
    """
    Generates weekly comparison reports showing delta analysis.
    
    Stores snapshots in weekly_snapshots/ directory.
    Compares current week vs previous week.
    """
    
    def __init__(self, snapshot_dir: str = "weekly_snapshots"):
        """Initialize weekly report generator."""
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(exist_ok=True)
    
    def save_snapshot(self, results: List[Dict], week_start: datetime) -> WeeklySnapshot:
        """
        Save current screening results as a weekly snapshot.
        
        Args:
            results: Screening results from InstrumentScreener
            week_start: Start date of the week
            
        Returns:
            WeeklySnapshot object
        """
        week_end = week_start + timedelta(days=6)
        
        # Calculate signal distribution
        signal_dist = {
            "GREEN": 0,
            "YELLOW": 0,
            "ORANGE": 0,
            "RED": 0
        }
        
        total_edge = 0
        total_confidence = 0
        
        for result in results:
            signal = result.get('signal', 'RED')
            signal_dist[signal] = signal_dist.get(signal, 0) + 1
            total_edge += result.get('best_edge', 0)
            
            # Extract confidence from signal_confidence string
            conf_str = result.get('signal_confidence', 'LÅG')
            if 'HÖG' in conf_str:
                conf_val = 0.8
            elif 'MÅTTLIG' in conf_str:
                conf_val = 0.6
            else:
                conf_val = 0.4
            total_confidence += conf_val
        
        # Top opportunities (sorted by score)
        top_opportunities = sorted(
            results,
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )[:10]
        
        # Simplify top opportunities for storage
        top_simple = [
            {
                'ticker': r.get('ticker'),
                'name': r.get('name'),
                'signal': r.get('signal'),
                'score': r.get('overall_score'),
                'edge': r.get('best_edge'),
                'confidence': r.get('signal_confidence')
            }
            for r in top_opportunities
        ]
        
        # Calculate market temperature
        total = len(results)
        red_pct = signal_dist['RED'] / total if total > 0 else 1.0
        green_yellow_pct = (signal_dist['GREEN'] + signal_dist['YELLOW']) / total if total > 0 else 0
        
        if red_pct >= 0.9:
            temperature = "FROZEN"
        elif red_pct >= 0.8:
            temperature = "COLD"
        elif red_pct >= 0.7:
            temperature = "COOL"
        elif green_yellow_pct >= 0.3:
            temperature = "WARM"
        elif green_yellow_pct >= 0.5:
            temperature = "HOT"
        else:
            temperature = "COOL"
        
        snapshot = WeeklySnapshot(
            week_start=week_start.strftime("%Y-%m-%d"),
            week_end=week_end.strftime("%Y-%m-%d"),
            timestamp=datetime.now().isoformat(),
            total_instruments=len(results),
            signal_distribution=signal_dist,
            top_opportunities=top_simple,
            avg_edge=total_edge / total if total > 0 else 0,
            avg_confidence=total_confidence / total if total > 0 else 0,
            market_temperature=temperature
        )
        
        # Save to file
        filename = self.snapshot_dir / f"snapshot_{week_start.strftime('%Y_%m_%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False)
        
        return snapshot
    
    def load_snapshot(self, week_start: datetime) -> Optional[WeeklySnapshot]:
        """Load a snapshot from a specific week."""
        filename = self.snapshot_dir / f"snapshot_{week_start.strftime('%Y_%m_%d')}.json"
        
        if not filename.exists():
            return None
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return WeeklySnapshot(**data)
    
    def get_latest_snapshot(self) -> Optional[WeeklySnapshot]:
        """Get the most recent snapshot."""
        snapshots = list(self.snapshot_dir.glob("snapshot_*.json"))
        if not snapshots:
            return None
        
        latest = max(snapshots, key=lambda p: p.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return WeeklySnapshot(**data)
    
    def compare_weeks(
        self,
        current_results: List[Dict],
        current_week: datetime,
        previous_snapshot: Optional[WeeklySnapshot] = None
    ) -> Tuple[WeeklySnapshot, Optional[Dict]]:
        """
        Compare current week results with previous week.
        
        Args:
            current_results: Current screening results
            current_week: Start date of current week
            previous_snapshot: Previous week's snapshot (optional, will load if None)
            
        Returns:
            (current_snapshot, delta_analysis)
        """
        # Save current snapshot
        current_snapshot = self.save_snapshot(current_results, current_week)
        
        # Load previous snapshot if not provided
        if previous_snapshot is None:
            previous_week = current_week - timedelta(days=7)
            previous_snapshot = self.load_snapshot(previous_week)
        
        if previous_snapshot is None:
            return current_snapshot, None
        
        # Perform delta analysis
        delta = self._calculate_delta(current_snapshot, previous_snapshot, current_results)
        
        return current_snapshot, delta
    
    def _calculate_delta(
        self,
        current: WeeklySnapshot,
        previous: WeeklySnapshot,
        current_results: List[Dict]
    ) -> Dict:
        """Calculate detailed delta between two snapshots."""
        
        # Signal distribution changes
        signal_delta = {}
        for signal in ['GREEN', 'YELLOW', 'ORANGE', 'RED']:
            curr_count = current.signal_distribution.get(signal, 0)
            prev_count = previous.signal_distribution.get(signal, 0)
            delta_count = curr_count - prev_count
            
            curr_pct = (curr_count / current.total_instruments * 100) if current.total_instruments > 0 else 0
            prev_pct = (prev_count / previous.total_instruments * 100) if previous.total_instruments > 0 else 0
            delta_pct = curr_pct - prev_pct
            
            signal_delta[signal] = {
                'current_count': curr_count,
                'previous_count': prev_count,
                'delta_count': delta_count,
                'current_pct': curr_pct,
                'previous_pct': prev_pct,
                'delta_pct': delta_pct
            }
        
        # Temperature trend
        temp_trend = self._temperature_trend(previous.market_temperature, current.market_temperature)
        
        # Instrument-level changes (track top instruments)
        instrument_deltas = []
        
        # Create lookup for previous top opportunities
        prev_instruments = {
            item['ticker']: item for item in previous.top_opportunities
        }
        
        for result in current_results:
            ticker = result.get('ticker')
            if ticker in prev_instruments:
                prev = prev_instruments[ticker]
                curr_signal = result.get('signal')
                prev_signal = prev.get('signal')
                
                if curr_signal != prev_signal:
                    # Signal changed
                    conf_change = self._extract_confidence_value(
                        result.get('signal_confidence')
                    ) - self._extract_confidence_value(
                        prev.get('confidence')
                    )
                    
                    score_change = result.get('overall_score', 0) - prev.get('score', 0)
                    edge_change = result.get('best_edge', 0) - prev.get('edge', 0)
                    
                    decision = self._determine_decision(
                        prev_signal, curr_signal, conf_change, score_change
                    )
                    
                    instrument_deltas.append(InstrumentDelta(
                        ticker=ticker,
                        name=result.get('name', ticker),
                        signal_change=f"{prev_signal} → {curr_signal}",
                        confidence_change=conf_change * 100,
                        score_change=score_change,
                        edge_change=edge_change,
                        decision=decision
                    ))
        
        # Sort by most significant changes
        instrument_deltas.sort(key=lambda x: abs(x.score_change), reverse=True)
        
        # New opportunities (RED → YELLOW/GREEN)
        new_opportunities = [
            d for d in instrument_deltas
            if 'RED' in d.signal_change and ('YELLOW' in d.signal_change or 'GREEN' in d.signal_change)
        ]
        
        # Degraded opportunities (YELLOW/GREEN → RED/ORANGE)
        degraded = [
            d for d in instrument_deltas
            if ('YELLOW' in d.signal_change or 'GREEN' in d.signal_change) and 'RED' in d.signal_change.split(' → ')[1]
        ]
        
        return {
            'signal_delta': signal_delta,
            'temperature_trend': temp_trend,
            'instrument_deltas': [asdict(d) for d in instrument_deltas[:20]],  # Top 20
            'new_opportunities': [asdict(d) for d in new_opportunities],
            'degraded_opportunities': [asdict(d) for d in degraded],
            'avg_edge_change': current.avg_edge - previous.avg_edge,
            'avg_confidence_change': current.avg_confidence - previous.avg_confidence
        }
    
    def _temperature_trend(self, prev: str, curr: str) -> str:
        """Determine temperature trend."""
        temps = ["FROZEN", "COLD", "COOL", "WARM", "HOT"]
        prev_idx = temps.index(prev) if prev in temps else 0
        curr_idx = temps.index(curr) if curr in temps else 0
        
        if curr_idx > prev_idx:
            return "VÄRMANDE (Förbättring)"
        elif curr_idx < prev_idx:
            return "KYLANDE (Försämring)"
        else:
            return "STABIL (Oförändrad)"
    
    def _extract_confidence_value(self, conf_str: str) -> float:
        """Extract numeric confidence from string."""
        if not conf_str:
            return 0.4
        if 'HÖG' in conf_str:
            return 0.8
        elif 'MÅTTLIG' in conf_str:
            return 0.6
        else:
            return 0.4
    
    def _determine_decision(
        self,
        prev_signal: str,
        curr_signal: str,
        conf_change: float,
        score_change: float
    ) -> str:
        """Determine investment decision based on changes."""
        signals = ['RED', 'ORANGE', 'YELLOW', 'GREEN']
        prev_idx = signals.index(prev_signal) if prev_signal in signals else 0
        curr_idx = signals.index(curr_signal) if curr_signal in signals else 0
        
        if curr_idx > prev_idx and conf_change > 0:
            return "ÖKA POSITION"
        elif curr_idx > prev_idx:
            return "NY MÖJLIGHET"
        elif curr_idx < prev_idx:
            return "MINSKA/STÄNG"
        elif conf_change > 0.1:
            return "BEHÅLL/ÖKA"
        elif conf_change < -0.1:
            return "BEHÅLL/MINSKA"
        else:
            return "BEHÅLL"
    
    def generate_report(
        self,
        current_snapshot: WeeklySnapshot,
        delta: Optional[Dict]
    ) -> str:
        """
        Generate formatted weekly report.
        
        Args:
            current_snapshot: Current week's snapshot
            delta: Delta analysis (optional)
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("VECKORAPPORT - DELTA-ANALYS")
        report.append("=" * 80)
        report.append(f"Period: {current_snapshot.week_start} till {current_snapshot.week_end}")
        report.append(f"Genererad: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")
        
        # Current state
        report.append("-" * 80)
        report.append("NUVARANDE MARKNADSSTATUS")
        report.append("-" * 80)
        report.append(f"Total instrument analyserade: {current_snapshot.total_instruments}")
        report.append(f"Marknadstemperatur: {current_snapshot.market_temperature}")
        report.append("")
        
        report.append("Signalfördelning:")
        for signal, count in current_snapshot.signal_distribution.items():
            pct = (count / current_snapshot.total_instruments * 100) if current_snapshot.total_instruments > 0 else 0
            icon = {"GREEN": "🟢", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}.get(signal, "")
            report.append(f"  {icon} {signal:<8}: {count:>3} ({pct:>5.1f}%)")
        
        report.append("")
        report.append(f"Genomsnittlig edge: {current_snapshot.avg_edge:+.4f}%")
        report.append(f"Genomsnittlig konfidens: {current_snapshot.avg_confidence*100:.1f}%")
        
        if delta is None:
            report.append("")
            report.append("⚠️  Ingen tidigare vecka att jämföra med - detta är första körningen.")
            return "\n".join(report)
        
        # Delta analysis
        report.append("")
        report.append("=" * 80)
        report.append("DELTA-ANALYS (Förra veckan → Denna vecka)")
        report.append("=" * 80)
        report.append("")
        
        # Temperature trend
        report.append(f"🌡️  Temperaturtrend: {delta['temperature_trend']}")
        report.append("")
        
        # Signal changes
        report.append("-" * 80)
        report.append("SIGNALFÖRDELNING - FÖRÄNDRINGAR")
        report.append("-" * 80)
        
        for signal in ['GREEN', 'YELLOW', 'ORANGE', 'RED']:
            sd = delta['signal_delta'][signal]
            icon = {"GREEN": "🟢", "YELLOW": "🟡", "ORANGE": "🟠", "RED": "🔴"}.get(signal, "")
            
            delta_str = f"{sd['delta_pct']:+.1f}%"
            trend = "📈" if sd['delta_pct'] > 0 else "📉" if sd['delta_pct'] < 0 else "➡️"
            
            report.append(
                f"{icon} {signal:<8}: {sd['previous_pct']:>5.1f}% → {sd['current_pct']:>5.1f}% "
                f"({delta_str}) {trend}"
            )
        
        # Edge and confidence changes
        report.append("")
        edge_trend = "📈" if delta['avg_edge_change'] > 0 else "📉"
        conf_trend = "📈" if delta['avg_confidence_change'] > 0 else "📉"
        report.append(f"Edge-förändring: {delta['avg_edge_change']:+.4f}% {edge_trend}")
        report.append(f"Konfidens-förändring: {delta['avg_confidence_change']*100:+.1f}% {conf_trend}")
        
        # New opportunities
        if delta['new_opportunities']:
            report.append("")
            report.append("-" * 80)
            report.append(f"NYA MÖJLIGHETER (RED → YELLOW/GREEN): {len(delta['new_opportunities'])} st")
            report.append("-" * 80)
            
            for opp in delta['new_opportunities'][:10]:
                report.append(
                    f"  ✨ {opp['name']} ({opp['ticker']}): {opp['signal_change']}"
                )
                report.append(
                    f"     Score: {opp['score_change']:+.1f} | "
                    f"Edge: {opp['edge_change']:+.2f}% | "
                    f"Beslut: {opp['decision']}"
                )
        
        # Degraded opportunities
        if delta['degraded_opportunities']:
            report.append("")
            report.append("-" * 80)
            report.append(f"FÖRSÄMRADE MÖJLIGHETER: {len(delta['degraded_opportunities'])} st")
            report.append("-" * 80)
            
            for deg in delta['degraded_opportunities'][:10]:
                report.append(
                    f"  ⚠️  {deg['name']} ({deg['ticker']}): {deg['signal_change']}"
                )
                report.append(
                    f"     Score: {deg['score_change']:+.1f} | "
                    f"Beslut: {deg['decision']}"
                )
        
        # Top confidence shifts
        top_conf_shifts = sorted(
            [d for d in delta['instrument_deltas'] if abs(d['confidence_change']) > 5],
            key=lambda x: abs(x['confidence_change']),
            reverse=True
        )[:10]
        
        if top_conf_shifts:
            report.append("")
            report.append("-" * 80)
            report.append("STÖRSTA KONFIDENSSKIFTEN")
            report.append("-" * 80)
            
            for shift in top_conf_shifts:
                trend = "📈" if shift['confidence_change'] > 0 else "📉"
                report.append(
                    f"  {trend} {shift['name']} ({shift['ticker']}): "
                    f"Konfidens {shift['confidence_change']:+.1f}%"
                )
                report.append(f"     Signal: {shift['signal_change']} | Beslut: {shift['decision']}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


# Convenience function
def generate_weekly_report(
    current_results: List[Dict],
    current_week: datetime = None
) -> str:
    """
    Generate a weekly delta report from screening results.
    
    Args:
        current_results: Results from instrument_screener
        current_week: Start of current week (defaults to today's week)
        
    Returns:
        Formatted report string
    """
    if current_week is None:
        today = datetime.now()
        # Get Monday of current week
        current_week = today - timedelta(days=today.weekday())
    
    generator = WeeklyReportGenerator()
    current_snapshot, delta = generator.compare_weeks(current_results, current_week)
    report = generator.generate_report(current_snapshot, delta)
    
    return report


if __name__ == "__main__":
    print("Weekly Report Module - Use generate_weekly_report() from your screening script")
    print("Example:")
    print("  from src.reporting.weekly_report import generate_weekly_report")
    print("  report = generate_weekly_report(screening_results)")
    print("  print(report)")
