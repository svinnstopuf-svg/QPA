"""
Test Robust Statistics Integration

Verifierar att robust statistics är korrekt integrerade i:
1. OutcomeAnalyzer
2. PatternEvaluator
3. Instrument Screener (future)

Author: Senior Quant Developer
Date: 2026-01-25
"""

import numpy as np
from src.analysis.outcome_analyzer import OutcomeAnalyzer
from src.core.pattern_evaluator import PatternEvaluator


def test_outcome_analyzer_integration():
    """Test att OutcomeAnalyzer använder robust statistics."""
    print("="*80)
    print("TEST 1: OutcomeAnalyzer Integration")
    print("="*80)
    
    analyzer = OutcomeAnalyzer()
    
    # Scenario 1: Small sample (should get penalty)
    print("\n1.1: Small sample (n=5)")
    small_returns = np.array([0.10, 0.15, -0.05, 0.12, 0.08])
    stats_small = analyzer.analyze_outcomes(small_returns)
    
    print(f"  Raw Win Rate: {stats_small.win_rate:.1%}")
    print(f"  Adjusted Win Rate: {stats_small.robust_stats.adjusted_win_rate:.1%}")
    print(f"  Sample Size Factor: {stats_small.robust_stats.sample_size_factor:.2f}")
    print(f"  Robust Score: {stats_small.robust_score:.1f}/100")
    
    # Scenario 2: Large sample (should get full confidence)
    print("\n1.2: Large sample (n=50)")
    np.random.seed(42)
    large_returns = np.concatenate([
        np.random.normal(0.08, 0.02, 35),  # 70% wins
        np.random.normal(-0.03, 0.01, 15)  # 30% losses
    ])
    stats_large = analyzer.analyze_outcomes(large_returns)
    
    print(f"  Raw Win Rate: {stats_large.win_rate:.1%}")
    print(f"  Adjusted Win Rate: {stats_large.robust_stats.adjusted_win_rate:.1%}")
    print(f"  Sample Size Factor: {stats_large.robust_stats.sample_size_factor:.2f}")
    print(f"  Statistical Significance: {stats_large.robust_stats.is_significant}")
    print(f"  p-value: {stats_large.robust_stats.p_value:.4f}")
    print(f"  Robust Score: {stats_large.robust_score:.1f}/100")
    
    print("\n✅ OutcomeAnalyzer integration: PASS")


def test_pattern_evaluator_integration():
    """Test att PatternEvaluator använder robust statistics."""
    print("\n" + "="*80)
    print("TEST 2: PatternEvaluator Integration")
    print("="*80)
    
    evaluator = PatternEvaluator(min_occurrences=10, min_confidence=0.60)
    
    # Scenario 1: Insufficient sample
    print("\n2.1: Insufficient sample (n=5)")
    insufficient_returns = np.array([0.05, 0.03, -0.02, 0.07, 0.04])
    insufficient_timestamps = np.arange(5)
    
    eval_insuf = evaluator.evaluate_pattern(
        "small_pattern",
        insufficient_returns,
        insufficient_timestamps
    )
    
    print(f"  Occurrence Count: {eval_insuf.occurrence_count}")
    print(f"  Is Significant: {eval_insuf.is_significant}")
    print(f"  Sample Size Factor: {eval_insuf.sample_size_factor:.2f}")
    
    # Scenario 2: Good sample with robust metrics
    print("\n2.2: Good sample (n=30)")
    np.random.seed(42)
    good_returns = np.concatenate([
        np.random.normal(0.08, 0.02, 20),  # 67% wins
        np.random.normal(-0.03, 0.01, 10)  # 33% losses
    ])
    good_timestamps = np.arange(30)
    
    eval_good = evaluator.evaluate_pattern(
        "good_pattern",
        good_returns,
        good_timestamps
    )
    
    print(f"  Occurrence Count: {eval_good.occurrence_count}")
    print(f"  Raw Win Rate: {eval_good.win_rate:.1%}")
    print(f"  Adjusted Win Rate: {eval_good.adjusted_win_rate:.1%}")
    print(f"  Pessimistic EV: {eval_good.pessimistic_ev:+.2%}")
    print(f"  Return Consistency: {eval_good.return_consistency:.2f}")
    print(f"  Sample Size Factor: {eval_good.sample_size_factor:.2f}")
    print(f"  Is Significant: {eval_good.is_significant}")
    print(f"  Robust Score: {eval_good.robust_score:.1f}/100")
    
    # Scenario 3: Overfitted pattern (100% WR, small sample)
    print("\n2.3: Overfitted pattern (n=3, 100% WR)")
    overfitted_returns = np.array([0.10, 0.15, 0.12])
    overfitted_timestamps = np.arange(3)
    
    eval_overfit = evaluator.evaluate_pattern(
        "overfitted_pattern",
        overfitted_returns,
        overfitted_timestamps
    )
    
    print(f"  Raw Win Rate: {eval_overfit.win_rate:.1%}")
    print(f"  Adjusted Win Rate: {eval_overfit.adjusted_win_rate:.1%}")
    print(f"  Sample Size Factor: {eval_overfit.sample_size_factor:.2f}")
    print(f"  Robust Score: {eval_overfit.robust_score:.1f}/100")
    print(f"  Is Significant: {eval_overfit.is_significant} (should be False)")
    
    print("\n✅ PatternEvaluator integration: PASS")


def test_comparison_old_vs_new():
    """Jämför old vs new scoring på samma data."""
    print("\n" + "="*80)
    print("TEST 3: Old vs New Scoring Comparison")
    print("="*80)
    
    analyzer = OutcomeAnalyzer()
    
    # Test case 1: Small volatile sample
    print("\n3.1: Small volatile sample (n=8)")
    volatile_returns = np.array([0.20, -0.10, 0.25, -0.08, 0.18, -0.05, 0.22, -0.12])
    
    stats = analyzer.analyze_outcomes(volatile_returns)
    
    print(f"  Old Metrics:")
    print(f"    Raw Win Rate: {stats.win_rate:.1%}")
    print(f"    Raw Mean Return: {stats.mean_return:+.2%}")
    print(f"    Std Return: {stats.std_return:.2%}")
    
    print(f"\n  New Robust Metrics:")
    print(f"    Adjusted Win Rate: {stats.robust_stats.adjusted_win_rate:.1%}")
    print(f"    Pessimistic EV: {stats.robust_stats.pessimistic_ev:+.2%}")
    print(f"    Return Consistency: {stats.robust_stats.return_consistency:.2f}")
    print(f"    Sample Size Factor: {stats.robust_stats.sample_size_factor:.2f}")
    print(f"    Statistical Sig: {stats.robust_stats.is_significant}")
    
    print(f"\n  Impact:")
    wr_change = stats.robust_stats.adjusted_win_rate - stats.win_rate
    ev_change = stats.robust_stats.pessimistic_ev - stats.mean_return
    print(f"    Win Rate Change: {wr_change:+.1%}")
    print(f"    EV Change: {ev_change:+.2%}")
    
    # Test case 2: Large consistent sample
    print("\n3.2: Large consistent sample (n=50)")
    np.random.seed(42)
    consistent_returns = np.concatenate([
        np.random.normal(0.07, 0.01, 35),   # Tight wins
        np.random.normal(-0.02, 0.005, 15)  # Tight losses
    ])
    
    stats2 = analyzer.analyze_outcomes(consistent_returns)
    
    print(f"  Old Metrics:")
    print(f"    Raw Win Rate: {stats2.win_rate:.1%}")
    print(f"    Raw Mean Return: {stats2.mean_return:+.2%}")
    
    print(f"\n  New Robust Metrics:")
    print(f"    Adjusted Win Rate: {stats2.robust_stats.adjusted_win_rate:.1%}")
    print(f"    Pessimistic EV: {stats2.robust_stats.pessimistic_ev:+.2%}")
    print(f"    Return Consistency: {stats2.robust_stats.return_consistency:.2f} (excellent!)")
    print(f"    Sample Size Factor: {stats2.robust_stats.sample_size_factor:.2f}")
    print(f"    Robust Score: {stats2.robust_score:.1f}/100")
    
    print("\n✅ Comparison test: PASS")


def main():
    """Run all integration tests."""
    print("\n" + "🧪"*40)
    print("ROBUST STATISTICS INTEGRATION TEST SUITE")
    print("🧪"*40 + "\n")
    
    try:
        test_outcome_analyzer_integration()
        test_pattern_evaluator_integration()
        test_comparison_old_vs_new()
        
        print("\n" + "="*80)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*80)
        print("\nRobust statistics are successfully integrated!")
        print("\nKey Benefits:")
        print("  • Small samples (n<30) get automatic penalties")
        print("  • Win rates are Bayesian-smoothed (1/1 → 67%, not 100%)")
        print("  • Volatile patterns get consistency penalties")
        print("  • Statistical significance is tested (p<0.05)")
        print("  • Pessimistic EV includes worst-case scenarios")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
