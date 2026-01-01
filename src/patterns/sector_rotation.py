"""
Sector Rotation Pattern Detector

Renaissance principle: Sector leadership predicts market direction.
Growth vs Value, Cyclical vs Defensive rotation.
"""

import numpy as np
import yfinance as yf
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SectorSignal:
    """Sector rotation signal."""
    leading_sector: str
    lagging_sector: str
    rotation_strength: float
    description: str


class SectorRotationDetector:
    """
    Detects sector rotation patterns.
    
    Sectors:
    - XLK: Technology (growth)
    - XLF: Financials (cyclical)
    - XLE: Energy (cyclical)
    - XLV: Healthcare (defensive)
    - XLP: Consumer Staples (defensive)
    - XLI: Industrials (cyclical)
    """
    
    def __init__(self, lookback_period: str = "1y"):
        """Initialize sector rotation detector."""
        self.lookback_period = lookback_period
        self.sectors = {
            'XLK': 'Technology',
            'XLF': 'Financials',
            'XLE': 'Energy',
            'XLV': 'Healthcare',
            'XLP': 'Consumer Staples',
            'XLI': 'Industrials'
        }
    
    def fetch_sector_performance(self) -> Dict[str, float]:
        """Fetch recent sector performance."""
        performance = {}
        
        for ticker, name in self.sectors.items():
            try:
                data = yf.download(ticker, period=self.lookback_period, progress=False)
                if data is not None and not data.empty:
                    returns = data['Close'].pct_change().sum()  # Cumulative return
                    performance[name] = returns
            except:
                pass
        
        return performance
    
    def detect_rotation(self) -> List[SectorSignal]:
        """
        Detect sector rotation patterns.
        
        Returns:
            List of SectorSignal objects
        """
        perf = self.fetch_sector_performance()
        
        if len(perf) < 2:
            return []
        
        # Sort by performance
        sorted_sectors = sorted(perf.items(), key=lambda x: x[1], reverse=True)
        
        signals = []
        
        # Leader vs laggard
        if len(sorted_sectors) >= 2:
            leader = sorted_sectors[0]
            laggard = sorted_sectors[-1]
            
            strength = abs(leader[1] - laggard[1])
            
            if strength > 0.05:  # 5% differential
                signals.append(SectorSignal(
                    leading_sector=leader[0],
                    lagging_sector=laggard[0],
                    rotation_strength=strength,
                    description=f"{leader[0]} outperforming {laggard[0]} by {strength:.1%} → Rotate to {leader[0]}"
                ))
        
        # Growth vs Defensive
        growth = perf.get('Technology', 0)
        defensive = (perf.get('Healthcare', 0) + perf.get('Consumer Staples', 0)) / 2
        
        if abs(growth - defensive) > 0.05:
            if growth > defensive:
                signals.append(SectorSignal(
                    leading_sector='Growth',
                    lagging_sector='Defensive',
                    rotation_strength=growth - defensive,
                    description=f"Growth (Tech) outperforming Defensive → Risk-on environment"
                ))
            else:
                signals.append(SectorSignal(
                    leading_sector='Defensive',
                    lagging_sector='Growth',
                    rotation_strength=defensive - growth,
                    description=f"Defensive outperforming Growth → Risk-off environment"
                ))
        
        return signals
    
    def create_report(self, signals: List[SectorSignal]) -> str:
        """Create sector rotation report."""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("SECTOR ROTATION ANALYSIS")
        lines.append("=" * 80)
        
        if not signals:
            lines.append("\nNo significant sector rotation detected.")
            return "\n".join(lines)
        
        lines.append(f"\nRotation signals: {len(signals)}")
        lines.append("")
        
        for i, sig in enumerate(signals, 1):
            lines.append(f"{i}. {sig.description}")
            lines.append(f"   Strength: {sig.rotation_strength:.1%}")
        
        return "\n".join(lines)
