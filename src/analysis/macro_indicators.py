"""
Macro Indicators - Advanced Market Risk Detection

Implements professional quant indicators:
1. Yield Curve Inversion (recession warning)
2. Credit Spreads (corporate stress)
3. Safe Haven Watch (capital flight detection)

Philosophy: "See the smoke before the fire starts"
"""

import yfinance as yf
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime, timedelta


@dataclass
class YieldCurveAnalysis:
    """Yield curve inversion analysis"""
    short_rate: float  # 13-week Treasury (^IRX)
    long_rate: float  # 10-year Treasury (^TNX)
    spread: float  # long - short (negative = inverted)
    is_inverted: bool
    inversion_magnitude: float  # How much inverted (basis points)
    risk_level: str  # LOW, MEDIUM, HIGH, EXTREME
    message: str


@dataclass
class CreditSpreadAnalysis:
    """Credit spread analysis"""
    treasury_return: float  # TLT recent return
    corporate_return: float  # LQD recent return
    spread: float  # TLT - LQD (positive = flight to safety)
    flight_to_safety: bool  # True if capital fleeing corporates
    stress_level: str  # LOW, MEDIUM, HIGH, EXTREME
    message: str


@dataclass
class SafeHavenWatch:
    """Safe haven capital flow analysis"""
    total_safe_havens: int
    green_count: int
    yellow_count: int
    red_count: int
    safe_haven_strength: float  # 0-100%
    capital_flight_detected: bool
    top_performers: List[Tuple[str, str, float]]  # (ticker, name, edge)
    message: str


class MacroIndicators:
    """
    Advanced macro indicators for professional risk assessment.
    
    These indicators help detect systemic risk BEFORE it shows up
    in individual stock signals.
    """
    
    def __init__(self):
        """Initialize macro indicators analyzer."""
        pass
    
    def analyze_yield_curve(self) -> Optional[YieldCurveAnalysis]:
        """
        Analyze yield curve inversion.
        
        Compares ^IRX (13-week T-bill) vs ^TNX (10-year T-note).
        Inverted curve (short > long) is historically accurate recession predictor.
        
        Returns:
            YieldCurveAnalysis or None if data unavailable
        """
        try:
            # Fetch recent rates
            irx = yf.Ticker("^IRX")  # 13-week Treasury
            tnx = yf.Ticker("^TNX")  # 10-year Treasury
            
            irx_hist = irx.history(period="5d")
            tnx_hist = tnx.history(period="5d")
            
            if irx_hist.empty or tnx_hist.empty:
                return None
            
            short_rate = irx_hist['Close'].iloc[-1]
            long_rate = tnx_hist['Close'].iloc[-1]
            
            spread = long_rate - short_rate  # Normal: positive, Inverted: negative
            is_inverted = spread < 0
            inversion_magnitude = abs(spread) if is_inverted else 0
            
            # Determine risk level
            if not is_inverted:
                if spread > 2.0:
                    risk_level = "LOW"
                    message = f"Kurvan normal (+{spread:.2f}%) - låg recession-risk"
                elif spread > 0.5:
                    risk_level = "MEDIUM"
                    message = f"Kurvan plattnar ut (+{spread:.2f}%) - bevaka läget"
                else:
                    risk_level = "HIGH"
                    message = f"Kurvan nästan platt (+{spread:.2f}%) - recession närmar sig"
            else:
                if inversion_magnitude < 0.25:
                    risk_level = "HIGH"
                    message = f"⚠️ INVERTERAD KURVA (-{inversion_magnitude:.2f}%) - recession-varning!"
                else:
                    risk_level = "EXTREME"
                    message = f"🚨 DJUPT INVERTERAD ({-spread:.2f}%) - recession mycket trolig!"
            
            return YieldCurveAnalysis(
                short_rate=short_rate,
                long_rate=long_rate,
                spread=spread,
                is_inverted=is_inverted,
                inversion_magnitude=inversion_magnitude,
                risk_level=risk_level,
                message=message
            )
            
        except Exception as e:
            print(f"⚠️ Kunde inte hämta yield curve data: {e}")
            return None
    
    def analyze_credit_spreads(self, lookback_days: int = 20) -> Optional[CreditSpreadAnalysis]:
        """
        Analyze credit spreads (corporate vs treasury bonds).
        
        Compares LQD (investment grade corporate) vs TLT (treasury).
        When TLT surges while LQD falls = fear of corporate defaults.
        
        Args:
            lookback_days: Days to calculate returns
            
        Returns:
            CreditSpreadAnalysis or None if data unavailable
        """
        try:
            # Fetch bond ETF data
            lqd = yf.Ticker("LQD")  # Corporate bonds
            tlt = yf.Ticker("TLT")  # Treasury bonds
            
            lqd_hist = lqd.history(period=f"{lookback_days + 5}d")
            tlt_hist = tlt.history(period=f"{lookback_days + 5}d")
            
            if len(lqd_hist) < lookback_days or len(tlt_hist) < lookback_days:
                return None
            
            # Calculate returns
            lqd_return = ((lqd_hist['Close'].iloc[-1] / lqd_hist['Close'].iloc[-lookback_days]) - 1) * 100
            tlt_return = ((tlt_hist['Close'].iloc[-1] / tlt_hist['Close'].iloc[-lookback_days]) - 1) * 100
            
            spread = tlt_return - lqd_return  # Positive = flight to safety
            
            flight_to_safety = tlt_return > 2 and lqd_return < 0  # TLT up, LQD down
            
            # Determine stress level
            if spread < 0:
                stress_level = "LOW"
                message = f"Företagsobligationer starkare än Treasury (spread: {spread:.1f}%)"
            elif spread < 2:
                stress_level = "MEDIUM"
                message = f"Neutral spread ({spread:.1f}%) - normal marknad"
            elif spread < 5:
                stress_level = "HIGH"
                if flight_to_safety:
                    message = f"⚠️ Kapitalflykt påbörjad (spread: {spread:.1f}%) - rädsla för konkurser"
                else:
                    message = f"Förhöjd spread ({spread:.1f}%) - viss stress i kreditmarka"
            else:
                stress_level = "EXTREME"
                message = f"🚨 EXTREM kapitalflykt (spread: {spread:.1f}%) - kreditmarknad i kris!"
            
            return CreditSpreadAnalysis(
                treasury_return=tlt_return,
                corporate_return=lqd_return,
                spread=spread,
                flight_to_safety=flight_to_safety,
                stress_level=stress_level,
                message=message
            )
            
        except Exception as e:
            print(f"⚠️ Kunde inte hämta credit spread data: {e}")
            return None
    
    def analyze_safe_haven_watch(
        self,
        all_weather_results: List,
        sp500_signal: str = "RED"
    ) -> SafeHavenWatch:
        """
        Analyze safe haven instrument performance.
        
        Groups All-Weather instruments and checks if they're GREEN
        while market (S&P 500) is RED. This indicates capital flight.
        
        Args:
            all_weather_results: List of InstrumentScoreV22 for All-Weather instruments
            sp500_signal: Current S&P 500 signal (GREEN/YELLOW/RED)
            
        Returns:
            SafeHavenWatch analysis
        """
        if not all_weather_results:
            return SafeHavenWatch(
                total_safe_havens=0,
                green_count=0,
                yellow_count=0,
                red_count=0,
                safe_haven_strength=0,
                capital_flight_detected=False,
                top_performers=[],
                message="Inga All-Weather instruments analyserade"
            )
        
        # Count signals
        green_count = sum(1 for r in all_weather_results if r.signal.name == "GREEN")
        yellow_count = sum(1 for r in all_weather_results if r.signal.name == "YELLOW")
        red_count = sum(1 for r in all_weather_results if r.signal.name == "RED")
        
        total = len(all_weather_results)
        safe_haven_strength = ((green_count + yellow_count) / total) * 100
        
        # Capital flight = safe havens GREEN while market RED
        capital_flight_detected = (safe_haven_strength > 30 and sp500_signal == "RED")
        
        # Get top performers
        positive_results = [r for r in all_weather_results 
                          if r.signal.name in ["GREEN", "YELLOW"] and r.net_edge_after_costs > 0]
        positive_results.sort(key=lambda x: x.net_edge_after_costs, reverse=True)
        
        top_performers = [
            (r.ticker, r.name, r.net_edge_after_costs)
            for r in positive_results[:5]
        ]
        
        # Generate message
        if capital_flight_detected:
            message = f"🚨 KAPITALFLYKT: {safe_haven_strength:.0f}% av safe havens är GREEN medan marknaden är RED!"
        elif safe_haven_strength > 50:
            message = f"⚠️ Stark safe haven-aktivitet ({safe_haven_strength:.0f}%) - investerare söker säkerhet"
        elif safe_haven_strength > 20:
            message = f"Måttlig safe haven-aktivitet ({safe_haven_strength:.0f}%)"
        else:
            message = f"Låg safe haven-aktivitet ({safe_haven_strength:.0f}%) - risk-on läge"
        
        return SafeHavenWatch(
            total_safe_havens=total,
            green_count=green_count,
            yellow_count=yellow_count,
            red_count=red_count,
            safe_haven_strength=safe_haven_strength,
            capital_flight_detected=capital_flight_detected,
            top_performers=top_performers,
            message=message
        )
    
    def get_systemic_risk_score(
        self,
        yield_curve: Optional[YieldCurveAnalysis],
        credit_spreads: Optional[CreditSpreadAnalysis],
        safe_haven: SafeHavenWatch,
        market_regime_multiplier: float
    ) -> Tuple[float, str]:
        """
        Calculate overall systemic risk score (0-100).
        
        Combines all macro indicators into single risk assessment.
        Higher score = higher systemic risk.
        
        Args:
            yield_curve: Yield curve analysis
            credit_spreads: Credit spread analysis
            safe_haven: Safe haven watch
            market_regime_multiplier: Current regime multiplier (0.2-1.0)
            
        Returns:
            (risk_score, risk_message)
        """
        risk_score = 0
        
        # Base score from regime (0-40 points)
        if market_regime_multiplier <= 0.2:
            risk_score += 40  # CRISIS
        elif market_regime_multiplier <= 0.4:
            risk_score += 30  # STRESSED
        elif market_regime_multiplier <= 0.7:
            risk_score += 15  # CAUTIOUS
        # HEALTHY = 0
        
        # Yield curve (0-30 points)
        if yield_curve:
            if yield_curve.risk_level == "EXTREME":
                risk_score += 30
            elif yield_curve.risk_level == "HIGH":
                risk_score += 20
            elif yield_curve.risk_level == "MEDIUM":
                risk_score += 10
        
        # Credit spreads (0-20 points)
        if credit_spreads:
            if credit_spreads.stress_level == "EXTREME":
                risk_score += 20
            elif credit_spreads.stress_level == "HIGH":
                risk_score += 15
            elif credit_spreads.stress_level == "MEDIUM":
                risk_score += 8
        
        # Safe haven activity (0-10 points)
        if safe_haven.capital_flight_detected:
            risk_score += 10
        elif safe_haven.safe_haven_strength > 50:
            risk_score += 5
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Generate message
        if risk_score >= 80:
            risk_message = "🚨 EXTREM systemrisk - recession mycket trolig"
        elif risk_score >= 60:
            risk_message = "⚠️ HÖG systemrisk - marknadskris pågår"
        elif risk_score >= 40:
            risk_message = "⚠️ FÖRHÖJD systemrisk - var försiktig"
        elif risk_score >= 20:
            risk_message = "⚠️ MÅTTLIG systemrisk - bevaka läget"
        else:
            risk_message = "✅ LÅG systemrisk - marknad ser hälsosam ut"
        
        return risk_score, risk_message


if __name__ == "__main__":
    # Test macro indicators
    print("🔍 TESTING MACRO INDICATORS")
    print("=" * 80)
    
    indicators = MacroIndicators()
    
    # Test yield curve
    print("\n1. YIELD CURVE ANALYSIS")
    print("-" * 80)
    yc = indicators.analyze_yield_curve()
    if yc:
        print(f"Short rate (^IRX): {yc.short_rate:.2f}%")
        print(f"Long rate (^TNX): {yc.long_rate:.2f}%")
        print(f"Spread: {yc.spread:+.2f}%")
        print(f"Inverted: {yc.is_inverted}")
        print(f"Risk: {yc.risk_level}")
        print(f"Message: {yc.message}")
    
    # Test credit spreads
    print("\n2. CREDIT SPREADS ANALYSIS")
    print("-" * 80)
    cs = indicators.analyze_credit_spreads()
    if cs:
        print(f"Treasury (TLT): {cs.treasury_return:+.2f}%")
        print(f"Corporate (LQD): {cs.corporate_return:+.2f}%")
        print(f"Spread: {cs.spread:+.2f}%")
        print(f"Flight to safety: {cs.flight_to_safety}")
        print(f"Stress: {cs.stress_level}")
        print(f"Message: {cs.message}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
