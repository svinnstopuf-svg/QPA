"""
Monte Carlo Simulation för Risk Validation

"Hur stor är risken att jag förlorar 20% av mitt kapital trots att jag har en edge?"

Detta är den ultimata uppgraderingen för kvartalsvisa genomgångar.
Genom att simulera 10,000+ scenarier får du svar på:
- Sannolikhet för olika drawdowns
- Förväntat worst-case scenario
- Validering av Kelly-faktor
- Statistisk förväntning av förlustsviter

Philosophy: Kasinot vet exakt hur mycket de kan förlora i värsta fall.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Optional matplotlib for plotting
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class TradingStats:
    """Historical trading statistics."""
    win_rate: float  # % of winning trades
    avg_win: float  # Average win %
    avg_loss: float  # Average loss %
    num_trades: int  # Number of trades per period
    kelly_fraction: float = 0.25  # Fraction of Kelly to use


@dataclass
class SimulationResult:
    """Monte Carlo simulation results."""
    final_capitals: np.ndarray  # Final capital for each simulation
    max_drawdowns: np.ndarray  # Max drawdown for each simulation
    worst_drawdown: float  # Worst observed drawdown
    median_return: float  # Median return
    prob_ruin: float  # Probability of >50% loss
    prob_20pct_dd: float  # Probability of 20% drawdown
    prob_30pct_dd: float  # Probability of 30% drawdown
    percentile_5: float  # 5th percentile return
    percentile_95: float  # 95th percentile return


class MonteCarloSimulator:
    """
    Monte Carlo simulator for trading system validation.
    
    Given historical win rate, avg win, and avg loss, simulates
    thousands of possible futures to understand risk.
    
    Usage:
        stats = TradingStats(win_rate=0.55, avg_win=2.5, avg_loss=-1.2, num_trades=50)
        sim = MonteCarloSimulator()
        result = sim.run_simulation(stats, num_simulations=10000)
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,  # Starting capital (SEK)
        time_periods: int = 252  # Trading days (1 year)
    ):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            initial_capital: Starting capital
            time_periods: Number of periods to simulate
        """
        self.initial_capital = initial_capital
        self.time_periods = time_periods
    
    def run_simulation(
        self,
        stats: TradingStats,
        num_simulations: int = 10000,
        seed: int = None
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation.
        
        Args:
            stats: Historical trading statistics
            num_simulations: Number of simulations to run
            seed: Random seed for reproducibility
            
        Returns:
            SimulationResult with risk metrics
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Arrays to store results
        final_capitals = np.zeros(num_simulations)
        max_drawdowns = np.zeros(num_simulations)
        
        # Run simulations
        for i in range(num_simulations):
            capital_path = self._simulate_one_path(stats)
            final_capitals[i] = capital_path[-1]
            max_drawdowns[i] = self._calculate_max_drawdown(capital_path)
        
        # Calculate statistics
        final_returns = (final_capitals / self.initial_capital - 1) * 100
        
        result = SimulationResult(
            final_capitals=final_capitals,
            max_drawdowns=max_drawdowns,
            worst_drawdown=np.max(max_drawdowns),
            median_return=np.median(final_returns),
            prob_ruin=np.mean(max_drawdowns > 50),  # >50% loss
            prob_20pct_dd=np.mean(max_drawdowns > 20),
            prob_30pct_dd=np.mean(max_drawdowns > 30),
            percentile_5=np.percentile(final_returns, 5),
            percentile_95=np.percentile(final_returns, 95)
        )
        
        return result
    
    def _simulate_one_path(self, stats: TradingStats) -> np.ndarray:
        """
        Simulate one capital path.
        
        Args:
            stats: Trading statistics
            
        Returns:
            Array of capital values over time
        """
        capital = self.initial_capital
        capital_path = np.zeros(self.time_periods + 1)
        capital_path[0] = capital
        
        # Calculate trades per period
        trades_per_period = stats.num_trades / self.time_periods
        
        for t in range(1, self.time_periods + 1):
            # Determine number of trades this period (Poisson-like)
            num_trades = np.random.poisson(trades_per_period)
            
            for _ in range(num_trades):
                # Win or loss?
                is_win = np.random.random() < stats.win_rate
                
                if is_win:
                    # Win: sample from distribution around avg_win
                    # Add some variance (±30%)
                    return_pct = stats.avg_win * (1 + np.random.normal(0, 0.3))
                else:
                    # Loss: sample from distribution around avg_loss
                    return_pct = stats.avg_loss * (1 + np.random.normal(0, 0.3))
                
                # Apply Kelly fraction to position size
                # Position size = kelly_fraction * capital
                # But we use a fraction of Kelly for safety
                edge = stats.win_rate * stats.avg_win + (1 - stats.win_rate) * stats.avg_loss
                
                if stats.avg_win > 0:
                    kelly_optimal = edge / stats.avg_win
                else:
                    kelly_optimal = 0
                
                # Actual position size (fraction of capital)
                position_fraction = kelly_optimal * stats.kelly_fraction
                position_fraction = np.clip(position_fraction, 0, 0.10)  # Max 10% per trade
                
                # Calculate P&L
                pnl = capital * position_fraction * (return_pct / 100)
                capital += pnl
                
                # Prevent negative capital
                if capital < 0:
                    capital = 0
                    break
            
            capital_path[t] = capital
            
            if capital == 0:
                # Ruin - stay at zero
                capital_path[t:] = 0
                break
        
        return capital_path
    
    def _calculate_max_drawdown(self, capital_path: np.ndarray) -> float:
        """
        Calculate maximum drawdown %.
        
        Args:
            capital_path: Array of capital values
            
        Returns:
            Max drawdown as percentage
        """
        if len(capital_path) == 0:
            return 0
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(capital_path)
        
        # Calculate drawdown at each point
        drawdown = (running_max - capital_path) / running_max * 100
        
        return np.max(drawdown)
    
    def plot_simulation_results(
        self,
        result: SimulationResult,
        output_path: str = None
    ):
        """
        Plot simulation results.
        
        Args:
            result: SimulationResult to plot
            output_path: Optional path to save plot
        """
        if not HAS_MATPLOTLIB:
            print("Warning: matplotlib not installed. Install with: pip install matplotlib")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Final returns distribution
        final_returns = (result.final_capitals / self.initial_capital - 1) * 100
        axes[0, 0].hist(final_returns, bins=50, alpha=0.7, edgecolor='black')
        axes[0, 0].axvline(result.median_return, color='red', 
                          linestyle='--', label=f'Median: {result.median_return:.1f}%')
        axes[0, 0].axvline(result.percentile_5, color='orange',
                          linestyle='--', label=f'5th %ile: {result.percentile_5:.1f}%')
        axes[0, 0].set_xlabel('Final Return (%)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Distribution of Final Returns')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        # Max drawdown distribution
        axes[0, 1].hist(result.max_drawdowns, bins=50, alpha=0.7, 
                       edgecolor='black', color='coral')
        axes[0, 1].axvline(result.worst_drawdown, color='red',
                          linestyle='--', label=f'Worst: {result.worst_drawdown:.1f}%')
        axes[0, 1].axvline(20, color='orange', linestyle='--', label='20% DD')
        axes[0, 1].set_xlabel('Max Drawdown (%)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Distribution of Max Drawdowns')
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)
        
        # Sample paths
        num_sample_paths = 100
        for i in range(num_sample_paths):
            # Re-run one simulation for path
            path = self._simulate_one_path(
                TradingStats(
                    win_rate=0.55,  # Placeholder - should use actual stats
                    avg_win=2.5,
                    avg_loss=-1.2,
                    num_trades=50
                )
            )
            returns = (path / self.initial_capital - 1) * 100
            axes[1, 0].plot(returns, alpha=0.1, color='blue')
        
        axes[1, 0].axhline(0, color='black', linestyle='--', linewidth=1)
        axes[1, 0].set_xlabel('Time Period')
        axes[1, 0].set_ylabel('Return (%)')
        axes[1, 0].set_title(f'Sample Paths (n={num_sample_paths})')
        axes[1, 0].grid(alpha=0.3)
        
        # Risk metrics table
        axes[1, 1].axis('off')
        risk_text = f"""
        RISK METRICS
        {'='*40}
        
        Median Return: {result.median_return:.1f}%
        5th Percentile: {result.percentile_5:.1f}%
        95th Percentile: {result.percentile_95:.1f}%
        
        Worst Drawdown: {result.worst_drawdown:.1f}%
        Prob(DD > 20%): {result.prob_20pct_dd*100:.1f}%
        Prob(DD > 30%): {result.prob_30pct_dd*100:.1f}%
        Prob(Ruin >50%): {result.prob_ruin*100:.1f}%
        
        {'='*40}
        Interpretation:
        - DD > 20% är {self._interpret_prob(result.prob_20pct_dd)}
        - Förlustsviter är statistiskt förväntade
        - Kelly-fraktion kan justeras baserat på risk
        """
        axes[1, 1].text(0.1, 0.5, risk_text, fontsize=10, 
                       verticalalignment='center', family='monospace')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {output_path}")
        else:
            plt.show()
    
    def _interpret_prob(self, prob: float) -> str:
        """Interpret probability level."""
        if prob < 0.05:
            return "mycket osannolikt (<5%)"
        elif prob < 0.20:
            return "osannolikt (<20%)"
        elif prob < 0.50:
            return "möjligt (20-50%)"
        else:
            return "troligt (>50%)"
    
    def generate_recommendations(
        self,
        result: SimulationResult,
        current_kelly_fraction: float
    ) -> str:
        """
        Generate recommendations based on simulation.
        
        Args:
            result: Simulation result
            current_kelly_fraction: Current Kelly fraction
            
        Returns:
            Recommendations text
        """
        lines = []
        lines.append("=" * 80)
        lines.append("MONTE CARLO RISK RECOMMENDATIONS")
        lines.append("=" * 80)
        lines.append("")
        
        # Risk assessment
        lines.append("📊 RISK ASSESSMENT")
        lines.append("-" * 80)
        lines.append(f"Median Return: {result.median_return:+.1f}%")
        lines.append(f"5th Percentile (bad year): {result.percentile_5:+.1f}%")
        lines.append(f"95th Percentile (good year): {result.percentile_95:+.1f}%")
        lines.append("")
        lines.append(f"Worst Drawdown Observed: {result.worst_drawdown:.1f}%")
        lines.append(f"Probability of 20% Drawdown: {result.prob_20pct_dd*100:.1f}%")
        lines.append(f"Probability of 30% Drawdown: {result.prob_30pct_dd*100:.1f}%")
        lines.append("")
        
        # Kelly adjustment
        lines.append("🎯 KELLY FRACTION RECOMMENDATION")
        lines.append("-" * 80)
        
        if result.prob_20pct_dd > 0.30:
            new_kelly = current_kelly_fraction * 0.7
            lines.append(f"⚠️  HIGH RISK - Reduce Kelly from {current_kelly_fraction:.2f} to {new_kelly:.2f}")
            lines.append(f"   Reason: {result.prob_20pct_dd*100:.1f}% risk of 20% drawdown")
        elif result.prob_20pct_dd > 0.15:
            lines.append(f"✅ ACCEPTABLE RISK - Keep Kelly at {current_kelly_fraction:.2f}")
            lines.append(f"   20% drawdown risk: {result.prob_20pct_dd*100:.1f}%")
        else:
            new_kelly = min(current_kelly_fraction * 1.2, 0.50)
            lines.append(f"📈 LOW RISK - Can increase Kelly from {current_kelly_fraction:.2f} to {new_kelly:.2f}")
            lines.append(f"   20% drawdown risk only: {result.prob_20pct_dd*100:.1f}%")
        
        lines.append("")
        
        # Psychological preparation
        lines.append("🧠 PSYCHOLOGICAL PREPARATION")
        lines.append("-" * 80)
        lines.append("Förlustsviter är STATISTISKT FÖRVÄNTADE:")
        lines.append(f"- I 5% av scenarier: Avkastning < {result.percentile_5:+.1f}%")
        lines.append(f"- Median scenario: {result.median_return:+.1f}%")
        lines.append(f"- Värsta drawdown: {result.worst_drawdown:.1f}%")
        lines.append("")
        lines.append("Detta ger dig lugn som Beslutsfattare - drawdowns är normala!")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def format_simulation_report(
    result: SimulationResult,
    stats: TradingStats
) -> str:
    """Format simulation report."""
    lines = []
    lines.append("=" * 80)
    lines.append("MONTE CARLO SIMULATION REPORT")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("📈 INPUT STATISTICS")
    lines.append("-" * 80)
    lines.append(f"Win Rate: {stats.win_rate*100:.1f}%")
    lines.append(f"Avg Win: {stats.avg_win:+.2f}%")
    lines.append(f"Avg Loss: {stats.avg_loss:+.2f}%")
    lines.append(f"Trades per Period: {stats.num_trades}")
    lines.append(f"Kelly Fraction: {stats.kelly_fraction:.2f}")
    lines.append("")
    
    lines.append("🎲 SIMULATION RESULTS")
    lines.append("-" * 80)
    lines.append(f"Median Return: {result.median_return:+.1f}%")
    lines.append(f"5th Percentile: {result.percentile_5:+.1f}%")
    lines.append(f"95th Percentile: {result.percentile_95:+.1f}%")
    lines.append("")
    lines.append(f"Worst Drawdown: {result.worst_drawdown:.1f}%")
    lines.append(f"Prob(DD > 20%): {result.prob_20pct_dd*100:.1f}%")
    lines.append(f"Prob(DD > 30%): {result.prob_30pct_dd*100:.1f}%")
    lines.append(f"Prob(Ruin): {result.prob_ruin*100:.2f}%")
    lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    print("Monte Carlo Simulator")
    print("\nExample:")
    print("  from src.analysis.monte_carlo import MonteCarloSimulator, TradingStats")
    print("  stats = TradingStats(win_rate=0.55, avg_win=2.5, avg_loss=-1.2, num_trades=50)")
    print("  sim = MonteCarloSimulator()")
    print("  result = sim.run_simulation(stats, num_simulations=10000)")
    print("  print(format_simulation_report(result, stats))")
