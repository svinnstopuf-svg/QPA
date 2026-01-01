"""
Enhetstester för PatternEvaluator.
"""

import numpy as np
import pytest
from datetime import datetime, timedelta
import sys
import os

# Lägg till src till path för imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.pattern_evaluator import PatternEvaluator, PatternEvaluation


class TestPatternEvaluator:
    """Tester för PatternEvaluator-klassen."""
    
    def setup_method(self):
        """Körs innan varje test."""
        self.evaluator = PatternEvaluator(
            min_occurrences=10,
            min_confidence=0.60
        )
    
    def test_evaluate_pattern_sufficient_data(self):
        """Testar utvärdering med tillräcklig data."""
        # Skapa syntetisk data
        returns = np.random.normal(0.01, 0.02, 50)
        timestamps = np.array([datetime(2020, 1, 1) + timedelta(days=i) for i in range(50)])
        
        result = self.evaluator.evaluate_pattern("test_pattern", returns, timestamps)
        
        assert isinstance(result, PatternEvaluation)
        assert result.pattern_id == "test_pattern"
        assert result.occurrence_count == 50
        assert result.sample_size == 50
        
    def test_evaluate_pattern_insufficient_data(self):
        """Testar utvärdering med otillräcklig data."""
        returns = np.array([0.01, 0.02, -0.01])
        timestamps = np.array([datetime(2020, 1, 1) + timedelta(days=i) for i in range(3)])
        
        result = self.evaluator.evaluate_pattern("test_pattern", returns, timestamps)
        
        assert result.is_significant == False
        assert result.occurrence_count == 3
        
    def test_max_drawdown_calculation(self):
        """Testar beräkning av max drawdown."""
        returns = np.array([0.1, 0.05, -0.15, -0.10, 0.20])
        
        result = self.evaluator.evaluate_pattern(
            "test_pattern",
            returns,
            np.array([datetime(2020, 1, 1) + timedelta(days=i) for i in range(len(returns))])
        )
        
        assert result.max_drawdown < 0  # Drawdown ska vara negativ
        
    def test_confidence_calculation(self):
        """Testar att konfidensberäkningen ger rimliga värden."""
        # Konsekvent positiva avkastningar
        returns = np.full(30, 0.01)
        timestamps = np.array([datetime(2020, 1, 1) + timedelta(days=i) for i in range(30)])
        
        result = self.evaluator.evaluate_pattern("test_pattern", returns, timestamps)
        
        assert 0 <= result.confidence_level <= 1
        assert result.confidence_level > 0.5  # Bör ha hög konfidensgrad
        
    def test_stability_score(self):
        """Testar att stabilitetsscore beräknas."""
        returns = np.random.normal(0.01, 0.02, 100)
        timestamps = np.array([datetime(2020, 1, 1) + timedelta(days=i) for i in range(100)])
        
        result = self.evaluator.evaluate_pattern("test_pattern", returns, timestamps)
        
        assert 0 <= result.stability_score <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
