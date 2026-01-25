"""
Instrument Screener V2.3 - Position Trading Edition

MAJOR CHANGE: Omställning från swing trading (1-5 dagar) till position trading (21-63 dagar).

Philosophy:
- Vi är POSITION TRADERS, inte day traders
- Vi köper BOTTNAR efter -15%+ decline
- Vi håller 1-3 MÅNADER (21-63 dagar)
- Vi kräver STRUKTURELLA mönster (PRIMARY), inte kalendereffekter

Key Changes from V2.2:
┌─────────────────────────┬─────────────┬──────────────┐
│ Feature                 │ V2.2 (Old)  │ V2.3 (New)   │
├─────────────────────────┼─────────────┼──────────────┤
│ Forward Period          │ 1 day       │ 21/42/63 days│
│ Pattern Priority        │ All equal   │ PRIMARY only │
│ Market Context          │ Any         │ -15% decline │
│ Signal Type             │ ENTER       │ POTENTIAL    │
│ Risk per Trade          │ Variable    │ 1% fixed     │
│ Volume Confirmation     │ Optional    │ REQUIRED     │
└─────────────────────────┴─────────────┴──────────────┘

Output: Top 5 setups for SUNDAY REVIEW, not immediate action.
"""

import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher
from src.filters.market_context_filter import MarketContextFilter
from src.filters.earnings_calendar import EarningsCalendar
from src.analysis.confidence_interval import calculate_win_rate_ci


@dataclass
class PositionTradingScore:
    """Position trading score for weekly review."""
    ticker: str
    name: str
    
    # Market Context
    decline_from_high: float  # % decline from 90d high
    price_vs_ema200: float  # % vs EMA 200
    context_valid: bool  # Passes Vattenpasset?
    
    # Pattern Analysis (PRIMARY only)
    primary_patterns: int
    best_pattern_name: str
    pattern_priority: str  # CORE, PRIMARY, SECONDARY, or INSUFFICIENT
    
    # Multi-Timeframe Edges
    edge_21d: float  # 1 month
    edge_42d: float  # 2 months
    edge_63d: float  # 3 months
    win_rate_63d: float
    
    # Risk Metrics (V4.0)
    expected_value: float
    risk_reward_ratio: float
    avg_win: float
    avg_loss: float
    
    # Quality Metrics
    bayesian_edge: float
    uncertainty: str
    sample_size: int
    
    # Warnings
    earnings_risk: str
    earnings_days: int
    volume_confirmed: bool
    
    # Position Sizing
    position_size_pct: float  # % of portfolio (1% risk)
    max_loss_pct: float  # Always 1.0%
    
    # Final Decision
    status: str  # POTENTIAL, WAIT, NO SETUP
    score: float  # 0-100 ranking score
    recommendation: str
    
    # Optional fields with defaults (must come last in dataclass)
    # Robust Statistics (Statistical Significance)
    adjusted_win_rate: float = 0.0  # Bayesian smoothed WR
    return_consistency: float = 0.0  # Mean/Std (Sharpe-like)
    p_value: float = 1.0  # Statistical significance
    sample_size_factor: float = 0.0  # Penalty factor (0-1)
    pessimistic_ev: float = 0.0  # Worst-case EV
    robust_score: float = 0.0  # 0-100 robust confidence score
    
    # Confidence Intervals
    win_rate_ci_lower: float = 0.0  # 95% CI lower bound
    win_rate_ci_upper: float = 0.0  # 95% CI upper bound
    win_rate_ci_margin: float = 0.0  # ± margin


class PositionTradingScreener:
    """
    Screen instruments for POSITION TRADING setups.
    
    Focus: Structural bottoms with 21-63 day holding periods.
    """
    
    def __init__(
        self,
        capital: float = 100000.0,
        max_risk_per_trade: float = 0.01,
        min_win_rate: float = 0.60,
        min_rrr: float = 3.0
    ):
        """
        Args:
            capital: Total portfolio capital (SEK)
            max_risk_per_trade: Max risk per trade (1% = 0.01)
            min_win_rate: Minimum 63-day win rate (60%)
            min_rrr: Minimum risk/reward ratio (3.0 = 1:3)
        """
        self.capital = capital
        self.max_risk_per_trade = max_risk_per_trade
        self.min_win_rate = min_win_rate
        self.min_rrr = min_rrr
        
        # Initialize components
        self.data_fetcher = DataFetcher()
        self.analyzer = QuantPatternAnalyzer(
            min_occurrences=5,  # Relaxed from 10 - position trading patterns are rarer
            min_confidence=0.60,
            forward_periods=21  # POSITION TRADING
        )
        self.context_filter = MarketContextFilter()
        self.earnings_calendar = EarningsCalendar()
    
    def screen_instruments(
        self,
        instruments: List[Tuple[str, str]]
    ) -> List[PositionTradingScore]:
        """
        Screen instruments for position trading setups.
        
        Args:
            instruments: List of (ticker, name) tuples
            
        Returns:
            List of PositionTradingScore, sorted by score
        """
        print("="*80)
        print("📊 POSITION TRADING SCREENER V2.3")
        print("="*80)
        print(f"\nMode: LONG-TERM (21-63 days)")
        print(f"Capital: {self.capital:,.0f} SEK")
        print(f"Risk per trade: {self.max_risk_per_trade*100:.1f}%")
        print(f"Min Win Rate: {self.min_win_rate*100:.0f}%")
        print(f"Min RRR: {self.min_rrr:.1f}:1")
        print(f"\nScanning {len(instruments)} instruments...\n")
        
        results = []
        
        for i, (ticker, name) in enumerate(instruments, 1):
            print(f"[{i}/{len(instruments)}] {name} ({ticker})...", end=" ")
            
            try:
                score = self._analyze_instrument(ticker, name)
                if score:
                    results.append(score)
                    status_icon = "✅" if score.status == "POTENTIAL" else "⊘"
                    print(f"{status_icon} {score.status} (Score: {score.score:.0f}/100)")
                else:
                    print("⚠️ Skipped")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _analyze_instrument(
        self,
        ticker: str,
        name: str
    ) -> PositionTradingScore:
        """Analyze single instrument."""
        
        # Fetch data
        market_data = self.data_fetcher.fetch_stock_data(ticker, period="15y")
        if market_data is None:
            return None
        
        market_data.ticker = ticker
        
        # Check market context
        context = self.context_filter.check_market_context(market_data)
        
        # Run analysis
        results = self.analyzer.analyze_market_data(market_data)
        
        # Check earnings
        earnings_risk = self.earnings_calendar.check_earnings_risk(ticker)
        
        # Find best pattern
        patterns = results['significant_patterns']
        
        if len(patterns) == 0:
            # No valid setups
            return PositionTradingScore(
                ticker=ticker,
                name=name,
                decline_from_high=context.decline_from_high,
                price_vs_ema200=context.price_vs_ema200,
                context_valid=context.is_valid_for_entry,
                primary_patterns=0,
                best_pattern_name="None",
                pattern_priority="N/A",
                edge_21d=0.0,
                edge_42d=0.0,
                edge_63d=0.0,
                win_rate_63d=0.0,
                expected_value=0.0,
                risk_reward_ratio=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                bayesian_edge=0.0,
                uncertainty="N/A",
                sample_size=0,
                earnings_risk=earnings_risk.risk_level,
                earnings_days=earnings_risk.days_until_earnings or 999,
                volume_confirmed=False,
                position_size_pct=0.0,
                max_loss_pct=0.0,
                status="NO SETUP",
                score=0.0,
                recommendation="Pass - No valid patterns"
            )
        
        # Filter patterns by sample size tiers:
        # CORE: ≥150 occurrences (highest confidence)
        # PRIMARY: ≥75 occurrences (good confidence)
        # SECONDARY: ≥30 occurrences (minimum acceptable)
        core_patterns = [p for p in patterns if p['sample_size'] >= 150 and p['metadata'].get('priority') == 'PRIMARY']
        primary_patterns = [p for p in patterns if p['sample_size'] >= 75 and p['metadata'].get('priority') == 'PRIMARY']
        secondary_patterns = [p for p in patterns if p['sample_size'] >= 30]
        
        if len(core_patterns) > 0:
            # Use best CORE pattern (structural + high sample size)
            best_pattern = max(core_patterns, key=lambda x: x['expected_value'])
            pattern_priority = "CORE"
        elif len(primary_patterns) > 0:
            # Use best PRIMARY pattern (structural + medium sample size)
            best_pattern = max(primary_patterns, key=lambda x: x['expected_value'])
            pattern_priority = "PRIMARY"
        elif len(secondary_patterns) > 0:
            # Fall back to SECONDARY (minimum sample size)
            best_pattern = max(secondary_patterns, key=lambda x: x['expected_value'])
            pattern_priority = "SECONDARY"
        else:
            # Insufficient sample size (<30)
            best_pattern = max(patterns, key=lambda x: x['expected_value'])
            pattern_priority = "INSUFFICIENT"
        
        # Extract metrics
        edge_21d = best_pattern['mean_return_21d']
        edge_42d = best_pattern['mean_return_42d']
        edge_63d = best_pattern['mean_return_63d']
        win_rate_63d = best_pattern['win_rate_63d']
        
        ev = best_pattern['expected_value']
        rrr = best_pattern['risk_reward_ratio']
        avg_win = best_pattern['avg_win']
        avg_loss = best_pattern['avg_loss']
        
        bayesian_edge = best_pattern['bayesian_edge']
        uncertainty = best_pattern['bayesian_uncertainty']
        sample_size = best_pattern['sample_size']
        
        # Extract robust statistics (if available)
        robust_stats = best_pattern.get('robust_stats')
        if robust_stats:
            adjusted_wr = robust_stats.adjusted_win_rate
            return_consistency = robust_stats.return_consistency
            p_value = robust_stats.p_value
            sample_size_factor = robust_stats.sample_size_factor
            pessimistic_ev = robust_stats.pessimistic_ev
            robust_score_val = best_pattern.get('robust_score', 0.0)
        else:
            # Fallback if robust stats not available
            adjusted_wr = win_rate_63d
            return_consistency = 0.0
            p_value = 1.0
            sample_size_factor = 0.0
            pessimistic_ev = ev
            robust_score_val = 0.0
        
        # Calculate confidence interval for win rate
        win_rate_ci = calculate_win_rate_ci(win_rate_63d, sample_size)
        
        # Volume confirmation
        metadata = best_pattern['metadata']
        volume_confirmed = metadata.get('volume_declining', False) and metadata.get('high_volume_breakout', False)
        
        # Calculate score (0-100)
        score = self._calculate_score(
            context_valid=context.is_valid_for_entry,
            pattern_priority=pattern_priority,
            sample_size=sample_size,
            ev=ev,
            rrr=rrr,
            win_rate=win_rate_63d,
            robust_score=robust_score_val,
            volume=volume_confirmed,
            earnings=earnings_risk.risk_level
        )
        
        # Determine status
        if not context.is_valid_for_entry:
            status = "NO SETUP"
            recommendation = f"Context invalid: {context.reason}"
        elif earnings_risk.risk_level == 'HIGH':
            status = "WAIT"
            recommendation = f"Earnings in {earnings_risk.days_until_earnings} days - DO NOT TRADE"
        elif pattern_priority == "INSUFFICIENT":
            status = "WAIT"
            recommendation = f"Insufficient sample size ({sample_size} < 30)"
        elif win_rate_63d < self.min_win_rate:
            status = "WAIT"
            recommendation = f"Win rate too low ({win_rate_63d*100:.0f}% < {self.min_win_rate*100:.0f}%)"
        elif rrr < self.min_rrr:
            status = "WAIT"
            recommendation = f"RRR too low ({rrr:.1f} < {self.min_rrr:.1f})"
        elif ev <= 0:
            status = "WAIT"
            recommendation = f"Negative EV ({ev*100:.2f}%)"
        elif pattern_priority == "SECONDARY":
            status = "POTENTIAL*"
            recommendation = f"⚠️ SECONDARY tier (30-74 samples) - Review carefully"
        elif pattern_priority == "PRIMARY":
            status = "POTENTIAL"
            recommendation = f"✅ PRIMARY tier (75-149 samples) - Valid setup"
        else:  # CORE
            status = "POTENTIAL"
            recommendation = f"✅✅ CORE tier (150+ samples) - High confidence setup"
        
        # Position sizing (1% risk)
        position_size_pct = 1.0  # Always 1% risk
        
        return PositionTradingScore(
            ticker=ticker,
            name=name,
            decline_from_high=context.decline_from_high,
            price_vs_ema200=context.price_vs_ema200,
            context_valid=context.is_valid_for_entry,
            primary_patterns=len(primary_patterns),
            best_pattern_name=best_pattern['description'],
            pattern_priority=pattern_priority,
            edge_21d=edge_21d,
            edge_42d=edge_42d,
            edge_63d=edge_63d,
            win_rate_63d=win_rate_63d,
            win_rate_ci_lower=win_rate_ci.lower_bound,
            win_rate_ci_upper=win_rate_ci.upper_bound,
            win_rate_ci_margin=win_rate_ci.margin_of_error,
            expected_value=ev,
            risk_reward_ratio=rrr,
            avg_win=avg_win,
            avg_loss=avg_loss,
            bayesian_edge=bayesian_edge,
            uncertainty=uncertainty,
            sample_size=sample_size,
            adjusted_win_rate=adjusted_wr,
            return_consistency=return_consistency,
            p_value=p_value,
            sample_size_factor=sample_size_factor,
            pessimistic_ev=pessimistic_ev,
            robust_score=robust_score_val,
            earnings_risk=earnings_risk.risk_level,
            earnings_days=earnings_risk.days_until_earnings or 999,
            volume_confirmed=volume_confirmed,
            position_size_pct=position_size_pct,
            max_loss_pct=self.max_risk_per_trade * 100,
            status=status,
            score=score,
            recommendation=recommendation
        )
    
    def _calculate_score(
        self,
        context_valid: bool,
        pattern_priority: str,
        sample_size: int,
        ev: float,
        rrr: float,
        win_rate: float,
        robust_score: float,
        volume: bool,
        earnings: str
    ) -> float:
        """Calculate 0-100 score for ranking using robust statistics."""
        
        # NEW APPROACH: Use robust_score as foundation (50% weight)
        # Combines: Bayesian WR, sample size penalty, consistency, pessimistic EV, significance
        base_score = robust_score * 0.50  # 50 points max from robust statistics
        
        # Context requirement (30 points) - NON-NEGOTIABLE
        if context_valid:
            base_score += 30
        
        # Pattern priority tier bonus (10 points)
        # Robust score already penalizes small samples, but we add tier bonus
        if pattern_priority == "CORE":
            base_score += 10
        elif pattern_priority == "PRIMARY":
            base_score += 7
        elif pattern_priority == "SECONDARY":
            base_score += 3
        # INSUFFICIENT gets 0 bonus
        
        # Volume confirmation (3 points)
        if volume:
            base_score += 3
        
        # Earnings penalty (multiplicative)
        if earnings == 'HIGH':
            base_score *= 0.5  # 50% penalty
        elif earnings == 'WARNING':
            base_score *= 0.8  # 20% penalty
        
        return min(100, base_score)
    
    def analyze_rejection_reasons(
        self,
        results: List[PositionTradingScore]
    ) -> Dict:
        """
        Analyze why instruments were rejected.
        Returns diagnostic statistics.
        """
        stats = {
            'total': len(results),
            'potential': 0,
            'no_patterns': 0,
            'context_invalid': 0,
            'earnings_risk': 0,
            'low_win_rate': 0,
            'low_rrr': 0,
            'negative_ev': 0,
            'secondary_only': 0
        }
        
        context_details = []
        near_misses = []  # Instruments that were close
        
        for result in results:
            if result.status == "POTENTIAL" or result.status == "POTENTIAL*":
                stats['potential'] += 1
            elif result.status == "NO SETUP":
                if result.best_pattern_name == "None":
                    stats['no_patterns'] += 1
                else:
                    stats['context_invalid'] += 1
                    context_details.append({
                        'ticker': result.ticker,
                        'decline': result.decline_from_high,
                        'vs_ema200': result.price_vs_ema200,
                        'has_pattern': result.best_pattern_name != "None"
                    })
                    
                    # Track "near misses" - instruments close to qualifying
                    if result.decline_from_high <= -7.0 and result.decline_from_high > -10.0:
                        near_misses.append({
                            'ticker': result.ticker,
                            'name': result.name,
                            'decline': result.decline_from_high,
                            'vs_ema200': result.price_vs_ema200,
                            'score': result.score,
                            'reason': 'Close to -10% threshold'
                        })
            elif result.status == "WAIT":
                if 'Earnings' in result.recommendation:
                    stats['earnings_risk'] += 1
                elif 'Win rate' in result.recommendation:
                    stats['low_win_rate'] += 1
                elif 'RRR' in result.recommendation:
                    stats['low_rrr'] += 1
                elif 'Negative EV' in result.recommendation:
                    stats['negative_ev'] += 1
                elif 'SECONDARY' in result.recommendation:
                    stats['secondary_only'] += 1
        
        # Calculate decline distribution
        decline_distribution = {
            '0% to -5%': len([r for r in results if r.decline_from_high > -5.0]),
            '-5% to -10%': len([r for r in results if -10.0 < r.decline_from_high <= -5.0]),
            '-10% to -15%': len([r for r in results if -15.0 < r.decline_from_high <= -10.0]),
            '-15% to -20%': len([r for r in results if -20.0 < r.decline_from_high <= -15.0]),
            'Below -20%': len([r for r in results if r.decline_from_high <= -20.0])
        }
        
        return {
            'stats': stats,
            'context_details': context_details,
            'near_misses': sorted(near_misses, key=lambda x: x['decline'])[:10],
            'decline_distribution': decline_distribution
        }
    
    def display_results(
        self,
        results: List[PositionTradingScore],
        top_n: int = 10
    ):
        """Display screening results."""
        print("\n" + "="*80)
        print(f"📊 SCREENING RESULTS - TOP {min(top_n, len(results))} SETUPS")
        print("="*80)
        
        # Filter POTENTIAL setups
        potential = [r for r in results if r.status.startswith("POTENTIAL")]
        no_setup = [r for r in results if r.status == "NO SETUP"]
        wait = [r for r in results if r.status == "WAIT"]
        
        print(f"\nSummary:")
        print(f"  POTENTIAL: {len(potential)}")
        print(f"  WAIT: {len(wait)}")
        print(f"  NO SETUP: {len(no_setup)}")
        
        if len(potential) == 0:
            print("\n❌ NO VALID SETUPS THIS WEEK")
            print("\nAll instruments either:")
            print("  - Don't meet context requirements (-15% decline + below EMA200)")
            print("  - Have quality metrics below thresholds (WR < 60%, RRR < 3.0)")
            print("  - Have earnings within 5 days")
            return
        
        print(f"\n🎯 TOP {min(top_n, len(potential))} POTENTIAL SETUPS:\n")
        print(f"{'Rank':<5} {'Ticker':<12} {'Pattern':<35} {'Score':<7} {'21d':<8} {'42d':<8} {'63d':<8} {'WR (±CI)':<15} {'RRR':<8}")
        print("-"*90)
        
        for i, result in enumerate(potential[:top_n], 1):
            pattern_short = result.best_pattern_name[:33] + ".." if len(result.best_pattern_name) > 35 else result.best_pattern_name
            
            # Priority flag
            if result.pattern_priority == "CORE":
                priority_flag = "⭐"
            elif result.pattern_priority == "PRIMARY":
                priority_flag = ""
            elif result.pattern_priority == "SECONDARY":
                priority_flag = "*"
            else:
                priority_flag = "?"
            
            # Format win rate with CI
            wr_with_ci = f"{result.win_rate_63d*100:.0f}% (±{result.win_rate_ci_margin*100:.0f}%)"
            
            print(f"{i:<5} {result.ticker:<12} {pattern_short:<35}{priority_flag} "
                  f"{result.score:<7.0f} "
                  f"{result.edge_21d*100:>6.1f}% "
                  f"{result.edge_42d*100:>6.1f}% "
                  f"{result.edge_63d*100:>6.1f}% "
                  f"{wr_with_ci:<15} "
                  f"{result.risk_reward_ratio:>6.1f}")
        
        print("\n⭐ = CORE (150+ samples) | * = SECONDARY (30-74 samples)")
        print("\n" + "="*80)


if __name__ == "__main__":
    # Example watchlist
    WATCHLIST = [
        ("NOLA-B.ST", "Nolato B"),
        ("SBB-B.ST", "SBB B"),
        ("SINCH.ST", "Sinch"),
        ("ERIC-B.ST", "Ericsson B"),
        ("INVE-B.ST", "Investor B"),
    ]
    
    screener = PositionTradingScreener(capital=100000.0)
    results = screener.screen_instruments(WATCHLIST)
    screener.display_results(results, top_n=5)
