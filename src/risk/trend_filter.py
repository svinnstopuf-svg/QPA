"""
Trend Filter - Multi-Timeframe Confirmation

Prevents "catching a falling knife" by ensuring price > 200-day MA.
A pattern can look GREEN short-term but be in a bearish long-term trend.

Philosophy:
- Only invest in GREEN/YELLOW if instrument is above 200-day SMA
- Protects against bull-market patterns in bear-market conditions
- Regime-aware: Different strategies for different market phases
"""

import numpy as np
from typing import Tuple, Dict
from dataclasses import dataclass
from enum import Enum


class TrendRegime(Enum):
    """Long-term trend regimes."""
    STRONG_UPTREND = "STRONG_UPTREND"  # Price >10% above 200 MA
    UPTREND = "UPTREND"  # Price >0% above 200 MA
    DOWNTREND = "DOWNTREND"  # Price <0% below 200 MA
    STRONG_DOWNTREND = "STRONG_DOWNTREND"  # Price >10% below 200 MA


@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    price: float
    ma_200: float
    ma_50: float = 0.0  # V3.0: For trend elasticity
    distance_from_ma: float = 0.0  # % above/below MA
    regime: TrendRegime = TrendRegime.DOWNTREND
    allow_long: bool = False  # Whether to allow long positions
    recommendation: str = ""  # Action recommendation
    trend_score: float = 0.0  # V3.0: 0-15 points (elastic scale)


class TrendFilter:
    """
    Filters trades based on long-term trend.
    
    Rules:
    1. GREEN/YELLOW only if price > 200-day MA
    2. Consider distance from MA (momentum)
    3. Adjust position size based on trend strength
    
    Examples:
    - Stock at +5% above 200 MA + GREEN signal → Full position
    - Stock at -5% below 200 MA + GREEN signal → No position (override)
    - Stock at +15% above 200 MA + YELLOW → Consider (strong trend)
    """
    
    def __init__(
        self,
        ma_period: int = 200,
        strong_trend_threshold: float = 10.0,  # % for strong trend
        allow_slight_below: bool = False,  # Allow slightly below MA
        enable_elasticity: bool = True,  # V3.0: Enable trend elasticity
        enable_the_stretch: bool = True  # V3.0: Enable mean reversion at extreme dips
    ):
        """
        Initialize trend filter.
        
        Args:
            ma_period: Moving average period (default 200 days)
            strong_trend_threshold: Threshold for strong trend (%)
            allow_slight_below: Allow positions slightly below MA
            enable_elasticity: V3.0 - Use sliding scale 50MA-200MA instead of binary
            enable_the_stretch: V3.0 - Allow mean reversion at >20% dips
        """
        self.ma_period = ma_period
        self.strong_trend_threshold = strong_trend_threshold
        self.allow_slight_below = allow_slight_below
        self.enable_elasticity = enable_elasticity
        self.enable_the_stretch = enable_the_stretch
    
    def calculate_sma(self, prices: np.ndarray, period: int = None) -> np.ndarray:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: Price series
            period: MA period (defaults to self.ma_period)
            
        Returns:
            SMA values
        """
        if period is None:
            period = self.ma_period
        
        sma = np.zeros(len(prices))
        
        for i in range(period, len(prices)):
            sma[i] = np.mean(prices[i-period:i])
        
        return sma
    
    def analyze_trend(
        self,
        prices: np.ndarray,
        current_signal: str = "YELLOW"
    ) -> TrendAnalysis:
        """
        Analyze trend and determine if trading is allowed.
        
        V3.0 Enhancements:
        - Trend Elasticity: Sliding scale between 50MA and 200MA
        - The Stretch: Mean reversion mode at >20% dips
        
        Args:
            prices: Price series
            current_signal: Current traffic light signal
            
        Returns:
            TrendAnalysis with recommendation
        """
        current_price = prices[-1]
        
        # Calculate 200-day MA
        ma_200 = self.calculate_sma(prices, self.ma_period)
        current_ma_200 = ma_200[-1]
        
        # V3.0: Calculate 50-day MA for elasticity
        ma_50 = self.calculate_sma(prices, 50)
        current_ma_50 = ma_50[-1]
        
        if current_ma_200 == 0:
            # Not enough data
            return TrendAnalysis(
                price=current_price,
                ma_200=0,
                ma_50=0,
                distance_from_ma=0,
                regime=TrendRegime.DOWNTREND,
                allow_long=False,
                recommendation="SKIP - Insufficient data",
                trend_score=0.0
            )
        
        # Calculate distance from 200MA
        distance_pct = ((current_price - current_ma_200) / current_ma_200) * 100
        
        # Determine regime
        if distance_pct > self.strong_trend_threshold:
            regime = TrendRegime.STRONG_UPTREND
        elif distance_pct > 0:
            regime = TrendRegime.UPTREND
        elif distance_pct > -self.strong_trend_threshold:
            regime = TrendRegime.DOWNTREND
        else:
            regime = TrendRegime.STRONG_DOWNTREND
        
        # V3.0: Calculate elastic trend score (0-15 points)
        trend_score = self._calculate_trend_score(
            current_price, current_ma_50, current_ma_200, distance_pct
        )
        
        # V3.0: THE STRETCH - Mean reversion at extreme dips
        is_stretch_mode = False
        if self.enable_the_stretch and distance_pct < -20.0:
            # >20% below 200MA = extreme dip = mean reversion opportunity
            is_stretch_mode = True
            allow_long = True  # Override normal trend filter
        # Normal trend logic
        elif regime in [TrendRegime.UPTREND, TrendRegime.STRONG_UPTREND]:
            allow_long = True
        elif self.allow_slight_below and distance_pct > -2.0:
            # Allow if within 2% below MA
            allow_long = True
        else:
            allow_long = False
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            regime, current_signal, distance_pct, allow_long, is_stretch_mode
        )
        
        return TrendAnalysis(
            price=current_price,
            ma_200=current_ma_200,
            ma_50=current_ma_50,
            distance_from_ma=distance_pct,
            regime=regime,
            allow_long=allow_long,
            recommendation=recommendation,
            trend_score=trend_score
        )
    
    def _calculate_trend_score(
        self,
        price: float,
        ma_50: float,
        ma_200: float,
        distance_pct: float
    ) -> float:
        """
        V3.0: Calculate elastic trend score (0-15 points).
        
        Logic:
        - Above 200MA: 15 points (full)
        - Between 50MA and 200MA: 7.5-15 points (sliding scale)
        - Below 50MA: 0 points
        """
        if not self.enable_elasticity:
            # Old binary logic
            return 15.0 if distance_pct > 0 else 0.0
        
        if price > ma_200:
            # Above 200MA = full strength
            return 15.0
        elif price > ma_50 and ma_50 > 0:
            # Between 50MA and 200MA = sliding scale
            if ma_200 == ma_50:
                return 7.5  # Avoid division by zero
            
            # Calculate position in gap
            gap_total = ma_200 - ma_50
            distance_from_50 = price - ma_50
            position_in_gap = distance_from_50 / gap_total if gap_total > 0 else 0
            
            # Scale from 7.5 to 15 points
            trend_score = 7.5 + (position_in_gap * 7.5)
            return max(0, min(15, trend_score))
        else:
            # Below 50MA = no points
            return 0.0
    
    def _generate_recommendation(
        self,
        regime: TrendRegime,
        signal: str,
        distance_pct: float,
        allow_long: bool,
        is_stretch_mode: bool = False
    ) -> str:
        """Generate action recommendation."""
        if is_stretch_mode:
            return f"ENTER - Mean Reversion ({distance_pct:.1f}% dip from 200MA)"
        
        if not allow_long:
            if signal in ["GREEN", "YELLOW"]:
                return f"OVERRIDE - Below 200 MA ({distance_pct:.1f}%) - Fallande kniv!"
            else:
                return "SKIP - Bearish trend confirmed"
        
        if regime == TrendRegime.STRONG_UPTREND:
            if signal == "GREEN":
                return "FULL POSITION - Strong uptrend + GREEN signal"
            elif signal == "YELLOW":
                return "CONSIDER - Strong uptrend + YELLOW signal"
            else:
                return "MONITOR - Strong uptrend but weak signal"
        
        elif regime == TrendRegime.UPTREND:
            if signal == "GREEN":
                return "FULL POSITION - Uptrend + GREEN signal"
            elif signal == "YELLOW":
                return "REDUCED POSITION - Uptrend + YELLOW signal"
            else:
                return "SKIP - Uptrend but weak signal"
        
        return "SKIP - Unclear trend"
    
    def batch_analyze_trends(
        self,
        instruments_data: Dict[str, Dict]
    ) -> Dict[str, TrendAnalysis]:
        """
        Analyze trends for multiple instruments.
        
        Args:
            instruments_data: Dict mapping ticker to data dict with:
                - prices: Price series
                - signal: Current signal
                
        Returns:
            Dict mapping ticker to TrendAnalysis
        """
        results = {}
        
        for ticker, data in instruments_data.items():
            analysis = self.analyze_trend(
                prices=data['prices'],
                current_signal=data.get('signal', 'YELLOW')
            )
            results[ticker] = analysis
        
        return results
    
    def filter_signals(
        self,
        signals: Dict[str, str],
        prices: Dict[str, np.ndarray]
    ) -> Dict[str, str]:
        """
        Filter signals based on trend.
        
        Override GREEN/YELLOW to RED if below 200 MA.
        
        Args:
            signals: Dict mapping ticker to signal (GREEN/YELLOW/etc)
            prices: Dict mapping ticker to price series
            
        Returns:
            Filtered signals
        """
        filtered = {}
        
        for ticker in signals.keys():
            if ticker not in prices:
                filtered[ticker] = signals[ticker]
                continue
            
            analysis = self.analyze_trend(
                prices=prices[ticker],
                current_signal=signals[ticker]
            )
            
            # Override if not allowed
            if not analysis.allow_long and signals[ticker] in ["GREEN", "YELLOW"]:
                filtered[ticker] = "RED"  # Override to RED
            else:
                filtered[ticker] = signals[ticker]
        
        return filtered


def format_trend_report(analyses: Dict[str, TrendAnalysis]) -> str:
    """Format trend analysis report."""
    lines = []
    lines.append("=" * 80)
    lines.append("TREND FILTER - 200-DAY MA ANALYS")
    lines.append("=" * 80)
    lines.append("")
    
    # Group by regime
    by_regime = {}
    for ticker, analysis in analyses.items():
        regime = analysis.regime.value
        if regime not in by_regime:
            by_regime[regime] = []
        by_regime[regime].append((ticker, analysis))
    
    # Sort regimes
    regime_order = [
        "STRONG_UPTREND",
        "UPTREND",
        "DOWNTREND",
        "STRONG_DOWNTREND"
    ]
    
    for regime_name in regime_order:
        if regime_name not in by_regime:
            continue
        
        items = by_regime[regime_name]
        icon = {"STRONG_UPTREND": "🚀", "UPTREND": "📈", "DOWNTREND": "📉", "STRONG_DOWNTREND": "⚠️"}.get(regime_name, "")
        
        lines.append(f"{icon} {regime_name}: {len(items)} instrument")
        lines.append("-" * 80)
        
        for ticker, analysis in sorted(items, key=lambda x: x[1].distance_from_ma, reverse=True):
            status = "✅ ALLOW" if analysis.allow_long else "❌ BLOCK"
            lines.append(
                f"  {ticker:<10} Price: {analysis.price:>8.2f} | "
                f"MA200: {analysis.ma_200:>8.2f} | "
                f"Distance: {analysis.distance_from_ma:>+6.1f}% | "
                f"{status}"
            )
            lines.append(f"    → {analysis.recommendation}")
        
        lines.append("")
    
    # Summary
    total = len(analyses)
    allowed = sum(1 for a in analyses.values() if a.allow_long)
    blocked = total - allowed
    
    lines.append("=" * 80)
    lines.append("SAMMANFATTNING")
    lines.append(f"Totalt: {total} | Tillåtna: {allowed} ({allowed/total*100:.1f}%) | Blockerade: {blocked} ({blocked/total*100:.1f}%)")
    lines.append("=" * 80)
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Trend Filter Module - 200-Day MA Confirmation")
    print("Usage:")
    print("  from src.risk.trend_filter import TrendFilter")
    print("  filter = TrendFilter()")
    print("  analysis = filter.analyze_trend(prices, signal='GREEN')")
