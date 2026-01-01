"""
Analys av historiska utfall (Y-variabler).

Beräknar fördelning, statistik och drawdown för att förstå vad som historiskt
hänt efter specifika marknadssituationer.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from scipy import stats


@dataclass
class OutcomeStatistics:
    """Statistik över historiska utfall."""
    mean_return: float
    median_return: float
    std_return: float
    skewness: float
    kurtosis: float
    min_return: float
    max_return: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    sample_size: int
    
    
class OutcomeAnalyzer:
    """
    Analyserar historiska utfall (Y) efter marknadssituationer (X).
    
    Fokuserar på:
    - Fördelning av framtida avkastning
    - Statistiska mått
    - Vinst/förlust-frekvens
    - Maximal historisk drawdown
    """
    
    def __init__(self):
        pass
    
    def analyze_outcomes(
        self,
        returns: np.ndarray,
        forward_periods: int = 1
    ) -> OutcomeStatistics:
        """
        Analyserar framtida avkastningar för en given uppsättning observationer.
        
        Args:
            returns: Array med avkastningar efter identifierade situationer
            forward_periods: Antal perioder framåt som avkastningen mäts över
            
        Returns:
            OutcomeStatistics med omfattande statistik
        """
        if len(returns) == 0:
            return self._create_empty_statistics()
        
        # Grundläggande statistik
        mean_return = np.mean(returns)
        median_return = np.median(returns)
        std_return = np.std(returns)
        
        # Fördelningsegenskaper
        skewness = float(stats.skew(returns))
        kurtosis = float(stats.kurtosis(returns))
        
        # Extremvärden
        min_return = np.min(returns)
        max_return = np.max(returns)
        
        # Percentiler för att förstå fördelningen
        percentile_5 = np.percentile(returns, 5)
        percentile_25 = np.percentile(returns, 25)
        percentile_75 = np.percentile(returns, 75)
        percentile_95 = np.percentile(returns, 95)
        
        # Vinst/förlust-analys
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        win_rate = len(wins) / len(returns) if len(returns) > 0 else 0.0
        avg_win = np.mean(wins) if len(wins) > 0 else 0.0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0
        
        # Profit factor
        total_wins = np.sum(wins) if len(wins) > 0 else 0.0
        total_losses = abs(np.sum(losses)) if len(losses) > 0 else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Maximal drawdown
        max_drawdown = self._calculate_max_drawdown(returns)
        
        return OutcomeStatistics(
            mean_return=mean_return,
            median_return=median_return,
            std_return=std_return,
            skewness=skewness,
            kurtosis=kurtosis,
            min_return=min_return,
            max_return=max_return,
            percentile_5=percentile_5,
            percentile_25=percentile_25,
            percentile_75=percentile_75,
            percentile_95=percentile_95,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            sample_size=len(returns)
        )
    
    def compare_to_baseline(
        self,
        pattern_returns: np.ndarray,
        baseline_returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Jämför mönsterutfall med en baslinje (t.ex. hela marknaden).
        
        Args:
            pattern_returns: Avkastningar efter mönster
            baseline_returns: Baseline avkastningar (t.ex. alla perioder)
            
        Returns:
            Dictionary med jämförelsestatistik
        """
        if len(pattern_returns) == 0 or len(baseline_returns) == 0:
            return {}
        
        pattern_mean = np.mean(pattern_returns)
        baseline_mean = np.mean(baseline_returns)
        
        pattern_std = np.std(pattern_returns)
        baseline_std = np.std(baseline_returns)
        
        pattern_wins = np.sum(pattern_returns > 0) / len(pattern_returns)
        baseline_wins = np.sum(baseline_returns > 0) / len(baseline_returns)
        
        # T-test för att se om skillnaden är statistiskt signifikant
        t_stat, p_value = stats.ttest_ind(pattern_returns, baseline_returns)
        
        return {
            'pattern_mean': pattern_mean,
            'baseline_mean': baseline_mean,
            'mean_difference': pattern_mean - baseline_mean,
            'pattern_std': pattern_std,
            'baseline_std': baseline_std,
            'pattern_win_rate': pattern_wins,
            'baseline_win_rate': baseline_wins,
            'win_rate_difference': pattern_wins - baseline_wins,
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'is_significant_5pct': p_value < 0.05,
            'is_significant_1pct': p_value < 0.01
        }
    
    def analyze_return_distribution(
        self,
        returns: np.ndarray,
        bins: int = 50
    ) -> Dict[str, np.ndarray]:
        """
        Analyserar fördelningen av avkastningar i detalj.
        
        Args:
            returns: Array med avkastningar
            bins: Antal bins för histogrammet
            
        Returns:
            Dictionary med histogram och density information
        """
        if len(returns) == 0:
            return {
                'counts': np.array([]),
                'bin_edges': np.array([]),
                'density': np.array([])
            }
        
        counts, bin_edges = np.histogram(returns, bins=bins)
        density = counts / len(returns)
        
        return {
            'counts': counts,
            'bin_edges': bin_edges,
            'density': density,
            'bin_centers': (bin_edges[:-1] + bin_edges[1:]) / 2
        }
    
    def calculate_risk_metrics(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.0
    ) -> Dict[str, float]:
        """
        Beräknar olika riskmått.
        
        Args:
            returns: Array med avkastningar
            risk_free_rate: Riskfri ränta (annualiserad)
            
        Returns:
            Dictionary med riskmått
        """
        if len(returns) == 0:
            return {}
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe ratio (antag 252 handelsdagar för annualisering)
        excess_return = mean_return - (risk_free_rate / 252)
        sharpe_ratio = (excess_return * np.sqrt(252)) / std_return if std_return > 0 else 0.0
        
        # Sortino ratio (använd endast nedåtgående volatilitet)
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else std_return
        sortino_ratio = (excess_return * np.sqrt(252)) / downside_std if downside_std > 0 else 0.0
        
        # Value at Risk (VaR) vid 95% konfidens
        var_95 = np.percentile(returns, 5)
        
        # Conditional Value at Risk (CVaR) - genomsnittlig förlust bortom VaR
        returns_beyond_var = returns[returns <= var_95]
        cvar_95 = np.mean(returns_beyond_var) if len(returns_beyond_var) > 0 else var_95
        
        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown(returns)
        
        # Calmar ratio (annualiserad avkastning / max drawdown)
        annualized_return = mean_return * 252
        calmar_ratio = abs(annualized_return / max_drawdown) if max_drawdown < 0 else 0.0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'downside_std': downside_std
        }
    
    def calculate_forward_returns(
        self,
        prices: np.ndarray,
        indices: np.ndarray,
        forward_periods: int = 1
    ) -> np.ndarray:
        """
        Beräknar framtida avkastningar från specifika tidpunkter.
        
        Args:
            prices: Array med priser
            indices: Indices för de tidpunkter vi vill mäta framtida avkastning från
            forward_periods: Antal perioder framåt att mäta
            
        Returns:
            Array med framtida avkastningar
        """
        forward_returns = []
        
        for idx in indices:
            future_idx = idx + forward_periods
            if future_idx < len(prices):
                ret = (prices[future_idx] - prices[idx]) / prices[idx]
                forward_returns.append(ret)
        
        return np.array(forward_returns)
    
    def analyze_temporal_stability(
        self,
        returns: np.ndarray,
        timestamps: np.ndarray,
        n_splits: int = 4
    ) -> Dict[str, List[float]]:
        """
        Analyserar om mönstret är stabilt över tid.
        
        Args:
            returns: Array med avkastningar
            timestamps: Tidsstämplar för varje avkastning
            n_splits: Antal tidsperioder att dela upp i
            
        Returns:
            Dictionary med statistik per tidsperiod
        """
        if len(returns) < n_splits * 5:  # Minst 5 observationer per period
            return {'periods': [], 'means': [], 'stds': [], 'win_rates': []}
        
        # Sortera efter tidsstämpel
        sorted_indices = np.argsort(timestamps)
        sorted_returns = returns[sorted_indices]
        
        period_size = len(sorted_returns) // n_splits
        
        means = []
        stds = []
        win_rates = []
        periods = []
        
        for i in range(n_splits):
            start_idx = i * period_size
            end_idx = (i + 1) * period_size if i < n_splits - 1 else len(sorted_returns)
            
            period_returns = sorted_returns[start_idx:end_idx]
            
            if len(period_returns) > 0:
                means.append(np.mean(period_returns))
                stds.append(np.std(period_returns))
                win_rates.append(np.sum(period_returns > 0) / len(period_returns))
                periods.append(i + 1)
        
        return {
            'periods': periods,
            'means': means,
            'stds': stds,
            'win_rates': win_rates,
            'mean_variation': np.std(means) if len(means) > 0 else 0.0,
            'is_stable': np.std(means) < np.mean(np.abs(means)) * 0.5 if len(means) > 0 and np.mean(np.abs(means)) > 0 else False
        }
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Beräknar maximal drawdown från avkastningsserie."""
        if len(returns) == 0:
            return 0.0
        
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        return np.min(drawdown)
    
    def _create_empty_statistics(self) -> OutcomeStatistics:
        """Skapar tom statistik för fall utan data."""
        return OutcomeStatistics(
            mean_return=0.0,
            median_return=0.0,
            std_return=0.0,
            skewness=0.0,
            kurtosis=0.0,
            min_return=0.0,
            max_return=0.0,
            percentile_5=0.0,
            percentile_25=0.0,
            percentile_75=0.0,
            percentile_95=0.0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            max_drawdown=0.0,
            sample_size=0
        )
