"""
Time-Based Exit Module - Dead Money Killer
===========================================

Automatically exits positions that haven't moved after 10 days.

Philosophy:
- Capital tied up in stagnant positions = opportunity cost
- "Dead money" prevents deploying capital to better opportunities
- Time is the scarcest resource in trading

Usage:
exit_mgr = TimeBasedExitManager(max_hold_days=10)
exit_signals = exit_mgr.check_positions(positions, current_prices)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ExitSignal:
    """Exit signal for a position."""
    ticker: str
    entry_date: str
    days_held: int
    entry_price: float
    current_price: float
    profit_pct: float
    exit_reason: str
    recommendation: str  # HOLD, SELL, STOP_LOSS


@dataclass
class TimeBasedExitResult:
    """Results from time-based exit analysis."""
    total_positions: int
    exit_signals: List[ExitSignal]
    dead_money_count: int
    dead_money_value_sek: float
    recommendation: str


class TimeBasedExitManager:
    """
    Manages time-based exits to prevent capital from rotting.
    
    Rules:
    1. If days_held > max_hold_days AND profit < breakeven → SELL (dead money)
    2. If profit > target → SELL (take profit)
    3. If loss > stop_loss → SELL (cut loss)
    4. Otherwise → HOLD
    """
    
    def __init__(
        self,
        max_hold_days: int = 10,
        breakeven_threshold_pct: float = 0.0,
        take_profit_pct: float = 5.0,
        stop_loss_pct: float = -5.0
    ):
        """
        Initialize time-based exit manager.
        
        Args:
            max_hold_days: Maximum days to hold before exit (default 10)
            breakeven_threshold_pct: Min profit % to avoid dead money exit (default 0%)
            take_profit_pct: Auto-exit if profit exceeds this (default 5%)
            stop_loss_pct: Auto-exit if loss exceeds this (default -5%)
        """
        self.max_hold_days = max_hold_days
        self.breakeven_threshold = breakeven_threshold_pct
        self.take_profit = take_profit_pct
        self.stop_loss = stop_loss_pct
    
    def calculate_profit(
        self,
        entry_price: float,
        current_price: float
    ) -> float:
        """
        Calculate profit percentage.
        
        Args:
            entry_price: Entry price
            current_price: Current price
            
        Returns:
            Profit % (positive = gain, negative = loss)
        """
        if entry_price == 0:
            return 0.0
        return ((current_price - entry_price) / entry_price) * 100
    
    def calculate_days_held(
        self,
        entry_date: str,
        current_date: Optional[str] = None
    ) -> int:
        """
        Calculate days held.
        
        Args:
            entry_date: Entry date (YYYY-MM-DD)
            current_date: Current date (YYYY-MM-DD), defaults to today
            
        Returns:
            Number of days held
        """
        try:
            entry = datetime.strptime(entry_date, "%Y-%m-%d")
            if current_date:
                current = datetime.strptime(current_date, "%Y-%m-%d")
            else:
                current = datetime.now()
            
            delta = current - entry
            return delta.days
        except:
            return 0
    
    def check_position(
        self,
        position: Dict,
        current_price: float,
        current_date: Optional[str] = None
    ) -> ExitSignal:
        """
        Check if position should be exited.
        
        Args:
            position: Position dict with ticker, entry_date, entry_price
            current_price: Current market price
            current_date: Current date (optional)
            
        Returns:
            ExitSignal with recommendation
        """
        ticker = position.get('ticker', 'UNKNOWN')
        entry_date = position.get('entry_date', '')
        entry_price = position.get('entry_price', 0)
        
        # Calculate metrics
        days_held = self.calculate_days_held(entry_date, current_date)
        profit_pct = self.calculate_profit(entry_price, current_price)
        
        # Determine exit reason and recommendation
        exit_reason = ""
        recommendation = "HOLD"
        
        # Check stop loss (highest priority)
        if profit_pct <= self.stop_loss:
            exit_reason = f"STOP LOSS: {profit_pct:.2f}% loss exceeds {self.stop_loss}%"
            recommendation = "SELL"
        
        # Check take profit
        elif profit_pct >= self.take_profit:
            exit_reason = f"TAKE PROFIT: {profit_pct:.2f}% gain exceeds target {self.take_profit}%"
            recommendation = "SELL"
        
        # Check dead money (time-based)
        elif days_held > self.max_hold_days and profit_pct < self.breakeven_threshold:
            exit_reason = f"DEAD MONEY: {days_held} days held with {profit_pct:.2f}% profit"
            recommendation = "SELL"
        
        # Hold
        else:
            if days_held > self.max_hold_days:
                exit_reason = f"HOLD: {days_held} days but {profit_pct:.2f}% profit (above breakeven)"
            else:
                exit_reason = f"HOLD: {days_held}/{self.max_hold_days} days, {profit_pct:.2f}% profit"
            recommendation = "HOLD"
        
        return ExitSignal(
            ticker=ticker,
            entry_date=entry_date,
            days_held=days_held,
            entry_price=entry_price,
            current_price=current_price,
            profit_pct=profit_pct,
            exit_reason=exit_reason,
            recommendation=recommendation
        )
    
    def check_positions(
        self,
        positions: List[Dict],
        current_prices: Dict[str, float],
        current_date: Optional[str] = None
    ) -> TimeBasedExitResult:
        """
        Check all positions for exit signals.
        
        Args:
            positions: List of position dicts
            current_prices: Dict mapping ticker → current price
            current_date: Current date (optional)
            
        Returns:
            TimeBasedExitResult with all exit signals
        """
        exit_signals = []
        dead_money_count = 0
        dead_money_value = 0
        
        for position in positions:
            ticker = position.get('ticker', '')
            current_price = current_prices.get(ticker, 0)
            
            if current_price == 0:
                # Skip if no price available
                continue
            
            signal = self.check_position(position, current_price, current_date)
            exit_signals.append(signal)
            
            # Track dead money
            if "DEAD MONEY" in signal.exit_reason:
                dead_money_count += 1
                position_value = position.get('shares', 0) * current_price
                dead_money_value += position_value
        
        # Generate recommendation
        sell_count = sum(1 for s in exit_signals if s.recommendation == "SELL")
        if sell_count > 0:
            recommendation = f"⚠️ {sell_count} position(s) should be exited ({dead_money_count} dead money)"
        else:
            recommendation = "✅ All positions within hold criteria"
        
        return TimeBasedExitResult(
            total_positions=len(positions),
            exit_signals=exit_signals,
            dead_money_count=dead_money_count,
            dead_money_value_sek=dead_money_value,
            recommendation=recommendation
        )
    
    def format_exit_report(self, result: TimeBasedExitResult) -> str:
        """
        Format exit report for display.
        
        Args:
            result: TimeBasedExitResult to format
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 100)
        lines.append("⏰ TIME-BASED EXIT ANALYSIS")
        lines.append("=" * 100)
        lines.append(f"\nPositions: {result.total_positions}")
        lines.append(f"Dead Money: {result.dead_money_count} ({result.dead_money_value_sek:,.0f} SEK)")
        lines.append(f"\n{result.recommendation}\n")
        
        # Group by recommendation
        sell_signals = [s for s in result.exit_signals if s.recommendation == "SELL"]
        hold_signals = [s for s in result.exit_signals if s.recommendation == "HOLD"]
        
        if sell_signals:
            lines.append("🚨 EXIT SIGNALS:")
            lines.append("-" * 100)
            lines.append(f"{'Ticker':<10} {'Days':<6} {'Entry':<10} {'Current':<10} {'Profit':<10} {'Reason'}")
            lines.append("-" * 100)
            
            for sig in sell_signals:
                lines.append(
                    f"{sig.ticker:<10} "
                    f"{sig.days_held:<6} "
                    f"{sig.entry_price:>9.2f} "
                    f"{sig.current_price:>9.2f} "
                    f"{sig.profit_pct:>+8.2f}% "
                    f"{sig.exit_reason}"
                )
            lines.append("")
        
        if hold_signals:
            lines.append("✅ HOLD POSITIONS:")
            lines.append("-" * 100)
            
            for sig in hold_signals[:5]:  # Show top 5
                lines.append(
                    f"{sig.ticker:<10} "
                    f"{sig.days_held:<6} days, "
                    f"{sig.profit_pct:>+6.2f}% - "
                    f"{sig.exit_reason}"
                )
            
            if len(hold_signals) > 5:
                lines.append(f"... and {len(hold_signals) - 5} more positions")
        
        lines.append("=" * 100)
        
        return "\n".join(lines)
