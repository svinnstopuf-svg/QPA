"""
Trailing Stop-Loss - Protect Profits in Trends

Quantitative Principle:
In strong trends, fixed stop-losses leave money on the table.
Trailing stops lock in profits while giving the trend room to breathe.

Methodology:
trailing_stop = highest_price_since_entry - (multiplier * ATR)

As price rises, the stop rises with it (but never falls).
Exit when current_price < trailing_stop.

Example:
Entry: 100, ATR: 2
Day 1: Price 102 → Stop = 102 - (2*2) = 98
Day 2: Price 105 → Stop = 105 - (2*2) = 101 (rises)
Day 3: Price 103 → Stop stays at 101 (doesn't fall)
Day 4: Price 100 → EXIT (below 101 stop)

Locked in 1% profit instead of losing -3% with fixed stop.
"""
from typing import Dict, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class TrailingStopState:
    """State of trailing stop for a position."""
    ticker: str
    entry_price: float
    current_price: float
    highest_price: float
    
    # Trailing stop
    trailing_stop_price: float
    atr: float
    atr_multiplier: float
    
    # Status
    stop_triggered: bool
    profit_pct: float
    profit_locked: float  # Minimum profit locked in


class TrailingStopManager:
    """
    Manages ATR-based trailing stops for open positions.
    
    Philosophy: Let winners run, but protect your gains.
    """
    
    def __init__(
        self,
        atr_multiplier: float = 2.0,
        min_profit_to_trail: float = 2.0  # Start trailing after 2% profit
    ):
        """
        Initialize trailing stop manager.
        
        Args:
            atr_multiplier: How many ATRs below highest price (2-3 typical)
            min_profit_to_trail: Minimum profit % before trailing activates
        """
        self.atr_multiplier = atr_multiplier
        self.min_profit_to_trail = min_profit_to_trail
    
    def update_stop(
        self,
        ticker: str,
        entry_price: float,
        current_price: float,
        highest_price: float,
        atr: float,
        previous_stop: float = None
    ) -> TrailingStopState:
        """
        Update trailing stop for a position.
        
        Args:
            ticker: Instrument ticker
            entry_price: Entry price
            current_price: Current market price
            highest_price: Highest price since entry
            atr: Current ATR value
            previous_stop: Previous trailing stop price (to prevent lowering)
            
        Returns:
            TrailingStopState with updated stop
        """
        # Calculate current profit
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Calculate potential trailing stop
        potential_stop = highest_price - (self.atr_multiplier * atr)
        
        # Only activate trailing if profit exceeds threshold
        if profit_pct < self.min_profit_to_trail:
            # Not yet profitable enough - use entry as stop
            trailing_stop = entry_price
        else:
            # Profitable - use trailing stop
            # Never lower the stop (only raise or keep same)
            if previous_stop is not None:
                trailing_stop = max(potential_stop, previous_stop)
            else:
                trailing_stop = potential_stop
        
        # Check if stop triggered
        stop_triggered = current_price < trailing_stop
        
        # Calculate locked profit (stop vs entry)
        profit_locked = ((trailing_stop - entry_price) / entry_price) * 100
        
        return TrailingStopState(
            ticker=ticker,
            entry_price=entry_price,
            current_price=current_price,
            highest_price=highest_price,
            trailing_stop_price=trailing_stop,
            atr=atr,
            atr_multiplier=self.atr_multiplier,
            stop_triggered=stop_triggered,
            profit_pct=profit_pct,
            profit_locked=profit_locked
        )
    
    def format_stop_report(self, state: TrailingStopState) -> str:
        """Generate formatted stop report."""
        report = f"""
{'='*70}
TRAILING STOP: {state.ticker}
{'='*70}

Position:
  Entry Price:       {state.entry_price:.2f}
  Current Price:     {state.current_price:.2f}
  Highest Price:     {state.highest_price:.2f}
  Current Profit:    {state.profit_pct:+.2f}%

Trailing Stop:
  ATR:               {state.atr:.2f}
  Multiplier:        {state.atr_multiplier}x
  Stop Price:        {state.trailing_stop_price:.2f}
  Profit Locked:     {state.profit_locked:+.2f}%

Status:
  Stop Triggered:    {'⚠️ YES - EXIT NOW' if state.stop_triggered else '✅ NO'}

Interpretation:
  {'Trailing stop hit - lock in profit and exit' if state.stop_triggered else 'Position still valid - let it run'}
{'='*70}
"""
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Trailing Stop Manager...")
    
    manager = TrailingStopManager(atr_multiplier=2.0, min_profit_to_trail=2.0)
    
    # Test Case 1: Winning trade that trails upward
    print("\n1. Winning Trade - Trailing Up:")
    
    entry = 100
    atr = 2.0
    
    # Simulate price rising
    prices = [100, 102, 105, 108, 110, 108, 106, 104]
    
    previous_stop = None
    for i, price in enumerate(prices):
        highest = max(prices[:i+1])
        
        state = manager.update_stop(
            "WINNER.ST",
            entry_price=entry,
            current_price=price,
            highest_price=highest,
            atr=atr,
            previous_stop=previous_stop
        )
        
        print(f"\nDay {i+1}: Price={price}, Highest={highest}, Stop={state.trailing_stop_price:.2f}, Triggered={state.stop_triggered}")
        
        previous_stop = state.trailing_stop_price
        
        if state.stop_triggered:
            print(manager.format_stop_report(state))
            break
    
    # Test Case 2: No trailing (not profitable enough)
    print("\n\n2. No Trailing Test (Insufficient Profit):")
    
    state = manager.update_stop(
        "FLAT.ST",
        entry_price=100,
        current_price=101,  # Only 1% profit
        highest_price=101,
        atr=2.0
    )
    
    print(manager.format_stop_report(state))
    
    # Test Case 3: Immediate stop-out
    print("\n3. Immediate Stop-Out Test:")
    
    state = manager.update_stop(
        "LOSER.ST",
        entry_price=100,
        current_price=95,  # Down 5%
        highest_price=100,
        atr=2.0
    )
    
    print(manager.format_stop_report(state))
    
    print("\n✅ Trailing Stop Manager - Tests Complete")
