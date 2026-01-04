"""
Risk Management Module

Advanced risk controls for V2.1:
- Volatility-adjusted position sizing (V-Kelly)
- Trend filter (200-day MA confirmation)
- Market regime detection (stress index)
"""

from .volatility_position_sizing import (
    VolatilityPositionSizer,
    PositionSize,
    format_position_report
)

from .trend_filter import (
    TrendFilter,
    TrendAnalysis,
    TrendRegime,
    format_trend_report
)

from .regime_detection import (
    RegimeDetector,
    RegimeAnalysis,
    MarketRegime,
    format_regime_report
)

__all__ = [
    # Volatility Position Sizing
    'VolatilityPositionSizer',
    'PositionSize',
    'format_position_report',
    
    # Trend Filter
    'TrendFilter',
    'TrendAnalysis',
    'TrendRegime',
    'format_trend_report',
    
    # Regime Detection
    'RegimeDetector',
    'RegimeAnalysis',
    'MarketRegime',
    'format_regime_report'
]
