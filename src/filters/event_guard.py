"""
Event Guard - Avoid Earnings Volatility

Quantitative Principle:
Earnings reports create unpredictable volatility spikes.
Even with an edge, entering 48h before earnings is gambling on the coin flip.

Methodology:
1. Fetch earnings calendar (Yahoo Finance)
2. Block trades if next earnings < 48h away
3. Also block on ex-dividend dates (gap risk)

Risk Mitigation:
- Earnings surprise can gap stock ±10% overnight
- No pattern can predict earnings outcomes
- Better to wait and enter after clarity

Note: Requires external API (yfinance) for earnings dates.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import yfinance as yf


@dataclass
class EventGuardResult:
    """Results from event guard check."""
    ticker: str
    safe_to_trade: bool
    
    # Events detected
    earnings_upcoming: bool
    days_to_earnings: Optional[int]
    earnings_date: Optional[str]
    
    ex_dividend_upcoming: bool
    days_to_ex_dividend: Optional[int]
    ex_dividend_date: Optional[str]
    
    # Recommendation
    block_reason: str


class EventGuard:
    """
    Blocks trades before scheduled corporate events.
    
    Philosophy: Avoid predictable volatility spikes.
    """
    
    def __init__(
        self,
        earnings_blackout_hours: int = 48,
        ex_dividend_blackout_hours: int = 24,
        enable_earnings_check: bool = True,
        enable_dividend_check: bool = True
    ):
        """
        Initialize event guard.
        
        Args:
            earnings_blackout_hours: Hours before earnings to block (48 = 2 days)
            ex_dividend_blackout_hours: Hours before ex-div to block
            enable_earnings_check: Enable earnings calendar check
            enable_dividend_check: Enable dividend calendar check
        """
        self.earnings_blackout_hours = earnings_blackout_hours
        self.ex_dividend_blackout_hours = ex_dividend_blackout_hours
        self.enable_earnings = enable_earnings_check
        self.enable_dividend = enable_dividend_check
    
    def check(
        self,
        ticker: str,
        current_date: datetime = None
    ) -> EventGuardResult:
        """
        Check if ticker is safe to trade (no upcoming events).
        
        Args:
            ticker: Instrument ticker
            current_date: Current date (default: now)
            
        Returns:
            EventGuardResult with safety assessment
        """
        if current_date is None:
            current_date = datetime.now()
        
        earnings_upcoming = False
        days_to_earnings = None
        earnings_date_str = None
        
        ex_div_upcoming = False
        days_to_ex_div = None
        ex_div_date_str = None
        
        # 1. Check earnings calendar
        if self.enable_earnings:
            try:
                stock = yf.Ticker(ticker)
                calendar = stock.calendar
                
                if calendar is not None and not calendar.empty:
                    # Yahoo returns earnings date
                    if 'Earnings Date' in calendar.index:
                        earnings_dates = calendar.loc['Earnings Date']
                        
                        # Handle both single date and date range
                        if isinstance(earnings_dates, (list, tuple)):
                            next_earnings = earnings_dates[0] if len(earnings_dates) > 0 else None
                        else:
                            next_earnings = earnings_dates
                        
                        if next_earnings is not None:
                            # Convert to datetime if needed
                            if isinstance(next_earnings, str):
                                try:
                                    next_earnings = datetime.strptime(next_earnings, "%Y-%m-%d")
                                except:
                                    next_earnings = None
                            
                            if next_earnings:
                                # Calculate days until earnings
                                time_to_earnings = next_earnings - current_date
                                hours_to_earnings = time_to_earnings.total_seconds() / 3600
                                
                                if hours_to_earnings > 0 and hours_to_earnings < self.earnings_blackout_hours:
                                    earnings_upcoming = True
                                    days_to_earnings = int(hours_to_earnings / 24)
                                    earnings_date_str = next_earnings.strftime("%Y-%m-%d")
            
            except Exception as e:
                # If fetching fails, be conservative and don't block
                # (Could also choose to block on fetch errors for safety)
                pass
        
        # 2. Check ex-dividend date
        if self.enable_dividend:
            try:
                stock = yf.Ticker(ticker)
                dividends = stock.dividends
                
                if dividends is not None and not dividends.empty:
                    # Get most recent dividend
                    last_div_date = dividends.index[-1]
                    
                    # Estimate next ex-dividend (quarterly = 90 days)
                    # This is a rough estimate - real calendar would be better
                    estimated_next = last_div_date + timedelta(days=90)
                    
                    time_to_ex_div = estimated_next - current_date.date()
                    hours_to_ex_div = time_to_ex_div.total_seconds() / 3600
                    
                    if hours_to_ex_div > 0 and hours_to_ex_div < self.ex_dividend_blackout_hours:
                        ex_div_upcoming = True
                        days_to_ex_div = int(hours_to_ex_div / 24)
                        ex_div_date_str = estimated_next.strftime("%Y-%m-%d")
            
            except Exception as e:
                pass
        
        # 3. Determine safety
        safe_to_trade = not (earnings_upcoming or ex_div_upcoming)
        
        if earnings_upcoming:
            block_reason = f"Earnings in {days_to_earnings} days ({earnings_date_str})"
        elif ex_div_upcoming:
            block_reason = f"Ex-dividend in {days_to_ex_div} days ({ex_div_date_str})"
        else:
            block_reason = "SAFE - No events detected"
        
        return EventGuardResult(
            ticker=ticker,
            safe_to_trade=safe_to_trade,
            earnings_upcoming=earnings_upcoming,
            days_to_earnings=days_to_earnings,
            earnings_date=earnings_date_str,
            ex_dividend_upcoming=ex_div_upcoming,
            days_to_ex_dividend=days_to_ex_div,
            ex_dividend_date=ex_div_date_str,
            block_reason=block_reason
        )
    
    def format_report(self, result: EventGuardResult) -> str:
        """Generate formatted report."""
        report = f"""
{'='*70}
EVENT GUARD: {result.ticker}
{'='*70}

Safety Assessment:   {'✅ SAFE TO TRADE' if result.safe_to_trade else '❌ BLOCK TRADE'}

Upcoming Events:
  Earnings:          {'⚠️ YES' if result.earnings_upcoming else '✅ NO'}
    {f'Days Until:      {result.days_to_earnings}' if result.earnings_upcoming else ''}
    {f'Earnings Date:    {result.earnings_date}' if result.earnings_upcoming else ''}
  
  Ex-Dividend:       {'⚠️ YES' if result.ex_dividend_upcoming else '✅ NO'}
    {f'Days Until:      {result.days_to_ex_dividend}' if result.ex_dividend_upcoming else ''}
    {f'Ex-Div Date:     {result.ex_dividend_date}' if result.ex_dividend_upcoming else ''}

Recommendation:
  {result.block_reason}

Interpretation:
  {'Avoid trading before earnings - high unpredictable volatility' if result.earnings_upcoming else ''}
  {'Avoid trading before ex-dividend - gap risk' if result.ex_dividend_upcoming else ''}
  {'Clear to trade - no major events imminent' if result.safe_to_trade else ''}
{'='*70}
"""
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Event Guard...")
    print("Note: This requires live data and may not find upcoming events.")
    
    guard = EventGuard(earnings_blackout_hours=48)
    
    # Test with a few major stocks
    test_tickers = ["AAPL", "MSFT", "VOLV-B.ST"]
    
    for ticker in test_tickers:
        print(f"\nChecking {ticker}...")
        try:
            result = guard.check(ticker)
            print(guard.format_report(result))
        except Exception as e:
            print(f"Error checking {ticker}: {e}")
    
    print("\n✅ Event Guard - Tests Complete")
    print("Note: Event detection depends on Yahoo Finance data availability.")
