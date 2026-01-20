"""
RVOL (Relative Volume) Filter
==============================

Ensures sufficient liquidity and market conviction by comparing
current volume to historical average.

Key Concept:
RVOL > 1.0 = Above-average volume (strong conviction)
RVOL < 1.0 = Below-average volume (weak conviction, reduce score)

Usage:
- Calculate RVOL = current_volume / avg_volume_20d
- If RVOL < 1.0: Reduce score by 50%
- If RVOL < 0.5: Block signal entirely (dead zone)
"""

import numpy as np
from typing import Tuple
from dataclasses import dataclass


@dataclass
class RVOLAnalysis:
    """Results from RVOL analysis."""
    rvol: float  # Relative volume ratio
    current_volume: float  # Today's volume
    avg_volume_20d: float  # 20-day average
    conviction_level: str  # HIGH, MEDIUM, LOW, DEAD
    score_multiplier: float  # 1.0, 0.5, or 0.0
    recommendation: str  # Message for user


class RVOLFilter:
    """
    Relative Volume filter for liquidity validation.
    
    Philosophy:
    - No volume = No conviction = No trade
    - RVOL is a "truth serum" for signals
    - Institutions move markets with volume
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        dead_zone_threshold: float = 0.5,
        full_strength_threshold: float = 1.0
    ):
        """
        Initialize RVOL filter.
        
        Args:
            lookback_period: Days to average volume (default 20)
            dead_zone_threshold: Below this = block signal (default 0.5)
            full_strength_threshold: Above this = full strength (default 1.0)
        """
        self.lookback_period = lookback_period
        self.dead_zone = dead_zone_threshold
        self.full_strength = full_strength_threshold
    
    def analyze_rvol(
        self,
        volume: np.ndarray,
        current_volume: float = None
    ) -> RVOLAnalysis:
        """
        Analyze relative volume for a stock.
        
        Args:
            volume: Historical volume array
            current_volume: Today's volume (uses last value if None)
            
        Returns:
            RVOLAnalysis with conviction level and score multiplier
        """
        if len(volume) < self.lookback_period:
            # Not enough data
            return RVOLAnalysis(
                rvol=0.0,
                current_volume=0.0,
                avg_volume_20d=0.0,
                conviction_level="UNKNOWN",
                score_multiplier=0.0,
                recommendation="Insufficient volume data"
            )
        
        # Get current volume (last data point if not specified)
        if current_volume is None:
            current_volume = float(volume[-1])
        
        # Calculate 20-day average volume
        avg_volume_20d = float(np.mean(volume[-self.lookback_period:]))
        
        if avg_volume_20d == 0:
            # Avoid division by zero
            return RVOLAnalysis(
                rvol=0.0,
                current_volume=current_volume,
                avg_volume_20d=0.0,
                conviction_level="DEAD",
                score_multiplier=0.0,
                recommendation="Zero average volume - illiquid stock"
            )
        
        # Calculate RVOL
        rvol = current_volume / avg_volume_20d
        
        # Determine conviction level and score multiplier
        if rvol >= self.full_strength:
            # Strong volume = full strength
            conviction_level = "HIGH"
            score_multiplier = 1.0
            recommendation = f"RVOL {rvol:.2f}x - Strong conviction"
            
        elif rvol >= self.dead_zone:
            # Moderate volume = reduced strength
            conviction_level = "MEDIUM"
            score_multiplier = 0.5
            recommendation = f"RVOL {rvol:.2f}x - Weak volume, reduce position"
            
        else:
            # Dead zone = block signal
            conviction_level = "LOW"
            score_multiplier = 0.0
            recommendation = f"RVOL {rvol:.2f}x - Dead zone, block signal"
        
        return RVOLAnalysis(
            rvol=rvol,
            current_volume=current_volume,
            avg_volume_20d=avg_volume_20d,
            conviction_level=conviction_level,
            score_multiplier=score_multiplier,
            recommendation=recommendation
        )
    
    def apply_rvol_penalty(
        self,
        score: float,
        rvol_analysis: RVOLAnalysis
    ) -> Tuple[float, str]:
        """
        Apply RVOL penalty to score.
        
        Args:
            score: Original score (0-100)
            rvol_analysis: RVOL analysis result
            
        Returns:
            Tuple of (adjusted_score, message)
        """
        adjusted_score = score * rvol_analysis.score_multiplier
        
        if rvol_analysis.conviction_level == "HIGH":
            message = f"✅ RVOL {rvol_analysis.rvol:.2f}x - Full strength"
        elif rvol_analysis.conviction_level == "MEDIUM":
            message = f"⚠️ RVOL {rvol_analysis.rvol:.2f}x - Score reduced 50%"
        else:
            message = f"🚫 RVOL {rvol_analysis.rvol:.2f}x - BLOCKED (dead zone)"
        
        return adjusted_score, message
