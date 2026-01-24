"""
FX Guard - Currency Impact Warning

Tracks SEK/USD and SEK/EUR rates to warn of FX headwinds.
Critical for non-SEK positions held 21-63 days.
"""

from dataclasses import dataclass
from typing import Optional
import yfinance as yf
from datetime import datetime, timedelta


@dataclass
class FXImpact:
    """FX impact analysis."""
    ticker: str
    currency: str  # "USD", "EUR", "SEK"
    fx_pair: str  # "SEKUSD=X"
    entry_fx_rate: float
    current_fx_rate: float
    fx_change_pct: float
    fx_impact_on_return: float  # How much FX ate into profit
    warning_level: str  # "NONE", "MINOR", "MODERATE", "SEVERE"
    message: str


class FXGuard:
    """
    Monitor currency exposure for non-SEK instruments.
    
    Logic:
    - For US stocks: Track SEK/USD
    - For EU stocks: Track SEK/EUR
    - If SEK strengthens: Profit eaten by FX
    - If SEK weakens: Bonus from FX
    
    Warning Levels:
    - NONE: FX < 2% impact
    - MINOR: 2-5% impact
    - MODERATE: 5-10% impact
    - SEVERE: >10% impact
    """
    
    def __init__(self):
        self.fx_cache = {}  # Cache FX rates
    
    def analyze_fx_impact(
        self,
        ticker: str,
        entry_date: datetime,
        current_date: Optional[datetime] = None,
        predicted_return_pct: float = 0.0
    ) -> FXImpact:
        """
        Analyze FX impact on a position.
        
        Args:
            ticker: Instrument ticker
            entry_date: Date position was opened
            current_date: Current date (default: today)
            predicted_return_pct: Expected return in local currency
            
        Returns:
            FXImpact with warning level
        """
        
        if current_date is None:
            current_date = datetime.now()
        
        # Determine currency
        currency = self._get_currency(ticker)
        
        if currency == "SEK":
            # No FX risk
            return FXImpact(
                ticker=ticker,
                currency="SEK",
                fx_pair="N/A",
                entry_fx_rate=1.0,
                current_fx_rate=1.0,
                fx_change_pct=0.0,
                fx_impact_on_return=0.0,
                warning_level="NONE",
                message="Swedish instrument - no FX risk"
            )
        
        # Get FX pair
        if currency == "USD":
            fx_pair = "SEKUSD=X"
        elif currency == "EUR":
            fx_pair = "SEKEUR=X"
        else:
            # Unknown currency - skip
            return FXImpact(
                ticker=ticker,
                currency=currency,
                fx_pair="N/A",
                entry_fx_rate=0.0,
                current_fx_rate=0.0,
                fx_change_pct=0.0,
                fx_impact_on_return=0.0,
                warning_level="NONE",
                message=f"Currency {currency} not tracked"
            )
        
        # Fetch FX rates
        try:
            entry_fx_rate = self._get_fx_rate(fx_pair, entry_date)
            current_fx_rate = self._get_fx_rate(fx_pair, current_date)
        except Exception as e:
            return FXImpact(
                ticker=ticker,
                currency=currency,
                fx_pair=fx_pair,
                entry_fx_rate=0.0,
                current_fx_rate=0.0,
                fx_change_pct=0.0,
                fx_impact_on_return=0.0,
                warning_level="NONE",
                message=f"Could not fetch FX data: {e}"
            )
        
        # Calculate FX change
        fx_change_pct = (current_fx_rate - entry_fx_rate) / entry_fx_rate
        
        # FX impact on return
        # If SEK strengthens (fx_change > 0): You lose
        # If SEK weakens (fx_change < 0): You gain
        fx_impact_on_return = -fx_change_pct  # Inverted
        
        # Determine warning level
        abs_impact = abs(fx_impact_on_return)
        
        if abs_impact < 0.02:
            warning_level = "NONE"
            message = f"FX impact negligible ({fx_impact_on_return*100:+.1f}%)"
        elif abs_impact < 0.05:
            warning_level = "MINOR"
            if fx_impact_on_return < 0:
                message = f"SEK stronger - eating {abs(fx_impact_on_return)*100:.1f}% of profit"
            else:
                message = f"SEK weaker - FX bonus {abs(fx_impact_on_return)*100:.1f}%"
        elif abs_impact < 0.10:
            warning_level = "MODERATE"
            if fx_impact_on_return < 0:
                message = f"⚠️ SEK much stronger - {abs(fx_impact_on_return)*100:.1f}% FX loss"
            else:
                message = f"💰 SEK much weaker - {abs(fx_impact_on_return)*100:.1f}% FX gain"
        else:
            warning_level = "SEVERE"
            if fx_impact_on_return < 0:
                message = f"🚨 SEVERE FX HEADWIND - {abs(fx_impact_on_return)*100:.1f}% loss from currency"
            else:
                message = f"💎 SEVERE FX TAILWIND - {abs(fx_impact_on_return)*100:.1f}% gain from currency"
        
        return FXImpact(
            ticker=ticker,
            currency=currency,
            fx_pair=fx_pair,
            entry_fx_rate=entry_fx_rate,
            current_fx_rate=current_fx_rate,
            fx_change_pct=fx_change_pct,
            fx_impact_on_return=fx_impact_on_return,
            warning_level=warning_level,
            message=message
        )
    
    def _get_currency(self, ticker: str) -> str:
        """Determine currency from ticker."""
        if ticker.endswith('.ST'):
            return "SEK"
        elif ticker.endswith('.OL') or ticker.endswith('.CO'):
            return "EUR"
        else:
            # Assume US for everything else
            return "USD"
    
    def _get_fx_rate(self, fx_pair: str, date: datetime) -> float:
        """Fetch FX rate for a specific date."""
        
        # Check cache
        cache_key = f"{fx_pair}_{date.strftime('%Y-%m-%d')}"
        if cache_key in self.fx_cache:
            return self.fx_cache[cache_key]
        
        # Fetch from Yahoo Finance
        try:
            # Get data for date +/- 5 days (in case of holidays)
            start_date = date - timedelta(days=5)
            end_date = date + timedelta(days=5)
            
            fx_data = yf.download(
                fx_pair,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                progress=False
            )
            
            if len(fx_data) == 0:
                raise ValueError("No FX data available")
            
            # Get closest date
            fx_rate = float(fx_data['Close'].iloc[-1])
            
            # Cache it
            self.fx_cache[cache_key] = fx_rate
            
            return fx_rate
        
        except Exception as e:
            raise ValueError(f"Failed to fetch FX rate: {e}")
