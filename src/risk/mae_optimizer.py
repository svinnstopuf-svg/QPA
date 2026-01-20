"""
MAE Optimization - Maximum Adverse Excursion Stop-Loss

Quantitative Principle:
Traditional fixed stop-losses (e.g. -5%) are arbitrary.
MAE (Maximum Adverse Excursion) measures how far price moved AGAINST you
before a trade completed. This reveals the natural "breathing room" needed.

Methodology:
1. For each historical trade, track MAE (worst drawdown during hold)
2. Calculate distribution of MAEs
3. Set stop at percentile (e.g. 85th) to avoid noise while protecting capital
4. Multiply by safety factor (e.g. 1.5x) for buffer

Example:
Historical MAEs: [-2%, -3%, -1.5%, -4%, -2.5%, -3.5%, -1%]
85th percentile: -3.7%
Stop-loss: -3.7% * 1.5 = -5.5%

This is tighter than arbitrary -5% but has statistical backing.
"""
from typing import List, Dict, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class MAEAnalysis:
    """Results from MAE analysis."""
    total_trades: int
    
    # MAE statistics
    mean_mae: float  # Average MAE (%)
    median_mae: float  # Median MAE (%)
    percentile_85_mae: float  # 85th percentile
    percentile_95_mae: float  # 95th percentile
    worst_mae: float  # Worst MAE
    
    # Recommended stops
    recommended_stop_85: float  # 85th percentile * 1.5
    recommended_stop_95: float  # 95th percentile * 1.5
    aggressive_stop: float  # Median * 1.5
    conservative_stop: float  # 95th * 1.5
    
    # Distribution
    mae_distribution: np.ndarray


class MAEOptimizer:
    """
    Calculates optimal stop-loss using Maximum Adverse Excursion.
    
    Philosophy: Let the data tell you where to stop, not arbitrary rules.
    """
    
    def __init__(
        self,
        safety_factor: float = 1.5,
        default_percentile: int = 85
    ):
        """
        Initialize MAE optimizer.
        
        Args:
            safety_factor: Multiplier for buffer (1.5 = 50% safety margin)
            default_percentile: Percentile to use for stop (85 = middle ground)
        """
        self.safety_factor = safety_factor
        self.default_percentile = default_percentile
    
    def analyze(
        self,
        prices: np.ndarray,
        entry_indices: List[int],
        exit_indices: List[int]
    ) -> MAEAnalysis:
        """
        Calculate MAE from historical trades.
        
        Args:
            prices: Price array
            entry_indices: List of entry indices
            exit_indices: List of exit indices (same length as entries)
            
        Returns:
            MAEAnalysis with recommendations
        """
        if len(entry_indices) != len(exit_indices):
            raise ValueError("Entry and exit indices must have same length")
        
        if len(entry_indices) == 0:
            return self._insufficient_data_result()
        
        # Calculate MAE for each trade
        maes = []
        
        for entry_idx, exit_idx in zip(entry_indices, exit_indices):
            if exit_idx <= entry_idx:
                continue  # Invalid trade
            
            entry_price = prices[entry_idx]
            trade_prices = prices[entry_idx:exit_idx+1]
            
            # MAE = worst drawdown during trade
            # Negative because it's drawdown
            mae_pct = ((np.min(trade_prices) - entry_price) / entry_price) * 100
            maes.append(mae_pct)
        
        if len(maes) == 0:
            return self._insufficient_data_result()
        
        maes = np.array(maes)
        
        # Calculate statistics
        mean_mae = np.mean(maes)
        median_mae = np.median(maes)
        p85_mae = np.percentile(maes, 85)
        p95_mae = np.percentile(maes, 95)
        worst_mae = np.min(maes)
        
        # Calculate recommended stops (with safety factor)
        # Note: MAE is negative, so we multiply by safety factor to go FURTHER negative
        rec_stop_85 = p85_mae * self.safety_factor
        rec_stop_95 = p95_mae * self.safety_factor
        aggressive_stop = median_mae * self.safety_factor
        conservative_stop = p95_mae * self.safety_factor
        
        return MAEAnalysis(
            total_trades=len(maes),
            mean_mae=mean_mae,
            median_mae=median_mae,
            percentile_85_mae=p85_mae,
            percentile_95_mae=p95_mae,
            worst_mae=worst_mae,
            recommended_stop_85=rec_stop_85,
            recommended_stop_95=rec_stop_95,
            aggressive_stop=aggressive_stop,
            conservative_stop=conservative_stop,
            mae_distribution=maes
        )
    
    def analyze_from_returns(
        self,
        forward_returns: List[List[float]]
    ) -> MAEAnalysis:
        """
        Calculate MAE from forward return paths.
        
        Simpler interface when you have return paths instead of price indices.
        
        Args:
            forward_returns: List of return paths (each path is list of % returns)
            
        Returns:
            MAEAnalysis
        """
        if len(forward_returns) == 0:
            return self._insufficient_data_result()
        
        maes = []
        
        for returns_path in forward_returns:
            if len(returns_path) == 0:
                continue
            
            # Convert to cumulative returns
            cum_returns = np.cumsum(returns_path)
            
            # MAE is worst cumulative return
            mae_pct = np.min(cum_returns)
            maes.append(mae_pct)
        
        if len(maes) == 0:
            return self._insufficient_data_result()
        
        maes = np.array(maes)
        
        # Same calculation as analyze()
        mean_mae = np.mean(maes)
        median_mae = np.median(maes)
        p85_mae = np.percentile(maes, 85)
        p95_mae = np.percentile(maes, 95)
        worst_mae = np.min(maes)
        
        rec_stop_85 = p85_mae * self.safety_factor
        rec_stop_95 = p95_mae * self.safety_factor
        aggressive_stop = median_mae * self.safety_factor
        conservative_stop = p95_mae * self.safety_factor
        
        return MAEAnalysis(
            total_trades=len(maes),
            mean_mae=mean_mae,
            median_mae=median_mae,
            percentile_85_mae=p85_mae,
            percentile_95_mae=p95_mae,
            worst_mae=worst_mae,
            recommended_stop_85=rec_stop_85,
            recommended_stop_95=rec_stop_95,
            aggressive_stop=aggressive_stop,
            conservative_stop=conservative_stop,
            mae_distribution=maes
        )
    
    def _insufficient_data_result(self) -> MAEAnalysis:
        """Return default result when no data."""
        return MAEAnalysis(
            total_trades=0,
            mean_mae=-5.0,
            median_mae=-5.0,
            percentile_85_mae=-5.0,
            percentile_95_mae=-5.0,
            worst_mae=-5.0,
            recommended_stop_85=-7.5,
            recommended_stop_95=-7.5,
            aggressive_stop=-7.5,
            conservative_stop=-7.5,
            mae_distribution=np.array([])
        )
    
    def format_report(self, analysis: MAEAnalysis) -> str:
        """Generate formatted report."""
        report = f"""
{'='*70}
MAE OPTIMIZATION ANALYSIS
{'='*70}

Historical Trades:   {analysis.total_trades}

MAE Distribution (Max Adverse Excursion):
  Mean:              {analysis.mean_mae:.2f}%
  Median:            {analysis.median_mae:.2f}%
  85th Percentile:   {analysis.percentile_85_mae:.2f}%
  95th Percentile:   {analysis.percentile_95_mae:.2f}%
  Worst:             {analysis.worst_mae:.2f}%

Recommended Stop-Losses (with {self.safety_factor}x safety factor):
  Aggressive:        {analysis.aggressive_stop:.2f}% (median-based)
  Balanced:          {analysis.recommended_stop_85:.2f}% (85th percentile)
  Conservative:      {analysis.conservative_stop:.2f}% (95th percentile)

Interpretation:
  - Aggressive stop catches 50% of historical MAEs
  - Balanced stop catches 85% of historical MAEs (recommended)
  - Conservative stop catches 95% of historical MAEs

Recommendation: Use {analysis.recommended_stop_85:.1f}% stop-loss
{'='*70}
"""
        return report


if __name__ == "__main__":
    # Test module
    print("Testing MAE Optimizer...")
    
    optimizer = MAEOptimizer(safety_factor=1.5)
    
    # Test Case 1: Price-based analysis
    print("\n1. Price-Based MAE Analysis:")
    
    # Simulate price series with trades
    prices = np.array([
        100, 101, 99, 102, 103, 105, 104, 106, 107, 105,
        108, 110, 109, 111, 112, 110, 113, 115, 114, 116
    ])
    
    # Trades: enter at idx, exit later
    entries = [0, 5, 10]
    exits = [4, 9, 14]
    
    analysis = optimizer.analyze(prices, entries, exits)
    print(optimizer.format_report(analysis))
    
    # Test Case 2: Returns-based analysis
    print("\n2. Returns-Based MAE Analysis:")
    
    # Simulate forward return paths
    np.random.seed(42)
    return_paths = []
    
    for _ in range(20):
        # Each trade: 10-day return path
        daily_returns = np.random.normal(0.002, 0.015, 10)  # 0.2% mean, 1.5% vol
        return_paths.append(daily_returns.tolist())
    
    analysis = optimizer.analyze_from_returns(return_paths)
    print(optimizer.format_report(analysis))
    
    # Test Case 3: High volatility scenario
    print("\n3. High Volatility MAE Analysis:")
    
    high_vol_paths = []
    for _ in range(20):
        daily_returns = np.random.normal(0.001, 0.03, 10)  # 3% daily vol
        high_vol_paths.append(daily_returns.tolist())
    
    analysis = optimizer.analyze_from_returns(high_vol_paths)
    print(optimizer.format_report(analysis))
    
    print("\n✅ MAE Optimizer - Tests Complete")
