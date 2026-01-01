"""
Macro Data Integration - VIX, Interest Rates, Sector Rotation

Renaissance principle: Incorporate multiple data sources.
Patterns may only work in specific macro regimes.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..utils.market_data import MarketData


@dataclass
class MacroEnvironment:
    """Current macro environment classification."""
    vix_level: str  # 'low', 'normal', 'high', 'extreme'
    vix_value: float
    interest_rate_trend: str  # 'falling', 'stable', 'rising'
    sector_leadership: str  # 'growth', 'value', 'defensive', 'cyclical'
    risk_on: bool  # Overall risk appetite


class MacroDataIntegrator:
    """
    Integrates macro data into pattern analysis.
    
    Features:
    - VIX (fear gauge)
    - 10-year treasury yields
    - Sector rotation (XLK, XLF, XLE, XLV, etc.)
    """
    
    def __init__(self):
        """Initialize macro data integrator."""
        self.vix_cache = None
        self.rates_cache = None
        self.sector_cache = {}
        
    def fetch_vix_data(self, period: str = "15y") -> Optional[pd.DataFrame]:
        """
        Fetch VIX data.
        
        Args:
            period: Data period (e.g. '15y', '10y')
            
        Returns:
            DataFrame with VIX data or None if failed
        """
        try:
            vix = yf.download("^VIX", period=period, progress=False)
            if vix is not None and not vix.empty:
                self.vix_cache = vix
                return vix
            return None
        except Exception as e:
            print(f"Failed to fetch VIX: {e}")
            return None
    
    def fetch_treasury_yields(self, period: str = "15y") -> Optional[pd.DataFrame]:
        """
        Fetch 10-year treasury yields.
        
        Args:
            period: Data period
            
        Returns:
            DataFrame with rates or None
        """
        try:
            # ^TNX is 10-year treasury yield
            rates = yf.download("^TNX", period=period, progress=False)
            if rates is not None and not rates.empty:
                self.rates_cache = rates
                return rates
            return None
        except Exception as e:
            print(f"Failed to fetch treasury yields: {e}")
            return None
    
    def classify_vix_regime(self, vix_value: float) -> str:
        """
        Classify VIX level.
        
        Args:
            vix_value: Current VIX value
            
        Returns:
            Classification: 'low', 'normal', 'high', 'extreme'
        """
        if vix_value < 15:
            return 'low'
        elif vix_value < 20:
            return 'normal'
        elif vix_value < 30:
            return 'high'
        else:
            return 'extreme'
    
    def classify_rate_trend(self, rates: pd.Series, lookback: int = 60) -> str:
        """
        Classify interest rate trend.
        
        Args:
            rates: Historical rates
            lookback: Days to look back
            
        Returns:
            'falling', 'stable', or 'rising'
        """
        if len(rates) < lookback:
            return 'stable'
        
        recent = rates.iloc[-lookback:]
        change = recent.iloc[-1] - recent.iloc[0]
        
        if change < -0.5:
            return 'falling'
        elif change > 0.5:
            return 'rising'
        else:
            return 'stable'
    
    def get_macro_environment(
        self,
        timestamp: datetime,
        market_data: MarketData
    ) -> MacroEnvironment:
        """
        Get current macro environment at specific timestamp.
        
        Args:
            timestamp: Point in time
            market_data: Market data for context
            
        Returns:
            MacroEnvironment classification
        """
        # VIX level
        vix_value = 20.0  # Default if data unavailable
        if self.vix_cache is not None:
            try:
                date_str = timestamp.strftime('%Y-%m-%d')
                if date_str in self.vix_cache.index:
                    vix_value = self.vix_cache.loc[date_str, 'Close']
            except:
                pass
        
        vix_level = self.classify_vix_regime(vix_value)
        
        # Interest rate trend
        rate_trend = 'stable'
        if self.rates_cache is not None:
            rate_trend = self.classify_rate_trend(self.rates_cache['Close'])
        
        # Sector leadership (simplified - based on market momentum)
        # In production: compare XLK/XLV/XLE/XLF performance
        recent_returns = market_data.returns[-20:] if len(market_data.returns) >= 20 else market_data.returns
        avg_return = np.mean(recent_returns)
        volatility = np.std(recent_returns)
        
        if avg_return > 0.001 and volatility < 0.015:
            sector_leadership = 'growth'
        elif avg_return < -0.001:
            sector_leadership = 'defensive'
        elif volatility > 0.02:
            sector_leadership = 'cyclical'
        else:
            sector_leadership = 'value'
        
        # Risk-on/risk-off
        risk_on = (vix_value < 20 and avg_return > 0)
        
        return MacroEnvironment(
            vix_level=vix_level,
            vix_value=vix_value,
            interest_rate_trend=rate_trend,
            sector_leadership=sector_leadership,
            risk_on=risk_on
        )
    
    def filter_patterns_by_macro(
        self,
        patterns: List[Dict],
        macro_env: MacroEnvironment
    ) -> List[Dict]:
        """
        Filter patterns based on macro environment.
        
        Args:
            patterns: List of pattern dicts
            macro_env: Current macro environment
            
        Returns:
            Filtered patterns that work in current macro regime
        """
        # Simple heuristic: high VIX favors defensive patterns
        # Low VIX favors momentum/growth patterns
        
        filtered = []
        for pattern in patterns:
            keep = True
            
            # Example filters (customize based on research)
            if macro_env.vix_level == 'extreme':
                # Only keep mean reversion patterns
                if 'drop' not in pattern.get('description', '').lower():
                    keep = False
            
            if macro_env.vix_level == 'low':
                # Favor momentum patterns
                if 'consecutive gain' not in pattern.get('description', '').lower():
                    keep = False
            
            if keep:
                filtered.append(pattern)
        
        return filtered
