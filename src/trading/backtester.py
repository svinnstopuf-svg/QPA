"""
Backtesting Engine - Test Strategies on Historical Data

Jim Simons principle: Test everything on out-of-sample data.
Account for all costs and realistic slippage.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BacktestResult:
    """Results from backtesting a strategy."""
    total_return: float  # %
    annual_return: float  # %
    sharpe_ratio: float
    max_drawdown: float  # %
    win_rate: float
    num_trades: int
    profit_factor: float
    avg_trade: float  # %
    best_trade: float  # %
    worst_trade: float  # %
    equity_curve: np.ndarray
    trade_log: List[Dict]
    
    @property
    def rating(self) -> str:
        """Rate strategy based on Sharpe ratio."""
        if self.sharpe_ratio >= 2.0:
            return "EXCELLENT"
        elif self.sharpe_ratio >= 1.0:
            return "GOOD"
        elif self.sharpe_ratio >= 0.5:
            return "MODERATE"
        else:
            return "POOR"


class Backtester:
    """
    Backtests trading strategies on historical data.
    
    Features:
    - Realistic transaction costs
    - Slippage modeling
    - Position sizing
    - Walk-forward analysis
    - Out-of-sample testing
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,
        transaction_cost: float = 0.0002,  # 0.02% per trade
        slippage: float = 0.0001,  # 0.01% slippage
        position_size: float = 1.0  # 100% of capital per trade
    ):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital
            transaction_cost: Cost per trade (%)
            slippage: Price slippage (%)
            position_size: Fraction of capital to trade
        """
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        self.position_size = position_size
    
    def backtest_pattern(
        self,
        pattern_indices: np.ndarray,
        forward_returns: np.ndarray,
        timestamps: np.ndarray
    ) -> BacktestResult:
        """
        Backtest a single pattern on historical data.
        
        Args:
            pattern_indices: Indices where pattern occurred
            forward_returns: Returns following pattern
            timestamps: Timestamps of pattern occurrences
            
        Returns:
            BacktestResult with performance metrics
        """
        capital = self.initial_capital
        equity_curve = [capital]
        trade_log = []
        
        wins = 0
        gross_profit = 0
        gross_loss = 0
        
        for i, ret in enumerate(forward_returns):
            # Calculate trade
            position_value = capital * self.position_size
            
            # Apply costs
            total_cost = self.transaction_cost + self.slippage
            net_return = ret - total_cost
            
            # Calculate P&L
            pnl = position_value * net_return
            capital += pnl
            equity_curve.append(capital)
            
            # Log trade
            trade_log.append({
                'timestamp': timestamps[i] if i < len(timestamps) else None,
                'return': ret,
                'net_return': net_return,
                'pnl': pnl,
                'capital': capital
            })
            
            # Track wins/losses
            if net_return > 0:
                wins += 1
                gross_profit += abs(pnl)
            else:
                gross_loss += abs(pnl)
        
        # Calculate metrics
        equity_curve = np.array(equity_curve)
        total_return = (capital - self.initial_capital) / self.initial_capital * 100
        
        # Annualize (assume 252 trading days per year)
        num_years = len(forward_returns) / 252
        annual_return = (np.power(capital / self.initial_capital, 1/num_years) - 1) * 100 if num_years > 0 else 0
        
        # Sharpe ratio
        returns = np.diff(equity_curve) / equity_curve[:-1]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Max drawdown
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max * 100
        max_drawdown = np.min(drawdown)
        
        # Win rate
        win_rate = wins / len(forward_returns) if len(forward_returns) > 0 else 0
        
        # Profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Trade statistics
        net_returns = [t['net_return'] for t in trade_log]
        avg_trade = np.mean(net_returns) * 100 if net_returns else 0
        best_trade = np.max(net_returns) * 100 if net_returns else 0
        worst_trade = np.min(net_returns) * 100 if net_returns else 0
        
        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            num_trades=len(forward_returns),
            profit_factor=profit_factor,
            avg_trade=avg_trade,
            best_trade=best_trade,
            worst_trade=worst_trade,
            equity_curve=equity_curve,
            trade_log=trade_log
        )
    
    def walk_forward_test(
        self,
        pattern_indices: np.ndarray,
        forward_returns: np.ndarray,
        timestamps: np.ndarray,
        train_ratio: float = 0.7
    ) -> Tuple[BacktestResult, BacktestResult]:
        """
        Walk-forward analysis: train on first X%, test on remaining.
        
        Args:
            pattern_indices: Pattern occurrence indices
            forward_returns: Forward returns
            timestamps: Timestamps
            train_ratio: Fraction of data to use for training
            
        Returns:
            Tuple of (in_sample_result, out_of_sample_result)
        """
        split_idx = int(len(forward_returns) * train_ratio)
        
        # In-sample (training period)
        in_sample_returns = forward_returns[:split_idx]
        in_sample_timestamps = timestamps[:split_idx]
        in_sample_result = self.backtest_pattern(
            pattern_indices[:split_idx],
            in_sample_returns,
            in_sample_timestamps
        )
        
        # Out-of-sample (testing period)
        out_sample_returns = forward_returns[split_idx:]
        out_sample_timestamps = timestamps[split_idx:]
        out_sample_result = self.backtest_pattern(
            pattern_indices[split_idx:],
            out_sample_returns,
            out_sample_timestamps
        )
        
        return in_sample_result, out_sample_result
    
    def create_backtest_report(
        self,
        result: BacktestResult,
        pattern_name: str = "Pattern",
        period_type: str = "Full Period"
    ) -> str:
        """
        Create formatted backtest report.
        
        Args:
            result: BacktestResult to format
            pattern_name: Name of pattern tested
            period_type: "Full Period", "In-Sample", "Out-of-Sample"
            
        Returns:
            Formatted report
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"BACKTEST RESULTAT - {pattern_name} ({period_type})")
        lines.append("=" * 80)
        lines.append("")
        
        # Performance metrics
        lines.append("📊 PRESTANDA:")
        lines.append(f"  Total avkastning: {result.total_return:+.2f}%")
        lines.append(f"  Årlig avkastning: {result.annual_return:+.2f}%")
        lines.append(f"  Sharpe ratio: {result.sharpe_ratio:.2f}")
        lines.append(f"  Max drawdown: {result.max_drawdown:.2f}%")
        lines.append("")
        
        # Trade statistics
        lines.append("📈 HANDEL:")
        lines.append(f"  Antal trades: {result.num_trades}")
        lines.append(f"  Vinstfrekvens: {result.win_rate*100:.1f}%")
        lines.append(f"  Genomsnittlig trade: {result.avg_trade:+.3f}%")
        lines.append(f"  Bästa trade: {result.best_trade:+.2f}%")
        lines.append(f"  Sämsta trade: {result.worst_trade:.2f}%")
        lines.append(f"  Profit factor: {result.profit_factor:.2f}")
        lines.append("")
        
        # Rating
        if result.sharpe_ratio >= 2.0 and result.max_drawdown > -10:
            rating = "🌟 EXCELLENT - Institutionell kvalitet"
        elif result.sharpe_ratio >= 1.0 and result.max_drawdown > -20:
            rating = "✅ GOOD - Handelbar strategi"
        elif result.sharpe_ratio >= 0.5:
            rating = "⚠️ MODERATE - Kräver förbättring"
        else:
            rating = "❌ POOR - Ej handelbar"
        
        lines.append(f"BEDÖMNING: {rating}")
        
        return "\n".join(lines)
