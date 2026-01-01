"""
Enhetstester för MarketDataProcessor.
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.market_data import MarketData, MarketDataProcessor
from datetime import datetime, timedelta


class TestMarketDataProcessor:
    """Tester för MarketDataProcessor-klassen."""
    
    def setup_method(self):
        """Körs innan varje test."""
        self.processor = MarketDataProcessor()
        
    def test_calculate_returns(self):
        """Testar beräkning av avkastningar."""
        prices = np.array([100, 102, 101, 105])
        
        returns = self.processor.calculate_returns(prices, periods=1)
        
        assert len(returns) == 3
        assert np.isclose(returns[0], 0.02)  # (102-100)/100
        
    def test_calculate_log_returns(self):
        """Testar beräkning av logaritmiska avkastningar."""
        prices = np.array([100, 102, 101, 105])
        
        log_returns = self.processor.calculate_returns(prices, periods=1, log_returns=True)
        
        assert len(log_returns) == 3
        assert log_returns[0] > 0
        
    def test_calculate_volatility(self):
        """Testar volatilitetsberäkning."""
        returns = np.random.normal(0, 0.02, 100)
        
        volatility = self.processor.calculate_volatility(returns, window=20, annualize=False)
        
        assert len(volatility) == len(returns)
        assert not np.all(np.isnan(volatility))
        
    def test_calculate_momentum(self):
        """Testar momentumberäkning."""
        prices = np.linspace(100, 120, 50)  # Stigande trend
        
        momentum = self.processor.calculate_momentum(prices, lookback=10)
        
        assert len(momentum) == 40
        assert np.all(momentum > 0)  # Alla ska vara positiva i stigande trend
        
    def test_identify_price_extremes(self):
        """Testar identifiering av extrema prisrörelser."""
        # Skapa priser med en extrem rörelse
        prices = np.ones(50) * 100
        prices[25] = 120  # 20% hopp
        
        extreme_high, extreme_low = self.processor.identify_price_extremes(
            prices,
            window=10,
            threshold=2.0
        )
        
        assert isinstance(extreme_high, np.ndarray)
        assert isinstance(extreme_low, np.ndarray)
        

class TestMarketData:
    """Tester för MarketData-klassen."""
    
    def test_market_data_creation(self):
        """Testar skapande av MarketData objekt."""
        n = 100
        timestamps = np.array([datetime(2020, 1, 1) + timedelta(days=i) for i in range(n)])
        prices = np.random.uniform(95, 105, n)
        volume = np.random.uniform(1e6, 2e6, n)
        
        market_data = MarketData(
            timestamps=timestamps,
            open_prices=prices,
            high_prices=prices * 1.01,
            low_prices=prices * 0.99,
            close_prices=prices,
            volume=volume
        )
        
        assert len(market_data) == n
        assert len(market_data.returns) == n - 1
        assert len(market_data.log_returns) == n - 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
