"""
Verktyg för att hantera och bearbeta historisk marknadsdata.

Hanterar pris, volym, volatilitet och andra mätbara marknadsvariabler.
"""

from typing import Optional, List, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MarketData:
    """Container för marknadsdata."""
    timestamps: np.ndarray
    open_prices: np.ndarray
    high_prices: np.ndarray
    low_prices: np.ndarray
    close_prices: np.ndarray
    volume: np.ndarray
    
    def __len__(self) -> int:
        return len(self.timestamps)
    
    @property
    def returns(self) -> np.ndarray:
        """Beräknar dagliga avkastningar."""
        return np.diff(self.close_prices) / self.close_prices[:-1]
    
    @property
    def log_returns(self) -> np.ndarray:
        """Beräknar logaritmiska avkastningar."""
        return np.log(self.close_prices[1:] / self.close_prices[:-1])


class MarketDataProcessor:
    """
    Bearbetar och beräknar statistik från marknadsdata.
    
    Fokus på mätbara variabler - inga tolkningar eller berättelser.
    """
    
    def __init__(self):
        pass
    
    def calculate_returns(
        self,
        prices: np.ndarray,
        periods: int = 1,
        log_returns: bool = False
    ) -> np.ndarray:
        """
        Beräknar avkastning över specificerade perioder.
        
        Args:
            prices: Array med priser
            periods: Antal perioder att beräkna avkastning över
            log_returns: Om True, använd logaritmiska avkastningar
            
        Returns:
            Array med avkastningar
        """
        if log_returns:
            returns = np.log(prices[periods:] / prices[:-periods])
        else:
            returns = (prices[periods:] - prices[:-periods]) / prices[:-periods]
        
        return returns
    
    def calculate_volatility(
        self,
        returns: np.ndarray,
        window: int = 20,
        annualize: bool = True
    ) -> np.ndarray:
        """
        Beräknar rullande volatilitet.
        
        Args:
            returns: Array med avkastningar
            window: Fönsterstorlek för rullande beräkning
            annualize: Om True, annualisera volatiliteten (anta 252 handelsdagar)
            
        Returns:
            Array med volatilitet
        """
        # Rullande standardavvikelse
        volatility = pd.Series(returns).rolling(window=window).std().values
        
        if annualize:
            volatility = volatility * np.sqrt(252)
        
        return volatility
    
    def calculate_volume_profile(
        self,
        volume: np.ndarray,
        window: int = 20
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Beräknar volymprofil - relativ volym jämfört med genomsnitt.
        
        Args:
            volume: Array med volymdata
            window: Fönsterstorlek för genomsnittsberäkning
            
        Returns:
            Tuple av (genomsnittlig volym, relativ volym)
        """
        avg_volume = pd.Series(volume).rolling(window=window).mean().values
        # Fix divide-by-zero: replace NaN and inf med 1.0 (neutral)
        with np.errstate(divide='ignore', invalid='ignore'):
            relative_volume = volume / avg_volume
        relative_volume = np.nan_to_num(relative_volume, nan=1.0, posinf=1.0, neginf=1.0)
        
        return avg_volume, relative_volume
    
    def identify_price_extremes(
        self,
        prices: np.ndarray,
        window: int = 20,
        threshold: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Identifierar prisrörelser som är extrema relativt historisk volatilitet.
        
        Args:
            prices: Array med priser
            window: Fönsterstorlek för att beräkna 'normal' volatilitet
            threshold: Antal standardavvikelser för att klassas som extrem
            
        Returns:
            Tuple av (boolean array för extremt höga, boolean array för extremt låga)
        """
        returns = self.calculate_returns(prices)
        volatility = pd.Series(returns).rolling(window=window).std().values
        mean_return = pd.Series(returns).rolling(window=window).mean().values
        
        # Z-score för varje avkastning
        z_scores = np.zeros(len(returns))
        valid_idx = ~np.isnan(volatility) & (volatility > 0)
        z_scores[valid_idx] = (returns[valid_idx] - mean_return[valid_idx]) / volatility[valid_idx]
        
        extreme_high = z_scores > threshold
        extreme_low = z_scores < -threshold
        
        return extreme_high, extreme_low
    
    def calculate_momentum(
        self,
        prices: np.ndarray,
        lookback: int = 20
    ) -> np.ndarray:
        """
        Beräknar prismomentum över specificerad period.
        
        Args:
            prices: Array med priser
            lookback: Antal perioder att mäta momentum över
            
        Returns:
            Array med momentum (procent förändring)
        """
        momentum = (prices[lookback:] - prices[:-lookback]) / prices[:-lookback]
        return momentum
    
    def detect_range_bound(
        self,
        prices: np.ndarray,
        window: int = 50,
        threshold: float = 0.10
    ) -> np.ndarray:
        """
        Identifierar perioder då marknaden är range-bound (sidledes).
        
        Args:
            prices: Array med priser
            window: Fönsterstorlek för analys
            threshold: Maximal rörelse (som andel) för att klassas som range-bound
            
        Returns:
            Boolean array som indikerar range-bound perioder
        """
        rolling_max = pd.Series(prices).rolling(window=window).max().values
        rolling_min = pd.Series(prices).rolling(window=window).min().values
        
        price_range = (rolling_max - rolling_min) / rolling_min
        is_range_bound = price_range < threshold
        
        return is_range_bound
    
    def calculate_intraday_volatility(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        method: str = 'parkinson'
    ) -> np.ndarray:
        """
        Beräknar intraday volatilitet baserat på high-low-close data.
        
        Args:
            high: Array med högsta priser
            low: Array med lägsta priser
            close: Array med stängningspriser
            method: Metod att använda ('parkinson' eller 'garman_klass')
            
        Returns:
            Array med intraday volatilitet
        """
        if method == 'parkinson':
            # Parkinson's volatility estimator
            volatility = np.sqrt((1 / (4 * np.log(2))) * np.log(high / low) ** 2)
        elif method == 'garman_klass':
            # Garman-Klass volatility estimator
            term1 = 0.5 * (np.log(high / low)) ** 2
            term2 = (2 * np.log(2) - 1) * (np.log(close / np.roll(close, 1))) ** 2
            volatility = np.sqrt(term1 - term2)
            volatility[0] = np.nan  # Första värdet är invalid
        else:
            raise ValueError(f"Okänd metod: {method}")
        
        return volatility
    
    def calculate_drawdown_series(self, prices: np.ndarray) -> np.ndarray:
        """
        Beräknar drawdown-serien över tid.
        
        Args:
            prices: Array med priser
            
        Returns:
            Array med drawdown värden (negativa)
        """
        cumulative = prices
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        return drawdown
    
    def get_calendar_features(self, timestamps: np.ndarray) -> dict:
        """
        Extraherar kalenderrelaterade features från tidsstämplar.
        
        Args:
            timestamps: Array med datetime objekt
            
        Returns:
            Dictionary med kalenderfeatures
        """
        if isinstance(timestamps[0], (int, float)):
            # Konvertera från unix timestamp om nödvändigt
            timestamps = pd.to_datetime(timestamps, unit='s')
        else:
            timestamps = pd.to_datetime(timestamps)
        
        return {
            'day_of_week': timestamps.dayofweek if hasattr(timestamps, 'dayofweek') else np.array([t.dayofweek for t in timestamps]),
            'day_of_month': timestamps.day if hasattr(timestamps, 'day') else np.array([t.day for t in timestamps]),
            'month': timestamps.month if hasattr(timestamps, 'month') else np.array([t.month for t in timestamps]),
            'quarter': timestamps.quarter if hasattr(timestamps, 'quarter') else np.array([t.quarter for t in timestamps]),
            'is_month_end': timestamps.is_month_end if hasattr(timestamps, 'is_month_end') else np.array([t.is_month_end for t in timestamps]),
            'is_month_start': timestamps.is_month_start if hasattr(timestamps, 'is_month_start') else np.array([t.is_month_start for t in timestamps]),
            'is_quarter_end': timestamps.is_quarter_end if hasattr(timestamps, 'is_quarter_end') else np.array([t.is_quarter_end for t in timestamps])
        }
