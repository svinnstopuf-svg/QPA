"""
Beta-Alpha Separation - Isolate Instrument-Specific Alpha

Quantitative Principle:
Total Return = Beta * Market Return + Alpha + Noise

We only want to trade instruments with significant ALPHA (excess return 
independent of market direction). Filter out instruments that just ride 
market momentum.

Methodology:
1. Calculate Beta vs OMXS30 (market exposure)
2. Calculate expected return from beta: Beta * Market_Return
3. Calculate Alpha: Actual_Return - Expected_Return
4. Only trade if Alpha > 0 AND statistically significant

Trading Logic:
- High Alpha, Low Beta: IDEAL (pure alpha play)
- High Alpha, High Beta: ACCEPTABLE (alpha + market exposure)
- Low Alpha, High Beta: BLOCK (just market momentum)
- Low Alpha, Low Beta: BLOCK (no edge)
"""
from typing import Dict, Tuple, List
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class BetaAlphaAnalysis:
    """Results from beta-alpha decomposition."""
    ticker: str
    beta: float  # Market exposure
    alpha_annualized: float  # Excess return vs market (%)
    alpha_daily: float  # Daily alpha (%)
    
    # Statistical significance
    alpha_t_stat: float  # t-statistic for alpha
    alpha_significant: bool  # Is alpha statistically significant?
    
    # Decomposition
    total_return: float  # Total return (%)
    market_return: float  # OMXS30 return (%)
    expected_return: float  # Beta * Market_Return
    
    # Quality metrics
    r_squared: float  # How much variance explained by market
    residual_volatility: float  # Idiosyncratic risk (%)
    
    # Trading decision
    tradable: bool  # Has significant positive alpha?
    edge_source: str  # "ALPHA", "BETA+ALPHA", "BETA_ONLY", "NO_EDGE"


class BetaAlphaSeparator:
    """
    Separates instrument returns into market beta and alpha components.
    
    Philosophy: Only trade instruments with genuine alpha, not market followers.
    """
    
    def __init__(
        self,
        market_ticker: str = "^OMX",  # OMXS30
        lookback_days: int = 90,
        alpha_significance_threshold: float = 1.96,  # 95% confidence
        min_alpha_pct: float = 0.5  # Minimum 0.5% annualized alpha
    ):
        """
        Initialize beta-alpha separator.
        
        Args:
            market_ticker: Market benchmark (default: OMXS30)
            lookback_days: Days of history for regression
            alpha_significance_threshold: t-stat threshold for significance
            min_alpha_pct: Minimum alpha to be considered tradable
        """
        self.market_ticker = market_ticker
        self.lookback_days = lookback_days
        self.alpha_threshold = alpha_significance_threshold
        self.min_alpha_pct = min_alpha_pct
        
        # Cache market data
        self._market_data = None
        self._market_returns = None
    
    def _fetch_market_data(self, end_date: datetime = None) -> np.ndarray:
        """Fetch and cache OMXS30 returns."""
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=self.lookback_days + 30)
        
        try:
            market = yf.download(
                self.market_ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if market.empty:
                raise ValueError(f"No data for market ticker {self.market_ticker}")
            
            returns = market['Close'].pct_change().dropna()
            return returns.values
        
        except Exception as e:
            raise ValueError(f"Failed to fetch market data: {e}")
    
    def analyze(
        self,
        ticker: str,
        end_date: datetime = None
    ) -> BetaAlphaAnalysis:
        """
        Perform beta-alpha decomposition for an instrument.
        
        Args:
            ticker: Instrument ticker
            end_date: End date for analysis (default: now)
            
        Returns:
            BetaAlphaAnalysis with decomposition results
        """
        if end_date is None:
            end_date = datetime.now()
        
        start_date = end_date - timedelta(days=self.lookback_days + 30)
        
        # 1. Fetch instrument data
        try:
            inst_data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if inst_data.empty or len(inst_data) < 20:
                # Not enough data - return neutral analysis
                return self._neutral_analysis(ticker, "INSUFFICIENT_DATA")
            
            # Handle both single-ticker and multi-ticker yfinance formats
            if isinstance(inst_data.columns, pd.MultiIndex):
                inst_returns = inst_data['Close'][ticker].pct_change().dropna()
            else:
                inst_returns = inst_data['Close'].pct_change().dropna()
        
        except Exception as e:
            return self._neutral_analysis(ticker, f"DATA_ERROR: {e}")
        
        # 2. Fetch market data
        try:
            market_data = yf.download(
                self.market_ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            # Handle both single-ticker and multi-ticker formats
            if isinstance(market_data.columns, pd.MultiIndex):
                market_returns_series = market_data['Close'][self.market_ticker].pct_change().dropna()
            else:
                market_returns_series = market_data['Close'].pct_change().dropna()
        
        except Exception as e:
            return self._neutral_analysis(ticker, f"MARKET_DATA_ERROR: {e}")
        
        # 3. Align dates (only use overlapping dates)
        common_dates = inst_returns.index.intersection(market_returns_series.index)
        
        if len(common_dates) < 20:
            return self._neutral_analysis(ticker, "INSUFFICIENT_OVERLAP")
        
        y = inst_returns.loc[common_dates].values
        x = market_returns_series.loc[common_dates].values
        
        # 4. OLS Regression: y = alpha + beta*x + epsilon
        # Add intercept to x
        X = np.vstack([np.ones(len(x)), x]).T
        
        # Solve via normal equations: (X'X)^-1 X'y
        try:
            beta_hat = np.linalg.lstsq(X, y, rcond=None)[0]
            alpha_daily = beta_hat[0]
            beta = beta_hat[1]
        except:
            return self._neutral_analysis(ticker, "REGRESSION_ERROR")
        
        # 5. Calculate residuals and statistics
        y_pred = X @ beta_hat
        residuals = y - y_pred
        
        # R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Residual volatility (idiosyncratic risk)
        residual_vol = np.std(residuals) * np.sqrt(252) * 100  # Annualized %
        
        # Alpha t-statistic
        n = len(y)
        dof = n - 2
        
        if dof > 0:
            s_squared = ss_res / dof
            var_alpha = s_squared * np.linalg.inv(X.T @ X)[0, 0]
            se_alpha = np.sqrt(var_alpha)
            
            alpha_t_stat = alpha_daily / se_alpha if se_alpha > 0 else 0
        else:
            alpha_t_stat = 0
        
        # 6. Annualize alpha
        alpha_annualized = alpha_daily * 252 * 100  # Convert to %
        
        # 7. Calculate returns
        total_return = (np.prod(1 + y) - 1) * 100
        market_return = (np.prod(1 + x) - 1) * 100
        expected_return = beta * market_return
        
        # 8. Determine statistical significance
        alpha_significant = abs(alpha_t_stat) > self.alpha_threshold
        
        # 9. Determine tradability
        # Must have:
        # - Positive alpha
        # - Statistical significance
        # - Above minimum threshold
        has_positive_alpha = alpha_annualized > self.min_alpha_pct
        tradable = has_positive_alpha and alpha_significant
        
        # 10. Classify edge source
        if tradable:
            if abs(beta) < 0.5:
                edge_source = "ALPHA"  # Pure alpha play
            else:
                edge_source = "BETA+ALPHA"  # Combined
        else:
            if abs(beta) > 0.8 and not has_positive_alpha:
                edge_source = "BETA_ONLY"  # Just riding market
            else:
                edge_source = "NO_EDGE"
        
        return BetaAlphaAnalysis(
            ticker=ticker,
            beta=beta,
            alpha_annualized=alpha_annualized,
            alpha_daily=alpha_daily,
            alpha_t_stat=alpha_t_stat,
            alpha_significant=alpha_significant,
            total_return=total_return,
            market_return=market_return,
            expected_return=expected_return,
            r_squared=r_squared,
            residual_volatility=residual_vol,
            tradable=tradable,
            edge_source=edge_source
        )
    
    def _neutral_analysis(self, ticker: str, reason: str) -> BetaAlphaAnalysis:
        """Return neutral analysis when data is unavailable."""
        return BetaAlphaAnalysis(
            ticker=ticker,
            beta=0.0,
            alpha_annualized=0.0,
            alpha_daily=0.0,
            alpha_t_stat=0.0,
            alpha_significant=False,
            total_return=0.0,
            market_return=0.0,
            expected_return=0.0,
            r_squared=0.0,
            residual_volatility=0.0,
            tradable=False,
            edge_source=f"ERROR: {reason}"
        )
    
    def format_analysis_report(self, analysis: BetaAlphaAnalysis) -> str:
        """Generate formatted analysis report."""
        report = f"""
{'='*70}
BETA-ALPHA ANALYSIS: {analysis.ticker}
{'='*70}

Return Decomposition ({self.lookback_days}d):
  Total Return:        {analysis.total_return:+6.2f}%
  Market Return:       {analysis.market_return:+6.2f}%
  Expected (Beta):     {analysis.expected_return:+6.2f}%
  Alpha (Excess):      {analysis.alpha_annualized:+6.2f}% annualized

Beta Exposure:
  Beta:                {analysis.beta:.2f}
  R²:                  {analysis.r_squared:.2f} ({analysis.r_squared*100:.0f}% explained by market)
  
Alpha Significance:
  Daily Alpha:         {analysis.alpha_daily*100:+.4f}%
  t-statistic:         {analysis.alpha_t_stat:.2f}
  Significant:         {'✅ YES' if analysis.alpha_significant else '❌ NO'}
  
Risk Metrics:
  Residual Vol:        {analysis.residual_volatility:.2f}% (idiosyncratic)

Trading Decision:
  Edge Source:         {analysis.edge_source}
  Tradable:            {'✅ YES' if analysis.tradable else '❌ BLOCK'}

Interpretation:
  {'Pure alpha play - low market dependence' if analysis.edge_source == 'ALPHA' else ''}
  {'Alpha + market exposure - acceptable' if analysis.edge_source == 'BETA+ALPHA' else ''}
  {'⚠️ Just riding market - no real edge' if analysis.edge_source == 'BETA_ONLY' else ''}
  {'No significant edge detected' if analysis.edge_source == 'NO_EDGE' else ''}
{'='*70}
"""
        return report
    
    def batch_analyze(
        self,
        tickers: List[str],
        end_date: datetime = None
    ) -> Dict[str, BetaAlphaAnalysis]:
        """
        Analyze multiple instruments.
        
        Args:
            tickers: List of tickers
            end_date: End date for analysis
            
        Returns:
            Dict mapping ticker -> BetaAlphaAnalysis
        """
        results = {}
        
        for ticker in tickers:
            try:
                analysis = self.analyze(ticker, end_date)
                results[ticker] = analysis
            except Exception as e:
                results[ticker] = self._neutral_analysis(ticker, f"ERROR: {e}")
        
        return results


if __name__ == "__main__":
    # Test module
    print("Testing Beta-Alpha Separator...")
    
    separator = BetaAlphaSeparator(
        market_ticker="^OMX",
        lookback_days=90,
        min_alpha_pct=0.5
    )
    
    # Test with a few Swedish stocks
    test_tickers = ["VOLV-B.ST", "HM-B.ST", "ERIC-B.ST"]
    
    print(f"\nAnalyzing {len(test_tickers)} instruments vs OMXS30...\n")
    
    for ticker in test_tickers:
        try:
            analysis = separator.analyze(ticker)
            print(separator.format_analysis_report(analysis))
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}\n")
    
    print("\n✅ Beta-Alpha Separator - Tests Complete")
