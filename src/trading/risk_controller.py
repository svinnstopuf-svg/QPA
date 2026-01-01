"""
Dynamic Risk Control System

Renaissance principle: Patterns degrade over time. 
Adapt position sizes based on realized vs expected performance.
Auto-disable patterns that stop working.
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RiskLimits:
    """Risk limits for a pattern."""
    max_drawdown_pct: float  # Max allowed drawdown (%)
    max_position_size: float  # Max position size (fraction)
    min_sharpe: float  # Min required Sharpe ratio
    lookback_window: int  # Days to evaluate performance


@dataclass
class PatternRiskStatus:
    """Current risk status of a pattern."""
    pattern_id: str
    is_enabled: bool
    current_kelly: float
    base_kelly: float
    adjustment_factor: float  # Multiplier on base Kelly
    reason: str  # Why adjusted
    current_drawdown: float
    current_sharpe: float
    trades_last_period: int


class DynamicRiskController:
    """
    Controls risk dynamically based on realized performance.
    
    Features:
    1. Adaptive Kelly: Reduce size if pattern underperforms
    2. Drawdown limits: Disable pattern if DD exceeds threshold
    3. Performance tracking: Monitor realized vs expected
    4. Auto-recovery: Re-enable patterns when they recover
    """
    
    def __init__(
        self,
        default_max_drawdown: float = 0.20,  # 20% max DD
        default_min_sharpe: float = 0.5,  # Min Sharpe to stay active
        lookback_window: int = 60,  # 60 days for evaluation
        adjustment_speed: float = 0.1  # How fast to adjust (0-1)
    ):
        """
        Initialize risk controller.
        
        Args:
            default_max_drawdown: Default max drawdown threshold
            default_min_sharpe: Default min Sharpe threshold
            lookback_window: Days to look back for performance eval
            adjustment_speed: Speed of Kelly adjustment (0.1 = slow, 1.0 = instant)
        """
        self.default_max_drawdown = default_max_drawdown
        self.default_min_sharpe = default_min_sharpe
        self.lookback_window = lookback_window
        self.adjustment_speed = adjustment_speed
        
        # Track pattern states
        self.pattern_states: Dict[str, PatternRiskStatus] = {}
    
    def calculate_realized_performance(
        self,
        returns: np.ndarray,
        lookback: Optional[int] = None
    ) -> tuple:
        """
        Calculate realized performance metrics.
        
        Args:
            returns: Historical returns
            lookback: Days to look back (None = all)
            
        Returns:
            Tuple of (sharpe, max_dd, mean_return, num_trades)
        """
        if lookback:
            returns = returns[-lookback:]
        
        if len(returns) == 0:
            return 0.0, 0.0, 0.0, 0
        
        # Sharpe ratio
        mean_ret = np.mean(returns)
        std_ret = np.std(returns)
        sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0
        
        # Max drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = np.min(drawdown)
        
        return sharpe, max_dd, mean_ret, len(returns)
    
    def calculate_adaptive_kelly(
        self,
        base_kelly: float,
        expected_sharpe: float,
        realized_sharpe: float,
        expected_return: float,
        realized_return: float
    ) -> tuple:
        """
        Calculate adjusted Kelly based on realized vs expected performance.
        
        If pattern underperforms: reduce Kelly
        If pattern overperforms: increase Kelly (capped)
        
        Args:
            base_kelly: Original Kelly fraction
            expected_sharpe: Expected Sharpe ratio
            realized_sharpe: Realized Sharpe ratio
            expected_return: Expected return
            realized_return: Realized return
            
        Returns:
            Tuple of (adjusted_kelly, adjustment_factor, reason)
        """
        # Performance ratio
        sharpe_ratio = realized_sharpe / expected_sharpe if expected_sharpe > 0 else 0
        return_ratio = realized_return / expected_return if expected_return != 0 else 0
        
        # Combined performance metric (weighted)
        perf_score = 0.7 * sharpe_ratio + 0.3 * (1 + return_ratio)
        
        # Adjustment factor (conservative)
        if perf_score > 1.2:
            # Outperforming - modest increase
            adjustment = 1.0 + (perf_score - 1.0) * self.adjustment_speed * 0.5
            adjustment = min(adjustment, 1.3)  # Cap at 1.3x
            reason = "Outperforming - modest increase"
        elif perf_score < 0.7:
            # Underperforming - aggressive decrease
            adjustment = perf_score * (1 - self.adjustment_speed)
            adjustment = max(adjustment, 0.2)  # Floor at 0.2x
            reason = "Underperforming - reduced size"
        else:
            # Normal performance
            adjustment = 1.0
            reason = "Normal performance"
        
        adjusted_kelly = base_kelly * adjustment
        
        return adjusted_kelly, adjustment, reason
    
    def check_risk_limits(
        self,
        pattern_id: str,
        realized_sharpe: float,
        realized_drawdown: float,
        risk_limits: Optional[RiskLimits] = None
    ) -> tuple:
        """
        Check if pattern violates risk limits.
        
        Args:
            pattern_id: Pattern identifier
            realized_sharpe: Current Sharpe ratio
            realized_drawdown: Current drawdown
            risk_limits: Custom risk limits (None = use defaults)
            
        Returns:
            Tuple of (is_enabled, reason)
        """
        if risk_limits is None:
            max_dd = self.default_max_drawdown
            min_sharpe = self.default_min_sharpe
        else:
            max_dd = risk_limits.max_drawdown_pct
            min_sharpe = risk_limits.min_sharpe
        
        # Check drawdown limit
        if realized_drawdown < -max_dd:
            return False, f"Drawdown {realized_drawdown:.1%} exceeds limit {-max_dd:.1%}"
        
        # Check Sharpe limit
        if realized_sharpe < min_sharpe:
            return False, f"Sharpe {realized_sharpe:.2f} below minimum {min_sharpe:.2f}"
        
        return True, "Within limits"
    
    def update_pattern_risk(
        self,
        pattern_id: str,
        base_kelly: float,
        expected_sharpe: float,
        expected_return: float,
        historical_returns: np.ndarray,
        risk_limits: Optional[RiskLimits] = None
    ) -> PatternRiskStatus:
        """
        Update risk status for a pattern based on recent performance.
        
        Args:
            pattern_id: Pattern identifier
            base_kelly: Base Kelly fraction
            expected_sharpe: Expected Sharpe (from backtest)
            expected_return: Expected return per trade
            historical_returns: Recent realized returns
            risk_limits: Optional custom risk limits
            
        Returns:
            PatternRiskStatus with current risk state
        """
        # Calculate realized metrics
        realized_sharpe, realized_dd, realized_return, num_trades = \
            self.calculate_realized_performance(historical_returns, self.lookback_window)
        
        # Check risk limits
        is_enabled, limit_reason = self.check_risk_limits(
            pattern_id, realized_sharpe, realized_dd, risk_limits
        )
        
        if not is_enabled:
            # Pattern disabled - set Kelly to 0
            status = PatternRiskStatus(
                pattern_id=pattern_id,
                is_enabled=False,
                current_kelly=0.0,
                base_kelly=base_kelly,
                adjustment_factor=0.0,
                reason=f"DISABLED: {limit_reason}",
                current_drawdown=realized_dd,
                current_sharpe=realized_sharpe,
                trades_last_period=num_trades
            )
        else:
            # Calculate adaptive Kelly
            adjusted_kelly, adjustment, adj_reason = self.calculate_adaptive_kelly(
                base_kelly,
                expected_sharpe,
                realized_sharpe,
                expected_return,
                realized_return
            )
            
            status = PatternRiskStatus(
                pattern_id=pattern_id,
                is_enabled=True,
                current_kelly=adjusted_kelly,
                base_kelly=base_kelly,
                adjustment_factor=adjustment,
                reason=adj_reason,
                current_drawdown=realized_dd,
                current_sharpe=realized_sharpe,
                trades_last_period=num_trades
            )
        
        # Store state
        self.pattern_states[pattern_id] = status
        
        return status
    
    def create_risk_report(self, risk_statuses: List[PatternRiskStatus]) -> str:
        """
        Create risk control report.
        
        Args:
            risk_statuses: List of PatternRiskStatus objects
            
        Returns:
            Formatted report
        """
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("DYNAMIC RISK CONTROL (Adaptive Position Sizing)")
        lines.append("=" * 80)
        lines.append(f"Lookback window: {self.lookback_window} days")
        lines.append(f"Max drawdown limit: {self.default_max_drawdown:.1%}")
        lines.append(f"Min Sharpe required: {self.default_min_sharpe:.2f}")
        lines.append("")
        
        # Active patterns
        active = [s for s in risk_statuses if s.is_enabled]
        disabled = [s for s in risk_statuses if not s.is_enabled]
        
        lines.append(f"Active Patterns: {len(active)}")
        lines.append(f"Disabled Patterns: {len(disabled)}")
        lines.append("")
        
        if active:
            lines.append("ACTIVE PATTERNS:")
            lines.append("-" * 80)
            for status in active:
                lines.append(f"\n{status.pattern_id}")
                lines.append(f"  Base Kelly: {status.base_kelly:.2%}")
                lines.append(f"  Adjusted Kelly: {status.current_kelly:.2%} " +
                           f"({status.adjustment_factor:.2f}x)")
                lines.append(f"  Reason: {status.reason}")
                lines.append(f"  Recent Sharpe: {status.current_sharpe:.2f}")
                lines.append(f"  Current Drawdown: {status.current_drawdown:.1%}")
                lines.append(f"  Trades (last {self.lookback_window}d): {status.trades_last_period}")
        
        if disabled:
            lines.append("\n\nDISABLED PATTERNS (Auto-stopped):")
            lines.append("-" * 80)
            for status in disabled:
                lines.append(f"\n❌ {status.pattern_id}")
                lines.append(f"  {status.reason}")
                lines.append(f"  Recent Sharpe: {status.current_sharpe:.2f}")
                lines.append(f"  Current Drawdown: {status.current_drawdown:.1%}")
        
        lines.append("\n\n⚠️ Renaissance principle: Cut losers fast, let winners run.")
        lines.append("⚠️ Patterns are automatically disabled when they stop working.")
        
        return "\n".join(lines)
