"""
Enhetstester för OutcomeAnalyzer.
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.analysis.outcome_analyzer import OutcomeAnalyzer, OutcomeStatistics


class TestOutcomeAnalyzer:
    """Tester för OutcomeAnalyzer-klassen."""
    
    def setup_method(self):
        """Körs innan varje test."""
        self.analyzer = OutcomeAnalyzer()
        
    def test_analyze_outcomes_basic(self):
        """Testar grundläggande utfallsanalys."""
        returns = np.random.normal(0.01, 0.02, 50)
        
        stats = self.analyzer.analyze_outcomes(returns)
        
        assert isinstance(stats, OutcomeStatistics)
        assert stats.sample_size == 50
        assert -1 < stats.mean_return < 1
        assert stats.std_return >= 0
        
    def test_analyze_outcomes_empty(self):
        """Testar analys med tom data."""
        returns = np.array([])
        
        stats = self.analyzer.analyze_outcomes(returns)
        
        assert stats.sample_size == 0
        assert stats.mean_return == 0.0
        
    def test_win_rate_calculation(self):
        """Testar beräkning av vinstfrekvens."""
        # 70% positiva avkastningar
        returns = np.concatenate([np.full(70, 0.01), np.full(30, -0.01)])
        
        stats = self.analyzer.analyze_outcomes(returns)
        
        assert 0.65 < stats.win_rate < 0.75
        
    def test_calculate_forward_returns(self):
        """Testar beräkning av framtida avkastningar."""
        prices = np.array([100, 102, 101, 105, 103, 108])
        indices = np.array([0, 2])  # Index 0 och 2
        
        forward_returns = self.analyzer.calculate_forward_returns(
            prices,
            indices,
            forward_periods=2
        )
        
        assert len(forward_returns) == 2
        # Från index 0 till 2: (101-100)/100
        # Från index 2 till 4: (103-101)/101
        
    def test_compare_to_baseline(self):
        """Testar jämförelse med baslinje."""
        pattern_returns = np.random.normal(0.015, 0.02, 50)
        baseline_returns = np.random.normal(0.005, 0.02, 200)
        
        comparison = self.analyzer.compare_to_baseline(pattern_returns, baseline_returns)
        
        assert 'pattern_mean' in comparison
        assert 'baseline_mean' in comparison
        assert 'mean_difference' in comparison
        assert 'p_value' in comparison
        
    def test_risk_metrics_calculation(self):
        """Testar beräkning av riskmått."""
        returns = np.random.normal(0.01, 0.02, 100)
        
        risk_metrics = self.analyzer.calculate_risk_metrics(returns)
        
        assert 'sharpe_ratio' in risk_metrics
        assert 'sortino_ratio' in risk_metrics
        assert 'var_95' in risk_metrics
        assert 'max_drawdown' in risk_metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
