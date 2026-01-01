"""
Multi-Ticker Basket Analysis

Renaissance principle: Diversify across multiple uncorrelated assets.
Analyze correlation structure and lead-lag relationships.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from ..utils.market_data import MarketData


@dataclass
class TickerBasket:
    """Collection of tickers with correlation info."""
    tickers: List[str]
    correlation_matrix: np.ndarray
    avg_correlation: float
    diversification_benefit: float  # How much correlation reduces edge


@dataclass
class CrossMarketSignal:
    """Signal from cross-market analysis."""
    primary_ticker: str
    related_ticker: str
    signal_type: str  # 'lead_lag', 'cointegration', 'divergence'
    strength: float  # Signal strength (0-1)
    description: str


class MultiTickerAnalyzer:
    """
    Analyzes baskets of tickers for correlation and cross-market signals.
    
    Features:
    1. Correlation matrix across tickers
    2. Lead-lag detection (does S&P lead OMX?)
    3. Cointegration pairs
    4. Divergence signals
    5. Optimal basket construction
    """
    
    def __init__(
        self,
        lag_window: int = 5,
        min_correlation: float = 0.3
    ):
        """
        Initialize multi-ticker analyzer.
        
        Args:
            lag_window: Max lag to test for lead-lag relationships
            min_correlation: Minimum correlation to flag
        """
        self.lag_window = lag_window
        self.min_correlation = min_correlation
    
    def calculate_correlation_matrix(
        self,
        ticker_returns: Dict[str, np.ndarray]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Calculate correlation matrix across tickers.
        
        Args:
            ticker_returns: Dict of ticker -> returns array
            
        Returns:
            Tuple of (correlation_matrix, ticker_names)
        """
        tickers = list(ticker_returns.keys())
        n = len(tickers)
        
        # Align lengths (use shortest)
        min_len = min(len(returns) for returns in ticker_returns.values())
        aligned_returns = {
            ticker: returns[-min_len:]
            for ticker, returns in ticker_returns.items()
        }
        
        # Build correlation matrix
        corr_matrix = np.zeros((n, n))
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    corr = np.corrcoef(
                        aligned_returns[ticker1],
                        aligned_returns[ticker2]
                    )[0, 1]
                    corr_matrix[i, j] = corr
        
        return corr_matrix, tickers
    
    def detect_lead_lag(
        self,
        leader_returns: np.ndarray,
        follower_returns: np.ndarray,
        max_lag: Optional[int] = None
    ) -> Tuple[int, float]:
        """
        Detect if one market leads another.
        
        Args:
            leader_returns: Potential leading market returns
            follower_returns: Potential following market returns
            max_lag: Max lag to test (None = use self.lag_window)
            
        Returns:
            Tuple of (optimal_lag, correlation_at_lag)
        """
        if max_lag is None:
            max_lag = self.lag_window
        
        # Align lengths
        min_len = min(len(leader_returns), len(follower_returns))
        leader_returns = leader_returns[-min_len:]
        follower_returns = follower_returns[-min_len:]
        
        best_lag = 0
        best_corr = 0.0
        
        for lag in range(1, max_lag + 1):
            if lag >= len(leader_returns):
                break
            
            # Correlate leader[t] with follower[t+lag]
            corr = np.corrcoef(
                leader_returns[:-lag],
                follower_returns[lag:]
            )[0, 1]
            
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
        
        return best_lag, best_corr
    
    def analyze_basket(
        self,
        ticker_data: Dict[str, MarketData],
        basket_name: str = "Multi-Asset Basket"
    ) -> TickerBasket:
        """
        Analyze a basket of tickers for diversification.
        
        Args:
            ticker_data: Dict of ticker -> MarketData
            basket_name: Name of basket
            
        Returns:
            TickerBasket with correlation info
        """
        # Extract returns
        ticker_returns = {
            ticker: data.returns
            for ticker, data in ticker_data.items()
        }
        
        # Calculate correlation
        corr_matrix, tickers = self.calculate_correlation_matrix(ticker_returns)
        
        # Average correlation (exclude diagonal)
        n = len(tickers)
        avg_corr = (np.sum(corr_matrix) - n) / (n * (n - 1)) if n > 1 else 0
        
        # Diversification benefit (lower correlation = more benefit)
        # Formula: benefit = sqrt(1 / (1 + (n-1)*avg_corr))
        div_benefit = np.sqrt(1 / (1 + (n - 1) * avg_corr)) if n > 1 else 1.0
        
        return TickerBasket(
            tickers=tickers,
            correlation_matrix=corr_matrix,
            avg_correlation=avg_corr,
            diversification_benefit=div_benefit
        )
    
    def find_cross_market_signals(
        self,
        ticker_data: Dict[str, MarketData],
        primary_ticker: str
    ) -> List[CrossMarketSignal]:
        """
        Find cross-market signals for a primary ticker.
        
        Args:
            ticker_data: Dict of ticker -> MarketData
            primary_ticker: Ticker to find signals for
            
        Returns:
            List of CrossMarketSignal objects
        """
        signals = []
        
        if primary_ticker not in ticker_data:
            return signals
        
        primary_returns = ticker_data[primary_ticker].returns
        
        for ticker, data in ticker_data.items():
            if ticker == primary_ticker:
                continue
            
            related_returns = data.returns
            
            # Test lead-lag
            lag, corr = self.detect_lead_lag(related_returns, primary_returns)
            
            if abs(corr) > self.min_correlation and lag > 0:
                signal = CrossMarketSignal(
                    primary_ticker=primary_ticker,
                    related_ticker=ticker,
                    signal_type='lead_lag',
                    strength=abs(corr),
                    description=f"{ticker} leads {primary_ticker} by {lag} days (corr={corr:.2f})"
                )
                signals.append(signal)
        
        return signals
    
    def create_basket_report(
        self,
        basket: TickerBasket,
        cross_signals: Optional[List[CrossMarketSignal]] = None
    ) -> str:
        """
        Create report for basket analysis.
        
        Args:
            basket: TickerBasket object
            cross_signals: Optional cross-market signals
            
        Returns:
            Formatted report
        """
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("MULTI-TICKER BASKET ANALYSIS")
        lines.append("=" * 80)
        lines.append(f"Tickers in basket: {len(basket.tickers)}")
        lines.append(f"Tickers: {', '.join(basket.tickers)}")
        lines.append("")
        
        # Correlation summary
        lines.append("CORRELATION STRUCTURE:")
        lines.append("-" * 80)
        lines.append(f"Average correlation: {basket.avg_correlation:.2%}")
        lines.append(f"Diversification benefit: {basket.diversification_benefit:.2%}")
        lines.append("")
        
        # Interpretation
        if basket.avg_correlation > 0.7:
            lines.append("⚠️ HIGH CORRELATION: Limited diversification benefit.")
            lines.append("   These assets move together - edge doesn't multiply.")
        elif basket.avg_correlation > 0.4:
            lines.append("📊 MODERATE CORRELATION: Some diversification benefit.")
            lines.append("   Patterns can be combined with caution.")
        else:
            lines.append("✅ LOW CORRELATION: Strong diversification benefit!")
            lines.append("   Combining patterns across these assets is powerful.")
        
        lines.append("")
        
        # Correlation matrix
        if len(basket.tickers) <= 10:  # Only show for small baskets
            lines.append("CORRELATION MATRIX:")
            lines.append("-" * 80)
            
            # Header
            header = "     " + " ".join(f"{ticker[:5]:>7}" for ticker in basket.tickers)
            lines.append(header)
            
            # Rows
            for i, ticker in enumerate(basket.tickers):
                row = f"{ticker[:5]:<5}"
                for j in range(len(basket.tickers)):
                    row += f"{basket.correlation_matrix[i, j]:>7.2f}"
                lines.append(row)
            
            lines.append("")
        
        # Cross-market signals
        if cross_signals:
            lines.append("CROSS-MARKET SIGNALS:")
            lines.append("-" * 80)
            for signal in cross_signals:
                lines.append(f"📡 {signal.description}")
                lines.append(f"   Strength: {signal.strength:.2%}")
            lines.append("")
        
        lines.append("⚠️ Renaissance principle: Diversify across UNCORRELATED signals.")
        lines.append("⚠️ 10 patterns with 0.7 correlation ≠ 10 independent patterns.")
        
        return "\n".join(lines)
