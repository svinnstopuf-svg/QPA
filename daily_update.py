"""
Daily Edge Calculator - Automated Pattern Monitoring

Renaissance principle: Monitor patterns daily. Alert when edge opportunities arise.
Recalculate all edges with fresh data. Track pattern degradation.
"""

import sys
from datetime import datetime
from typing import Dict, List
from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher
from src.analysis.bayesian_estimator import BayesianEdgeEstimator


class DailyUpdateEngine:
    """
    Daily update engine for pattern monitoring.
    
    Features:
    - Fetches latest market data
    - Recalculates all pattern edges
    - Detects tradeable opportunities
    - Sends alerts (console/email/webhook)
    """
    
    def __init__(
        self,
        tickers: List[str] = ["^GSPC", "^OMX"],
        min_edge_threshold: float = 0.10  # 0.10% after costs
    ):
        """
        Initialize daily update engine.
        
        Args:
            tickers: List of tickers to monitor
            min_edge_threshold: Minimum edge to trigger alert
        """
        self.tickers = tickers
        self.min_edge_threshold = min_edge_threshold
        self.data_fetcher = DataFetcher()
        self.bayesian = BayesianEdgeEstimator(min_threshold=0.001)
    
    def fetch_latest_data(self, ticker: str) -> 'MarketData':
        """Fetch latest market data for ticker."""
        print(f"Fetching latest data for {ticker}...")
        return self.data_fetcher.fetch_stock_data(ticker, period="15y")
    
    def analyze_ticker(self, ticker: str) -> Dict:
        """
        Run full analysis on ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Dictionary with analysis results
        """
        # Fetch data
        market_data = self.fetch_latest_data(ticker)
        if market_data is None:
            return {'ticker': ticker, 'error': 'Failed to fetch data'}
        
        # Initialize analyzer
        analyzer = QuantPatternAnalyzer(
            min_occurrences=15,
            min_confidence=0.55,
            forward_periods=1
        )
        
        # Run analysis
        analysis_results = analyzer.analyze_market_data(market_data)
        
        # Find tradeable strategies
        tradeable = []
        for result in analysis_results['results']:
            if result['pattern_eval'].is_significant:
                bayesian_est = result['bayesian_estimate']
                
                # Only alert if probability of edge > threshold is high
                if bayesian_est.probability_above_threshold > 0.75:
                    tradeable.append({
                        'pattern': result['situation'].description,
                        'edge': bayesian_est.point_estimate * 100,
                        'ci_95': bayesian_est.credible_interval_95,
                        'probability': bayesian_est.probability_above_threshold,
                        'sample_size': bayesian_est.sample_size,
                        'uncertainty': bayesian_est.uncertainty_level
                    })
        
        return {
            'ticker': ticker,
            'timestamp': datetime.now(),
            'total_patterns': len(analysis_results['results']),
            'significant_patterns': len(analysis_results['significant_patterns']),
            'tradeable_patterns': tradeable
        }
    
    def generate_alert(self, results: List[Dict]) -> str:
        """
        Generate alert message from analysis results.
        
        Args:
            results: List of analysis results per ticker
            
        Returns:
            Formatted alert message
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"DAILY EDGE UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 80)
        lines.append("")
        
        # Count total opportunities
        total_opportunities = sum(
            len(r.get('tradeable_patterns', []))
            for r in results
        )
        
        if total_opportunities == 0:
            lines.append("❌ No tradeable opportunities found today.")
            lines.append("")
            for result in results:
                lines.append(f"{result['ticker']}: {result['significant_patterns']} patterns analyzed, none tradeable")
            return "\n".join(lines)
        
        lines.append(f"✅ {total_opportunities} TRADEABLE OPPORTUNITIES FOUND!")
        lines.append("")
        
        for result in results:
            if result.get('error'):
                lines.append(f"❌ {result['ticker']}: {result['error']}")
                continue
            
            tradeable = result.get('tradeable_patterns', [])
            if not tradeable:
                continue
            
            lines.append(f"📊 {result['ticker']}")
            lines.append("-" * 80)
            
            for i, pattern in enumerate(tradeable, 1):
                lines.append(f"\n{i}. {pattern['pattern']}")
                lines.append(f"   Edge: {pattern['edge']:+.2f}%")
                lines.append(f"   95% CI: [{pattern['ci_95'][0]*100:+.2f}%, {pattern['ci_95'][1]*100:+.2f}%]")
                lines.append(f"   P(edge > 0.1%): {pattern['probability']:.1%}")
                lines.append(f"   Sample size: {pattern['sample_size']} ({pattern['uncertainty'].upper()} uncertainty)")
                
                if pattern['uncertainty'] == 'high':
                    lines.append(f"   ⚠️ WARNING: Small sample - use quarter Kelly (0.25x)")
                elif pattern['uncertainty'] == 'medium':
                    lines.append(f"   ⚠️ Use half Kelly (0.5x) due to moderate uncertainty")
                else:
                    lines.append(f"   ✅ Large sample - standard Kelly appropriate")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append("⚠️ IMPORTANT:")
        lines.append("   - Only trade patterns with P(edge > 0.1%) > 75%")
        lines.append("   - Adjust Kelly fraction based on uncertainty level")
        lines.append("   - Monitor out-of-sample performance continuously")
        lines.append("   - This is not investment advice")
        
        return "\n".join(lines)
    
    def run_daily_update(self) -> str:
        """
        Run daily update for all tickers.
        
        Returns:
            Alert message
        """
        print(f"\n{'='*80}")
        print(f"Starting daily update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        results = []
        for ticker in self.tickers:
            print(f"\nAnalyzing {ticker}...")
            result = self.analyze_ticker(ticker)
            results.append(result)
            print(f"  ✓ {ticker} complete: {result.get('significant_patterns', 0)} patterns found")
        
        # Generate alert
        alert = self.generate_alert(results)
        
        return alert


def main():
    """Main entry point for daily updates."""
    # Configure tickers to monitor
    tickers = ["^GSPC", "^OMX"]  # S&P 500, OMXS30
    
    # Can add more: ["^DJI", "^IXIC", "^FTSE", "AAPL", "MSFT"]
    
    # Run update
    engine = DailyUpdateEngine(tickers=tickers, min_edge_threshold=0.10)
    alert_message = engine.run_daily_update()
    
    # Display alert
    print("\n\n")
    print(alert_message)
    
    # TODO: Send email/webhook notification
    # send_email(alert_message)
    # send_slack_webhook(alert_message)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
