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
from .utils.data_fetcher import DataFetcher
from .patterns.detector import PatternDetector, MarketSituation
from .core.pattern_evaluator import PatternEvaluator, PatternEvaluation
from .core.pattern_monitor import PatternMonitor, PatternStatus
from .analysis.outcome_analyzer import OutcomeAnalyzer, OutcomeStatistics
from .communication.formatter import InsightFormatter, ConsoleFormatter

__all__ = [
    'QuantPatternAnalyzer',
    'MarketData',
    'MarketDataProcessor',
    'DataFetcher',
    'PatternDetector',
    'MarketSituation',
    'PatternEvaluator',
    'PatternEvaluation',
    'PatternMonitor',
    'PatternStatus',
    'OutcomeAnalyzer',
    'OutcomeStatistics',
    'InsightFormatter',
    'ConsoleFormatter',
]
