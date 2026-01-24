"""
Earnings Calendar Risk Filter

Flags instruments with upcoming earnings reports as high-risk.
Trading before earnings = high volatility and unpredictable outcomes.

Philosophy:
- Position traders avoid earnings surprises
- 10-day buffer before earnings = safer risk management
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import yfinance as yf


@dataclass
class EarningsRisk:
    """Risk assessment for upcoming earnings."""
    has_upcoming_earnings: bool
    days_until_earnings: Optional[int]
    earnings_date: Optional[datetime]
    risk_level: str  # "SAFE", "WARNING", "HIGH"
    message: str


class EarningsCalendar:
    """
    Check if instrument has upcoming earnings within risk window.
    
    Risk Levels:
    - SAFE: No earnings in next 10 days
    - WARNING: Earnings in 5-10 days
    - HIGH: Earnings in 0-5 days (DO NOT TRADE)
    """
    
    def __init__(self, risk_window_days: int = 10):
        self.risk_window_days = risk_window_days
    
    def check_earnings_risk(
        self,
        ticker: str,
        current_date: Optional[datetime] = None
    ) -> EarningsRisk:
        """
        Check if ticker has earnings coming up within risk window.
        
        Args:
            ticker: Stock ticker symbol
            current_date: Current date (defaults to today)
            
        Returns:
            EarningsRisk with risk assessment
        """
        if current_date is None:
            current_date = datetime.now()
        
        try:
            # Fetch earnings calendar from yfinance
            stock = yf.Ticker(ticker)
            earnings_dates = stock.calendar
            
            if earnings_dates is None or len(earnings_dates) == 0:
                return EarningsRisk(
                    has_upcoming_earnings=False,
                    days_until_earnings=None,
                    earnings_date=None,
                    risk_level="SAFE",
                    message="No earnings data available (proceed with caution)"
                )
            
            # Get next earnings date
            # yfinance calendar returns dict, not DataFrame
            # Try to extract earnings date from various possible formats
            next_earnings = None
            
            if isinstance(earnings_dates, dict):
                # Format 1: dict with 'Earnings Date' key
                if 'Earnings Date' in earnings_dates:
                    dates = earnings_dates['Earnings Date']
                    if isinstance(dates, (list, tuple)) and len(dates) > 0:
                        next_earnings = dates[0]
                    else:
                        next_earnings = dates
            elif hasattr(earnings_dates, 'index') and 'Earnings Date' in earnings_dates.index:
                # Format 2: DataFrame/Series with index
                next_earnings = earnings_dates.loc['Earnings Date'].iloc[0]
            
            # Validate we found a date
            if next_earnings is None:
                return EarningsRisk(
                    has_upcoming_earnings=False,
                    days_until_earnings=None,
                    earnings_date=None,
                    risk_level="SAFE",
                    message="No earnings date found in calendar data"
                )
            
            # Convert to datetime if needed - ensure both are datetime objects
            if isinstance(next_earnings, str):
                next_earnings = datetime.strptime(next_earnings, '%Y-%m-%d')
            elif hasattr(next_earnings, 'to_pydatetime'):
                # Pandas Timestamp
                next_earnings = next_earnings.to_pydatetime()
            elif hasattr(next_earnings, '__class__') and next_earnings.__class__.__name__ == 'date':
                # Convert date to datetime (set time to midnight)
                from datetime import date
                if isinstance(next_earnings, date) and not isinstance(next_earnings, datetime):
                    next_earnings = datetime.combine(next_earnings, datetime.min.time())
            
            # Ensure current_date is also datetime (not just date)
            if hasattr(current_date, '__class__') and current_date.__class__.__name__ == 'date':
                from datetime import date
                if isinstance(current_date, date) and not isinstance(current_date, datetime):
                    current_date = datetime.combine(current_date, datetime.min.time())
            
            # Calculate days until earnings
            days_until = (next_earnings - current_date).days
            
            # Assess risk level
            if days_until < 0:
                # Earnings already happened
                return EarningsRisk(
                    has_upcoming_earnings=False,
                    days_until_earnings=None,
                    earnings_date=None,
                    risk_level="SAFE",
                    message="Last earnings already reported"
                )
            elif days_until <= 5:
                return EarningsRisk(
                    has_upcoming_earnings=True,
                    days_until_earnings=days_until,
                    earnings_date=next_earnings,
                    risk_level="HIGH",
                    message=f"⚠️ EARNINGS IN {days_until} DAYS - DO NOT TRADE"
                )
            elif days_until <= self.risk_window_days:
                return EarningsRisk(
                    has_upcoming_earnings=True,
                    days_until_earnings=days_until,
                    earnings_date=next_earnings,
                    risk_level="WARNING",
                    message=f"⚠️ Earnings in {days_until} days - High risk window"
                )
            else:
                return EarningsRisk(
                    has_upcoming_earnings=True,
                    days_until_earnings=days_until,
                    earnings_date=next_earnings,
                    risk_level="SAFE",
                    message=f"Earnings in {days_until} days (safe window)"
                )
                
        except Exception as e:
            # Failed to fetch earnings (network error, API limit, etc.)
            return EarningsRisk(
                has_upcoming_earnings=False,
                days_until_earnings=None,
                earnings_date=None,
                risk_level="WARNING",
                message=f"Could not fetch earnings data: {str(e)}"
            )
    
    def is_safe_to_trade(self, ticker: str) -> bool:
        """
        Quick check: Is it safe to trade this ticker?
        
        Returns:
            False if HIGH risk (earnings in 0-5 days), True otherwise
        """
        risk = self.check_earnings_risk(ticker)
        return risk.risk_level != "HIGH"
