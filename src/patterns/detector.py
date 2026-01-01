"""
Mönsterigenkänning för marknadssituationer.

Identifierar mätbara situationer (X) baserat på:
- Prisrörelser
- Volatilitet  
- Volym
- Tid och kalendereffekter
- Relationer mellan tillgångar (om tillämpligt)
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from ..utils.market_data import MarketData, MarketDataProcessor


@dataclass
class MarketSituation:
    """Representerar en identifierad marknadssituation."""
    situation_id: str
    description: str
    timestamp_indices: np.ndarray  # Indices när denna situation inträffade
    confidence: float
    metadata: Dict


class PatternDetector:
    """
    Identifierar specifika marknadssituationer baserat på mätbara kriterier.
    
    Detta är X-variablerna i analysramverket.
    Ingen tolkning - bara mätning.
    """
    
    def __init__(self):
        self.processor = MarketDataProcessor()
        
    def detect_high_volatility_regime(
        self,
        market_data: MarketData,
        threshold_percentile: float = 75,
        window: int = 20
    ) -> MarketSituation:
        """
        Identifierar perioder med hög volatilitet.
        
        Args:
            market_data: Marknadsdata att analysera
            threshold_percentile: Percentil för att klassas som 'hög' volatilitet
            window: Fönster för volatilitetsberäkning
            
        Returns:
            MarketSituation med perioder av hög volatilitet
        """
        returns = market_data.returns
        volatility = self.processor.calculate_volatility(returns, window=window, annualize=False)
        
        # Beräkna tröskelvärde baserat på percentil
        threshold = np.nanpercentile(volatility, threshold_percentile)
        
        # Identifiera perioder över tröskelvärdet
        high_vol_mask = volatility > threshold
        indices = np.where(high_vol_mask)[0]
        
        confidence = len(indices) / len(volatility) if len(volatility) > 0 else 0.0
        
        return MarketSituation(
            situation_id="high_volatility",
            description=f"Volatilitet över {threshold_percentile}:e percentilen",
            timestamp_indices=indices,
            confidence=confidence,
            metadata={
                'threshold': threshold,
                'window': window,
                'mean_volatility': np.nanmean(volatility),
                'max_volatility': np.nanmax(volatility)
            }
        )
    
    def detect_momentum_regime(
        self,
        market_data: MarketData,
        lookback: int = 20,
        threshold: float = 0.05
    ) -> Tuple[MarketSituation, MarketSituation]:
        """
        Identifierar perioder med positivt eller negativt momentum.
        
        Args:
            market_data: Marknadsdata att analysera
            lookback: Antal perioder för momentumberäkning
            threshold: Minimum momentum för att klassas som tydligt momentum
            
        Returns:
            Tuple av (positivt momentum situation, negativt momentum situation)
        """
        momentum = self.processor.calculate_momentum(market_data.close_prices, lookback=lookback)
        
        # Lägg till NaN för de första lookback perioderna för att matcha längden
        full_momentum = np.full(len(market_data), np.nan)
        full_momentum[lookback:] = momentum
        
        positive_indices = np.where(momentum > threshold)[0] + lookback
        negative_indices = np.where(momentum < -threshold)[0] + lookback
        
        positive_situation = MarketSituation(
            situation_id="positive_momentum",
            description=f"Positivt momentum över {threshold*100:.1f}% på {lookback} perioder",
            timestamp_indices=positive_indices,
            confidence=len(positive_indices) / len(market_data),
            metadata={
                'lookback': lookback,
                'threshold': threshold,
                'mean_momentum': np.mean(momentum[momentum > threshold]) if len(positive_indices) > 0 else 0.0
            }
        )
        
        negative_situation = MarketSituation(
            situation_id="negative_momentum",
            description=f"Negativt momentum under -{threshold*100:.1f}% på {lookback} perioder",
            timestamp_indices=negative_indices,
            confidence=len(negative_indices) / len(market_data),
            metadata={
                'lookback': lookback,
                'threshold': -threshold,
                'mean_momentum': np.mean(momentum[momentum < -threshold]) if len(negative_indices) > 0 else 0.0
            }
        )
        
        return positive_situation, negative_situation
    
    def detect_volume_spike(
        self,
        market_data: MarketData,
        threshold_multiplier: float = 2.0,
        window: int = 20
    ) -> MarketSituation:
        """
        Identifierar perioder med ovanligt hög volym.
        
        Args:
            market_data: Marknadsdata att analysera
            threshold_multiplier: Hur många gånger genomsnittet för att räknas som spike
            window: Fönster för genomsnittsberäkning
            
        Returns:
            MarketSituation med volymspikes
        """
        avg_volume, relative_volume = self.processor.calculate_volume_profile(
            market_data.volume,
            window=window
        )
        
        spike_mask = relative_volume > threshold_multiplier
        indices = np.where(spike_mask)[0]
        
        return MarketSituation(
            situation_id="volume_spike",
            description=f"Volym över {threshold_multiplier}x genomsnitt ({window} perioder)",
            timestamp_indices=indices,
            confidence=len(indices) / len(market_data),
            metadata={
                'threshold_multiplier': threshold_multiplier,
                'window': window,
                'mean_relative_volume': np.nanmean(relative_volume),
                'max_relative_volume': np.nanmax(relative_volume)
            }
        )
    
    def detect_extreme_moves(
        self,
        market_data: MarketData,
        threshold_std: float = 2.5,
        window: int = 20
    ) -> Tuple[MarketSituation, MarketSituation]:
        """
        Identifierar extrema prisrörelser (outliers).
        
        Args:
            market_data: Marknadsdata att analysera
            threshold_std: Antal standardavvikelser för att räknas som extrem
            window: Fönster för att beräkna 'normal' volatilitet
            
        Returns:
            Tuple av (extrema uppgångar, extrema nedgångar)
        """
        extreme_high, extreme_low = self.processor.identify_price_extremes(
            market_data.close_prices,
            window=window,
            threshold=threshold_std
        )
        
        # Lägg till en period i början för att matcha längden
        extreme_high = np.concatenate([[False], extreme_high])
        extreme_low = np.concatenate([[False], extreme_low])
        
        high_indices = np.where(extreme_high)[0]
        low_indices = np.where(extreme_low)[0]
        
        extreme_up = MarketSituation(
            situation_id="extreme_move_up",
            description=f"Extrema uppgångar (>{threshold_std} std över {window} perioder)",
            timestamp_indices=high_indices,
            confidence=len(high_indices) / len(market_data),
            metadata={
                'threshold_std': threshold_std,
                'window': window,
                'count': len(high_indices)
            }
        )
        
        extreme_down = MarketSituation(
            situation_id="extreme_move_down",
            description=f"Extrema nedgångar (<-{threshold_std} std över {window} perioder)",
            timestamp_indices=low_indices,
            confidence=len(low_indices) / len(market_data),
            metadata={
                'threshold_std': -threshold_std,
                'window': window,
                'count': len(low_indices)
            }
        )
        
        return extreme_up, extreme_down
    
    def detect_range_bound_period(
        self,
        market_data: MarketData,
        window: int = 50,
        max_range: float = 0.10
    ) -> MarketSituation:
        """
        Identifierar sidledes marknader (range-bound).
        
        Args:
            market_data: Marknadsdata att analysera
            window: Fönster för att mäta prisrange
            max_range: Maximal rörelse (procent) för att räknas som sidledes
            
        Returns:
            MarketSituation för range-bound perioder
        """
        is_range_bound = self.processor.detect_range_bound(
            market_data.close_prices,
            window=window,
            threshold=max_range
        )
        
        indices = np.where(is_range_bound)[0]
        
        return MarketSituation(
            situation_id="range_bound",
            description=f"Sidledes marknad (rörelse <{max_range*100:.1f}% över {window} perioder)",
            timestamp_indices=indices,
            confidence=len(indices) / len(market_data),
            metadata={
                'window': window,
                'max_range': max_range,
                'periods': len(indices)
            }
        )
    
    def detect_calendar_patterns(
        self,
        market_data: MarketData
    ) -> Dict[str, MarketSituation]:
        """
        Identifierar kalenderrelaterade mönster.
        
        Args:
            market_data: Marknadsdata att analysera
            
        Returns:
            Dictionary med olika kalendersituationer
        """
        calendar_features = self.processor.get_calendar_features(market_data.timestamps)
        
        situations = {}
        
        # Månadsskifte
        month_end_indices = np.where(calendar_features['is_month_end'])[0]
        situations['month_end'] = MarketSituation(
            situation_id="month_end",
            description="Sista handelsdagen i månaden",
            timestamp_indices=month_end_indices,
            confidence=len(month_end_indices) / len(market_data),
            metadata={'count': len(month_end_indices)}
        )
        
        # Månadsbörjan
        month_start_indices = np.where(calendar_features['is_month_start'])[0]
        situations['month_start'] = MarketSituation(
            situation_id="month_start",
            description="Första handelsdagen i månaden",
            timestamp_indices=month_start_indices,
            confidence=len(month_start_indices) / len(market_data),
            metadata={'count': len(month_start_indices)}
        )
        
        # Kvartalsslut
        quarter_end_indices = np.where(calendar_features['is_quarter_end'])[0]
        situations['quarter_end'] = MarketSituation(
            situation_id="quarter_end",
            description="Sista handelsdagen i kvartalet",
            timestamp_indices=quarter_end_indices,
            confidence=len(quarter_end_indices) / len(market_data),
            metadata={'count': len(quarter_end_indices)}
        )
        
        # Veckodagar
        for day in range(5):  # 0 = måndag, 4 = fredag
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][day]
            day_indices = np.where(calendar_features['day_of_week'] == day)[0]
            situations[f'weekday_{day}'] = MarketSituation(
                situation_id=f"weekday_{day}",
                description=f"{day_name}",
                timestamp_indices=day_indices,
                confidence=len(day_indices) / len(market_data),
                metadata={'day_name': day_name, 'count': len(day_indices)}
            )
        
        return situations
    
    def detect_all_patterns(self, market_data: MarketData) -> Dict[str, MarketSituation]:
        """
        Kör alla mönsterdetektorer och returnerar alla identifierade situationer.
        
        Args:
            market_data: Marknadsdata att analysera
            
        Returns:
            Dictionary med alla identifierade marknadssituationer
        """
        situations = {}
        
        # Volatilitetsregimer
        situations['high_volatility'] = self.detect_high_volatility_regime(market_data)
        
        # Momentum
        pos_mom, neg_mom = self.detect_momentum_regime(market_data)
        situations['positive_momentum'] = pos_mom
        situations['negative_momentum'] = neg_mom
        
        # Volym
        situations['volume_spike'] = self.detect_volume_spike(market_data)
        
        # Extrema rörelser
        extreme_up, extreme_down = self.detect_extreme_moves(market_data)
        situations['extreme_move_up'] = extreme_up
        situations['extreme_move_down'] = extreme_down
        
        # Range-bound
        situations['range_bound'] = self.detect_range_bound_period(market_data)
        
        # Kalendereffekter
        calendar_situations = self.detect_calendar_patterns(market_data)
        situations.update(calendar_situations)
        
        return situations
