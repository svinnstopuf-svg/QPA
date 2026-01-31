"""
Hard Limits - Non-Negotiable Risk Constraints

1. MAE Hard Cap (6% Stop-Loss Maximum)
   - Optimal_Stop = abs(Avg_MAE) × 1.5
   - If stop requires >6% → REJECT trade
   - Philosophy: If volatility is too high, setup is not tradeable

2. Sector Diversification Limit
   - Max 3 positions per GICS sector
   - Setup #4 in same sector requires +10% Robust_Score vs #3
   - Philosophy: Avoid sector concentration risk

These are ABSOLUTE limits. No exceptions.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import defaultdict


@dataclass
class MAELimitCheck:
    """Result of MAE hard cap validation"""
    ticker: str
    optimal_stop_pct: float
    passed: bool  # stop <= 6%
    avg_mae: float
    safety_factor: float
    reason: str


@dataclass
class SectorDiversificationCheck:
    """Result of sector diversification check"""
    ticker: str
    sector: str
    sector_count: int  # How many already in this sector
    passed: bool
    
    # If sector_count == 3, requires higher robust score
    robust_score_required: Optional[float]
    robust_score_actual: float
    robust_score_penalty: Optional[float]  # +10% if #4 in sector
    
    reason: str


class HardLimits:
    """
    Enforces non-negotiable risk limits.
    
    Principle: Om matematiken inte konvergerar, existerar inte affären.
    """
    
    MAE_HARD_CAP = 0.06  # 6% maximum stop-loss
    MAX_POSITIONS_PER_SECTOR = 3
    SECTOR_PENALTY_PCT = 0.10  # +10% Robust Score required for #4
    
    def __init__(self):
        pass
    
    def check_mae_limit(
        self,
        ticker: str,
        avg_loss: float,
        safety_factor: float = 1.5
    ) -> MAELimitCheck:
        """
        Check if MAE-based stop-loss is within hard cap.
        
        Args:
            ticker: Stock ticker
            avg_loss: Average loss from pattern (negative value)
            safety_factor: Multiplier for stop-loss (default 1.5)
        
        Returns:
            MAELimitCheck with pass/fail
        """
        if avg_loss >= 0:
            # No historical losses - cannot calculate MAE
            # Use default 6% (at the limit)
            optimal_stop = self.MAE_HARD_CAP
            passed = True
            reason = f"✅ No historical losses - default stop {optimal_stop*100:.1f}%"
        else:
            # Calculate optimal stop with safety factor
            avg_mae = abs(avg_loss)
            optimal_stop = avg_mae * safety_factor
            
            if optimal_stop <= self.MAE_HARD_CAP:
                passed = True
                reason = f"✅ MAE PASS: Stop {optimal_stop*100:.1f}% ≤ {self.MAE_HARD_CAP*100:.0f}% hard cap"
            else:
                passed = False
                reason = (
                    f"❌ MAE HARD CAP EXCEEDED: "
                    f"Stop requires {optimal_stop*100:.1f}% "
                    f"(avg MAE {avg_mae*100:.1f}% × {safety_factor}) "
                    f"> {self.MAE_HARD_CAP*100:.0f}% cap. "
                    f"Volatility too high - REJECT TRADE."
                )
        
        return MAELimitCheck(
            ticker=ticker,
            optimal_stop_pct=optimal_stop,
            passed=passed,
            avg_mae=abs(avg_loss) if avg_loss < 0 else 0.0,
            safety_factor=safety_factor,
            reason=reason
        )
    
    def check_sector_diversification(
        self,
        ticker: str,
        sector: str,
        robust_score: float,
        existing_setups: List,
        sector_map: Dict[str, str]
    ) -> SectorDiversificationCheck:
        """
        Check sector diversification limit.
        
        Rules:
        - Max 3 positions per GICS sector
        - If this would be #4, require Robust_Score ≥ (best_in_sector + 10%)
        
        Args:
            ticker: Current ticker
            sector: GICS sector
            robust_score: Robust score for this setup
            existing_setups: List of higher-ranked setups
            sector_map: Dict[ticker, sector]
        
        Returns:
            SectorDiversificationCheck with pass/fail
        """
        # Count how many setups already in this sector
        sector_count = sum(
            1 for setup in existing_setups
            if sector_map.get(setup.ticker, "Unknown") == sector
        )
        
        if sector_count < self.MAX_POSITIONS_PER_SECTOR:
            # Under limit - OK
            return SectorDiversificationCheck(
                ticker=ticker,
                sector=sector,
                sector_count=sector_count,
                passed=True,
                robust_score_required=None,
                robust_score_actual=robust_score,
                robust_score_penalty=None,
                reason=f"✅ Sector OK: {sector_count}/{self.MAX_POSITIONS_PER_SECTOR} positions in {sector}"
            )
        
        # At limit (3) - would be #4
        # Find best robust score in this sector from existing setups
        sector_robust_scores = [
            setup.robust_score
            for setup in existing_setups
            if sector_map.get(setup.ticker, "Unknown") == sector
            and hasattr(setup, 'robust_score')
        ]
        
        if len(sector_robust_scores) > 0:
            best_in_sector = max(sector_robust_scores)
            required_score = best_in_sector + (best_in_sector * self.SECTOR_PENALTY_PCT)
        else:
            # No robust scores found - use default
            required_score = robust_score + 10.0
        
        passed = robust_score >= required_score
        
        if passed:
            reason = (
                f"✅ Sector PASS: Would be #4 in {sector} but Robust Score "
                f"{robust_score:.1f} ≥ required {required_score:.1f} "
                f"(best +10%)"
            )
        else:
            reason = (
                f"❌ SECTOR LIMIT: Already {sector_count} in {sector}. "
                f"Setup #4 requires Robust Score ≥{required_score:.1f} "
                f"(current: {robust_score:.1f}). "
                f"REJECT to maintain diversification."
            )
        
        return SectorDiversificationCheck(
            ticker=ticker,
            sector=sector,
            sector_count=sector_count,
            passed=passed,
            robust_score_required=required_score,
            robust_score_actual=robust_score,
            robust_score_penalty=self.SECTOR_PENALTY_PCT,
            reason=reason
        )
    
    def validate_setup(
        self,
        ticker: str,
        sector: str,
        robust_score: float,
        avg_loss: float,
        existing_setups: List,
        sector_map: Dict[str, str]
    ) -> tuple[bool, MAELimitCheck, SectorDiversificationCheck]:
        """
        Run both hard limit checks.
        
        Args:
            ticker: Stock ticker
            sector: GICS sector
            robust_score: Robust score
            avg_loss: Average loss (negative)
            existing_setups: Higher-ranked setups
            sector_map: Dict[ticker, sector]
        
        Returns:
            (passed_both: bool, mae_check, sector_check)
        """
        # Check MAE hard cap
        mae_check = self.check_mae_limit(ticker, avg_loss)
        
        # Check sector diversification
        sector_check = self.check_sector_diversification(
            ticker,
            sector,
            robust_score,
            existing_setups,
            sector_map
        )
        
        # Both must pass
        passed_both = mae_check.passed and sector_check.passed
        
        return passed_both, mae_check, sector_check
