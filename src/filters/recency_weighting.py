"""
Recency Weighting - Time-Decay for Historical Data

Quantitative Principle:
Recent observations contain more information about current market state than old data.
Apply exponential decay to observations based on age.

Weighting Function:
- Last 30 days: weight = 1.0 (full strength)
- 30-60 days: weight = 0.5-1.0 (linear decay)
- 60-90 days: weight = 0.1-0.5 (strong decay)
- >90 days: weight = 0.1 (minimal influence)

Application:
- SNR calculation (weighted average of edges)
- Conviction scoring (recency-adjusted consistency)
- Pattern edge calculation (weight recent wins higher)
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np


class RecencyWeighting:
    """
    Applies time-decay weighting to historical observations.
    
    Philosophy: The half-life of alpha is ~30 days. Older data is stale.
    """
    
    def __init__(
        self,
        full_strength_days: int = 30,
        half_strength_days: int = 60,
        minimum_weight: float = 0.1
    ):
        """
        Initialize recency weighting calculator.
        
        Args:
            full_strength_days: Days at full weight (1.0)
            half_strength_days: Days at half weight (0.5)
            minimum_weight: Floor weight for old data
        """
        self.full_strength_days = full_strength_days
        self.half_strength_days = half_strength_days
        self.minimum_weight = minimum_weight
    
    def calculate_weight(self, days_ago: int) -> float:
        """
        Calculate time-decay weight for an observation.
        
        Decay Function:
        - [0, 30]: weight = 1.0
        - (30, 60]: weight = 1.0 - 0.5 * ((days - 30) / 30)
        - (60, 90]: weight = 0.5 - 0.4 * ((days - 60) / 30)
        - >90: weight = 0.1
        
        Args:
            days_ago: Number of days since observation
            
        Returns:
            Weight between 0.1 and 1.0
        """
        if days_ago <= self.full_strength_days:
            return 1.0
        elif days_ago <= self.half_strength_days:
            # Linear decay from 1.0 to 0.5
            progress = (days_ago - self.full_strength_days) / (self.half_strength_days - self.full_strength_days)
            return 1.0 - (0.5 * progress)
        elif days_ago <= 90:
            # Linear decay from 0.5 to 0.1
            progress = (days_ago - self.half_strength_days) / (90 - self.half_strength_days)
            return 0.5 - (0.4 * progress)
        else:
            return self.minimum_weight
    
    def calculate_weighted_average(
        self,
        values: List[float],
        dates: List[str],
        reference_date: str = None
    ) -> float:
        """
        Calculate recency-weighted average.
        
        Args:
            values: List of numerical values (e.g. edges, scores)
            dates: List of dates (YYYY-MM-DD format)
            reference_date: Date to calculate from (default: today)
            
        Returns:
            Weighted average
        """
        if not values or not dates or len(values) != len(dates):
            return 0.0
        
        # Parse reference date
        if reference_date is None:
            ref = datetime.now()
        else:
            ref = datetime.strptime(reference_date, "%Y-%m-%d")
        
        # Calculate weights
        weights = []
        for date_str in dates:
            try:
                obs_date = datetime.strptime(date_str, "%Y-%m-%d")
                days_ago = (ref - obs_date).days
                weight = self.calculate_weight(days_ago)
                weights.append(weight)
            except:
                weights.append(self.minimum_weight)  # Fallback for bad dates
        
        # Weighted average
        weights = np.array(weights)
        values = np.array(values)
        
        total_weight = np.sum(weights)
        if total_weight == 0:
            return 0.0
        
        return np.sum(values * weights) / total_weight
    
    def calculate_weighted_snr(
        self,
        edges: List[float],
        dates: List[str],
        volatility: float,
        reference_date: str = None
    ) -> float:
        """
        Calculate recency-weighted Signal-to-Noise Ratio.
        
        SNR = Weighted_Edge / Volatility
        
        Args:
            edges: List of edge values (%)
            dates: List of dates (YYYY-MM-DD)
            volatility: ATR estimate (%)
            reference_date: Reference date (default: today)
            
        Returns:
            Weighted SNR
        """
        if volatility == 0:
            return 0.0
        
        weighted_edge = self.calculate_weighted_average(edges, dates, reference_date)
        return weighted_edge / volatility
    
    def calculate_weighted_consistency(
        self,
        investable_flags: List[bool],
        dates: List[str],
        reference_date: str = None
    ) -> float:
        """
        Calculate recency-weighted consistency score.
        
        Recent investable days count more than old ones.
        
        Args:
            investable_flags: List of booleans (True = investable day)
            dates: List of dates
            reference_date: Reference date (default: today)
            
        Returns:
            Weighted consistency (0-100)
        """
        if not investable_flags or not dates:
            return 0.0
        
        # Convert bools to floats
        values = [1.0 if flag else 0.0 for flag in investable_flags]
        
        # Calculate weighted average
        weighted_avg = self.calculate_weighted_average(values, dates, reference_date)
        
        return weighted_avg * 100  # Convert to 0-100 scale
    
    def analyze_recency_impact(
        self,
        values: List[float],
        dates: List[str],
        reference_date: str = None
    ) -> Dict:
        """
        Analyze how recency weighting affects the average.
        
        Useful for debugging and understanding impact.
        
        Args:
            values: List of values
            dates: List of dates
            reference_date: Reference date
            
        Returns:
            Dict with analysis metrics
        """
        if not values or not dates:
            return {
                'unweighted_avg': 0.0,
                'weighted_avg': 0.0,
                'impact': 0.0,
                'recent_avg_30d': 0.0,
                'old_avg_60d_plus': 0.0
            }
        
        # Parse reference date
        if reference_date is None:
            ref = datetime.now()
        else:
            ref = datetime.strptime(reference_date, "%Y-%m-%d")
        
        # Calculate unweighted average
        unweighted_avg = np.mean(values)
        
        # Calculate weighted average
        weighted_avg = self.calculate_weighted_average(values, dates, reference_date)
        
        # Recent vs old averages
        recent_values = []
        old_values = []
        
        for i, date_str in enumerate(dates):
            try:
                obs_date = datetime.strptime(date_str, "%Y-%m-%d")
                days_ago = (ref - obs_date).days
                
                if days_ago <= 30:
                    recent_values.append(values[i])
                elif days_ago >= 60:
                    old_values.append(values[i])
            except:
                pass
        
        recent_avg = np.mean(recent_values) if recent_values else 0.0
        old_avg = np.mean(old_values) if old_values else 0.0
        
        return {
            'unweighted_avg': unweighted_avg,
            'weighted_avg': weighted_avg,
            'impact': weighted_avg - unweighted_avg,
            'recent_avg_30d': recent_avg,
            'old_avg_60d_plus': old_avg,
            'recency_advantage': recent_avg - old_avg
        }
    
    def format_analysis_report(
        self,
        ticker: str,
        values: List[float],
        dates: List[str],
        value_type: str = "Edge"
    ) -> str:
        """
        Generate formatted analysis report.
        
        Args:
            ticker: Instrument ticker
            values: List of values
            dates: List of dates
            value_type: Type of value (e.g. "Edge", "Score")
            
        Returns:
            Formatted report string
        """
        analysis = self.analyze_recency_impact(values, dates)
        
        report = f"""
{'='*60}
RECENCY WEIGHTING ANALYSIS: {ticker}
{'='*60}

{value_type} Analysis:
  Unweighted Average: {analysis['unweighted_avg']:.2f}
  Weighted Average:   {analysis['weighted_avg']:.2f}
  Impact:             {analysis['impact']:+.2f}

Time Buckets:
  Recent (0-30d):     {analysis['recent_avg_30d']:.2f}
  Old (60d+):         {analysis['old_avg_60d_plus']:.2f}
  Recency Advantage:  {analysis['recency_advantage']:+.2f}

Interpretation:
  {'Recent data STRONGER than old' if analysis['impact'] > 0 else 'Recent data WEAKER than old'}
  {'✅ Positive trend' if analysis['recency_advantage'] > 0 else '⚠️ Negative trend'}
{'='*60}
"""
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Recency Weighting Module...")
    
    weighting = RecencyWeighting()
    
    # Test weight calculation
    print("\n1. Weight Decay Function:")
    test_days = [0, 15, 30, 45, 60, 75, 90, 120]
    for days in test_days:
        weight = weighting.calculate_weight(days)
        print(f"  {days:3d} days ago: weight = {weight:.2f}")
    
    # Test weighted average
    print("\n2. Weighted Average (Improving Trend):")
    values = [1.0, 1.2, 1.5, 1.8, 2.0]  # Improving over time
    dates = [
        (datetime.now() - timedelta(days=80)).strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
    ]
    
    unweighted = np.mean(values)
    weighted = weighting.calculate_weighted_average(values, dates)
    
    print(f"  Unweighted: {unweighted:.2f}")
    print(f"  Weighted:   {weighted:.2f}")
    print(f"  Impact:     {weighted - unweighted:+.2f} (should be positive)")
    
    # Test SNR
    print("\n3. Weighted SNR:")
    snr = weighting.calculate_weighted_snr(values, dates, volatility=1.5)
    print(f"  SNR: {snr:.2f}")
    
    # Full analysis report
    print(weighting.format_analysis_report("TEST.ST", values, dates, "Edge"))
    
    print("\n✅ Recency Weighting Module - Tests Complete")
