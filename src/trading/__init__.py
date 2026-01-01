"""Trading module for generating actionable signals."""

from .strategy_generator import TradingStrategyGenerator, TradingSignal
from .pattern_combiner import PatternCombiner, CombinedSignal

__all__ = [
    'TradingStrategyGenerator',
    'TradingSignal',
    'PatternCombiner',
    'CombinedSignal'
]
