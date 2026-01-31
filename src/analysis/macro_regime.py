"""
Global Macro Regime Analyzer - The 'Wind' Filter

Determines market regime (AGGRESSIVE vs DEFENSIVE) based on:
1. S&P 500 vs 200-day EMA
2. US 10Y Yield trend (3-week)
3. USD/SEK positioning

Regime affects position sizing:
- AGGRESSIVE: Normal position sizes (100%)
- DEFENSIVE: Reduced position sizes (50%)
"""

from dataclasses import dataclass
from typing import Optional
import yfinance as yf
import pandas as pd
import numpy as np
from enum import Enum


class MarketRegime(Enum):
    """Market regime classification"""
    AGGRESSIVE = "AGGRESSIVE"
    DEFENSIVE = "DEFENSIVE"
    UNKNOWN = "UNKNOWN"


@dataclass
class MacroRegimeAnalysis:
    """Results of macro regime analysis"""
    regime: MarketRegime
    position_size_multiplier: float  # 1.0 for AGGRESSIVE, 0.5 for DEFENSIVE
    
    # S&P 500 metrics
    sp500_price: float
    sp500_ema200: float
    sp500_above_ema: bool
    sp500_distance_pct: float  # % above/below EMA
    
    # US 10Y Yield metrics
    us10y_current: float
    us10y_3w_ago: float
    us10y_trend: str  # "Rising", "Falling", "Flat"
    us10y_change_bps: float  # Change in basis points
    
    # USD/SEK metrics
    usdsek_current: float
    usdsek_zscore: float
    
    # Decision factors
    defensive_signals: list  # List of reasons for defensive regime
    
    @property
    def recommendation(self) -> str:
        """Get trading recommendation based on regime"""
        if self.regime == MarketRegime.AGGRESSIVE:
            return "Full position sizing (100%). Market conditions favorable."
        elif self.regime == MarketRegime.DEFENSIVE:
            return f"Reduced position sizing (50%). Reasons: {', '.join(self.defensive_signals)}"
        else:
            return "Cannot determine regime - insufficient data"


class MacroRegimeAnalyzer:
    """
    Analyzes global macro conditions to determine trading regime
    """
    
    # Thresholds
    YIELD_RISING_THRESHOLD_BPS = 30  # 30 basis points rise = defensive
    
    def __init__(self):
        pass
    
    def analyze_regime(self) -> MacroRegimeAnalysis:
        """
        Analyze current macro regime
        
        Returns:
            MacroRegimeAnalysis with regime classification and metrics
        """
        
        # Initialize defensive signals list
        defensive_signals = []
        
        # 1. Analyze S&P 500
        sp500_price, sp500_ema200, sp500_above_ema, sp500_distance = self._analyze_sp500()
        
        if not sp500_above_ema:
            defensive_signals.append("S&P 500 below 200-day EMA")
        
        # 2. Analyze US 10Y Yield
        us10y_current, us10y_3w_ago, us10y_trend, us10y_change_bps = self._analyze_us10y()
        
        if us10y_trend == "Rising" and us10y_change_bps > self.YIELD_RISING_THRESHOLD_BPS:
            defensive_signals.append(f"10Y yield rising sharply (+{us10y_change_bps:.0f} bps)")
        
        # 3. Analyze USD/SEK
        usdsek_current, usdsek_zscore = self._analyze_usdsek()
        
        # Determine regime
        if len(defensive_signals) > 0:
            regime = MarketRegime.DEFENSIVE
            position_multiplier = 0.5  # Half size
        else:
            regime = MarketRegime.AGGRESSIVE
            position_multiplier = 1.0  # Full size
        
        return MacroRegimeAnalysis(
            regime=regime,
            position_size_multiplier=position_multiplier,
            sp500_price=sp500_price,
            sp500_ema200=sp500_ema200,
            sp500_above_ema=sp500_above_ema,
            sp500_distance_pct=sp500_distance,
            us10y_current=us10y_current,
            us10y_3w_ago=us10y_3w_ago,
            us10y_trend=us10y_trend,
            us10y_change_bps=us10y_change_bps,
            usdsek_current=usdsek_current,
            usdsek_zscore=usdsek_zscore,
            defensive_signals=defensive_signals
        )
    
    def _analyze_sp500(self) -> tuple[float, float, bool, float]:
        """
        Analyze S&P 500 position relative to 200-day EMA
        
        Returns:
            (current_price, ema200, above_ema, distance_pct)
        """
        try:
            sp500 = yf.Ticker("^GSPC")
            hist = sp500.history(period="1y")  # Need 1 year for 200-day EMA
            
            if hist.empty or len(hist) < 200:
                return 0.0, 0.0, True, 0.0  # Default to neutral
            
            # Calculate 200-day EMA
            ema200 = hist['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
            current_price = hist['Close'].iloc[-1]
            
            above_ema = current_price > ema200
            distance_pct = ((current_price / ema200) - 1) * 100
            
            return current_price, ema200, above_ema, distance_pct
        
        except Exception as e:
            print(f"   ⚠️ S&P 500 analysis failed: {e}")
            return 0.0, 0.0, True, 0.0
    
    def _analyze_us10y(self) -> tuple[float, float, str, float]:
        """
        Analyze US 10Y Treasury yield trend
        
        Returns:
            (current_yield, yield_3w_ago, trend, change_bps)
        """
        try:
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="3mo")  # Need 3 months for 3-week comparison
            
            if hist.empty or len(hist) < 15:
                return 0.0, 0.0, "Flat", 0.0
            
            # Current yield
            current_yield = hist['Close'].iloc[-1]
            
            # 3 weeks ago (approximately 15 trading days)
            if len(hist) >= 15:
                yield_3w_ago = hist['Close'].iloc[-15]
            else:
                yield_3w_ago = hist['Close'].iloc[0]
            
            # Calculate change in basis points
            change_bps = (current_yield - yield_3w_ago) * 100
            
            # Determine trend
            if change_bps > 10:  # Rising if > 10 bps
                trend = "Rising"
            elif change_bps < -10:  # Falling if < -10 bps
                trend = "Falling"
            else:
                trend = "Flat"
            
            return current_yield, yield_3w_ago, trend, change_bps
        
        except Exception as e:
            print(f"   ⚠️ US 10Y analysis failed: {e}")
            return 0.0, 0.0, "Flat", 0.0
    
    def _analyze_usdsek(self) -> tuple[float, float]:
        """
        Analyze USD/SEK positioning
        
        Returns:
            (current_rate, zscore)
        """
        try:
            usdsek = yf.Ticker("USDSEK=X")
            hist = usdsek.history(period="1y")
            
            if hist.empty or len(hist) < 200:
                return 0.0, 0.0
            
            current_rate = hist['Close'].iloc[-1]
            
            # Calculate 200-day mean and std
            mean_200d = hist['Close'].rolling(200).mean().iloc[-1]
            std_200d = hist['Close'].rolling(200).std().iloc[-1]
            
            if std_200d > 0:
                zscore = (current_rate - mean_200d) / std_200d
            else:
                zscore = 0.0
            
            return current_rate, zscore
        
        except Exception as e:
            print(f"   ⚠️ USD/SEK analysis failed: {e}")
            return 0.0, 0.0


def format_regime_summary(analysis: MacroRegimeAnalysis) -> str:
    """
    Format regime analysis into readable summary
    
    Args:
        analysis: MacroRegimeAnalysis object
    
    Returns:
        Multi-line string summary
    """
    summary = []
    summary.append(f"MARKET REGIME: {analysis.regime.value}")
    summary.append(f"Position Size Multiplier: {analysis.position_size_multiplier:.0%}")
    summary.append("")
    
    summary.append("S&P 500:")
    summary.append(f"  Current: {analysis.sp500_price:.2f}")
    summary.append(f"  200-day EMA: {analysis.sp500_ema200:.2f}")
    summary.append(f"  Position: {analysis.sp500_distance_pct:+.2f}% {'above' if analysis.sp500_above_ema else 'below'} EMA")
    status = "✅ Bullish" if analysis.sp500_above_ema else "⚠️ Bearish"
    summary.append(f"  Status: {status}")
    summary.append("")
    
    summary.append("US 10Y Treasury Yield:")
    summary.append(f"  Current: {analysis.us10y_current:.2f}%")
    summary.append(f"  3 weeks ago: {analysis.us10y_3w_ago:.2f}%")
    summary.append(f"  Change: {analysis.us10y_change_bps:+.0f} basis points")
    summary.append(f"  Trend: {analysis.us10y_trend}")
    summary.append("")
    
    summary.append("USD/SEK:")
    summary.append(f"  Current: {analysis.usdsek_current:.4f}")
    summary.append(f"  Z-Score: {analysis.usdsek_zscore:+.2f}")
    summary.append("")
    
    if len(analysis.defensive_signals) > 0:
        summary.append("⚠️ DEFENSIVE SIGNALS:")
        for signal in analysis.defensive_signals:
            summary.append(f"  • {signal}")
    else:
        summary.append("✅ NO DEFENSIVE SIGNALS - AGGRESSIVE REGIME")
    
    summary.append("")
    summary.append(f"RECOMMENDATION: {analysis.recommendation}")
    
    return "\n".join(summary)
