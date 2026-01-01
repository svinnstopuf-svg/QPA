"""
Permutation testing for validating pattern edge against randomness.

This is Jim Simons' approach: prove that patterns are better than
random day assignments through Monte Carlo simulation.
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PermutationTestResult:
    """Results from permutation test."""
    real_mean_return: float
    random_mean_returns: np.ndarray
    percentile_rank: float  # 0-100: where real pattern ranks among shuffled
    is_better_than_random: bool
    p_value: float
    n_permutations: int


class PermutationTester:
    """
    Tests if patterns are statistically better than random.
    
    Method: 
    1. Take the observed pattern's returns
    2. Create 1000+ random patterns by shuffling day assignments
    3. Compare real pattern to distribution of random patterns
    4. Show percentile rank: "Better than 95% of random patterns"
    """
    
    def __init__(self, n_permutations: int = 1000):
        """
        Initialize permutation tester.
        
        Args:
            n_permutations: Number of random shuffles to generate
        """
        self.n_permutations = n_permutations
    
    def test_pattern(
        self,
        pattern_returns: np.ndarray,
        all_market_returns: np.ndarray,
        pattern_size: int
    ) -> PermutationTestResult:
        """
        Test if a pattern's performance is better than random.
        
        Args:
            pattern_returns: Actual returns from the pattern
            all_market_returns: All available market returns
            pattern_size: Number of observations in pattern
            
        Returns:
            PermutationTestResult with statistical validation
        """
        if len(pattern_returns) == 0:
            return PermutationTestResult(
                real_mean_return=0.0,
                random_mean_returns=np.array([]),
                percentile_rank=0.0,
                is_better_than_random=False,
                p_value=1.0,
                n_permutations=0
            )
        
        # Calculate real pattern mean
        real_mean = np.mean(pattern_returns)
        
        # Generate random patterns by shuffling
        random_means = []
        rng = np.random.RandomState(42)  # For reproducibility
        
        for _ in range(self.n_permutations):
            # Randomly select pattern_size returns from all market returns
            if len(all_market_returns) >= pattern_size:
                random_indices = rng.choice(len(all_market_returns), size=pattern_size, replace=False)
                random_returns = all_market_returns[random_indices]
                random_means.append(np.mean(random_returns))
            else:
                # If not enough data, use bootstrapping
                random_returns = rng.choice(all_market_returns, size=pattern_size, replace=True)
                random_means.append(np.mean(random_returns))
        
        random_means = np.array(random_means)
        
        # Calculate percentile rank
        # How many random patterns are worse than the real pattern?
        if real_mean >= 0:
            # For positive patterns: how many are below us?
            n_worse = np.sum(random_means < real_mean)
        else:
            # For negative patterns: how many are above us (more negative)?
            n_worse = np.sum(random_means > real_mean)
        
        percentile_rank = (n_worse / self.n_permutations) * 100
        
        # P-value: probability of seeing this or better by chance
        if real_mean >= 0:
            p_value = np.sum(random_means >= real_mean) / self.n_permutations
        else:
            p_value = np.sum(random_means <= real_mean) / self.n_permutations
        
        # Threshold: better than 90% of random patterns
        is_better_than_random = percentile_rank >= 90.0
        
        return PermutationTestResult(
            real_mean_return=real_mean,
            random_mean_returns=random_means,
            percentile_rank=percentile_rank,
            is_better_than_random=is_better_than_random,
            p_value=p_value,
            n_permutations=self.n_permutations
        )
    
    def format_result(self, result: PermutationTestResult) -> str:
        """
        Format permutation test result for user display.
        
        Args:
            result: PermutationTestResult to format
            
        Returns:
            Formatted string
        """
        lines = []
        lines.append("### Shuffle Test (Validering mot slumpen)")
        lines.append(f"Mönstrets avkastning: {result.real_mean_return*100:.2f}%")
        lines.append(f"Jämfört med {result.n_permutations} slumpmässiga dagindelningar:")
        lines.append(f"**Bättre än {result.percentile_rank:.1f}% av slumpmässiga mönster**")
        
        if result.is_better_than_random:
            lines.append("✅ Detta mönster är statistiskt bättre än slump")
        else:
            lines.append("❌ Detta mönster är INTE tydligt bättre än slump")
            lines.append("⚠️ Kan vara överanpassning eller brus")
        
        lines.append(f"P-värde: {result.p_value:.3f}")
        
        return "\n".join(lines)
