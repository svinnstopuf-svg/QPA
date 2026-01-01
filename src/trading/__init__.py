"""Trading module for generating actionable signals."""

from .strategy_generator import TradingStrategyGenerator, TradingSignal
from .pattern_combiner import PatternCombiner, CombinedSignal
from .backtester import Backtester, BacktestResult
from .portfolio_optimizer import PortfolioOptimizer, PositionSize

__all__ = [
    'TradingStrategyGenerator',
    'TradingSignal',
    'PatternCombiner',
    'CombinedSignal',
    'Backtester',
    'BacktestResult',
    'PortfolioOptimizer',
    'PositionSize'
]
