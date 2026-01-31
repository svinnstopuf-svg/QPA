"""
Momentum Exit Strategy

Philosophy:
- Let winners run with trailing stops
- Cut losses quickly (2x ATR)
- Exit on momentum exhaustion signals
- Use ATR-based profit targets

Exit Methods:
1. Trailing Stop (2-3x ATR below high)
2. Profit Targets (multiples of initial risk)
3. Volume Climax Detection (exhaustion)
4. Parabolic Move Detection (unsustainable)
5. Breakdown below EMA50 (trend broken)
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from ..utils.market_data import MarketData


@dataclass
class MomentumExit:
    """Exit signal for momentum trade"""
    should_exit: bool
    exit_reason: str
    exit_type: str  # "STOP", "TARGET", "EXHAUSTION", "BREAKDOWN"
    exit_price: float
    profit_loss_pct: float
    
    # Stop management
    trailing_stop: float
    profit_target_1: float  # 2R (2x initial risk)
    profit_target_2: float  # 3R
    profit_target_3: float  # 5R
    
    # Signals
    volume_climax_detected: bool
    parabolic_move_detected: bool
    ema50_breakdown: bool
    
    description: str


class MomentumExitManager:
    """
    Manages exits for momentum trades.
    
    Key principles:
    - Trail stop as profit grows
    - Lock in profits at key levels
    - Exit on exhaustion signals before reversal
    """
    
    def __init__(
        self,
        initial_stop_atr_multiplier: float = 2.0,
        trailing_stop_atr_multiplier: float = 2.5,
        profit_target_multiples: Tuple[float, float, float] = (2.0, 3.0, 5.0)
    ):
        self.initial_stop_atr = initial_stop_atr_multiplier
        self.trailing_stop_atr = trailing_stop_atr_multiplier
        self.profit_targets = profit_target_multiples
    
    def calculate_atr(self, market_data: MarketData, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = market_data.high_prices
        low = market_data.low_prices
        close = market_data.close_prices
        
        if len(close) < period:
            return 0.0
        
        tr = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - np.roll(close, 1)),
                np.abs(low - np.roll(close, 1))
            )
        )
        tr[0] = high[0] - low[0]
        
        atr = np.mean(tr[-period:])
        return atr
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate current EMA value"""
        if len(prices) < period:
            return 0.0
        
        ema = np.mean(prices[:period])
        multiplier = 2.0 / (period + 1)
        
        for i in range(period, len(prices)):
            ema = (prices[i] - ema) * multiplier + ema
        
        return ema
    
    def detect_volume_climax(
        self,
        market_data: MarketData,
        lookback: int = 60
    ) -> bool:
        """
        Detect volume climax (potential exhaustion).
        
        Signals:
        - Volume spike 3x+ average
        - Wide-range bar
        - After extended move
        
        Returns:
            True if climax detected
        """
        volume = market_data.volume
        high = market_data.high_prices
        low = market_data.low_prices
        close = market_data.close_prices
        
        if len(volume) < lookback:
            return False
        
        # Recent volume vs average
        recent_vol = volume[-1]
        avg_vol = np.mean(volume[-lookback:-1])
        
        if recent_vol < avg_vol * 3.0:  # Need 3x surge
            return False
        
        # Wide range bar check
        recent_range = (high[-1] - low[-1]) / close[-1]
        avg_range = np.mean((high[-lookback:-1] - low[-lookback:-1]) / close[-lookback:-1])
        
        if recent_range < avg_range * 2.0:  # Need 2x wider range
            return False
        
        # Extended move check (>20% in last 30 days)
        if len(close) >= 30:
            move_30d = ((close[-1] - close[-30]) / close[-30]) * 100
            if move_30d < 20:
                return False
        
        return True
    
    def detect_parabolic_move(
        self,
        market_data: MarketData,
        min_acceleration: float = 0.5
    ) -> bool:
        """
        Detect parabolic (unsustainable) price move.
        
        Signals:
        - Accelerating gains (each week > previous)
        - Steep angle (>45 degrees)
        - Extended from moving average
        
        Returns:
            True if parabolic detected
        """
        prices = market_data.close_prices
        
        if len(prices) < 21:  # Need 3 weeks
            return False
        
        # Calculate weekly gains
        week1_gain = ((prices[-7] - prices[-14]) / prices[-14]) * 100
        week2_gain = ((prices[-1] - prices[-7]) / prices[-7]) * 100
        
        # Check acceleration
        if week2_gain <= week1_gain:  # Not accelerating
            return False
        
        acceleration_rate = (week2_gain - week1_gain) / week1_gain if week1_gain > 0 else 0
        
        if acceleration_rate < min_acceleration:
            return False
        
        # Check distance from EMA20
        ema20 = self.calculate_ema(prices, 20)
        distance_from_ema = ((prices[-1] - ema20) / ema20) * 100
        
        if distance_from_ema < 15:  # Need >15% extension
            return False
        
        return True
    
    def check_ema50_breakdown(
        self,
        market_data: MarketData
    ) -> bool:
        """
        Check if price broke below EMA50 (trend broken).
        
        Returns:
            True if breakdown occurred
        """
        prices = market_data.close_prices
        
        if len(prices) < 50:
            return False
        
        ema50 = self.calculate_ema(prices, 50)
        current_price = prices[-1]
        previous_price = prices[-2]
        
        # Breakdown: was above EMA50, now below
        breakdown = (previous_price > ema50) and (current_price < ema50)
        
        return breakdown
    
    def calculate_trailing_stop(
        self,
        entry_price: float,
        highest_price_since_entry: float,
        current_atr: float,
        profit_pct: float
    ) -> float:
        """
        Calculate trailing stop based on profit level.
        
        Rules:
        - 0-20% profit: Initial stop (entry - 2*ATR)
        - 20-40% profit: Break-even + 1*ATR
        - 40%+ profit: Trail 2.5*ATR below high
        
        Returns:
            Stop price
        """
        initial_stop = entry_price - (self.initial_stop_atr * current_atr)
        
        if profit_pct < 20:
            # Initial stop
            return initial_stop
        elif profit_pct < 40:
            # Move to break-even + 1*ATR
            return entry_price + (1.0 * current_atr)
        else:
            # Trail below high
            return highest_price_since_entry - (self.trailing_stop_atr * current_atr)
    
    def calculate_profit_targets(
        self,
        entry_price: float,
        stop_loss: float
    ) -> Tuple[float, float, float]:
        """
        Calculate profit targets based on initial risk.
        
        Returns:
            (target_2R, target_3R, target_5R)
        """
        initial_risk = entry_price - stop_loss
        
        target_2R = entry_price + (2 * initial_risk)
        target_3R = entry_price + (3 * initial_risk)
        target_5R = entry_price + (5 * initial_risk)
        
        return target_2R, target_3R, target_5R
    
    def evaluate_exit(
        self,
        market_data: MarketData,
        entry_price: float,
        initial_stop: float,
        highest_price_since_entry: float
    ) -> MomentumExit:
        """
        Evaluate if momentum trade should exit.
        
        Args:
            market_data: Current market data
            entry_price: Original entry price
            initial_stop: Initial stop loss
            highest_price_since_entry: Highest price reached since entry
        
        Returns:
            MomentumExit with decision and details
        """
        current_price = market_data.close_prices[-1]
        current_atr = self.calculate_atr(market_data)
        
        # Calculate current profit
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Calculate trailing stop
        trailing_stop = self.calculate_trailing_stop(
            entry_price,
            highest_price_since_entry,
            current_atr,
            profit_pct
        )
        
        # Calculate profit targets
        target_2R, target_3R, target_5R = self.calculate_profit_targets(
            entry_price,
            initial_stop
        )
        
        # Check exhaustion signals
        volume_climax = self.detect_volume_climax(market_data)
        parabolic = self.detect_parabolic_move(market_data)
        ema50_breakdown = self.check_ema50_breakdown(market_data)
        
        # Determine exit
        should_exit = False
        exit_reason = ""
        exit_type = ""
        
        # 1. Stop hit
        if current_price <= trailing_stop:
            should_exit = True
            exit_reason = f"Trailing stop hit: {trailing_stop:.2f}"
            exit_type = "STOP"
        
        # 2. Target hit (optional - could scale out instead)
        elif current_price >= target_5R:
            should_exit = False  # Let it run, but could scale out
            exit_reason = f"Target 5R reached: {target_5R:.2f} (consider partial exit)"
            exit_type = "TARGET"
        
        # 3. Volume climax
        elif volume_climax:
            should_exit = True
            exit_reason = "Volume climax detected - exhaustion signal"
            exit_type = "EXHAUSTION"
        
        # 4. Parabolic move
        elif parabolic and profit_pct > 40:
            should_exit = True
            exit_reason = f"Parabolic move with {profit_pct:.1f}% profit - take profits"
            exit_type = "EXHAUSTION"
        
        # 5. EMA50 breakdown
        elif ema50_breakdown:
            should_exit = True
            exit_reason = "Price broke below EMA50 - trend broken"
            exit_type = "BREAKDOWN"
        
        # Default: Hold
        else:
            exit_reason = f"HOLD - Profit: {profit_pct:+.1f}%, Stop: {trailing_stop:.2f}"
            exit_type = "HOLD"
        
        return MomentumExit(
            should_exit=should_exit,
            exit_reason=exit_reason,
            exit_type=exit_type,
            exit_price=current_price,
            profit_loss_pct=profit_pct,
            trailing_stop=trailing_stop,
            profit_target_1=target_2R,
            profit_target_2=target_3R,
            profit_target_3=target_5R,
            volume_climax_detected=volume_climax,
            parabolic_move_detected=parabolic,
            ema50_breakdown=ema50_breakdown,
            description=exit_reason
        )
    
    def calculate_position_scaling(
        self,
        current_price: float,
        entry_price: float,
        profit_target_1: float,
        profit_target_2: float,
        profit_target_3: float
    ) -> str:
        """
        Suggest position scaling strategy.
        
        Returns:
            Recommendation string
        """
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        if current_price < profit_target_1:
            return "100% position - no scaling yet"
        elif current_price < profit_target_2:
            return "Consider selling 33% at 2R (keep 67%)"
        elif current_price < profit_target_3:
            return "Consider selling another 33% at 3R (keep 33%)"
        else:
            return "Consider selling final 33% at 5R or trail with runner"


def format_exit_report(exit: MomentumExit) -> str:
    """Format exit analysis report"""
    lines = []
    
    lines.append("="*80)
    lines.append("MOMENTUM EXIT ANALYSIS")
    lines.append("="*80)
    
    lines.append(f"\nCurrent P/L: {exit.profit_loss_pct:+.1f}%")
    lines.append(f"Exit Price: {exit.exit_price:.2f}")
    
    lines.append(f"\nSTOP MANAGEMENT:")
    lines.append(f"  Trailing Stop: {exit.trailing_stop:.2f}")
    
    lines.append(f"\nPROFIT TARGETS:")
    lines.append(f"  Target 2R: {exit.profit_target_1:.2f}")
    lines.append(f"  Target 3R: {exit.profit_target_2:.2f}")
    lines.append(f"  Target 5R: {exit.profit_target_3:.2f}")
    
    lines.append(f"\nEXHAUSTION SIGNALS:")
    lines.append(f"  Volume Climax: {'⚠️ YES' if exit.volume_climax_detected else '✓ No'}")
    lines.append(f"  Parabolic Move: {'⚠️ YES' if exit.parabolic_move_detected else '✓ No'}")
    lines.append(f"  EMA50 Breakdown: {'⚠️ YES' if exit.ema50_breakdown else '✓ No'}")
    
    lines.append(f"\nDECISION:")
    if exit.should_exit:
        lines.append(f"  🚨 EXIT NOW - {exit.exit_type}")
    else:
        lines.append(f"  ✓ HOLD")
    lines.append(f"  {exit.description}")
    
    return "\n".join(lines)
