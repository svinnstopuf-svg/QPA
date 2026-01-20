"""
Market Breadth Indicator - Measure Market Health

Quantitative Principle:
A healthy bull market has broad participation (most stocks rising).
A weak rally has narrow leadership (only a few stocks up while market rises).

Breadth Metric:
% of OMXS30 constituents trading above their 200-day MA.

Trading Logic:
- Breadth >= 60%: HEALTHY (broad rally, safe to trade)
- Breadth 40-60%: NEUTRAL (mixed market, proceed with caution)
- Breadth < 40%: WEAK (narrow rally or bear market, BLOCK new trades)

This prevents entering positions during weak market rallies that are 
likely to reverse.
"""
from typing import List, Dict
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class BreadthAnalysis:
    """Results from market breadth analysis."""
    date: str
    breadth_pct: float  # % of constituents above 200MA
    constituents_analyzed: int
    constituents_above_200ma: int
    
    # Regime classification
    breadth_regime: str  # HEALTHY, NEUTRAL, WEAK
    tradable: bool  # Can we trade in this environment?
    
    # Details for debugging
    failed_tickers: List[str]  # Tickers that failed to fetch


class MarketBreadthIndicator:
    """
    Measures market breadth for OMXS30.
    
    Philosophy: Only trade when market has broad participation.
    """
    
    # OMXS30 constituents (as of 2024 - update periodically)
    OMXS30_CONSTITUENTS = [
        "ABB.ST", "ALFA.ST", "ALIV-SDB.ST", "ASSA-B.ST", "ATCO-A.ST",
        "ATCO-B.ST", "AZN.ST", "BOL.ST", "ELUX-B.ST", "ERIC-B.ST",
        "ESSITY-B.ST", "EVO.ST", "GETI-B.ST", "HM-B.ST", "HEXA-B.ST",
        "INVE-B.ST", "KINV-B.ST", "NIBE-B.ST", "NDA-SE.ST", "SAND.ST",
        "SBB-B.ST", "SCA-B.ST", "SEB-A.ST", "SECU-B.ST", "SKA-B.ST",
        "SKF-B.ST", "SWED-A.ST", "TEL2-B.ST", "VOLV-B.ST", "WALL-B.ST"
    ]
    
    def __init__(
        self,
        healthy_threshold: float = 60.0,
        weak_threshold: float = 40.0,
        ma_period: int = 200
    ):
        """
        Initialize market breadth indicator.
        
        Args:
            healthy_threshold: Breadth % for HEALTHY regime
            weak_threshold: Breadth % below which is WEAK
            ma_period: MA period for trend (default 200)
        """
        self.healthy_threshold = healthy_threshold
        self.weak_threshold = weak_threshold
        self.ma_period = ma_period
    
    def analyze_breadth(
        self,
        end_date: datetime = None,
        constituents: List[str] = None
    ) -> BreadthAnalysis:
        """
        Calculate market breadth as of a specific date.
        
        Args:
            end_date: Date to measure breadth (default: today)
            constituents: List of tickers (default: OMXS30)
            
        Returns:
            BreadthAnalysis with results
        """
        if end_date is None:
            end_date = datetime.now()
        
        if constituents is None:
            constituents = self.OMXS30_CONSTITUENTS
        
        # We need at least ma_period + 30 days of history
        start_date = end_date - timedelta(days=self.ma_period + 60)
        
        above_200ma = 0
        failed_tickers = []
        
        for ticker in constituents:
            try:
                # Fetch data for this ticker
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    progress=False
                )
                
                if data.empty or len(data) < self.ma_period:
                    failed_tickers.append(ticker)
                    continue
                
                # Calculate 200-day MA
                # Handle both single and multi-ticker format
                if isinstance(data.columns, pd.MultiIndex):
                    close_prices = data['Close'][ticker]
                else:
                    close_prices = data['Close']
                
                ma_200 = close_prices.rolling(window=self.ma_period).mean()
                
                # Get current price and MA
                current_price = close_prices.iloc[-1]
                current_ma = ma_200.iloc[-1]
                
                # Check if above MA
                if pd.notna(current_price) and pd.notna(current_ma):
                    if current_price > current_ma:
                        above_200ma += 1
                else:
                    failed_tickers.append(ticker)
            
            except Exception as e:
                failed_tickers.append(ticker)
                continue
        
        # Calculate breadth
        constituents_analyzed = len(constituents) - len(failed_tickers)
        
        if constituents_analyzed == 0:
            # No data available
            return BreadthAnalysis(
                date=end_date.strftime("%Y-%m-%d"),
                breadth_pct=0.0,
                constituents_analyzed=0,
                constituents_above_200ma=0,
                breadth_regime="ERROR",
                tradable=False,
                failed_tickers=failed_tickers
            )
        
        breadth_pct = (above_200ma / constituents_analyzed) * 100
        
        # Determine regime
        if breadth_pct >= self.healthy_threshold:
            breadth_regime = "HEALTHY"
            tradable = True
        elif breadth_pct >= self.weak_threshold:
            breadth_regime = "NEUTRAL"
            tradable = True  # Proceed with caution
        else:
            breadth_regime = "WEAK"
            tradable = False  # Block new trades
        
        return BreadthAnalysis(
            date=end_date.strftime("%Y-%m-%d"),
            breadth_pct=breadth_pct,
            constituents_analyzed=constituents_analyzed,
            constituents_above_200ma=above_200ma,
            breadth_regime=breadth_regime,
            tradable=tradable,
            failed_tickers=failed_tickers
        )
    
    def analyze_breadth_trend(
        self,
        days_back: int = 30,
        end_date: datetime = None
    ) -> Dict:
        """
        Analyze breadth trend over time.
        
        Useful for detecting improving or deteriorating market conditions.
        
        Args:
            days_back: Number of days to analyze
            end_date: End date (default: today)
            
        Returns:
            Dict with trend analysis
        """
        if end_date is None:
            end_date = datetime.now()
        
        # Sample breadth at weekly intervals
        breadth_history = []
        
        for i in range(0, days_back, 7):
            sample_date = end_date - timedelta(days=i)
            analysis = self.analyze_breadth(sample_date)
            
            breadth_history.append({
                'date': analysis.date,
                'breadth_pct': analysis.breadth_pct,
                'regime': analysis.breadth_regime
            })
        
        # Reverse to chronological order
        breadth_history.reverse()
        
        # Calculate trend
        if len(breadth_history) >= 2:
            first_breadth = breadth_history[0]['breadth_pct']
            last_breadth = breadth_history[-1]['breadth_pct']
            breadth_change = last_breadth - first_breadth
            
            if breadth_change > 10:
                trend = "IMPROVING"
            elif breadth_change < -10:
                trend = "DETERIORATING"
            else:
                trend = "STABLE"
        else:
            trend = "UNKNOWN"
        
        return {
            'history': breadth_history,
            'trend': trend,
            'current_breadth': breadth_history[-1]['breadth_pct'] if breadth_history else 0,
            'first_breadth': breadth_history[0]['breadth_pct'] if breadth_history else 0,
            'breadth_change': breadth_change if len(breadth_history) >= 2 else 0
        }
    
    def format_analysis_report(self, analysis: BreadthAnalysis) -> str:
        """Generate formatted breadth report."""
        report = f"""
{'='*70}
MARKET BREADTH ANALYSIS: OMXS30
{'='*70}

Date: {analysis.date}

Breadth Metrics:
  Above 200-day MA:    {analysis.constituents_above_200ma}/{analysis.constituents_analyzed} constituents
  Breadth:             {analysis.breadth_pct:.1f}%
  
Market Regime:
  Classification:      {analysis.breadth_regime}
  Tradable:            {'✅ YES' if analysis.tradable else '❌ BLOCK NEW TRADES'}

Interpretation:
  {'Broad rally - healthy market participation' if analysis.breadth_regime == 'HEALTHY' else ''}
  {'Mixed market - some leadership, proceed with caution' if analysis.breadth_regime == 'NEUTRAL' else ''}
  {'⚠️ Narrow rally or bear market - BLOCK new entries' if analysis.breadth_regime == 'WEAK' else ''}

Quality:
  Failed tickers:      {len(analysis.failed_tickers)} ({', '.join(analysis.failed_tickers[:5]) if analysis.failed_tickers else 'None'})
{'='*70}
"""
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Market Breadth Indicator...")
    
    breadth_indicator = MarketBreadthIndicator(
        healthy_threshold=60.0,
        weak_threshold=40.0
    )
    
    print("\n1. Current Market Breadth:")
    analysis = breadth_indicator.analyze_breadth()
    print(breadth_indicator.format_analysis_report(analysis))
    
    print("\n2. Breadth Trend (30-day):")
    trend = breadth_indicator.analyze_breadth_trend(days_back=30)
    print(f"  Current:     {trend['current_breadth']:.1f}%")
    print(f"  30d ago:     {trend['first_breadth']:.1f}%")
    print(f"  Change:      {trend['breadth_change']:+.1f}%")
    print(f"  Trend:       {trend['trend']}")
    
    print("\n✅ Market Breadth Indicator - Tests Complete")
