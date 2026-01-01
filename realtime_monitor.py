"""
Real-Time Signal Monitor

Renaissance principle: Monitor patterns continuously.
Alert immediately when high-confidence patterns activate.
"""

import time
import sys
from datetime import datetime
from typing import List, Dict
from src import QuantPatternAnalyzer
from src.utils.data_fetcher import DataFetcher
from src.patterns.technical_patterns import TechnicalPatternDetector


class RealtimeSignalMonitor:
    """
    Monitors market in real-time for pattern activation.
    
    Features:
    - Polls market data every N minutes
    - Detects pattern activation
    - Alerts when high-confidence signals appear
    - Tracks edge estimates in real-time
    """
    
    def __init__(
        self,
        tickers: List[str] = ["^GSPC"],
        poll_interval: int = 300,  # 5 minutes
        min_confidence: float = 0.75  # 75% P(edge > threshold)
    ):
        """
        Initialize real-time monitor.
        
        Args:
            tickers: List of tickers to monitor
            poll_interval: Seconds between checks
            min_confidence: Minimum P(edge > threshold) to alert
        """
        self.tickers = tickers
        self.poll_interval = poll_interval
        self.min_confidence = min_confidence
        self.data_fetcher = DataFetcher()
        self.last_alerts = {}  # Prevent duplicate alerts
    
    def check_patterns(self, ticker: str) -> List[Dict]:
        """
        Check for active patterns on ticker.
        
        Returns:
            List of active pattern alerts
        """
        # Fetch latest data
        market_data = self.data_fetcher.fetch_stock_data(ticker, period="5y")
        if market_data is None:
            return []
        
        # Initialize analyzer
        analyzer = QuantPatternAnalyzer(
            min_occurrences=15,
            min_confidence=0.55,
            forward_periods=1
        )
        
        # Quick analysis (skip full backtesting for speed)
        results = analyzer.analyze_market_data(market_data)
        
        # Detect technical patterns
        tech_detector = TechnicalPatternDetector()
        tech_patterns = tech_detector.detect_all_technical_patterns(market_data)
        
        alerts = []
        
        # Check if any patterns are active NOW
        current_idx = len(market_data) - 1
        
        for result in results['results']:
            if not result['pattern_eval'].is_significant:
                continue
            
            situation = result['situation']
            bayesian_est = result.get('bayesian_estimate')
            
            # Check if pattern is active at current time
            if current_idx in situation.timestamp_indices:
                if bayesian_est and bayesian_est.probability_above_threshold > self.min_confidence:
                    alerts.append({
                        'ticker': ticker,
                        'pattern': situation.description,
                        'edge': bayesian_est.point_estimate * 100,
                        'confidence': bayesian_est.probability_above_threshold,
                        'ci_95': bayesian_est.credible_interval_95,
                        'type': 'statistical'
                    })
        
        # Check technical patterns
        for pattern_id, situation in tech_patterns.items():
            if current_idx in situation.timestamp_indices:
                alerts.append({
                    'ticker': ticker,
                    'pattern': situation.description,
                    'edge': 'Unknown',
                    'confidence': 0.6,  # Default for technical
                    'ci_95': None,
                    'type': 'technical'
                })
        
        return alerts
    
    def format_alert(self, alert: Dict) -> str:
        """Format alert message."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"🚨 SIGNAL ALERT: {alert['ticker']}")
        lines.append("=" * 60)
        lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Pattern: {alert['pattern']}")
        lines.append(f"Type: {alert['type'].upper()}")
        
        if alert['type'] == 'statistical':
            lines.append(f"Edge: {alert['edge']:+.2f}%")
            lines.append(f"Confidence: {alert['confidence']:.1%}")
            if alert['ci_95']:
                lines.append(f"95% CI: [{alert['ci_95'][0]*100:+.2f}%, {alert['ci_95'][1]*100:+.2f}%]")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def should_alert(self, alert: Dict) -> bool:
        """Check if we should alert (prevent duplicates)."""
        key = f"{alert['ticker']}_{alert['pattern']}"
        last_alert_time = self.last_alerts.get(key, 0)
        
        # Only alert once per hour for same pattern
        if time.time() - last_alert_time < 3600:
            return False
        
        self.last_alerts[key] = time.time()
        return True
    
    def run(self):
        """Run real-time monitoring loop."""
        print(f"\n{'='*60}")
        print(f"Real-Time Signal Monitor Started")
        print(f"{'='*60}")
        print(f"Monitoring: {', '.join(self.tickers)}")
        print(f"Poll interval: {self.poll_interval} seconds")
        print(f"Min confidence: {self.min_confidence:.0%}")
        print(f"{'='*60}\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] Checking patterns (iteration {iteration})...")
                
                for ticker in self.tickers:
                    try:
                        alerts = self.check_patterns(ticker)
                        
                        for alert in alerts:
                            if self.should_alert(alert):
                                alert_msg = self.format_alert(alert)
                                print(f"\n{alert_msg}\n")
                                
                                # TODO: Send email/Slack notification
                                # send_notification(alert_msg)
                        
                        if not alerts:
                            print(f"  {ticker}: No active patterns")
                    
                    except Exception as e:
                        print(f"  {ticker}: Error - {str(e)}")
                
                print(f"  Next check in {self.poll_interval} seconds...\n")
                time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            print(f"\n\n{'='*60}")
            print("Monitor stopped by user")
            print(f"{'='*60}\n")
            return 0


def main():
    """Main entry point."""
    # Configure monitoring
    tickers = ["^GSPC", "^OMX"]  # S&P 500, OMXS30
    poll_interval = 300  # 5 minutes
    
    # For testing: use shorter interval
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        poll_interval = 60  # 1 minute for testing
    
    monitor = RealtimeSignalMonitor(
        tickers=tickers,
        poll_interval=poll_interval,
        min_confidence=0.75
    )
    
    return monitor.run()


if __name__ == "__main__":
    sys.exit(main())
