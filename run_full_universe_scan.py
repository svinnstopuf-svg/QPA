"""
Full Universe Scan - Position Trading Edition

Scans ALL 800 instruments with position trading system.
Saves results to CSV for later analysis.

Expected runtime: 4-6 hours (800 instruments × 20-30 sec each)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
from datetime import datetime
from instrument_screener_v23_position import PositionTradingScreener
from instruments_universe_800 import (
    SWEDISH_INSTRUMENTS,
    US_LARGE_CAP,
    ALL_WEATHER_HEDGE
)


def load_full_universe():
    """Load all 800 instruments."""
    # Read the rest of the file
    import instruments_universe_800 as universe
    
    all_tickers = []
    all_tickers.extend(SWEDISH_INSTRUMENTS)
    all_tickers.extend(US_LARGE_CAP)
    all_tickers.extend(ALL_WEATHER_HEDGE)
    
    # Try to get remaining categories
    try:
        all_tickers.extend(universe.SECTOR_ETFS)
    except:
        pass
    
    try:
        all_tickers.extend(universe.GLOBAL_EMERGING)
    except:
        pass
    
    # Create (ticker, name) tuples
    instruments = [(ticker, ticker) for ticker in all_tickers]
    
    return instruments


def save_results_to_csv(results, filename):
    """Save screening results to CSV."""
    if len(results) == 0:
        print("No results to save")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Ticker', 'Name', 'Status', 'Score',
            'Decline%', 'Price_vs_EMA200%', 'Context_Valid',
            'Primary_Patterns', 'Pattern_Name', 'Pattern_Priority',
            'Edge_21d%', 'Edge_42d%', 'Edge_63d%', 'Win_Rate_63d%',
            'Expected_Value%', 'RRR', 'Avg_Win%', 'Avg_Loss%',
            'Bayesian_Edge%', 'Uncertainty', 'Sample_Size',
            'Earnings_Risk', 'Earnings_Days', 'Volume_Confirmed',
            'Recommendation'
        ])
        
        # Data
        for result in results:
            writer.writerow([
                result.ticker,
                result.name,
                result.status,
                f"{result.score:.1f}",
                f"{result.decline_from_high:.1f}",
                f"{result.price_vs_ema200:.1f}",
                result.context_valid,
                result.primary_patterns,
                result.best_pattern_name,
                result.pattern_priority,
                f"{result.edge_21d*100:.2f}",
                f"{result.edge_42d*100:.2f}",
                f"{result.edge_63d*100:.2f}",
                f"{result.win_rate_63d*100:.1f}",
                f"{result.expected_value*100:.2f}",
                f"{result.risk_reward_ratio:.2f}",
                f"{result.avg_win*100:.2f}",
                f"{result.avg_loss*100:.2f}",
                f"{result.bayesian_edge*100:.2f}",
                result.uncertainty,
                result.sample_size,
                result.earnings_risk,
                result.earnings_days,
                result.volume_confirmed,
                result.recommendation
            ])
    
    print(f"\n✅ Results saved to: {filename}")


def main():
    """Run full universe scan."""
    print("="*80)
    print("FULL UNIVERSE SCAN - POSITION TRADING")
    print("="*80)
    
    # Load instruments
    instruments = load_full_universe()
    print(f"\nLoaded {len(instruments)} instruments")
    print(f"Estimated runtime: {len(instruments) * 25 / 3600:.1f} hours")
    print("\n⚠️  This will take several hours. Results saved incrementally.")
    print("\n🚀 Starting scan...")
    
    # Initialize screener
    screener = PositionTradingScreener(capital=100000.0)
    
    # Scan in batches (save every 100)
    batch_size = 100
    all_results = []
    
    for batch_start in range(0, len(instruments), batch_size):
        batch_end = min(batch_start + batch_size, len(instruments))
        batch = instruments[batch_start:batch_end]
        
        print(f"\n{'='*80}")
        print(f"BATCH {batch_start//batch_size + 1}/{(len(instruments)-1)//batch_size + 1}")
        print(f"Instruments {batch_start+1}-{batch_end} of {len(instruments)}")
        print('='*80)
        
        batch_results = screener.screen_instruments(batch)
        all_results.extend(batch_results)
        
        # Save intermediate results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"universe_scan_batch_{batch_start//batch_size + 1}_{timestamp}.csv"
        save_results_to_csv(batch_results, temp_filename)
        
        print(f"\n✅ Batch {batch_start//batch_size + 1} complete")
        print(f"   POTENTIAL: {len([r for r in batch_results if r.status.startswith('POTENTIAL')])}")
        print(f"   WAIT: {len([r for r in batch_results if r.status == 'WAIT'])}")
        print(f"   NO SETUP: {len([r for r in batch_results if r.status == 'NO SETUP'])}")
    
    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_filename = f"universe_scan_FULL_{timestamp}.csv"
    save_results_to_csv(all_results, final_filename)
    
    # Display summary
    print("\n" + "="*80)
    print("SCAN COMPLETE")
    print("="*80)
    
    potential = [r for r in all_results if r.status.startswith("POTENTIAL")]
    wait = [r for r in all_results if r.status == "WAIT"]
    no_setup = [r for r in all_results if r.status == "NO SETUP"]
    
    print(f"\nTotal Instruments: {len(all_results)}")
    print(f"  POTENTIAL: {len(potential)}")
    print(f"  WAIT: {len(wait)}")
    print(f"  NO SETUP: {len(no_setup)}")
    
    if len(potential) > 0:
        print(f"\n🎯 TOP 10 POTENTIAL SETUPS:")
        print("-"*80)
        
        for i, result in enumerate(potential[:10], 1):
            print(f"{i}. {result.ticker} ({result.best_pattern_name[:40]})")
            print(f"   Score: {result.score:.0f}/100 | "
                  f"63d: {result.edge_63d*100:+.1f}% | "
                  f"WR: {result.win_rate_63d*100:.0f}% | "
                  f"RRR: {result.risk_reward_ratio:.1f}")
    
    print(f"\n📁 Results saved to: {final_filename}")
    print("="*80)


if __name__ == "__main__":
    main()
