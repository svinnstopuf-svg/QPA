"""
Huvudapplikation som orkestrerar hela analysprocessen.

Kombinerar mönsterigenkänning, utvärdering och kommunikation
för att leverera statistiska insikter om marknadsbe teende.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime

from .utils.market_data import MarketData, MarketDataProcessor
from .patterns.detector import PatternDetector, MarketSituation
from .patterns.technical_patterns import TechnicalPatternDetector
from .patterns.position_trading_patterns import PositionTradingPatternDetector
from .filters.market_context_filter import MarketContextFilter
from .filters.earnings_calendar import EarningsCalendar
from .core.pattern_evaluator import PatternEvaluator, PatternEvaluation
from .core.pattern_monitor import PatternMonitor, PatternStatus
from .analysis.outcome_analyzer import OutcomeAnalyzer, OutcomeStatistics
from .analysis.baseline_comparator import BaselineComparator, BaselineComparison
from .analysis.permutation_tester import PermutationTester
from .analysis.regime_analyzer import RegimeAnalyzer
from .analysis.bayesian_estimator import BayesianEdgeEstimator
from .trading.strategy_generator import TradingStrategyGenerator
from .trading.pattern_combiner import PatternCombiner
from .trading.backtester import Backtester
from .trading.portfolio_optimizer import PortfolioOptimizer
from .communication.formatter import InsightFormatter, ConsoleFormatter


class QuantPatternAnalyzer:
    """
    Huvudklass för kvantitativ mönsteranalys.
    
    Denna klass:
    1. Identifierar marknadssituationer (X)
    2. Analyserar historiska utfall (Y)
    3. Utvärderar mönstrens robusthet
    4. Kommunicerar insikter på ett användarvänligt sätt
    """
    
    def __init__(
        self,
        min_occurrences: int = 30,
        min_confidence: float = 0.70,
        forward_periods: int = 21  # Changed from 1 to 21 for position trading
    ):
        """
        Initialiserar analysverktyget.
        
        Args:
            min_occurrences: Minsta antal observationer för att mönster ska vara giltigt
            min_confidence: Minsta konfidensgrad för signifikans
            forward_periods: Antal perioder framåt att mäta utfall över (21 = position trading)
        """
        self.pattern_detector = PatternDetector()
        self.technical_detector = TechnicalPatternDetector()
        self.position_detector = PositionTradingPatternDetector()  # NEW: Position trading patterns
        self.context_filter = MarketContextFilter()  # NEW: Market context pre-filter
        self.earnings_calendar = EarningsCalendar(risk_window_days=10)  # NEW: Earnings risk filter
        self.pattern_evaluator = PatternEvaluator(
            min_occurrences=min_occurrences,
            min_confidence=min_confidence
        )
        self.pattern_monitor = PatternMonitor(
            degradation_threshold=0.15,
            min_sharpe_ratio=0.0,
            stability_threshold=0.60
        )
        self.outcome_analyzer = OutcomeAnalyzer()
        self.baseline_comparator = BaselineComparator()
        self.permutation_tester = PermutationTester(n_permutations=1000)
        self.regime_analyzer = RegimeAnalyzer(trend_window=50, vol_window=20)
        self.bayesian_estimator = BayesianEdgeEstimator(
            prior_mean=0.0,  # No edge a priori
            prior_std=0.01,  # 1% daily vol
            min_threshold=0.001  # 0.1% edge threshold
        )
        self.strategy_generator = TradingStrategyGenerator(
            min_edge_threshold=0.10,  # Need 0.10% edge after costs
            transaction_cost=0.02  # 0.02% realistic trading cost
        )
        self.pattern_combiner = PatternCombiner(
            correlation_penalty=0.5,  # 50% penalty for correlation
            min_patterns=1,  # Allow single pattern (changed from 2)
            max_patterns=10
        )
        self.backtester = Backtester(
            initial_capital=100000,
            transaction_cost=0.0002,  # 0.02%
            slippage=0.0001  # 0.01%
        )
        self.portfolio_optimizer = PortfolioOptimizer(
            max_position_size=0.25,  # Max 25% per pattern
            kelly_fraction=0.5,  # Half-Kelly for safety
            min_edge=0.001  # 0.1% min edge
        )
        self.formatter = InsightFormatter()
        self.console_formatter = ConsoleFormatter()
        
        self.forward_periods = forward_periods
        
    def analyze_market_data(
        self,
        market_data: MarketData,
        patterns_to_analyze: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyserar marknadsdata och identifierar statistiska mönster.
        
        Args:
            market_data: MarketData objekt med historisk data
            patterns_to_analyze: Specifika mönster att analysera, None = alla
            
        Returns:
            Dictionary med analysresultat
        """
        print("Analyserar marknadsdata...")
        
        # EARNINGS RISK CHECK (V4.0)
        ticker = market_data.ticker if hasattr(market_data, 'ticker') else None
        earnings_risk = None
        if ticker:
            earnings_risk = self.earnings_calendar.check_earnings_risk(ticker)
            print(f"Earnings Risk: {earnings_risk.risk_level} - {earnings_risk.message}")
        
        # PHASE 1: Check market context for position trading
        market_context = self.context_filter.check_market_context(market_data)
        print(f"Market Context: {'VALID' if market_context.is_valid_for_entry else 'NO SETUP'}")
        print(f"  Decline: {market_context.decline_from_high:.1f}% | Price vs EMA200: {market_context.price_vs_ema200:+.1f}%")
        
        # Steg 1: Identifiera alla marknadssituationer
        all_situations = {}
        
        # Add PRIMARY patterns (structural reversals) if context is valid
        if market_context.is_valid_for_entry:
            print("Detecting PRIMARY patterns (structural reversals)...")
            position_patterns = self.position_detector.detect_all_position_patterns(market_data)
            all_situations.update(position_patterns)
            print(f"  Found {len(position_patterns)} PRIMARY patterns")
        else:
            print("Skipping PRIMARY patterns (context not valid for position trading)")
        
        # Add SECONDARY patterns (calendar, momentum) - always detect but lower priority
        print("Detecting SECONDARY patterns (calendar, momentum)...")
        secondary_patterns = self.pattern_detector.detect_all_patterns(market_data)
        # Tag all as SECONDARY
        for situation in secondary_patterns.values():
            if 'priority' not in situation.metadata:
                situation.metadata['priority'] = 'SECONDARY'
        all_situations.update(secondary_patterns)
        
        # Add technical patterns (SECONDARY)
        technical_patterns = self.technical_detector.detect_all_technical_patterns(market_data)
        for situation in technical_patterns.values():
            if 'priority' not in situation.metadata:
                situation.metadata['priority'] = 'SECONDARY'
        all_situations.update(technical_patterns)
        
        # Filtrera om specifika mönster önskas
        if patterns_to_analyze:
            all_situations = {
                k: v for k, v in all_situations.items()
                if k in patterns_to_analyze
            }
        
        print(f"Identifierade {len(all_situations)} marknadssituationer")
        
        # Steg 2: För varje situation, analysera historiska utfall
        results = []
        significant_patterns = []
        
        for situation_id, situation in all_situations.items():
            # MULTI-TIMEFRAME: Calculate returns for 21, 42, and 63 days
            forward_returns_21d = self.outcome_analyzer.calculate_forward_returns(
                prices=market_data.close_prices,
                indices=situation.timestamp_indices,
                forward_periods=21
            )
            forward_returns_42d = self.outcome_analyzer.calculate_forward_returns(
                prices=market_data.close_prices,
                indices=situation.timestamp_indices,
                forward_periods=42
            )
            forward_returns_63d = self.outcome_analyzer.calculate_forward_returns(
                prices=market_data.close_prices,
                indices=situation.timestamp_indices,
                forward_periods=63
            )
            
            # Use primary timeframe (21d) for main analysis
            forward_returns = forward_returns_21d
            
            if len(forward_returns) == 0:
                continue
            
            # Analysera utfall
            outcome_stats = self.outcome_analyzer.analyze_outcomes(
                returns=forward_returns,
                forward_periods=self.forward_periods
            )
            
            # Utvärdera mönstrets robusthet
            # Vi behöver timestamps för de identifierade situationerna
            situation_timestamps = market_data.timestamps[situation.timestamp_indices]
            
            pattern_eval = self.pattern_evaluator.evaluate_pattern(
                pattern_id=situation_id,
                historical_returns=forward_returns,
                timestamps=situation_timestamps
            )
            
            # Jämför mot baseline (hela marknadens genomsnitt)
            baseline_returns = market_data.returns[:-self.forward_periods] if self.forward_periods > 0 else market_data.returns
            baseline_comparison = self.outcome_analyzer.compare_to_baseline(
                pattern_returns=forward_returns,
                baseline_returns=baseline_returns
            )
            
            # Permutation test - validerar mot slump (endast för signifikanta mönster)
            permutation_result = None
            if pattern_eval.is_significant:
                permutation_result = self.permutation_tester.test_pattern(
                    pattern_returns=forward_returns,
                    all_market_returns=baseline_returns,
                    pattern_size=len(forward_returns)
                )
            
            # Regime analysis - split prestanda per marknadsregim (endast för signifikanta mönster)
            regime_stats = None
            if pattern_eval.is_significant:
                regime_stats = self.regime_analyzer.analyze_pattern_by_regime(
                    market_data=market_data,
                    pattern_indices=situation.timestamp_indices,
                    forward_returns=forward_returns
                )
            
            # Bayesian uncertainty estimation (alltid, speciellt för små samples)
            bayesian_estimate = self.bayesian_estimator.estimate_edge(
                returns=forward_returns,
                transaction_cost=0.0002  # 0.02%
            )
            
            # Lagra resultat
            result = {
                'situation_id': situation_id,
                'situation': situation,
                'outcome_stats': outcome_stats,
                'pattern_eval': pattern_eval,
                'forward_returns': forward_returns,
                'baseline_comparison': baseline_comparison,
                'permutation_result': permutation_result,
                'regime_stats': regime_stats,
                'bayesian_estimate': bayesian_estimate
            }
            results.append(result)
            
            # Spara signifikanta mönster
            if pattern_eval.is_significant:
                # Calculate outcome stats for all timeframes
                outcome_stats_42d = self.outcome_analyzer.analyze_outcomes(
                    returns=forward_returns_42d,
                    forward_periods=42
                ) if len(forward_returns_42d) > 0 else None
                
                outcome_stats_63d = self.outcome_analyzer.analyze_outcomes(
                    returns=forward_returns_63d,
                    forward_periods=63
                ) if len(forward_returns_63d) > 0 else None
                
                # EXPECTED VALUE (EV) calculation
                # EV = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
                win_rate = outcome_stats.win_rate
                loss_rate = 1.0 - win_rate
                avg_win = outcome_stats.avg_win
                avg_loss = abs(outcome_stats.avg_loss)  # Make positive
                expected_value = (win_rate * avg_win) - (loss_rate * avg_loss)
                
                # RISK/REWARD RATIO (RRR) calculation
                # RRR = Avg Win / Avg Loss (target: >= 1:3 means 3.0+)
                risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0
                
                # QUALITY FILTERS: Only show patterns with positive EV and RRR >= 1:3
                if expected_value <= 0:
                    continue  # Skip: Negative expected value
                if risk_reward_ratio < 3.0:
                    continue  # Skip: Risk/Reward worse than 1:3
                
                significant_patterns.append({
                    'description': situation.description,
                    'sample_size': outcome_stats.sample_size,
                    'statistical_strength': pattern_eval.statistical_strength,
                    'stability_score': pattern_eval.stability_score,
                    'mean_return': outcome_stats.mean_return,
                    'win_rate': outcome_stats.win_rate,
                    'metadata': situation.metadata,  # Include for warning checks
                    'bayesian_edge': bayesian_estimate.bias_adjusted_edge if bayesian_estimate else outcome_stats.mean_return,  # V3.0: Use Bayesian survivorship-adjusted edge
                    'bayesian_uncertainty': bayesian_estimate.uncertainty_level if bayesian_estimate else 'UNKNOWN',
                    # MULTI-TIMEFRAME DATA (Position Trading)
                    'mean_return_21d': outcome_stats.mean_return,
                    'win_rate_21d': outcome_stats.win_rate,
                    'mean_return_42d': outcome_stats_42d.mean_return if outcome_stats_42d else 0.0,
                    'win_rate_42d': outcome_stats_42d.win_rate if outcome_stats_42d else 0.0,
                    'mean_return_63d': outcome_stats_63d.mean_return if outcome_stats_63d else 0.0,
                    'win_rate_63d': outcome_stats_63d.win_rate if outcome_stats_63d else 0.0,
                    # RISK MANAGEMENT (V4.0)
                    'expected_value': expected_value,
                    'risk_reward_ratio': risk_reward_ratio,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    # EARNINGS RISK (V4.0)
                    'earnings_risk': earnings_risk.risk_level if earnings_risk else 'UNKNOWN',
                    'earnings_message': earnings_risk.message if earnings_risk else 'No earnings data',
                    'earnings_days_until': earnings_risk.days_until_earnings if earnings_risk else None,
                })
        
        print(f"Hittade {len(significant_patterns)} signifikanta mönster")
        
        return {
            'results': results,
            'significant_patterns': significant_patterns,
            'total_patterns': len(all_situations),
            'market_data': market_data
        }
    
    def generate_report(self, analysis_results: Dict) -> str:
        """
        Genererar en användarvänlig rapport från analysresultat.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            
        Returns:
            Formaterad rapport som sträng
        """
        lines = []
        
        # Sammanfattning
        summary = self.formatter.format_summary(
            significant_patterns=analysis_results['significant_patterns'],
            total_patterns=analysis_results['total_patterns']
        )
        lines.append(summary)
        lines.append("\n" + "="*80 + "\n")
        
        # Detaljerade insikter för signifikanta mönster
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant:
                insight = self.formatter.format_pattern_insight(
                    situation=result['situation'],
                    outcome_stats=result['outcome_stats'],
                    pattern_eval=result['pattern_eval'],
                    baseline_comparison=result.get('baseline_comparison'),
                    permutation_result=result.get('permutation_result'),
                    regime_stats=result.get('regime_stats')
                )
                lines.append(insight)
                lines.append("\n" + "-"*80 + "\n")
        
        return "\n".join(lines)
    
    def compare_pattern_to_baseline(
        self,
        market_data: MarketData,
        situation: MarketSituation
    ) -> Dict:
        """
        Jämför ett specifikt mönster med baseline (hela marknaden).
        
        Args:
            market_data: MarketData objekt
            situation: MarketSituation att jämföra
            
        Returns:
            Dictionary med jämförelseresultat
        """
        # Beräkna avkastning för mönstret
        pattern_returns = self.outcome_analyzer.calculate_forward_returns(
            prices=market_data.close_prices,
            indices=situation.timestamp_indices,
            forward_periods=self.forward_periods
        )
        
        # Beräkna baseline (alla perioder)
        baseline_returns = market_data.returns[:-self.forward_periods] if self.forward_periods > 0 else market_data.returns
        
        # Jämför
        comparison = self.outcome_analyzer.compare_to_baseline(
            pattern_returns=pattern_returns,
            baseline_returns=baseline_returns
        )
        
        return comparison
    
    def get_current_market_situation(
        self,
        market_data: MarketData,
        lookback_window: int = 50
    ) -> Dict:
        """
        Analyserar den nuvarande marknadssituationen.
        
        Args:
            market_data: MarketData objekt
            lookback_window: Antal perioder att analysera bakåt
            
        Returns:
            Dictionary med information om nuvarande situation
        """
        # Ta de senaste observationerna
        recent_data = MarketData(
            timestamps=market_data.timestamps[-lookback_window:],
            open_prices=market_data.open_prices[-lookback_window:],
            high_prices=market_data.high_prices[-lookback_window:],
            low_prices=market_data.low_prices[-lookback_window:],
            close_prices=market_data.close_prices[-lookback_window:],
            volume=market_data.volume[-lookback_window:]
        )
        
        # Identifiera mönster i recent data
        situations = self.pattern_detector.detect_all_patterns(recent_data)
        
        # Identifiera vilka situationer som är aktiva NU (sista datapunkten)
        active_situations = []
        for situation_id, situation in situations.items():
            # Kolla om sista indexet finns i situation's indices
            last_idx = len(recent_data) - 1
            if last_idx in situation.timestamp_indices:
                active_situations.append({
                    'id': situation_id,
                    'description': situation.description,
                    'situation': situation
                })
        
        return {
            'active_situations': active_situations,
            'recent_data': recent_data,
            'lookback_window': lookback_window
        }
    
    def monitor_patterns(self, analysis_results: Dict) -> Dict[str, PatternStatus]:
        """
        Övervakar alla signifikanta mönster för att identifiera försämring.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            
        Returns:
            Dictionary med PatternStatus för varje mönster
        """
        # Förbered data för övervakning
        patterns_data = {}
        
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant:
                situation_id = result['situation_id']
                forward_returns = result['forward_returns']
                situation = result['situation']
                market_data = analysis_results['market_data']
                
                # Hämta timestamps för observationerna
                timestamps = market_data.timestamps[situation.timestamp_indices]
                
                patterns_data[situation_id] = {
                    'returns': forward_returns,
                    'timestamps': timestamps
                }
        
        # Övervaka alla mönster
        pattern_statuses = self.pattern_monitor.monitor_all_patterns(
            patterns_data,
            lookback_recent=50
        )
        
        return pattern_statuses
    
    def generate_monitoring_report(self, pattern_statuses: Dict[str, PatternStatus]) -> str:
        """
        Genererar en rapport över mönsterövervakning.
        
        Args:
            pattern_statuses: Dictionary med PatternStatus
            
        Returns:
            Formaterad rapport som sträng
        """
        return self.pattern_monitor.generate_monitoring_report(pattern_statuses)
    
    def find_tradeable_strategies(self, analysis_results: Dict) -> str:
        """
        Hitta handelbara strategier baserat på regimfiltrering.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            
        Returns:
            Rapport över handelbara strategier
        """
        patterns_with_regimes = []
        
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant and result.get('regime_stats'):
                patterns_with_regimes.append({
                    'description': result['situation'].description,
                    'regime_stats': result['regime_stats'],
                    'pattern_id': result['situation_id'],
                    'overall_edge': result['outcome_stats'].mean_return
                })
        
        # Filtrera till endast handelbara
        tradeable = self.strategy_generator.filter_tradeable_patterns(patterns_with_regimes)
        
        # Skapa rapport
        return self.strategy_generator.create_strategy_report(tradeable)
    
    def generate_combined_strategy(
        self,
        analysis_results: Dict,
        market_data: MarketData
    ) -> str:
        """
        Genererar kombinerad strategi från flera mönster.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            market_data: MarketData för regimklassificering
            
        Returns:
            Rapport över kombinerad strategi
        """
        # Hitta handelbara mönster
        patterns_with_regimes = []
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant and result.get('regime_stats'):
                patterns_with_regimes.append({
                    'description': result['situation'].description,
                    'regime_stats': result['regime_stats'],
                    'pattern_id': result['situation_id'],
                    'overall_edge': result['outcome_stats'].mean_return
                })
        
        tradeable = self.strategy_generator.filter_tradeable_patterns(patterns_with_regimes)
        
        if not tradeable:
            return "❌ Inga mönster att kombinera."
        
        # Klassificera nuvarande regim
        last_idx = len(market_data) - 1
        current_regime = self.regime_analyzer.classify_regime(market_data, last_idx)
        
        # Kombinera mönster
        combined = self.pattern_combiner.combine_patterns(
            tradeable,
            current_regime
        )
        
        return self.pattern_combiner.create_combination_report(combined)
    
    def create_summary_table(self, analysis_results: Dict) -> str:
        """
        Skapar en sammanfattningstabell över alla signifikanta mönster.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            
        Returns:
            Formaterad tabell som sträng
        """
        if not analysis_results['significant_patterns']:
            return "Inga signifikanta mönster hittades."
        
        table_data = []
        for pattern in analysis_results['significant_patterns']:
            # Check for data sufficiency and regime risk warnings
            warning = ""
            if 'metadata' in pattern and pattern['metadata'].get('is_seasonal'):
                if not pattern['metadata'].get('data_sufficient', True):
                    warning = " [!]"
                elif pattern['metadata'].get('regime_risk', False):
                    warning = " [!]"
            
            table_data.append({
                'Mönster': (pattern['description'][:37] + '...' if len(pattern['description']) > 37 else pattern['description']) + warning,
                'Antal': str(pattern['sample_size']),
                'Genomsnitt': self.console_formatter.format_percentage(pattern['mean_return']),
                'Vinstfrekvens': self.console_formatter.format_percentage(pattern['win_rate']),
                'Hist. Styrka': self.console_formatter.format_percentage(pattern['statistical_strength'])
            })
        
        headers = ['Mönster', 'Antal', 'Genomsnitt', 'Vinstfrekvens', 'Hist. Styrka']
        table = self.console_formatter.format_table(table_data, headers)
        
        # Add warning legend if needed
        has_seasonal_warnings = any(
            'metadata' in p and p['metadata'].get('is_seasonal') and 
            not p['metadata'].get('data_sufficient', True)
            for p in analysis_results['significant_patterns']
        )
        has_regime_warnings = any(
            'metadata' in p and p['metadata'].get('regime_risk', False)
            for p in analysis_results['significant_patterns']
        )
        
        if has_seasonal_warnings:
            table += "\n\n[!] = VARNING: Säsongsmönster med <10 års data - resultat är preliminära!"
        elif has_regime_warnings:
            table += "\n\n[!] = VARNING: Veckodagsmönster med <8 års data - hög risk för regimberoende (lokal stabilitet)!"
        
        return table
    
    def backtest_patterns(self, analysis_results: Dict, walk_forward: bool = True) -> str:
        """
        Backtestar signifikanta mönster med walk-forward analysis.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            walk_forward: Om True, använd walk-forward validation
            
        Returns:
            Rapport över backtest-resultat
        """
        lines = []
        lines.append("\n" + "="*80)
        lines.append("BACKTEST RESULTAT (Walk-Forward Validation)")
        lines.append("="*80)
        
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant:
                description = result['situation'].description
                forward_returns = result['forward_returns']
                timestamps = analysis_results['market_data'].timestamps[
                    result['situation'].timestamp_indices
                ]
                
                if walk_forward:
                    # Split data 70/30 in-sample/out-of-sample
                    split_idx = int(len(forward_returns) * 0.7)
                    pattern_indices = result['situation'].timestamp_indices
                    
                    # In-sample backtest
                    in_sample_result = self.backtester.backtest_pattern(
                        pattern_indices[:split_idx],
                        forward_returns[:split_idx],
                        timestamps[:split_idx]
                    )
                    
                    # Out-of-sample backtest
                    out_sample_result = self.backtester.backtest_pattern(
                        pattern_indices[split_idx:],
                        forward_returns[split_idx:],
                        timestamps[split_idx:]
                    )
                    
                    lines.append(f"\n{description}")
                    lines.append("-" * 80)
                    lines.append("📊 IN-SAMPLE (70% av data - träning)")
                    lines.append(self._format_backtest_result(in_sample_result))
                    lines.append("\n📊 OUT-OF-SAMPLE (30% av data - validering)")
                    lines.append(self._format_backtest_result(out_sample_result))
                    
                    # Warn if out-of-sample is significantly worse
                    if out_sample_result.sharpe_ratio < in_sample_result.sharpe_ratio * 0.5:
                        lines.append("\n⚠️ VARNING: Out-of-sample är mycket sämre än in-sample - risk för överanpassning!")
                else:
                    # Full period backtest
                    pattern_indices = result['situation'].timestamp_indices
                    bt_result = self.backtester.backtest_pattern(
                        pattern_indices,
                        forward_returns,
                        timestamps
                    )
                    lines.append(f"\n{description}")
                    lines.append("-" * 80)
                    lines.append(self._format_backtest_result(bt_result))
        
        return "\n".join(lines)
    
    def _format_backtest_result(self, result) -> str:
        """Formaterar backtest-resultat."""
        lines = []
        lines.append(f"  Total avkastning: {result.total_return:+.2%}")
        lines.append(f"  Årlig avkastning: {result.annual_return:+.2%}")
        lines.append(f"  Sharpe ratio: {result.sharpe_ratio:.2f} ({result.rating})")
        lines.append(f"  Max drawdown: {result.max_drawdown:.2%}")
        lines.append(f"  Vinstfrekvens: {result.win_rate:.1%}")
        lines.append(f"  Profit factor: {result.profit_factor:.2f}")
        lines.append(f"  Antal trades: {result.num_trades}")
        return "\n".join(lines)
    
    def show_bayesian_uncertainty(self, analysis_results: Dict) -> str:
        """
        Visa Bayesian uncertainty för alla signifikanta mönster.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            
        Returns:
            Rapport över uncertainty
        """
        reports = []
        
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant:
                bayesian_est = result.get('bayesian_estimate')
                if bayesian_est:
                    report = self.bayesian_estimator.create_uncertainty_report(
                        bayesian_est,
                        result['situation'].description
                    )
                    reports.append(report)
        
        return "\n".join(reports) if reports else "\nInga signifikanta mönster att analysera."
    
    def optimize_portfolio(self, analysis_results: Dict, total_capital: float = 100000) -> str:
        """
        Skapa Kelly Criterion-baserad portfolio-allokering.
        
        Args:
            analysis_results: Resultat från analyze_market_data
            total_capital: Totalt kapital att allokera
            
        Returns:
            Rapport över portfolio-allokering
        """
        # Samla tradeable patterns
        patterns_for_optimization = []
        
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant:
                # Extrahera statistik
                pattern_dict = {
                    'pattern_id': result['situation_id'],
                    'description': result['situation'].description,
                    'win_rate': result['outcome_stats'].win_rate,
                    'overall_edge': result['outcome_stats'].mean_return,
                    'volatility': result['outcome_stats'].std_return
                }
                patterns_for_optimization.append(pattern_dict)
        
        if not patterns_for_optimization:
            return "\n\n" + "="*80 + "\nPORTFOLIO OPTIMIZATION\n" + "="*80 + "\n\n❌ Inga mönster att optimera."
        
        # Beräkna position sizes
        position_sizes = self.portfolio_optimizer.calculate_position_sizes(patterns_for_optimization)
        
        # Skapa rapport
        return "\n\n" + self.portfolio_optimizer.create_portfolio_allocation(position_sizes, total_capital)
