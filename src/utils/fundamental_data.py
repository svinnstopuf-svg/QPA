"""
Fundamental Data Fetcher

Hämtar fundamentaldata från Yahoo Finance för instrument-screening.
Inkluderar: P/E ratio, P/B ratio, dividend yield, market cap, etc.
"""

import yfinance as yf
from typing import Dict, Optional
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')


@dataclass
class FundamentalData:
    """Container för fundamentaldata."""
    ticker: str
    
    # Valuation metrics
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    
    # Dividend metrics
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    
    # Size metrics
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    
    # Profitability metrics
    profit_margin: Optional[float] = None
    roe: Optional[float] = None  # Return on Equity
    
    # Growth metrics
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    
    # Quality score (computed)
    quality_score: Optional[float] = None
    
    def __post_init__(self):
        """Beräkna quality score efter initialisering."""
        self.quality_score = self._calculate_quality_score()
    
    def _calculate_quality_score(self) -> float:
        """
        Beräkna en quality score (0-100) baserat på fundamentals.
        
        Scoring:
        - P/E < 15: +20, P/E 15-25: +10, P/E > 25: +0
        - P/B < 1.5: +15, P/B 1.5-3: +10, P/B > 3: +0
        - Dividend yield > 3%: +15, 2-3%: +10, < 2%: +5
        - Profit margin > 15%: +20, 10-15%: +15, 5-10%: +10, < 5%: +0
        - ROE > 15%: +15, 10-15%: +10, < 10%: +0
        - Revenue growth > 10%: +15, 5-10%: +10, < 5%: +0
        """
        score = 0.0
        components = 0
        
        # P/E ratio (lower is better)
        if self.pe_ratio is not None and self.pe_ratio > 0:
            if self.pe_ratio < 15:
                score += 20
            elif self.pe_ratio < 25:
                score += 10
            components += 1
        
        # P/B ratio (lower is better)
        if self.pb_ratio is not None and self.pb_ratio > 0:
            if self.pb_ratio < 1.5:
                score += 15
            elif self.pb_ratio < 3:
                score += 10
            components += 1
        
        # Dividend yield (higher is better)
        if self.dividend_yield is not None:
            if self.dividend_yield > 0.03:
                score += 15
            elif self.dividend_yield > 0.02:
                score += 10
            elif self.dividend_yield > 0:
                score += 5
            components += 1
        
        # Profit margin (higher is better)
        if self.profit_margin is not None:
            if self.profit_margin > 0.15:
                score += 20
            elif self.profit_margin > 0.10:
                score += 15
            elif self.profit_margin > 0.05:
                score += 10
            components += 1
        
        # ROE (higher is better)
        if self.roe is not None:
            if self.roe > 0.15:
                score += 15
            elif self.roe > 0.10:
                score += 10
            components += 1
        
        # Revenue growth (higher is better)
        if self.revenue_growth is not None:
            if self.revenue_growth > 0.10:
                score += 15
            elif self.revenue_growth > 0.05:
                score += 10
            components += 1
        
        # Normalisera till 0-100 baserat på antal tillgängliga komponenter
        if components > 0:
            max_possible = {
                1: 20, 2: 35, 3: 50, 4: 70, 5: 85, 6: 100
            }.get(components, 100)
            return min(100, (score / max_possible) * 100)
        
        return 0.0


class FundamentalDataFetcher:
    """Hämtar fundamentaldata från Yahoo Finance."""
    
    def __init__(self):
        self.cache = {}
    
    def fetch(self, ticker: str) -> Optional[FundamentalData]:
        """
        Hämta fundamentaldata för en ticker.
        
        Args:
            ticker: Ticker symbol (e.g., "AAPL", "VOLV-B.ST")
            
        Returns:
            FundamentalData object eller None om data inte tillgänglig
        """
        # Check cache
        if ticker in self.cache:
            return self.cache[ticker]
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extrahera data (med fallback till None)
            data = FundamentalData(
                ticker=ticker,
                pe_ratio=self._safe_get(info, 'trailingPE', 'forwardPE'),
                pb_ratio=self._safe_get(info, 'priceToBook'),
                ps_ratio=self._safe_get(info, 'priceToSalesTrailing12Months'),
                dividend_yield=self._safe_get(info, 'dividendYield'),
                payout_ratio=self._safe_get(info, 'payoutRatio'),
                market_cap=self._safe_get(info, 'marketCap'),
                enterprise_value=self._safe_get(info, 'enterpriseValue'),
                profit_margin=self._safe_get(info, 'profitMargins'),
                roe=self._safe_get(info, 'returnOnEquity'),
                revenue_growth=self._safe_get(info, 'revenueGrowth'),
                earnings_growth=self._safe_get(info, 'earningsGrowth')
            )
            
            # Cache result
            self.cache[ticker] = data
            return data
            
        except Exception as e:
            print(f"  ⚠️ Kunde inte hämta fundamentals för {ticker}: {e}")
            return None
    
    def _safe_get(self, info: dict, *keys):
        """Försök hämta värde från flera möjliga nycklar."""
        for key in keys:
            value = info.get(key)
            if value is not None and value != 'N/A':
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def apply_fundamental_filters(
        self, 
        data: FundamentalData,
        max_pe: float = 30,
        min_dividend_yield: float = 0.0,
        min_market_cap: float = 0
    ) -> bool:
        """
        Applicera fundamental filters.
        
        Args:
            data: FundamentalData objekt
            max_pe: Max P/E ratio (None = ingen filter)
            min_dividend_yield: Min dividend yield (None = ingen filter)
            min_market_cap: Min market cap i USD (None = ingen filter)
            
        Returns:
            True om instrumentet passerar alla filter
        """
        # P/E filter
        if max_pe is not None and data.pe_ratio is not None:
            if data.pe_ratio > max_pe or data.pe_ratio < 0:
                return False
        
        # Dividend yield filter
        if min_dividend_yield is not None and data.dividend_yield is not None:
            if data.dividend_yield < min_dividend_yield:
                return False
        
        # Market cap filter
        if min_market_cap is not None and data.market_cap is not None:
            if data.market_cap < min_market_cap:
                return False
        
        return True
    
    def get_quality_category(self, quality_score: float) -> str:
        """Kategorisera quality score."""
        if quality_score >= 75:
            return "HIGH QUALITY"
        elif quality_score >= 50:
            return "MEDIUM QUALITY"
        elif quality_score >= 25:
            return "LOW QUALITY"
        else:
            return "POOR QUALITY"


def format_fundamental_report(data: FundamentalData) -> str:
    """Formatera fundamentaldata för display."""
    lines = []
    lines.append(f"FUNDAMENTALS - {data.ticker}")
    lines.append("-" * 60)
    
    # Valuation
    lines.append("\nVALUATION:")
    if data.pe_ratio:
        lines.append(f"  P/E Ratio:        {data.pe_ratio:>10.2f}")
    if data.pb_ratio:
        lines.append(f"  P/B Ratio:        {data.pb_ratio:>10.2f}")
    if data.ps_ratio:
        lines.append(f"  P/S Ratio:        {data.ps_ratio:>10.2f}")
    
    # Dividend
    lines.append("\nDIVIDEND:")
    if data.dividend_yield:
        lines.append(f"  Yield:            {data.dividend_yield*100:>10.2f}%")
    if data.payout_ratio:
        lines.append(f"  Payout Ratio:     {data.payout_ratio*100:>10.2f}%")
    
    # Size
    lines.append("\nSIZE:")
    if data.market_cap:
        lines.append(f"  Market Cap:       ${data.market_cap/1e9:>10.2f}B")
    if data.enterprise_value:
        lines.append(f"  Enterprise Value: ${data.enterprise_value/1e9:>10.2f}B")
    
    # Profitability
    lines.append("\nPROFITABILITY:")
    if data.profit_margin:
        lines.append(f"  Profit Margin:    {data.profit_margin*100:>10.2f}%")
    if data.roe:
        lines.append(f"  ROE:              {data.roe*100:>10.2f}%")
    
    # Growth
    lines.append("\nGROWTH:")
    if data.revenue_growth:
        lines.append(f"  Revenue Growth:   {data.revenue_growth*100:>10.2f}%")
    if data.earnings_growth:
        lines.append(f"  Earnings Growth:  {data.earnings_growth*100:>10.2f}%")
    
    # Quality score
    if data.quality_score is not None:
        fetcher = FundamentalDataFetcher()
        category = fetcher.get_quality_category(data.quality_score)
        lines.append("\nQUALITY SCORE:")
        lines.append(f"  Score:            {data.quality_score:>10.1f}/100")
        lines.append(f"  Category:         {category}")
    
    return "\n".join(lines)


# Test function
if __name__ == "__main__":
    fetcher = FundamentalDataFetcher()
    
    # Test med några ticker
    test_tickers = ["AAPL", "MSFT", "VOLV-B.ST"]
    
    for ticker in test_tickers:
        print(f"\n{'='*60}")
        data = fetcher.fetch(ticker)
        if data:
            print(format_fundamental_report(data))
        else:
            print(f"Kunde inte hämta data för {ticker}")
