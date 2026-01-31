"""
Motor B: Momentum/Launchpad Engine

Detects instruments showing:
1. Strong uptrend (Price > EMA50 > EMA200)
2. Near 52-week high (Price > 0.95 * 52w_High)
3. RS-Rating: Outperforming 95% of universe (3/6/12 month weighted)
4. VCP-Logic: Volatility contraction (ATR compression)

Philosophy: Buy strength, not weakness. Catch leaders BEFORE breakout.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..utils.market_data import MarketData


@dataclass
class MomentumSignal:
    """Momentum/Launchpad signal result"""
    ticker: str
    is_valid: bool
    
    # Trend Check
    price_above_ema50: bool
    ema50_above_ema200: bool
    trend_alignment: bool  # Both above
    
    # 52-Week High Proximity
    high_52w: float
    current_price: float
    distance_from_52w: float  # % from 52w high
    near_high: bool  # > 95% of 52w high
    
    # RS-Rating (Relative Strength vs Universe)
    rs_rating: float  # 0-100 (percentile rank)
    return_3m: float
    return_6m: float
    return_12m: float
    weighted_return: float
    
    # VCP-Logic (Volatility Contraction)
    atr_5d: float
    atr_20d: float
    atr_ratio: float  # ATR(5) / ATR(20)
    volatility_contracted: bool  # ratio < 0.85
    
    # Final
    reason: str


class MomentumEngine:
    """
    Motor B: Detect momentum leaders with VCP setups.
    
    Requirements:
    1. Uptrend: Price > EMA50 > EMA200
    2. Near 52w high: Price > 0.95 * High_52w
    3. RS-Rating ≥ 95 (top 5% of universe)
    4. VCP: ATR(5) / ATR(20) < 0.85
    """
    
    def __init__(
        self,
        min_rs_rating: float = 95.0,
        min_52w_proximity: float = 0.95,
        max_atr_ratio: float = 0.85
    ):
        self.min_rs_rating = min_rs_rating
        self.min_52w_proximity = min_52w_proximity
        self.max_atr_ratio = max_atr_ratio
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)
        
        ema = np.zeros(len(prices))
        ema[:period] = np.nan
        
        # Start with SMA
        ema[period-1] = np.mean(prices[:period])
        
        # EMA multiplier
        multiplier = 2.0 / (period + 1)
        
        # Calculate EMA
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def calculate_atr(self, market_data: MarketData, period: int) -> np.ndarray:
        """Calculate Average True Range"""
        high = market_data.high_prices
        low = market_data.low_prices
        close = market_data.close_prices
        
        # True Range
        tr = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - np.roll(close, 1)),
                np.abs(low - np.roll(close, 1))
            )
        )
        tr[0] = high[0] - low[0]  # First day
        
        # ATR as EMA of TR
        atr = pd.Series(tr).ewm(span=period, adjust=False).mean().values
        
        return atr
    
    def calculate_rs_vs_spy(
        self,
        ticker_returns: Tuple[float, float, float],
        spy_returns: Optional[Tuple[float, float, float]] = None
    ) -> float:
        """
        Calculate RS vs SPY benchmark.
        
        Returns:
            RS score (>100 = outperforming SPY)
        """
        if not spy_returns:
            return 100.0  # Neutral if no SPY data
        
        # Weighted returns
        ticker_weighted = (ticker_returns[0] * 0.40 + 
                          ticker_returns[1] * 0.30 + 
                          ticker_returns[2] * 0.30)
        spy_weighted = (spy_returns[0] * 0.40 + 
                       spy_returns[1] * 0.30 + 
                       spy_returns[2] * 0.30)
        
        # Relative strength
        rs_vs_spy = (ticker_weighted / spy_weighted) * 100 if spy_weighted != 0 else 100.0
        
        return rs_vs_spy
    
    def detect_rs_trend(
        self,
        ticker: str,
        market_data: MarketData,
        universe_returns: Dict[str, Tuple[float, float, float]]
    ) -> str:
        """
        Detect if RS-Rating is improving, declining, or stable.
        
        Returns:
            "IMPROVING", "DECLINING", "STABLE"
        """
        if len(market_data.close_prices) < 252:
            return "UNKNOWN"
        
        # Calculate RS-Rating now vs 30 days ago
        rs_now, _, _, _, _ = self.calculate_rs_rating(ticker, market_data, universe_returns)
        
        # Simulate 30 days ago
        if len(market_data.close_prices) < 282:
            return "UNKNOWN"
        
        prices_30d_ago = market_data.close_prices[:-30]
        past_data = MarketData(
            timestamps=market_data.timestamps[:-30],
            open_prices=market_data.open_prices[:-30],
            high_prices=market_data.high_prices[:-30],
            low_prices=market_data.low_prices[:-30],
            close_prices=prices_30d_ago,
            volume=market_data.volume[:-30]
        )
        
        rs_30d_ago, _, _, _, _ = self.calculate_rs_rating(ticker, past_data, universe_returns)
        
        # Trend
        diff = rs_now - rs_30d_ago
        if diff > 5:
            return "IMPROVING"
        elif diff < -5:
            return "DECLINING"
        else:
            return "STABLE"
    
    def calculate_rs_rating(
        self,
        ticker: str,
        market_data: MarketData,
        universe_returns: Dict[str, Tuple[float, float, float]]
    ) -> Tuple[float, float, float, float, float]:
        """
        Calculate RS-Rating (Relative Strength percentile rank).
        
        Args:
            ticker: Current ticker
            market_data: Price data for ticker
            universe_returns: Dict[ticker, (return_3m, return_6m, return_12m)]
        
        Returns:
            (rs_rating, return_3m, return_6m, return_12m, weighted_return)
        """
        prices = market_data.close_prices
        
        # Calculate returns for this ticker
        if len(prices) < 252:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        
        # 3-month return (63 days)
        return_3m = (prices[-1] - prices[-63]) / prices[-63] if len(prices) >= 63 else 0.0
        
        # 6-month return (126 days)
        return_6m = (prices[-1] - prices[-126]) / prices[-126] if len(prices) >= 126 else 0.0
        
        # 12-month return (252 days)
        return_12m = (prices[-1] - prices[-252]) / prices[-252] if len(prices) >= 252 else 0.0
        
        # Weighted return (3m: 40%, 6m: 30%, 12m: 30%)
        weighted_return = (return_3m * 0.40) + (return_6m * 0.30) + (return_12m * 0.30)
        
        # Calculate percentile rank vs universe
        if len(universe_returns) > 0:
            # Get weighted returns for all tickers in universe
            universe_weighted = [
                (r3m * 0.40) + (r6m * 0.30) + (r12m * 0.30)
                for _, (r3m, r6m, r12m) in universe_returns.items()
            ]
            
            # Percentile rank (0-100)
            better_than = sum(1 for r in universe_weighted if weighted_return > r)
            rs_rating = (better_than / len(universe_weighted)) * 100
        else:
            rs_rating = 50.0  # Default if no universe data
        
        return rs_rating, return_3m, return_6m, return_12m, weighted_return
    
    def detect_momentum_signal(
        self,
        ticker: str,
        market_data: MarketData,
        universe_returns: Optional[Dict[str, Tuple[float, float, float]]] = None
    ) -> MomentumSignal:
        """
        Detect if instrument qualifies as Momentum/Launchpad setup.
        
        Args:
            ticker: Stock ticker
            market_data: OHLCV data
            universe_returns: Dict of returns for RS-Rating calculation
        
        Returns:
            MomentumSignal with validation result
        """
        prices = market_data.close_prices
        
        if len(prices) < 252:
            return MomentumSignal(
                ticker=ticker,
                is_valid=False,
                price_above_ema50=False,
                ema50_above_ema200=False,
                trend_alignment=False,
                high_52w=0.0,
                current_price=prices[-1] if len(prices) > 0 else 0.0,
                distance_from_52w=0.0,
                near_high=False,
                rs_rating=0.0,
                return_3m=0.0,
                return_6m=0.0,
                return_12m=0.0,
                weighted_return=0.0,
                atr_5d=0.0,
                atr_20d=0.0,
                atr_ratio=0.0,
                volatility_contracted=False,
                reason="Insufficient data (<252 days)"
            )
        
        current_price = prices[-1]
        
        # 1. TREND CHECK: Price > EMA50 > EMA200
        ema50 = self.calculate_ema(prices, 50)
        ema200 = self.calculate_ema(prices, 200)
        
        current_ema50 = ema50[-1]
        current_ema200 = ema200[-1]
        
        price_above_ema50 = current_price > current_ema50
        ema50_above_ema200 = current_ema50 > current_ema200
        trend_alignment = price_above_ema50 and ema50_above_ema200
        
        # 2. 52-WEEK HIGH PROXIMITY
        lookback_252 = prices[-252:]
        high_52w = np.max(lookback_252)
        distance_from_52w = ((current_price - high_52w) / high_52w) * 100
        near_high = current_price >= (high_52w * self.min_52w_proximity)
        
        # 3. RS-RATING
        if universe_returns is None:
            universe_returns = {}
        
        rs_rating, return_3m, return_6m, return_12m, weighted_return = self.calculate_rs_rating(
            ticker, market_data, universe_returns
        )
        
        # 4. VCP-LOGIC: Volatility Contraction
        atr = self.calculate_atr(market_data, period=20)
        
        # ATR(5) - simple average of last 5 TRs
        atr_5d = np.mean(atr[-5:]) if len(atr) >= 5 else 0.0
        atr_20d = atr[-1] if len(atr) > 0 else 0.0
        
        atr_ratio = atr_5d / atr_20d if atr_20d > 0 else 1.0
        volatility_contracted = atr_ratio < self.max_atr_ratio
        
        # VALIDATION
        if not trend_alignment:
            reason = f"Trend broken: Price vs EMA50: {price_above_ema50}, EMA50 vs EMA200: {ema50_above_ema200}"
            is_valid = False
        elif not near_high:
            reason = f"Not near 52w high: {distance_from_52w:.1f}% from high (need >-5%)"
            is_valid = False
        elif rs_rating < self.min_rs_rating:
            reason = f"RS-Rating too low: {rs_rating:.1f} < {self.min_rs_rating}"
            is_valid = False
        elif not volatility_contracted:
            reason = f"No VCP: ATR ratio {atr_ratio:.2f} ≥ {self.max_atr_ratio}"
            is_valid = False
        else:
            reason = f"MOMENTUM LEADER: RS={rs_rating:.0f}, VCP ratio={atr_ratio:.2f}, {distance_from_52w:.1f}% from 52w high"
            is_valid = True
        
        return MomentumSignal(
            ticker=ticker,
            is_valid=is_valid,
            price_above_ema50=price_above_ema50,
            ema50_above_ema200=ema50_above_ema200,
            trend_alignment=trend_alignment,
            high_52w=high_52w,
            current_price=current_price,
            distance_from_52w=distance_from_52w,
            near_high=near_high,
            rs_rating=rs_rating,
            return_3m=return_3m,
            return_6m=return_6m,
            return_12m=return_12m,
            weighted_return=weighted_return,
            atr_5d=atr_5d,
            atr_20d=atr_20d,
            atr_ratio=atr_ratio,
            volatility_contracted=volatility_contracted,
            reason=reason
        )


def calculate_universe_returns(
    tickers: List[str],
    market_data_dict: Dict[str, MarketData]
) -> Dict[str, Tuple[float, float, float]]:
    """
    Calculate 3/6/12-month returns for entire universe.
    
    Args:
        tickers: List of all tickers
        market_data_dict: Dict[ticker, MarketData]
    
    Returns:
        Dict[ticker, (return_3m, return_6m, return_12m)]
    """
    universe_returns = {}
    
    for ticker in tickers:
        if ticker not in market_data_dict:
            continue
        
        prices = market_data_dict[ticker].close_prices
        
        if len(prices) < 252:
            continue
        
        # Calculate returns
        return_3m = (prices[-1] - prices[-63]) / prices[-63] if len(prices) >= 63 else 0.0
        return_6m = (prices[-1] - prices[-126]) / prices[-126] if len(prices) >= 126 else 0.0
        return_12m = (prices[-1] - prices[-252]) / prices[-252] if len(prices) >= 252 else 0.0
        
        universe_returns[ticker] = (return_3m, return_6m, return_12m)
    
    return universe_returns
