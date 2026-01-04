"""
Quarterly Audit Module - Pattern Performance & Degradation Analysis

För systemarkitekten att köra var 3:e månad:
- Identifierar mest lönsamma mönster i realtid
- Detekterar degradation och försämrade patterns
- Rekommenderar åtgärder (behåll, justera, ta bort)
- Validerar Bayesian predictions mot actual outcomes
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class PatternPerformance:
    """Performance metrics for a specific pattern."""
    pattern_id: str
    pattern_name: str
    occurrences: int
    avg_edge_predicted: float
    avg_edge_actual: float
    prediction_accuracy: float  # % correct direction
    win_rate: float
    avg_return_when_active: float
    sharpe_ratio: float
    stability_score: float
    degradation_rate: float  # % per quarter
    recommendation: str  # "KEEP", "ADJUST", "MONITOR", "REMOVE"


@dataclass
class QuarterlyAuditReport:
    """Complete quarterly audit results."""
    quarter_start: str
    quarter_end: str
    timestamp: str
    total_patterns_analyzed: int
    patterns_performance: List[PatternPerformance]
    best_patterns: List[str]  # Top 5
    worst_patterns: List[str]  # Bottom 5
    degrading_patterns: List[str]  # Significant degradation
    recommendations: Dict[str, List[str]]
    summary_stats: Dict


class QuarterlyAuditor:
    """
    Performs quarterly audits of pattern performance.
    
    Compares predicted edges vs actual outcomes.
    Identifies degradation trends over 3+ months.
    Provides actionable recommendations.
    """
    
    def __init__(
        self,
        signal_log_dir: str = "signal_logs",
        audit_dir: str = "quarterly_audits"
    ):
        """Initialize quarterly auditor."""
        self.signal_log_dir = Path(signal_log_dir)
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(exist_ok=True)
    
    def generate_quarterly_audit(
        self,
        quarter_end: datetime = None,
        lookback_quarters: int = 1
    ) -> QuarterlyAuditReport:
        """
        Generate comprehensive quarterly audit report.
        
        Args:
            quarter_end: End date of quarter (defaults to today)
            lookback_quarters: Number of quarters to analyze (default 1)
            
        Returns:
            QuarterlyAuditReport with full analysis
        """
        if quarter_end is None:
            quarter_end = datetime.now()
        
        quarter_start = quarter_end - timedelta(days=90 * lookback_quarters)
        
        # Load signal logs from tracking system
        signal_data = self._load_signal_logs(quarter_start, quarter_end)
        
        if not signal_data:
            print("⚠️  No signal data found for this period")
            return self._empty_report(quarter_start, quarter_end)
        
        # Analyze each pattern's performance
        pattern_performances = self._analyze_pattern_performance(signal_data)
        
        # Identify best and worst
        sorted_by_edge = sorted(
            pattern_performances,
            key=lambda x: x.avg_edge_actual,
            reverse=True
        )
        
        best_patterns = [p.pattern_id for p in sorted_by_edge[:5]]
        worst_patterns = [p.pattern_id for p in sorted_by_edge[-5:]]
        
        # Identify degrading patterns
        degrading_patterns = [
            p.pattern_id for p in pattern_performances
            if p.degradation_rate < -10  # >10% degradation per quarter
        ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(pattern_performances)
        
        # Summary statistics
        summary_stats = self._calculate_summary_stats(pattern_performances)
        
        report = QuarterlyAuditReport(
            quarter_start=quarter_start.strftime("%Y-%m-%d"),
            quarter_end=quarter_end.strftime("%Y-%m-%d"),
            timestamp=datetime.now().isoformat(),
            total_patterns_analyzed=len(pattern_performances),
            patterns_performance=pattern_performances,
            best_patterns=best_patterns,
            worst_patterns=worst_patterns,
            degrading_patterns=degrading_patterns,
            recommendations=recommendations,
            summary_stats=summary_stats
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _load_signal_logs(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Load signal logs from tracking system."""
        signal_file = self.signal_log_dir / "signal_history.jsonl"
        
        if not signal_file.exists():
            return []
        
        signals = []
        with open(signal_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_date = datetime.fromisoformat(entry['timestamp'])
                    
                    if start_date <= entry_date <= end_date:
                        signals.append(entry)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        return signals
    
    def _analyze_pattern_performance(
        self,
        signal_data: List[Dict]
    ) -> List[PatternPerformance]:
        """Analyze performance of each pattern."""
        # Group by pattern
        pattern_groups = {}
        
        for signal in signal_data:
            # Extract patterns from metadata if available
            patterns = signal.get('patterns', [])
            
            for pattern in patterns:
                pattern_id = pattern.get('pattern_id', 'unknown')
                
                if pattern_id not in pattern_groups:
                    pattern_groups[pattern_id] = []
                
                pattern_groups[pattern_id].append({
                    'signal': signal,
                    'pattern': pattern
                })
        
        # Analyze each pattern
        performances = []
        
        for pattern_id, entries in pattern_groups.items():
            perf = self._calculate_pattern_metrics(pattern_id, entries)
            if perf:
                performances.append(perf)
        
        return performances
    
    def _calculate_pattern_metrics(
        self,
        pattern_id: str,
        entries: List[Dict]
    ) -> Optional[PatternPerformance]:
        """Calculate detailed metrics for a single pattern."""
        if not entries:
            return None
        
        # Extract data
        predicted_edges = []
        actual_returns = []
        directions_correct = []
        
        for entry in entries:
            pattern = entry['pattern']
            signal = entry['signal']
            
            predicted_edge = pattern.get('edge', 0)
            predicted_edges.append(predicted_edge)
            
            # Get actual outcomes (1 month)
            outcomes = signal.get('outcomes', {})
            if '1m' in outcomes and outcomes['1m'] is not None:
                actual_return = outcomes['1m']
                actual_returns.append(actual_return)
                
                # Check if direction was correct
                if (predicted_edge > 0 and actual_return > 0) or \
                   (predicted_edge < 0 and actual_return < 0):
                    directions_correct.append(1)
                else:
                    directions_correct.append(0)
        
        if not actual_returns:
            return None
        
        # Calculate metrics
        avg_predicted = np.mean(predicted_edges)
        avg_actual = np.mean(actual_returns)
        
        # Prediction accuracy (% correct direction)
        accuracy = np.mean(directions_correct) if directions_correct else 0
        
        # Win rate (% positive returns)
        win_rate = np.mean([1 if r > 0 else 0 for r in actual_returns])
        
        # Sharpe ratio (simplified)
        if np.std(actual_returns) > 0:
            sharpe = np.mean(actual_returns) / np.std(actual_returns) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Stability score (consistency of returns)
        stability = 1 - (np.std(actual_returns) / (abs(np.mean(actual_returns)) + 0.01))
        stability = max(0, min(1, stability))
        
        # Degradation rate (compare first half vs second half)
        mid_point = len(actual_returns) // 2
        if mid_point > 0:
            first_half_avg = np.mean(actual_returns[:mid_point])
            second_half_avg = np.mean(actual_returns[mid_point:])
            
            if first_half_avg != 0:
                degradation = ((second_half_avg - first_half_avg) / abs(first_half_avg)) * 100
            else:
                degradation = 0
        else:
            degradation = 0
        
        # Determine recommendation
        recommendation = self._determine_pattern_recommendation(
            avg_actual, accuracy, win_rate, stability, degradation
        )
        
        return PatternPerformance(
            pattern_id=pattern_id,
            pattern_name=pattern_id.replace('_', ' ').title(),
            occurrences=len(entries),
            avg_edge_predicted=avg_predicted,
            avg_edge_actual=avg_actual,
            prediction_accuracy=accuracy * 100,
            win_rate=win_rate * 100,
            avg_return_when_active=avg_actual,
            sharpe_ratio=sharpe,
            stability_score=stability * 100,
            degradation_rate=degradation,
            recommendation=recommendation
        )
    
    def _determine_pattern_recommendation(
        self,
        avg_actual: float,
        accuracy: float,
        win_rate: float,
        stability: float,
        degradation: float
    ) -> str:
        """Determine recommendation for a pattern."""
        # REMOVE if:
        # - Negative edge AND low accuracy
        # - Heavy degradation
        if (avg_actual < -0.05 and accuracy < 0.4) or degradation < -30:
            return "REMOVE"
        
        # MONITOR if:
        # - Moderate degradation
        # - Low stability
        # - Edge near zero
        if degradation < -10 or stability < 0.3 or abs(avg_actual) < 0.05:
            return "MONITOR"
        
        # ADJUST if:
        # - Good edge but poor prediction accuracy
        # - Needs parameter tuning
        if avg_actual > 0.1 and accuracy < 0.55:
            return "ADJUST"
        
        # KEEP if strong performance
        if avg_actual > 0.1 and accuracy > 0.6 and win_rate > 55:
            return "KEEP"
        
        return "MONITOR"
    
    def _generate_recommendations(
        self,
        performances: List[PatternPerformance]
    ) -> Dict[str, List[str]]:
        """Generate actionable recommendations."""
        recommendations = {
            "KEEP": [],
            "ADJUST": [],
            "MONITOR": [],
            "REMOVE": []
        }
        
        for perf in performances:
            rec_text = f"{perf.pattern_name}: " \
                      f"Edge {perf.avg_edge_actual:+.2f}%, " \
                      f"Accuracy {perf.prediction_accuracy:.1f}%, " \
                      f"Degradation {perf.degradation_rate:+.1f}%"
            
            recommendations[perf.recommendation].append(rec_text)
        
        return recommendations
    
    def _calculate_summary_stats(
        self,
        performances: List[PatternPerformance]
    ) -> Dict:
        """Calculate summary statistics."""
        if not performances:
            return {}
        
        avg_edge = np.mean([p.avg_edge_actual for p in performances])
        avg_accuracy = np.mean([p.prediction_accuracy for p in performances])
        avg_win_rate = np.mean([p.win_rate for p in performances])
        avg_sharpe = np.mean([p.sharpe_ratio for p in performances])
        avg_degradation = np.mean([p.degradation_rate for p in performances])
        
        # Count by recommendation
        rec_counts = {
            "KEEP": sum(1 for p in performances if p.recommendation == "KEEP"),
            "ADJUST": sum(1 for p in performances if p.recommendation == "ADJUST"),
            "MONITOR": sum(1 for p in performances if p.recommendation == "MONITOR"),
            "REMOVE": sum(1 for p in performances if p.recommendation == "REMOVE")
        }
        
        return {
            "avg_edge_actual": avg_edge,
            "avg_prediction_accuracy": avg_accuracy,
            "avg_win_rate": avg_win_rate,
            "avg_sharpe_ratio": avg_sharpe,
            "avg_degradation_rate": avg_degradation,
            "recommendation_counts": rec_counts
        }
    
    def _empty_report(
        self,
        quarter_start: datetime,
        quarter_end: datetime
    ) -> QuarterlyAuditReport:
        """Generate empty report when no data available."""
        return QuarterlyAuditReport(
            quarter_start=quarter_start.strftime("%Y-%m-%d"),
            quarter_end=quarter_end.strftime("%Y-%m-%d"),
            timestamp=datetime.now().isoformat(),
            total_patterns_analyzed=0,
            patterns_performance=[],
            best_patterns=[],
            worst_patterns=[],
            degrading_patterns=[],
            recommendations={},
            summary_stats={}
        )
    
    def _save_report(self, report: QuarterlyAuditReport):
        """Save audit report to file."""
        filename = self.audit_dir / f"audit_{report.quarter_start}_{report.quarter_end}.json"
        
        # Convert to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
    
    def format_report(self, report: QuarterlyAuditReport) -> str:
        """Format audit report as human-readable text."""
        lines = []
        lines.append("=" * 80)
        lines.append("KVARTALSREVISION - PATTERN PERFORMANCE & DEGRADATION")
        lines.append("=" * 80)
        lines.append(f"Period: {report.quarter_start} till {report.quarter_end}")
        lines.append(f"Genererad: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Analyserade patterns: {report.total_patterns_analyzed}")
        lines.append("")
        
        if not report.patterns_performance:
            lines.append("⚠️  Ingen data tillgänglig för denna period")
            lines.append("   Kör signal tracking under minst 1 månad innan första revisionen")
            return "\n".join(lines)
        
        # Summary statistics
        lines.append("-" * 80)
        lines.append("SAMMANFATTNING")
        lines.append("-" * 80)
        stats = report.summary_stats
        lines.append(f"Genomsnittlig edge (actual): {stats['avg_edge_actual']:+.3f}%")
        lines.append(f"Genomsnittlig prediction accuracy: {stats['avg_prediction_accuracy']:.1f}%")
        lines.append(f"Genomsnittlig win rate: {stats['avg_win_rate']:.1f}%")
        lines.append(f"Genomsnittlig Sharpe ratio: {stats['avg_sharpe_ratio']:.2f}")
        lines.append(f"Genomsnittlig degradation rate: {stats['avg_degradation_rate']:+.1f}% per kvartal")
        lines.append("")
        
        # Recommendation breakdown
        lines.append("Rekommendationsfördelning:")
        rec_counts = stats['recommendation_counts']
        for rec, count in rec_counts.items():
            icon = {"KEEP": "✅", "ADJUST": "🔧", "MONITOR": "👁️", "REMOVE": "❌"}.get(rec, "")
            lines.append(f"  {icon} {rec}: {count} patterns")
        lines.append("")
        
        # Best patterns
        if report.best_patterns:
            lines.append("-" * 80)
            lines.append("🏆 TOP 5 MEST LÖNSAMMA PATTERNS")
            lines.append("-" * 80)
            
            for i, pattern_id in enumerate(report.best_patterns, 1):
                perf = next((p for p in report.patterns_performance if p.pattern_id == pattern_id), None)
                if perf:
                    lines.append(f"{i}. {perf.pattern_name}")
                    lines.append(f"   Edge: {perf.avg_edge_actual:+.3f}% | "
                               f"Accuracy: {perf.prediction_accuracy:.1f}% | "
                               f"Win Rate: {perf.win_rate:.1f}%")
                    lines.append(f"   Sharpe: {perf.sharpe_ratio:.2f} | "
                               f"Stability: {perf.stability_score:.1f}% | "
                               f"Degradation: {perf.degradation_rate:+.1f}%")
                    lines.append(f"   Rekommendation: {perf.recommendation}")
                    lines.append("")
        
        # Worst patterns
        if report.worst_patterns:
            lines.append("-" * 80)
            lines.append("⚠️  BOTTOM 5 SÄMST PRESTERANDE PATTERNS")
            lines.append("-" * 80)
            
            for i, pattern_id in enumerate(report.worst_patterns, 1):
                perf = next((p for p in report.patterns_performance if p.pattern_id == pattern_id), None)
                if perf:
                    lines.append(f"{i}. {perf.pattern_name}")
                    lines.append(f"   Edge: {perf.avg_edge_actual:+.3f}% | "
                               f"Accuracy: {perf.prediction_accuracy:.1f}%")
                    lines.append(f"   Degradation: {perf.degradation_rate:+.1f}% | "
                               f"Rekommendation: {perf.recommendation}")
                    lines.append("")
        
        # Degrading patterns
        if report.degrading_patterns:
            lines.append("-" * 80)
            lines.append("🚨 DEGRADERANDE PATTERNS (Kräver uppmärksamhet!)")
            lines.append("-" * 80)
            
            for pattern_id in report.degrading_patterns:
                perf = next((p for p in report.patterns_performance if p.pattern_id == pattern_id), None)
                if perf:
                    lines.append(f"❗ {perf.pattern_name}")
                    lines.append(f"   Degradation: {perf.degradation_rate:+.1f}% per kvartal")
                    lines.append(f"   Edge (predicted): {perf.avg_edge_predicted:+.3f}% → "
                               f"(actual): {perf.avg_edge_actual:+.3f}%")
                    lines.append(f"   Åtgärd: {perf.recommendation}")
                    lines.append("")
        
        # Detailed recommendations
        lines.append("-" * 80)
        lines.append("DETALJERADE REKOMMENDATIONER")
        lines.append("-" * 80)
        
        for rec_type in ["REMOVE", "MONITOR", "ADJUST", "KEEP"]:
            if report.recommendations.get(rec_type):
                icon = {"KEEP": "✅", "ADJUST": "🔧", "MONITOR": "👁️", "REMOVE": "❌"}.get(rec_type, "")
                lines.append(f"\n{icon} {rec_type}:")
                for rec in report.recommendations[rec_type]:
                    lines.append(f"  • {rec}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("ÅTGÄRDSPLAN")
        lines.append("=" * 80)
        lines.append("")
        
        if report.recommendations.get("REMOVE"):
            lines.append("🚫 TA BORT:")
            lines.append("   Dessa patterns presterar dåligt och bör tas bort från modellen")
            lines.append("")
        
        if report.recommendations.get("ADJUST"):
            lines.append("🔧 JUSTERA:")
            lines.append("   Dessa patterns har potential men behöver parameterjustering")
            lines.append("   Överväg att justera tröskelvärden eller fönsterstorlekar")
            lines.append("")
        
        if report.recommendations.get("MONITOR"):
            lines.append("👁️  ÖVERVAKA:")
            lines.append("   Dessa patterns visar varningssignaler - övervaka nästa kvartal")
            lines.append("")
        
        if report.recommendations.get("KEEP"):
            lines.append("✅ BEHÅLL:")
            lines.append("   Dessa patterns presterar väl - fortsätt använda")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def generate_quarterly_audit(
    quarter_end: datetime = None,
    lookback_quarters: int = 1
) -> str:
    """
    Convenience function to generate and format quarterly audit.
    
    Args:
        quarter_end: End date of quarter (defaults to today)
        lookback_quarters: Number of quarters to analyze
        
    Returns:
        Formatted audit report string
    """
    auditor = QuarterlyAuditor()
    report = auditor.generate_quarterly_audit(quarter_end, lookback_quarters)
    return auditor.format_report(report)


if __name__ == "__main__":
    print("Quarterly Audit Module - Run every 3 months")
    print("Usage:")
    print("  from src.reporting.quarterly_audit import generate_quarterly_audit")
    print("  report = generate_quarterly_audit()")
    print("  print(report)")
