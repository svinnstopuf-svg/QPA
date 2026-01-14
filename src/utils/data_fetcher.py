"""
Hämtar riktig marknadsdata från Yahoo Finance.
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from .market_data import MarketData


class DataFetcher:
    """
    Hämtar historisk marknadsdata från Yahoo Finance.
    """
    
    def __init__(self):
        pass
    
    def fetch_stock_data(
        self,
        ticker: str,
        period: str = "2y",
        interval: str = "1d",
        end_date: Optional[datetime] = None
    ) -> Optional[MarketData]:
        """
        Hämtar aktiedata från Yahoo Finance.
        
        Args:
            ticker: Aktiesymbol (t.ex. "AAPL", "MSFT", "^GSPC" för S&P 500)
            period: Tidsperiod att hämta ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: Dataintervall ("1d", "1wk", "1mo")
            end_date: Optional end date for point-in-time analysis
            
        Returns:
            MarketData objekt eller None om det misslyckas
        """
        try:
            print(f"Hämtar data för {ticker}...")
            stock = yf.Ticker(ticker)
            
            if end_date:
                # Point-in-time: use start/end dates instead of period
                # Calculate start date based on period
                if period == "15y":
                    start_date = end_date - timedelta(days=15*365)
                elif period == "10y":
                    start_date = end_date - timedelta(days=10*365)
                elif period == "5y":
                    start_date = end_date - timedelta(days=5*365)
                elif period == "2y":
                    start_date = end_date - timedelta(days=2*365)
                else:
                    start_date = end_date - timedelta(days=2*365)  # default 2y
                
                # Add 1 day since yfinance end_date is exclusive
                df = stock.history(start=start_date, end=end_date + timedelta(days=1), interval=interval)
            else:
                df = stock.history(period=period, interval=interval)
            
            if df.empty:
                print(f"Ingen data hittades för {ticker}")
                return None
            
            # Konvertera till MarketData format
            market_data = MarketData(
                timestamps=df.index.to_numpy(),
                open_prices=df['Open'].to_numpy(),
                high_prices=df['High'].to_numpy(),
                low_prices=df['Low'].to_numpy(),
                close_prices=df['Close'].to_numpy(),
                volume=df['Volume'].to_numpy()
            )
            
            print(f"Hämtade {len(market_data)} datapunkter för {ticker}")
            print(f"Period: {df.index[0].date()} till {df.index[-1].date()}")
            
            return market_data
            
        except Exception as e:
            print(f"Fel vid hämtning av data för {ticker}: {e}")
            return None
    
    def fetch_index_data(
        self,
        index: str = "^GSPC",
        period: str = "2y"
    ) -> Optional[MarketData]:
        """
        Hämtar indexdata från Yahoo Finance.
        
        Populära index:
        - "^GSPC": S&P 500
        - "^DJI": Dow Jones Industrial Average
        - "^IXIC": NASDAQ Composite
        - "^FTSE": FTSE 100
        - "^OMXS30": OMX Stockholm 30
        
        Args:
            index: Indexsymbol
            period: Tidsperiod att hämta
            
        Returns:
            MarketData objekt eller None om det misslyckas
        """
        return self.fetch_stock_data(index, period=period, interval="1d")
    
    def fetch_multiple_tickers(
        self,
        tickers: list,
        period: str = "2y"
    ) -> dict:
        """
        Hämtar data för flera aktier/index.
        
        Args:
            tickers: Lista med tickersymboler
            period: Tidsperiod att hämta
            
        Returns:
            Dictionary med ticker som nyckel och MarketData som värde
        """
        results = {}
        for ticker in tickers:
            data = self.fetch_stock_data(ticker, period=period)
            if data is not None:
                results[ticker] = data
        return results
