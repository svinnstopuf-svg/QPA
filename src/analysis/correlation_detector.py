"""
Correlation Detector - Identifies Correlated Instruments

Groups instruments with correlation > 0.6 to prevent concentration risk.
Recommends only 1 instrument per cluster.
"""

from dataclasses import dataclass
from typing import List, Dict
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta


@dataclass
class CorrelationCluster:
    """Group of correlated instruments."""
    tickers: List[str]
    avg_correlation: float
    recommended_ticker: str  # Best one to hold
    risk_warning: str


class CorrelationDetector:
    """
    Detect correlation clusters to avoid concentration risk.
    
    Logic:
    1. Calculate pairwise correlation (90-day returns)
    2. Group instruments with corr > 0.6
    3. Within each cluster, recommend the one with best risk/reward
    """
    
    def __init__(
        self,
        correlation_threshold: float = 0.6,
        lookback_days: int = 90
    ):
        self.correlation_threshold = correlation_threshold
        self.lookback_days = lookback_days
        self.price_cache = {}
    
    def find_clusters(
        self,
        tickers: List[str],
        scores: Dict[str, float]  # Ticker -> score/quality metric
    ) -> List[CorrelationCluster]:
        """
        Find correlation clusters among tickers.
        
        Args:
            tickers: List of tickers to analyze
            scores: Dict of ticker -> quality score (for ranking)
            
        Returns:
            List of CorrelationCluster objects
        """
        
        if len(tickers) < 2:
            return []
        
        # Fetch price data
        returns_matrix = self._get_returns_matrix(tickers)
        
        if returns_matrix is None or len(returns_matrix) == 0:
            return []
        
        # Calculate correlation matrix
        try:
            corr_matrix = np.corrcoef(returns_matrix)
        except Exception as e:
            print(f"  ⚠️ Correlation calculation failed: {e}")
            return []
        
        # Find clusters using simple linkage
        clusters = []
        used_tickers = set()
        
        for i, ticker_i in enumerate(tickers):
            if ticker_i in used_tickers:
                continue
            
            # Find all tickers correlated with ticker_i
            cluster_tickers = [ticker_i]
            
            for j, ticker_j in enumerate(tickers):
                if i == j or ticker_j in used_tickers:
                    continue
                
                correlation = corr_matrix[i, j]
                
                if correlation >= self.correlation_threshold:
                    cluster_tickers.append(ticker_j)
            
            # Only create cluster if > 1 ticker
            if len(cluster_tickers) > 1:
                # Calculate avg correlation within cluster
                correlations = []
                for idx_i, tick_i in enumerate(cluster_tickers):
                    i_global = tickers.index(tick_i)
                    for idx_j, tick_j in enumerate(cluster_tickers):
                        if idx_i < idx_j:
                            j_global = tickers.index(tick_j)
                            correlations.append(corr_matrix[i_global, j_global])
                
                avg_corr = float(np.mean(correlations)) if correlations else 0.0
                
                # Recommend best ticker (highest score)
                recommended = max(cluster_tickers, key=lambda t: scores.get(t, 0.0))
                
                # Create warning
                other_tickers = [t for t in cluster_tickers if t != recommended]
                risk_warning = f"Highly correlated with {', '.join(other_tickers[:3])} - diversification illusion"
                
                clusters.append(CorrelationCluster(
                    tickers=cluster_tickers,
                    avg_correlation=avg_corr,
                    recommended_ticker=recommended,
                    risk_warning=risk_warning
                ))
                
                # Mark as used
                used_tickers.update(cluster_tickers)
        
        return clusters
    
    def _get_returns_matrix(self, tickers: List[str]) -> np.ndarray:
        """
        Get returns matrix for correlation calculation.
        
        Returns:
            numpy array of shape (n_tickers, n_days)
        """
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days + 30)  # Extra buffer
        
        returns_list = []
        valid_tickers = []
        
        for ticker in tickers:
            try:
                # Check cache
                cache_key = f"{ticker}_{start_date.strftime('%Y%m%d')}"
                
                if cache_key in self.price_cache:
                    returns = self.price_cache[cache_key]
                else:
                    # Fetch data
                    data = yf.download(
                        ticker,
                        start=start_date.strftime('%Y-%m-%d'),
                        end=end_date.strftime('%Y-%m-%d'),
                        progress=False
                    )
                    
                    if len(data) < self.lookback_days:
                        continue
                    
                    # Calculate returns
                    prices = data['Close'].values
                    returns = np.diff(prices) / prices[:-1]
                    
                    # Take last lookback_days
                    returns = returns[-self.lookback_days:]
                    
                    # Cache it
                    self.price_cache[cache_key] = returns
                
                returns_list.append(returns)
                valid_tickers.append(ticker)
            
            except Exception as e:
                # Skip this ticker
                continue
        
        if len(returns_list) < 2:
            return None
        
        # Ensure all returns have same length
        min_length = min(len(r) for r in returns_list)
        returns_list = [r[-min_length:] for r in returns_list]
        
        return np.array(returns_list)
