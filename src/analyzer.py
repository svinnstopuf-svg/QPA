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
from .analysis.outcome_analyzer import OutcomeAnalyzer, OutcomeStatistics
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
        self.outcome_analyzer = OutcomeAnalyzer()
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
            
            # Lagra resultat
            result = {
                'situation_id': situation_id,
                'situation': situation,
                'outcome_stats': outcome_stats,
                'pattern_eval': pattern_eval,
                'forward_returns': forward_returns
            }
            results.append(result)
            
            # Spara signifikanta mönster
            if pattern_eval.is_significant:
                significant_patterns.append({
                    'description': situation.description,
                    'sample_size': outcome_stats.sample_size,
                    'confidence': pattern_eval.confidence_level,
                    'mean_return': outcome_stats.mean_return,
                    'win_rate': outcome_stats.win_rate
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
                    pattern_eval=result['pattern_eval']
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
            table_data.append({
                'Mönster': pattern['description'][:40] + '...' if len(pattern['description']) > 40 else pattern['description'],
                'Antal': str(pattern['sample_size']),
                'Genomsnitt': self.console_formatter.format_percentage(pattern['mean_return']),
                'Vinstfrekvens': self.console_formatter.format_percentage(pattern['win_rate']),
                'Konfidensgrad': self.console_formatter.format_percentage(pattern['confidence'])
            })
        
        headers = ['Mönster', 'Antal', 'Genomsnitt', 'Vinstfrekvens', 'Konfidensgrad']
        return self.console_formatter.format_table(table_data, headers)
