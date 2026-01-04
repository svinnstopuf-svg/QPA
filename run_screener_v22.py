"""
Quick Run Script for Instrument Screener V2.2

Enkel körning av hela analysen med alla V2.2 features.
"""

from instrument_screener_v22 import InstrumentScreenerV22, format_v22_report
from instruments_universe import get_all_instruments
from src.tracking.signal_tracker import SignalTracker
from src.reporting.weekly_report import WeeklyReportGenerator
from src.reporting.quarterly_audit import QuarterlyAuditor
from datetime import datetime

def main():
    """Run full V2.2 screening analysis."""
    
    print("\n🎰 Starting Instrument Screener V2.2 - Casino-Style Risk Improvements\n")
    
    # Initialize screener with V2.2 filters enabled
    screener = InstrumentScreenerV22(
        min_data_years=5.0,
        min_avg_volume=50000,
        enable_v22_filters=True  # Set to False to run V2.1 only
    )
    
    # Get 250 instruments universe
    instruments = get_all_instruments()
    
    print(f"Loaded {len(instruments)} instruments from universe\n")
    
    # Run analysis
    results = screener.screen_instruments(instruments)
    
    # Format and display DAILY report
    daily_report = format_v22_report(results)
    print("\n" + daily_report)
    
    # Save daily report
    today = datetime.now().strftime("%Y-%m-%d")
    daily_file = f"reports/daily_screener_{today}.txt"
    
    # Create reports directory if it doesn't exist
    import os
    os.makedirs("reports", exist_ok=True)
    
    with open(daily_file, 'w', encoding='utf-8') as f:
        f.write(daily_report)
    
    print(f"\n✅ Daily Report saved to: {daily_file}")
    
    # Auto-track new signals for weekly/quarterly reports
    tracker = SignalTracker()
    for result in results:
        if result.entry_recommendation.startswith("ENTER"):
            tracker.track_signal(
                ticker=result.ticker,
                pattern_name=result.best_pattern_name,
                entry_date=today,
                entry_price=0,  # Would need live price
                confidence=result.final_score / 100,
                edge=result.net_edge_after_costs / 100
            )
    
    # Generate WEEKLY report
    print("\n" + "="*100)
    print("📅 WEEKLY REPORT (Delta Analysis)")
    print("="*100)
    try:
        weekly_gen = WeeklyReportGenerator(tracker)
        weekly_report = weekly_gen.generate_weekly_report()
        print(weekly_report)
        
        weekly_file = f"reports/weekly_report_{today}.txt"
        with open(weekly_file, 'w', encoding='utf-8') as f:
            f.write(weekly_report)
        print(f"\n✅ Weekly Report saved to: {weekly_file}")
    except Exception as e:
        print(f"\n⚠️ Weekly report: {e}")
        print("   (Needs historical data from previous runs)")
    
    # Generate QUARTERLY audit
    print("\n" + "="*100)
    print("📊 QUARTERLY AUDIT (Pattern Performance)")
    print("="*100)
    try:
        auditor = QuarterlyAuditor(tracker)
        quarterly_report = auditor.generate_quarterly_audit()
        print(quarterly_report)
        
        quarterly_file = f"reports/quarterly_audit_{today}.txt"
        with open(quarterly_file, 'w', encoding='utf-8') as f:
            f.write(quarterly_report)
        print(f"\n✅ Quarterly Audit saved to: {quarterly_file}")
    except Exception as e:
        print(f"\n⚠️ Quarterly audit: {e}")
        print("   (Needs 3 months of historical data)")
    
    # Optional: Generate detailed CSV
    generate_csv = input("\nGenerate detailed CSV? (y/n): ")
    if generate_csv.lower() == 'y':
        save_detailed_csv(results)

def save_detailed_csv(results):
    """Save detailed results to CSV."""
    import csv
    
    csv_file = "screener_v22_detailed.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Rank', 'Ticker', 'Name', 'Category',
            'Signal', 'Best Edge %', 'Net Edge %', 'Cost Profitable',
            'V-Kelly Position %', 'Trend Aligned', 'Regime Multiplier',
            'Breakout Confidence', 'Volatility Regime',
            'Final Allocation %', 'Entry Recommendation', 'Final Score'
        ])
        
        # Data
        for i, r in enumerate(results, 1):
            signal_text = "GREEN" if r.signal.name == "GREEN" else \
                         "YELLOW" if r.signal.name == "YELLOW" else \
                         "ORANGE" if r.signal.name == "ORANGE" else "RED"
            
            writer.writerow([
                i,
                r.ticker,
                r.name,
                r.category,
                signal_text,
                f"{r.best_edge:.2f}",
                f"{r.net_edge_after_costs:.2f}",
                r.cost_profitable,
                f"{r.v_kelly_position:.2f}",
                r.trend_aligned,
                f"{r.regime_multiplier:.2f}",
                r.breakout_confidence,
                r.volatility_regime,
                f"{r.final_allocation:.2f}",
                r.entry_recommendation,
                f"{r.final_score:.1f}"
            ])
    
    print(f"✅ Detailed CSV saved to: {csv_file}")

if __name__ == "__main__":
    main()
