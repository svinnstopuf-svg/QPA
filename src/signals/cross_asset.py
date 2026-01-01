"""
Cross-Asset Signal Generator

Renaissance principle: Markets are interconnected.
Use rates, FX, commodities to predict equity moves.
"""

import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from ..utils.market_data import MarketData


@dataclass
class CrossAssetSignal:
    """Signal from cross-asset relationship."""
    primary_asset: str
    related_asset: str
    signal_type: str  # 'lead_lag', 'divergence', 'correlation_break'
    strength: float  # 0-1
    lag_days: int
    correlation: float
    description: str
    actionable: bool


class CrossAssetSignalGenerator:
    """
    Generates signals from cross-asset relationships.
    
    Relationships:
    1. S&P 500 leads OMXS30 (US market → Europe)
    2. VIX predicts equity reversals
    3. 10Y yields → growth vs value rotation
    4. USD/SEK → OMXS30 (currency effects)
    5. Oil prices → energy sector
    6. Gold → risk-off/risk-on
    """
    
    def __init__(self, lookback_period: str = "5y"):
        """
        Initialize cross-asset signal generator.
        
        Args:
            lookback_period: Period for correlation analysis
        """
        self.lookback_period = lookback_period
        self.asset_cache = {}
    
    def fetch_asset(self, ticker: str) -> Optional[np.ndarray]:
        """Fetch asset data and cache it."""
        if ticker in self.asset_cache:
            return self.asset_cache[ticker]
        
        try:
            data = yf.download(ticker, period=self.lookback_period, progress=False)
            if data is not None and not data.empty:
                returns = data['Close'].pct_change().dropna().values
                self.asset_cache[ticker] = returns
                return returns
        except:
            return None
        
        return None
    
    def detect_lead_lag(
        self,
        leader_ticker: str,
        follower_ticker: str,
        max_lag: int = 5
    ) -> Optional[CrossAssetSignal]:
        """
        Detect if one asset leads another.
        
        Args:
            leader_ticker: Ticker that might lead
            follower_ticker: Ticker that might follow
            max_lag: Maximum lag to test (days)
            
        Returns:
            CrossAssetSignal if lead-lag found
        """
        leader = self.fetch_asset(leader_ticker)
        follower = self.fetch_asset(follower_ticker)
        
        if leader is None or follower is None:
            return None
        
        # Align lengths
        min_len = min(len(leader), len(follower))
        leader = leader[-min_len:]
        follower = follower[-min_len:]
        
        best_lag = 0
        best_corr = 0.0
        
        for lag in range(1, max_lag + 1):
            if lag >= len(leader):
                break
            
            # Test if leader[t] correlates with follower[t+lag]
            corr = np.corrcoef(leader[:-lag], follower[lag:])[0, 1]
            
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
        
        # Only signal if correlation is significant (>0.3)
        if abs(best_corr) > 0.3 and best_lag > 0:
            return CrossAssetSignal(
                primary_asset=follower_ticker,
                related_asset=leader_ticker,
                signal_type='lead_lag',
                strength=abs(best_corr),
                lag_days=best_lag,
                correlation=best_corr,
                description=f"{leader_ticker} leads {follower_ticker} by {best_lag} days (r={best_corr:.2f})",
                actionable=True
            )
        
        return None
    
    def detect_vix_equity_signal(
        self,
        equity_ticker: str
    ) -> Optional[CrossAssetSignal]:
        """
        VIX spike → mean reversion in equities.
        
        Args:
            equity_ticker: Equity to analyze
            
        Returns:
            Signal if VIX pattern detected
        """
        vix = self.fetch_asset("^VIX")
        equity = self.fetch_asset(equity_ticker)
        
        if vix is None or equity is None:
            return None
        
        # Get current VIX level (last 20 days avg)
        recent_vix = vix[-20:].mean() if len(vix) >= 20 else vix.mean()
        historical_vix = vix.mean()
        
        # VIX spike = > 1.5x historical average
        if recent_vix > historical_vix * 1.5:
            # Check correlation between VIX spikes and equity reversals
            # (Simplified - in production, track actual reversals)
            return CrossAssetSignal(
                primary_asset=equity_ticker,
                related_asset="VIX",
                signal_type='divergence',
                strength=0.7,
                lag_days=1,
                correlation=-0.8,  # VIX negatively correlated with equities
                description=f"VIX spike detected ({recent_vix:.1f} vs {historical_vix:.1f} avg) → potential {equity_ticker} reversal",
                actionable=True
            )
        
        return None
    
    def detect_yield_rotation(
        self,
        equity_ticker: str
    ) -> Optional[CrossAssetSignal]:
        """
        10Y yield changes → growth/value rotation.
        
        Args:
            equity_ticker: Equity to analyze
            
        Returns:
            Signal if yield pattern detected
        """
        yields = self.fetch_asset("^TNX")  # 10-year treasury
        
        if yields is None:
            return None
        
        # Yield trend (last 60 days)
        if len(yields) < 60:
            return None
        
        recent_yield_change = yields[-60:].sum()  # Cumulative change
        
        # Rising yields (>5% cumulative) → value rotation
        if recent_yield_change > 0.05:
            return CrossAssetSignal(
                primary_asset=equity_ticker,
                related_asset="^TNX",
                signal_type='correlation_break',
                strength=0.6,
                lag_days=0,
                correlation=0.4,
                description=f"Rising yields (+{recent_yield_change*100:.1f}%) → favor value over growth",
                actionable=True
            )
        
        # Falling yields → growth rotation
        elif recent_yield_change < -0.05:
            return CrossAssetSignal(
                primary_asset=equity_ticker,
                related_asset="^TNX",
                signal_type='correlation_break',
                strength=0.6,
                lag_days=0,
                correlation=0.4,
                description=f"Falling yields ({recent_yield_change*100:.1f}%) → favor growth over value",
                actionable=True
            )
        
        return None
    
    def detect_currency_effect(
        self,
        equity_ticker: str,
        currency_pair: str = "SEK=X"  # USD/SEK
    ) -> Optional[CrossAssetSignal]:
        """
        Currency moves affect international equities.
        
        Args:
            equity_ticker: Equity ticker
            currency_pair: Currency pair (default USD/SEK for OMXS30)
            
        Returns:
            Signal if currency effect detected
        """
        fx = self.fetch_asset(currency_pair)
        equity = self.fetch_asset(equity_ticker)
        
        if fx is None or equity is None:
            return None
        
        # Align
        min_len = min(len(fx), len(equity))
        fx = fx[-min_len:]
        equity = equity[-min_len:]
        
        # Correlation
        corr = np.corrcoef(fx, equity)[0, 1]
        
        # If strong correlation, currency moves predict equity moves
        if abs(corr) > 0.3:
            return CrossAssetSignal(
                primary_asset=equity_ticker,
                related_asset=currency_pair,
                signal_type='correlation_break',
                strength=abs(corr),
                lag_days=0,
                correlation=corr,
                description=f"{currency_pair} affects {equity_ticker} (r={corr:.2f})",
                actionable=True if abs(corr) > 0.5 else False
            )
        
        return None
    
    def generate_all_signals(
        self,
        primary_ticker: str
    ) -> List[CrossAssetSignal]:
        """
        Generate all cross-asset signals for a ticker.
        
        Args:
            primary_ticker: Primary ticker to analyze
            
        Returns:
            List of all detected signals
        """
        signals = []
        
        # 1. Lead-lag from major indices
        major_indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P, Dow, Nasdaq
        for leader in major_indices:
            if leader != primary_ticker:
                sig = self.detect_lead_lag(leader, primary_ticker, max_lag=5)
                if sig:
                    signals.append(sig)
        
        # 2. VIX equity signal
        vix_sig = self.detect_vix_equity_signal(primary_ticker)
        if vix_sig:
            signals.append(vix_sig)
        
        # 3. Yield rotation
        yield_sig = self.detect_yield_rotation(primary_ticker)
        if yield_sig:
            signals.append(yield_sig)
        
        # 4. Currency effect (for non-USD assets)
        if "OMX" in primary_ticker or primary_ticker.endswith(".ST"):
            fx_sig = self.detect_currency_effect(primary_ticker, "SEK=X")
            if fx_sig:
                signals.append(fx_sig)
        
        return signals
    
    def create_signal_report(
        self,
        signals: List[CrossAssetSignal],
        ticker: str
    ) -> str:
        """Create report for cross-asset signals."""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append(f"CROSS-ASSET SIGNALS: {ticker}")
        lines.append("=" * 80)
        
        if not signals:
            lines.append("\n❌ No cross-asset signals detected.")
            return "\n".join(lines)
        
        actionable = [s for s in signals if s.actionable]
        
        lines.append(f"\nTotal signals: {len(signals)}")
        lines.append(f"Actionable signals: {len(actionable)}")
        lines.append("")
        
        for i, sig in enumerate(signals, 1):
            icon = "✅" if sig.actionable else "📊"
            lines.append(f"{icon} {i}. {sig.description}")
            lines.append(f"    Type: {sig.signal_type}")
            lines.append(f"    Strength: {sig.strength:.2f}")
            if sig.lag_days > 0:
                lines.append(f"    Lag: {sig.lag_days} days")
            lines.append(f"    Correlation: {sig.correlation:+.2f}")
        
        lines.append("")
        lines.append("⚠️ Renaissance principle: Use cross-asset signals as confirmation.")
        lines.append("⚠️ Never trade solely on cross-asset correlations.")
        
        return "\n".join(lines)
