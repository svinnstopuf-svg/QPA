"""
Elite Sunday Report Formatter

Format: Top 10, ranked by Multi-Factor.

Each setup shows:
1. THE WHY LOG: One aggressive, objective sentence explaining the edge
2. ARCHITECTURE: Entry/Stop/Target/Size (concrete numbers)
3. COMPROMISE-LOG: Which filters were close to threshold
4. EXECUTION STATUS: 🟢 ACTIVE or 🟡 WATCHLIST
5. TIME-STOP: Exit if target not reached within 10 days and price < Entry + 1%

Philosophy: Eliminate decision paralysis. Only the best 5. No exceptions.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta


@dataclass
class CompromiseWarning:
    """A filter that was close to threshold"""
    filter_name: str
    actual_value: float
    threshold_value: float
    margin_pct: float  # How close to failing (%)
    
    def __str__(self) -> str:
        return f"{self.filter_name}: {self.actual_value:.2f} vs threshold {self.threshold_value:.2f} (margin: {self.margin_pct:+.1f}%)"


class EliteReportFormatter:
    """
    Formats Sunday Report for Top 5 setups only.
    
    Principle: Ruthless clarity. No fluff.
    """
    
    # Thresholds for compromise detection
    COMPROMISE_MARGIN_PCT = 15.0  # If within 15% of threshold, flag as compromise
    
    def __init__(self):
        pass
    
    def generate_why_log(
        self,
        ticker: str,
        robust_score: float,
        quality_score: float,
        rrr: float,
        rs_rating: Optional[float],
        convergence: bool,
        timing_confidence: float
    ) -> str:
        """
        Generate "The Why Log" - one aggressive, objective sentence.
        
        Rules:
        - Lead with the STRONGEST differentiator
        - Use concrete numbers
        - No hedging or qualifiers
        
        Args:
            ticker: Stock ticker
            robust_score: Robust score (0-100)
            quality_score: Quality score (0-100)
            rrr: Risk/reward ratio
            rs_rating: RS-Rating (0-100) if Motor B active
            convergence: Alpha-Switch convergence detected
            timing_confidence: Timing score (0-100)
        
        Returns:
            One sentence explaining the edge
        """
        # Identify strongest edge
        edges = []
        
        if convergence:
            edges.append(("CONVERGENCE", f"Alpha-Switch convergence (Motor A→B)", 1000))
        
        if rs_rating and rs_rating >= 98:
            edges.append(("RS", f"RS-Rating {rs_rating:.0f} (top 2% of universe)", 900))
        
        if rrr >= 5.0:
            edges.append(("RRR", f"Best risk/reward in universe (1:{rrr:.1f})", 800))
        
        if robust_score >= 90:
            edges.append(("ROBUST", f"Robust Score {robust_score:.0f} (extreme statistical edge)", 700))
        
        if quality_score >= 85 and rrr >= 4.0:
            edges.append(("COMBO", f"Elite quality (Q:{quality_score:.0f}) with superior RRR (1:{rrr:.1f})", 600))
        
        if timing_confidence >= 70:
            edges.append(("TIMING", f"Timing confidence {timing_confidence:.0f}% (reversal imminent)", 500))
        
        if quality_score >= 90:
            edges.append(("QUALITY", f"Institutional-grade quality (Q:{quality_score:.0f})", 400))
        
        if robust_score >= 80:
            edges.append(("STATISTICAL", f"Statistically dominant (Robust:{robust_score:.0f}, Q:{quality_score:.0f})", 300))
        
        # Pick strongest
        if len(edges) > 0:
            edges.sort(key=lambda x: x[2], reverse=True)
            why_log = edges[0][1]
        else:
            # Fallback
            why_log = f"Multi-Factor Rank {(robust_score*0.6 + quality_score*0.4):.1f} (R:{robust_score:.0f}, Q:{quality_score:.0f})"
        
        return why_log
    
    def detect_compromises(
        self,
        setup
    ) -> List[CompromiseWarning]:
        """
        Detect filters that were close to failing.
        
        Checks:
        - Win Rate vs 60% threshold
        - RRR vs 3.0 threshold
        - P-Value vs 0.05 threshold
        - Quality Score vs 40 threshold
        - Timing vs 50% threshold
        - MAE Stop vs 6% hard cap
        
        Returns:
            List of CompromiseWarning for filters within 15% of threshold
        """
        compromises = []
        
        # Win Rate check (threshold 60%)
        if hasattr(setup, 'win_rate_63d'):
            threshold = 0.60
            actual = setup.win_rate_63d
            margin = ((actual - threshold) / threshold) * 100
            
            if 0 < margin < self.COMPROMISE_MARGIN_PCT:
                compromises.append(CompromiseWarning(
                    "Win Rate",
                    actual,
                    threshold,
                    margin
                ))
        
        # RRR check (threshold 3.0)
        if hasattr(setup, 'risk_reward_ratio'):
            threshold = 3.0
            actual = setup.risk_reward_ratio
            margin = ((actual - threshold) / threshold) * 100
            
            if 0 < margin < self.COMPROMISE_MARGIN_PCT:
                compromises.append(CompromiseWarning(
                    "Risk/Reward Ratio",
                    actual,
                    threshold,
                    margin
                ))
        
        # P-Value check (threshold 0.05 - lower is better)
        if hasattr(setup, 'p_value'):
            threshold = 0.05
            actual = setup.p_value
            # For p-value, margin is how close to EXCEEDING threshold
            margin = ((threshold - actual) / threshold) * 100
            
            if actual < threshold and margin < self.COMPROMISE_MARGIN_PCT:
                compromises.append(CompromiseWarning(
                    "P-Value (stat sig)",
                    actual,
                    threshold,
                    margin
                ))
        
        # Quality Score check (threshold 40)
        if hasattr(setup, 'quality_score'):
            threshold = 40.0
            actual = setup.quality_score
            margin = ((actual - threshold) / threshold) * 100
            
            if 0 < margin < self.COMPROMISE_MARGIN_PCT:
                compromises.append(CompromiseWarning(
                    "Quality Score",
                    actual,
                    threshold,
                    margin
                ))
        
        # Timing check (threshold 50%)
        if hasattr(setup, 'timing_confidence'):
            threshold = 50.0
            actual = setup.timing_confidence
            margin = ((actual - threshold) / threshold) * 100
            
            if 0 < margin < self.COMPROMISE_MARGIN_PCT:
                compromises.append(CompromiseWarning(
                    "Timing Confidence",
                    actual,
                    threshold,
                    margin
                ))
        
        # MAE Stop check (threshold 6%)
        if hasattr(setup, 'optimal_stop_pct'):
            threshold = 0.06
            actual = setup.optimal_stop_pct
            margin = ((threshold - actual) / threshold) * 100
            
            if actual > 0 and margin < self.COMPROMISE_MARGIN_PCT:
                compromises.append(CompromiseWarning(
                    "MAE Stop (hard cap 6%)",
                    actual,
                    threshold,
                    margin
                ))
        
        return compromises
    
    def format_setup(
        self,
        rank: int,
        setup,
        entry_date: datetime
    ) -> str:
        """
        Format single setup for Sunday Report.
        
        Args:
            rank: Ranking (1-10)
            setup: Setup object with all metrics
            entry_date: Expected entry date (Monday)
        
        Returns:
            Formatted string for display
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        signal_emoji = "🟢" if getattr(setup, 'signal_status', '') == 'ACTIVE BUY SIGNAL' else "🟡"
        lines.append(f"{signal_emoji} RANK [{rank}]: {setup.ticker} - {setup.best_pattern_name}")
        lines.append("=" * 80)
        
        # THE WHY LOG
        why_log = self.generate_why_log(
            ticker=setup.ticker,
            robust_score=getattr(setup, 'robust_score', 0),
            quality_score=getattr(setup, 'quality_score', 0),
            rrr=getattr(setup, 'risk_reward_ratio', 0),
            rs_rating=getattr(setup, 'rs_rating', None),
            convergence=getattr(setup, 'convergence_detected', False),
            timing_confidence=getattr(setup, 'timing_confidence', 0)
        )
        lines.append(f"\n📌 THE WHY: {why_log}")
        
        # ARCHITECTURE
        current_price = getattr(setup, 'current_price', 0)
        if current_price == 0 and hasattr(setup, 'quality_analysis'):
            # Try to get from quality analysis or use estimate
            current_price = 100.0  # Placeholder
        
        stop_pct = getattr(setup, 'optimal_stop_pct', 0.05)
        stop_price = current_price * (1 - stop_pct)
        
        # Target based on avg_win
        avg_win = getattr(setup, 'avg_win', 0.10)
        target_price = current_price * (1 + avg_win)
        
        position_sek = getattr(setup, 'position_size_sek', 0)
        shares = int(position_sek / current_price) if current_price > 0 else 0
        
        lines.append(f"\n🎯 ARCHITECTURE:")
        lines.append(f"   ENTRY: {current_price:.2f} SEK")
        lines.append(f"   STOP: {stop_price:.2f} SEK ({-stop_pct*100:.1f}%)")
        lines.append(f"   TARGET: {target_price:.2f} SEK ({+avg_win*100:.1f}%)")
        lines.append(f"   SIZE: {position_sek:,.0f} SEK ({shares} shares)")
        
        # COMPROMISE-LOG
        compromises = self.detect_compromises(setup)
        if len(compromises) > 0:
            lines.append(f"\n⚠️ COMPROMISE-LOG (Close to thresholds):")
            for comp in compromises:
                lines.append(f"   • {comp}")
        else:
            lines.append(f"\n✅ COMPROMISE-LOG: Clean (all filters passed with margin)")
        
        # EXECUTION STATUS
        signal_status = getattr(setup, 'signal_status', 'UNKNOWN')
        lines.append(f"\n🚦 EXECUTION STATUS: {signal_status}")
        
        if signal_status == "ACTIVE BUY SIGNAL":
            lines.append(f"   → Execute Monday morning (market open or intraday low)")
            lines.append(f"   → Set stop-loss immediately: {stop_price:.2f} SEK")
        else:
            waiting_reason = getattr(setup, 'waiting_reason', 'Unknown')
            lines.append(f"   → WAIT FOR: {waiting_reason}")
            lines.append(f"   → Monitor daily for trigger")
        
        # TIME-STOP
        exit_date = entry_date + timedelta(days=10)
        lines.append(f"\n⏱️ TIME-STOP:")
        lines.append(f"   If target NOT reached by {exit_date.strftime('%Y-%m-%d')} (10 trading days)")
        lines.append(f"   AND price < {current_price * 1.01:.2f} SEK (Entry + 1%)")
        lines.append(f"   → CLOSE POSITION (prevent dead capital)")
        
        # METRICS SUMMARY
        lines.append(f"\n📊 METRICS:")
        lines.append(f"   Multi-Factor: {getattr(setup, 'multi_factor_rank', 0):.1f} = (R:{getattr(setup, 'robust_score', 0):.0f} × 0.6) + (Q:{getattr(setup, 'quality_score', 0):.0f} × 0.4)")
        lines.append(f"   Timing: {getattr(setup, 'timing_confidence', 0):.0f}%")
        lines.append(f"   Edge 63d: {getattr(setup, 'edge_63d', 0)*100:+.1f}%")
        lines.append(f"   Win Rate: {getattr(setup, 'win_rate_63d', 0)*100:.0f}% (n={getattr(setup, 'sample_size', 0)})")
        lines.append(f"   Expected Profit: {getattr(setup, 'ev_sek', 0):+,.0f} SEK")
        
        # Special flags
        if getattr(setup, 'convergence_detected', False):
            lines.append(f"\n🎯 ALPHA-SWITCH: Convergence detected (1.2x Robust boost applied)")
        
        if hasattr(setup, 'iron_curtain_bootstrap'):
            bootstrap = setup.iron_curtain_bootstrap
            lines.append(f"\n🛡️ IRON CURTAIN: {bootstrap.n_positive_ev}/{bootstrap.n_simulations} simulations positive ({bootstrap.pass_rate*100:.0f}%)")
        
        if hasattr(setup, 'kaufman_er'):
            lines.append(f"   Kaufman ER: {setup.kaufman_er:.3f} (signal/noise ratio)")
        
        lines.append("")  # Blank line
        
        return "\n".join(lines)
    
    def generate_sunday_report(
        self,
        top_5_setups: List,
        macro_regime,
        entry_date: Optional[datetime] = None
    ) -> str:
        """
        Generate complete Sunday Report for Top 10.
        
        Args:
            top_10_setups: Top 10 setups (already sorted)
            macro_regime: MacroRegimeAnalysis
            entry_date: Expected entry date (defaults to next Monday)
        
        Returns:
            Complete formatted report
        """
        if entry_date is None:
            # Default to next Monday
            today = datetime.now()
            days_ahead = (7 - today.weekday()) % 7  # Days until Monday
            if days_ahead == 0:
                days_ahead = 7  # If today is Monday, target next Monday
            entry_date = today + timedelta(days=days_ahead)
        
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("🎯 SUNDAY ELITE REPORT - TOP 5 SETUPS ONLY")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Expected Entry: {entry_date.strftime('%A, %Y-%m-%d')}")
        lines.append("")
        
        # Macro Regime
        lines.append("🌐 MACRO REGIME:")
        lines.append(f"   {macro_regime.regime.value}")
        lines.append(f"   Position Multiplier: {macro_regime.position_size_multiplier:.0%}")
        if len(macro_regime.defensive_signals) > 0:
            lines.append(f"   Defensive Signals:")
            for signal in macro_regime.defensive_signals:
                lines.append(f"      • {signal}")
        lines.append("")
        
        # Philosophy
        lines.append("💎 PHILOSOPHY:")
        lines.append("   Only Top 5. No exceptions.")
        lines.append("   If math doesn't converge, trade doesn't exist.")
        lines.append("   Eliminate human bias. Follow the architecture.")
        lines.append("")
        
        # Top 5 Setups
        lines.append("=" * 80)
        lines.append("TOP 5 SETUPS (Ranked by Multi-Factor)")
        lines.append("=" * 80)
        
        if len(top_5_setups) == 0:
            lines.append("\n❌ NO SETUPS QUALIFIED")
            lines.append("   Market conditions not favorable or all setups failed filters.")
            lines.append("   DO NOT TRADE this week.")
        else:
            for i, setup in enumerate(top_5_setups[:5], 1):
                setup_text = self.format_setup(i, setup, entry_date)
                lines.append(setup_text)
        
        # Footer
        lines.append("=" * 80)
        lines.append("END OF SUNDAY ELITE REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def save_report(
        self,
        report: str,
        output_path: str
    ) -> None:
        """
        Save report to file.
        
        Args:
            report: Formatted report string
            output_path: File path to save to
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Elite Report saved: {output_path}")
