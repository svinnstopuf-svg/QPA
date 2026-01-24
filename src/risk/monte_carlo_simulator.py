"""
Monte Carlo Simulator - Probabilistic Risk Analysis

Simulates 500 price paths to calculate probability of hitting stop-loss.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class MonteCarloResult:
    """Monte Carlo simulation result."""
    ticker: str
    probability_of_stopout: float  # 0-1 (probability of hitting stop)
    mean_return: float  # Expected return
    percentile_5: float  # 5th percentile (worst case)
    percentile_95: float  # 95th percentile (best case)
    risk_rating: str  # "LOW", "MODERATE", "HIGH", "EXTREME"
    num_paths: int = 500


class MonteCarloSimulator:
    """
    Monte Carlo simulator for position risk analysis.
    
    Simulates price paths using historical volatility to estimate:
    - Probability of hitting stop-loss
    - Distribution of potential outcomes
    """
    
    def __init__(self, num_paths: int = 500, holding_days: int = 63):
        self.num_paths = num_paths
        self.holding_days = holding_days
    
    def simulate(
        self,
        ticker: str,
        current_price: float,
        stop_loss: float,
        historical_returns: np.ndarray
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation.
        
        Args:
            ticker: Instrument ticker
            current_price: Current price
            stop_loss: Stop-loss price
            historical_returns: Array of historical daily returns
            
        Returns:
            MonteCarloResult with P(stop-out) and distribution
        """
        
        # Calculate historical volatility
        volatility = float(np.std(historical_returns))
        mean_return = float(np.mean(historical_returns))
        
        # Simulate paths
        final_returns = []
        stopout_count = 0
        
        for _ in range(self.num_paths):
            price = current_price
            hit_stop = False
            
            for day in range(self.holding_days):
                # Generate random return using GBM
                daily_return = np.random.normal(mean_return, volatility)
                price *= (1 + daily_return)
                
                # Check if hit stop-loss
                if price <= stop_loss:
                    hit_stop = True
                    break
            
            if hit_stop:
                stopout_count += 1
                final_return = (stop_loss - current_price) / current_price
            else:
                final_return = (price - current_price) / current_price
            
            final_returns.append(final_return)
        
        # Calculate statistics
        final_returns = np.array(final_returns)
        probability_of_stopout = stopout_count / self.num_paths
        mean_final_return = float(np.mean(final_returns))
        percentile_5 = float(np.percentile(final_returns, 5))
        percentile_95 = float(np.percentile(final_returns, 95))
        
        # Risk rating
        if probability_of_stopout < 0.15:
            risk_rating = "LOW"
        elif probability_of_stopout < 0.30:
            risk_rating = "MODERATE"
        elif probability_of_stopout < 0.50:
            risk_rating = "HIGH"
        else:
            risk_rating = "EXTREME"
        
        return MonteCarloResult(
            ticker=ticker,
            probability_of_stopout=probability_of_stopout,
            mean_return=mean_final_return,
            percentile_5=percentile_5,
            percentile_95=percentile_95,
            risk_rating=risk_rating,
            num_paths=self.num_paths
        )
