"""
Regime-dependent pattern analysis.

Jim Simons insight: Pattern behavior changes drastically in different market regimes.
Wednesday effect in bull market ≠ Wednesday effect in bear market.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from ..utils.market_data import MarketData


@dataclass
class RegimeStats:
    """Statistics for a specific market regime."""
    regime_name: str
    n_observations: int
    mean_return: float
    win_rate: float
    std_return: float
    is_sufficient_data: bool  # At least 20 observations


class RegimeAnalyzer:
    """
    Analyzes pattern performance across different market regimes.
    
    Regimes classified:
    - Uptrend vs Downtrend (based on moving average)
    - High volatility vs Low volatility
    """
    
    def __init__(self, trend_window: int = 50, vol_window: int = 20):
        """
        Initialize regime analyzer.
        
        Args:
            trend_window: Window for trend classification
            vol_window: Window for volatility classification
        """
        self.trend_window = trend_window
        self.vol_window = vol_window
    
    def classify_regime(
        self,
        market_data: MarketData,
        index: int
    ) -> Dict[str, str]:
        """
        Classify the market regime at a specific index.
        
        Args:
            market_data: Full market data
            index: Index to classify
            
        Returns:
            Dictionary with regime classifications
        """
        regime = {}
        
        # Trend regime (uptrend/downtrend)
        if index >= self.trend_window:
            window_data = market_data.close_prices[index-self.trend_window:index+1]
            ma = np.mean(window_data)
            current_price = market_data.close_prices[index]
            
            if current_price > ma * 1.02:  # 2% above MA
                regime['trend'] = 'uptrend'
            elif current_price < ma * 0.98:  # 2% below MA
                regime['trend'] = 'downtrend'
            else:
                regime['trend'] = 'neutral'
        else:
            regime['trend'] = 'unknown'
        
        # Volatility regime (high/low)
        if index >= self.vol_window:
            window_returns = market_data.returns[index-self.vol_window:index]
            volatility = np.std(window_returns)
            
            # Compare to overall volatility
            overall_vol = np.std(market_data.returns[:index])
            
            if volatility > overall_vol * 1.5:
                regime['volatility'] = 'high_vol'
            elif volatility < overall_vol * 0.7:
                regime['volatility'] = 'low_vol'
            else:
                regime['volatility'] = 'normal_vol'
        else:
            regime['volatility'] = 'unknown'
        
        return regime
    
    def analyze_pattern_by_regime(
        self,
        market_data: MarketData,
        pattern_indices: np.ndarray,
        forward_returns: np.ndarray
    ) -> Dict[str, RegimeStats]:
        """
        Split pattern performance by regime.
        
        Args:
            market_data: Full market data
            pattern_indices: Indices where pattern occurred
            forward_returns: Returns following pattern
            
        Returns:
            Dictionary mapping regime names to statistics
        """
        # Classify each pattern occurrence
        regime_returns = {
            'uptrend': [],
            'downtrend': [],
            'neutral': [],
            'high_vol': [],
            'low_vol': [],
            'normal_vol': []
        }
        
        for idx, pattern_idx in enumerate(pattern_indices):
            if idx >= len(forward_returns):
                break
            
            regime = self.classify_regime(market_data, pattern_idx)
            ret = forward_returns[idx]
            
            # Store return by trend regime
            if regime.get('trend') in regime_returns:
                regime_returns[regime['trend']].append(ret)
            
            # Store return by volatility regime
            if regime.get('volatility') in regime_returns:
                regime_returns[regime['volatility']].append(ret)
        
        # Calculate statistics for each regime
        regime_stats = {}
        
        for regime_name, returns in regime_returns.items():
            if len(returns) == 0:
                continue
            
            returns_array = np.array(returns)
            
            regime_stats[regime_name] = RegimeStats(
                regime_name=regime_name,
                n_observations=len(returns),
                mean_return=np.mean(returns_array),
                win_rate=np.mean(returns_array > 0),
                std_return=np.std(returns_array),
                is_sufficient_data=len(returns) >= 20
            )
        
        return regime_stats
    
    def format_regime_analysis(
        self,
        regime_stats: Dict[str, RegimeStats],
        pattern_name: str
    ) -> str:
        """
        Format regime analysis for display.
        
        Args:
            regime_stats: Dictionary of regime statistics
            pattern_name: Name of the pattern
            
        Returns:
            Formatted string
        """
        lines = []
        lines.append(f"### Regimberoende analys: {pattern_name}")
        lines.append("")
        lines.append("**VIKTIGT**: Mönstrets beteende varierar kraftigt beroende på marknadsregim.")
        lines.append("")
        
        # Trend regimes
        trend_regimes = ['uptrend', 'downtrend', 'neutral']
        trend_data = {k: v for k, v in regime_stats.items() if k in trend_regimes}
        
        if trend_data:
            lines.append("**Trendberoende:**")
            for regime_name, stats in sorted(trend_data.items(), key=lambda x: x[1].mean_return, reverse=True):
                suffix = "" if stats.is_sufficient_data else " ⚠️ FÅ OBS"
                lines.append(f"  • {regime_name.upper()}: {stats.mean_return*100:+.2f}% "
                           f"({stats.n_observations} obs, {stats.win_rate*100:.0f}% vinstfrekvens){suffix}")
            lines.append("")
        
        # Volatility regimes
        vol_regimes = ['high_vol', 'low_vol', 'normal_vol']
        vol_data = {k: v for k, v in regime_stats.items() if k in vol_regimes}
        
        if vol_data:
            lines.append("**Volatilitetsberoende:**")
            for regime_name, stats in sorted(vol_data.items(), key=lambda x: x[1].mean_return, reverse=True):
                suffix = "" if stats.is_sufficient_data else " ⚠️ FÅ OBS"
                lines.append(f"  • {regime_name.upper()}: {stats.mean_return*100:+.2f}% "
                           f"({stats.n_observations} obs, {stats.win_rate*100:.0f}% vinstfrekvens){suffix}")
            lines.append("")
        
        # Warning if large discrepancy
        if trend_data:
            returns = [s.mean_return for s in trend_data.values()]
            if max(returns) - min(returns) > 0.003:  # 0.3% difference
                lines.append("⚠️ **STOR SKILLNAD mellan regimer - mönstret är STARKT regimberoende!**")
        
        return "\n".join(lines)
