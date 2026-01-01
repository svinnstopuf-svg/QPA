"""
Quant Pattern Analyzer - Ett statistiskt observationsinstrument för finansiella marknader.

Inspirerat av Jim Simons och Renaissance Technologies tillvägagångssätt:
- Mätbara variabler
- Historisk data
- Sannolikheter, inte förutsägelser
- Inga berättelser, bara statistik
"""

__version__ = "0.1.0"

from .analyzer import QuantPatternAnalyzer
from .utils.market_data import MarketData, MarketDataProcessor
from .patterns.detector import PatternDetector, MarketSituation
from .core.pattern_evaluator import PatternEvaluator, PatternEvaluation
from .analysis.outcome_analyzer import OutcomeAnalyzer, OutcomeStatistics
from .communication.formatter import InsightFormatter, ConsoleFormatter

__all__ = [
    'QuantPatternAnalyzer',
    'MarketData',
    'MarketDataProcessor',
    'PatternDetector',
    'MarketSituation',
    'PatternEvaluator',
    'PatternEvaluation',
    'OutcomeAnalyzer',
    'OutcomeStatistics',
    'InsightFormatter',
    'ConsoleFormatter',
]
