"""
Portfolio Health Tracker

Tracks existing positions and re-scans them for continued validity.
Flags: HOLD, EXIT, ADD based on current edge.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json
from pathlib import Path
from datetime import datetime


@dataclass
class Position:
    """Current portfolio position."""
    ticker: str
    entry_date: str
    entry_price: float
    shares: int
    pattern_type: str
    neckline_price: Optional[float] = None


@dataclass
class PositionHealth:
    """Health assessment of a position."""
    ticker: str
    action: str  # "HOLD", "EXIT", "ADD"
    reason: str
    current_price: float
    current_profit_pct: float
    current_edge: float  # Re-scanned edge
    original_edge: float
    edge_degradation: float  # How much edge has degraded
    days_held: int


class PortfolioHealthTracker:
    """
    Track and re-evaluate existing positions.
    
    Reads positions from positions.json and re-scans each one.
    """
    
    def __init__(self, positions_file: str = "positions.json"):
        self.positions_file = Path(positions_file)
    
    def load_positions(self) -> List[Position]:
        """Load current positions from file."""
        
        if not self.positions_file.exists():
            return []
        
        try:
            with open(self.positions_file, 'r') as f:
                data = json.load(f)
            
            positions = []
            for pos_data in data.get('positions', []):
                positions.append(Position(
                    ticker=pos_data['ticker'],
                    entry_date=pos_data['entry_date'],
                    entry_price=pos_data['entry_price'],
                    shares=pos_data['shares'],
                    pattern_type=pos_data.get('pattern_type', 'UNKNOWN'),
                    neckline_price=pos_data.get('neckline_price')
                ))
            
            return positions
        
        except Exception as e:
            print(f"  ⚠️ Could not load positions: {e}")
            return []
    
    def assess_health(
        self,
        positions: List[Position],
        current_edges: Dict[str, float],  # Ticker -> current edge from re-scan
        current_prices: Dict[str, float],  # Ticker -> current price
        exit_signals: Dict[str, str]  # Ticker -> exit reason (from Exit Guard)
    ) -> List[PositionHealth]:
        """
        Assess health of all positions.
        
        Args:
            positions: List of current positions
            current_edges: Dict of re-scanned edges
            current_prices: Dict of current prices
            exit_signals: Dict of exit signals from Exit Guard
            
        Returns:
            List of PositionHealth assessments
        """
        
        assessments = []
        
        for pos in positions:
            # Get current data
            current_price = current_prices.get(pos.ticker, pos.entry_price)
            current_edge = current_edges.get(pos.ticker, 0.0)
            exit_reason = exit_signals.get(pos.ticker)
            
            # Calculate metrics
            current_profit_pct = (current_price - pos.entry_price) / pos.entry_price
            
            # Estimate original edge (we don't have it stored, assume 5%)
            original_edge = 0.05  # Conservative assumption
            edge_degradation = original_edge - current_edge
            
            # Calculate days held
            try:
                entry_date = datetime.strptime(pos.entry_date, '%Y-%m-%d')
                days_held = (datetime.now() - entry_date).days
            except:
                days_held = 0
            
            # Determine action
            if exit_reason:
                # Exit Guard triggered
                action = "EXIT"
                reason = exit_reason
            elif current_edge < 0:
                # Edge turned negative
                action = "EXIT"
                reason = f"Edge degraded from {original_edge*100:.1f}% to {current_edge*100:.1f}%"
            elif current_edge < original_edge * 0.5:
                # Edge degraded significantly
                action = "EXIT"
                reason = f"Edge degraded {edge_degradation*100:.1f}% - thesis weakening"
            elif current_profit_pct > 0.20 and current_edge > 0.03:
                # Up 20%+ and still has edge - consider adding
                action = "ADD"
                reason = f"Strong momentum (+{current_profit_pct*100:.1f}%) and edge intact ({current_edge*100:.1f}%)"
            else:
                # Hold
                action = "HOLD"
                reason = f"Edge intact ({current_edge*100:+.1f}%), profit {current_profit_pct*100:+.1f}%"
            
            assessments.append(PositionHealth(
                ticker=pos.ticker,
                action=action,
                reason=reason,
                current_price=current_price,
                current_profit_pct=current_profit_pct,
                current_edge=current_edge,
                original_edge=original_edge,
                edge_degradation=edge_degradation,
                days_held=days_held
            ))
        
        return assessments
    
    def save_positions(self, positions: List[Position]):
        """Save positions to file."""
        
        data = {
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'positions': [
                {
                    'ticker': p.ticker,
                    'entry_date': p.entry_date,
                    'entry_price': p.entry_price,
                    'shares': p.shares,
                    'pattern_type': p.pattern_type,
                    'neckline_price': p.neckline_price
                }
                for p in positions
            ]
        }
        
        with open(self.positions_file, 'w') as f:
            json.dump(data, f, indent=2)
