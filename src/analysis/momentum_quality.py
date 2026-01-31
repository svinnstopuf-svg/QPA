"""
Momentum Quality Analyzer

Quality filters specific to momentum trading:
1. Institutional Ownership (>30%)
2. Earnings Growth (accelerating)
3. Float (<500M shares for better volatility)
4. Liquidity (>$10M daily volume)
5. Sector Rotation (leading sectors)
6. Price Strength (above key MAs)

Different from mean reversion quality which focuses on:
- Value metrics (ROE, margins)
- Distressed situations
- Recovery potential
"""

import numpy as np
import yfinance as yf
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class MomentumQuality:
    """Quality assessment for momentum stock"""
    ticker: str
    
    # Institutional metrics
    institutional_ownership_pct: float
    institutional_score: float  # 0-100
    
    # Growth metrics
    earnings_growth_yoy: float
    revenue_growth_yoy: float
    earnings_accelerating: bool
    growth_score: float  # 0-100
    
    # Float/Liquidity
    shares_outstanding: float
    float_shares: float
    avg_daily_volume: float
    avg_daily_dollar_volume: float
    liquidity_score: float  # 0-100
    
    # Price strength
    price_above_ma50: bool
    price_above_ma200: bool
    ma50_above_ma200: bool
    price_strength_score: float  # 0-100
    
    # Sector
    sector: str
    industry: str
    sector_momentum_rank: float  # 0-100
    
    # Overall
    momentum_quality_score: float  # 0-100
    quality_tier: str  # "LEADER", "CONTENDER", "LAGGARD"
    
    warnings: list


class MomentumQualityAnalyzer:
    """
    Analyze fundamental quality for momentum stocks.
    
    Focus on growth, institutional support, and liquidity
    rather than value metrics.
    """
    
    def __init__(
        self,
        min_institutional_ownership: float = 0.30,
        min_daily_dollar_volume: float = 10_000_000,
        max_float: float = 500_000_000
    ):
        self.min_institutional = min_institutional_ownership
        self.min_dollar_volume = min_daily_dollar_volume
        self.max_float = max_float
    
    def analyze_quality(self, ticker: str) -> MomentumQuality:
        """
        Perform complete quality analysis.
        
        Args:
            ticker: Stock ticker
        
        Returns:
            MomentumQuality with assessment
        """
        warnings = []
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Institutional ownership
            inst_own = info.get('heldPercentInstitutions', 0.0)
            inst_score = self._score_institutional(inst_own, warnings)
            
            # Growth metrics
            earnings_growth = info.get('earningsGrowth', 0.0) or 0.0
            revenue_growth = info.get('revenueGrowth', 0.0) or 0.0
            
            # Check if earnings accelerating (need historical data)
            earnings_accelerating = earnings_growth > 0.15  # >15% YoY
            growth_score = self._score_growth(
                earnings_growth, revenue_growth, earnings_accelerating, warnings
            )
            
            # Float and liquidity
            shares_out = info.get('sharesOutstanding', 0)
            float_shares = info.get('floatShares', shares_out)
            avg_volume = info.get('averageVolume', 0)
            current_price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
            
            avg_dollar_volume = avg_volume * current_price
            liquidity_score = self._score_liquidity(
                float_shares, avg_dollar_volume, warnings
            )
            
            # Price strength
            hist = stock.history(period="1y")
            if len(hist) >= 200:
                ma50 = hist['Close'].rolling(50).mean().iloc[-1]
                ma200 = hist['Close'].rolling(200).mean().iloc[-1]
                current = hist['Close'].iloc[-1]
                
                price_above_ma50 = current > ma50
                price_above_ma200 = current > ma200
                ma50_above_ma200 = ma50 > ma200
            else:
                price_above_ma50 = False
                price_above_ma200 = False
                ma50_above_ma200 = False
                warnings.append("Insufficient price history for MA calculation")
            
            price_strength_score = self._score_price_strength(
                price_above_ma50, price_above_ma200, ma50_above_ma200
            )
            
            # Sector
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            sector_momentum_rank = 50.0  # Placeholder (would need sector comparison)
            
            # Overall quality score
            overall_score = (
                inst_score * 0.25 +
                growth_score * 0.30 +
                liquidity_score * 0.20 +
                price_strength_score * 0.25
            )
            
            # Quality tier
            if overall_score >= 75:
                tier = "LEADER"
            elif overall_score >= 50:
                tier = "CONTENDER"
            else:
                tier = "LAGGARD"
            
            return MomentumQuality(
                ticker=ticker,
                institutional_ownership_pct=inst_own,
                institutional_score=inst_score,
                earnings_growth_yoy=earnings_growth,
                revenue_growth_yoy=revenue_growth,
                earnings_accelerating=earnings_accelerating,
                growth_score=growth_score,
                shares_outstanding=shares_out,
                float_shares=float_shares,
                avg_daily_volume=avg_volume,
                avg_daily_dollar_volume=avg_dollar_volume,
                liquidity_score=liquidity_score,
                price_above_ma50=price_above_ma50,
                price_above_ma200=price_above_ma200,
                ma50_above_ma200=ma50_above_ma200,
                price_strength_score=price_strength_score,
                sector=sector,
                industry=industry,
                sector_momentum_rank=sector_momentum_rank,
                momentum_quality_score=overall_score,
                quality_tier=tier,
                warnings=warnings
            )
        
        except Exception as e:
            warnings.append(f"Quality analysis failed: {e}")
            return self._create_empty_quality(ticker, warnings)
    
    def _score_institutional(self, inst_own: float, warnings: list) -> float:
        """
        Score institutional ownership.
        
        Momentum stocks benefit from institutional support.
        Target: 30-80% (too high can mean crowded)
        """
        if inst_own < 0.10:
            warnings.append(f"Very low institutional ownership: {inst_own*100:.1f}%")
            return 20.0
        elif inst_own < 0.30:
            warnings.append(f"Low institutional ownership: {inst_own*100:.1f}%")
            return 50.0
        elif inst_own <= 0.80:
            # Sweet spot
            return 100.0
        else:
            warnings.append(f"Very high institutional ownership: {inst_own*100:.1f}% (crowded?)")
            return 70.0
    
    def _score_growth(
        self,
        earnings_growth: float,
        revenue_growth: float,
        accelerating: bool,
        warnings: list
    ) -> float:
        """
        Score growth metrics.
        
        Momentum thrives on growth acceleration.
        """
        score = 0.0
        
        # Earnings growth
        if earnings_growth < 0:
            warnings.append(f"Negative earnings growth: {earnings_growth*100:.1f}%")
            score += 0
        elif earnings_growth < 0.10:
            score += 40
        elif earnings_growth < 0.25:
            score += 70
        else:
            score += 100
        
        # Revenue growth
        if revenue_growth < 0:
            warnings.append(f"Negative revenue growth")
        elif revenue_growth > 0.15:
            score += 20  # Bonus for strong revenue
        
        # Acceleration bonus
        if accelerating:
            score += 30
        
        return min(100, score)
    
    def _score_liquidity(
        self,
        float_shares: float,
        dollar_volume: float,
        warnings: list
    ) -> float:
        """
        Score float and liquidity.
        
        Momentum needs liquidity but not too much float.
        """
        score = 50.0
        
        # Dollar volume check
        if dollar_volume < 1_000_000:
            warnings.append(f"Very low liquidity: ${dollar_volume/1e6:.1f}M/day")
            score = 10.0
        elif dollar_volume < self.min_dollar_volume:
            warnings.append(f"Low liquidity: ${dollar_volume/1e6:.1f}M/day")
            score = 50.0
        elif dollar_volume > 100_000_000:
            score = 100.0  # Excellent liquidity
        else:
            score = 80.0
        
        # Float check (lower is better for momentum)
        if float_shares > 0:
            if float_shares < 50_000_000:
                score += 20  # Bonus for small float
            elif float_shares > self.max_float:
                warnings.append(f"Large float: {float_shares/1e6:.0f}M shares")
                score -= 20
        
        return max(0, min(100, score))
    
    def _score_price_strength(
        self,
        above_ma50: bool,
        above_ma200: bool,
        ma50_above_ma200: bool
    ) -> float:
        """
        Score price strength relative to moving averages.
        
        Momentum requires strong price action.
        """
        if above_ma50 and above_ma200 and ma50_above_ma200:
            return 100.0  # Perfect alignment
        elif above_ma50 and above_ma200:
            return 80.0  # Good but MA50 might be crossing down
        elif above_ma50:
            return 50.0  # Weak
        else:
            return 20.0  # Not in uptrend
    
    def _create_empty_quality(self, ticker: str, warnings: list) -> MomentumQuality:
        """Create empty quality object on error"""
        return MomentumQuality(
            ticker=ticker,
            institutional_ownership_pct=0.0,
            institutional_score=0.0,
            earnings_growth_yoy=0.0,
            revenue_growth_yoy=0.0,
            earnings_accelerating=False,
            growth_score=0.0,
            shares_outstanding=0,
            float_shares=0,
            avg_daily_volume=0,
            avg_daily_dollar_volume=0.0,
            liquidity_score=0.0,
            price_above_ma50=False,
            price_above_ma200=False,
            ma50_above_ma200=False,
            price_strength_score=0.0,
            sector="Unknown",
            industry="Unknown",
            sector_momentum_rank=0.0,
            momentum_quality_score=0.0,
            quality_tier="UNKNOWN",
            warnings=warnings
        )


def format_momentum_quality(quality: MomentumQuality) -> str:
    """Format momentum quality report"""
    lines = []
    
    lines.append("="*80)
    lines.append(f"MOMENTUM QUALITY: {quality.ticker}")
    lines.append("="*80)
    
    lines.append(f"\nOVERALL: {quality.momentum_quality_score:.0f}/100 - {quality.quality_tier}")
    
    lines.append(f"\nINSTITUTIONAL ({quality.institutional_score:.0f}/100):")
    lines.append(f"  Ownership: {quality.institutional_ownership_pct*100:.1f}%")
    
    lines.append(f"\nGROWTH ({quality.growth_score:.0f}/100):")
    lines.append(f"  Earnings Growth YoY: {quality.earnings_growth_yoy*100:+.1f}%")
    lines.append(f"  Revenue Growth YoY: {quality.revenue_growth_yoy*100:+.1f}%")
    lines.append(f"  Accelerating: {'✓ YES' if quality.earnings_accelerating else '✗ No'}")
    
    lines.append(f"\nLIQUIDITY ({quality.liquidity_score:.0f}/100):")
    lines.append(f"  Float: {quality.float_shares/1e6:.0f}M shares")
    lines.append(f"  Avg Volume: {quality.avg_daily_volume/1e6:.1f}M shares/day")
    lines.append(f"  Dollar Volume: ${quality.avg_daily_dollar_volume/1e6:.1f}M/day")
    
    lines.append(f"\nPRICE STRENGTH ({quality.price_strength_score:.0f}/100):")
    lines.append(f"  Price > MA50: {'✓' if quality.price_above_ma50 else '✗'}")
    lines.append(f"  Price > MA200: {'✓' if quality.price_above_ma200 else '✗'}")
    lines.append(f"  MA50 > MA200: {'✓' if quality.ma50_above_ma200 else '✗'}")
    
    lines.append(f"\nSECTOR:")
    lines.append(f"  {quality.sector} - {quality.industry}")
    
    if quality.warnings:
        lines.append(f"\n⚠️ WARNINGS:")
        for warning in quality.warnings:
            lines.append(f"  - {warning}")
    
    return "\n".join(lines)
