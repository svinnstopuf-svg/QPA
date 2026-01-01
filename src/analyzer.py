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
from .core.pattern_evaluator import PatternEvaluator, PatternEvaluation
from .core.pattern_monitor import PatternMonitor, PatternStatus
from .analysis.outcome_analyzer import OutcomeAnalyzer, OutcomeStatistics
from .analysis.baseline_comparator import BaselineComparator, BaselineComparison
from .analysis.permutation_tester import PermutationTester
from .analysis.regime_analyzer import RegimeAnalyzer
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
        forward_periods: int = 1
    ):
        """
        Initialiserar analysverktyget.
        
        Args:
            min_occurrences: Minsta antal observationer för att mönster ska vara giltigt
            min_confidence: Minsta konfidensgrad för signifikans
            forward_periods: Antal perioder framåt att mäta utfall över
        """
        self.pattern_detector = PatternDetector()
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
        
        # Steg 1: Identifiera alla marknadssituationer
        all_situations = self.pattern_detector.detect_all_patterns(market_data)
        
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
            # Beräkna framtida avkastningar från identifierade tidpunkter
            forward_returns = self.outcome_analyzer.calculate_forward_returns(
                prices=market_data.close_prices,
                indices=situation.timestamp_indices,
                forward_periods=self.forward_periods
            )
            
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
            
            # Lagra resultat
            result = {
                'situation_id': situation_id,
                'situation': situation,
                'outcome_stats': outcome_stats,
                'pattern_eval': pattern_eval,
                'forward_returns': forward_returns,
                'baseline_comparison': baseline_comparison,
                'permutation_result': permutation_result,
                'regime_stats': regime_stats
            }
            results.append(result)
            
            # Spara signifikanta mönster
            if pattern_eval.is_significant:
                significant_patterns.append({
                    'description': situation.description,
                    'sample_size': outcome_stats.sample_size,
                    'statistical_strength': pattern_eval.statistical_strength,
                    'stability_score': pattern_eval.stability_score,
                    'mean_return': outcome_stats.mean_return,
                    'win_rate': outcome_stats.win_rate,
                    'metadata': situation.metadata  # Include for warning checks
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
