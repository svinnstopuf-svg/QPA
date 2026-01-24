"""Quick analyzer for scan results."""
import csv
import sys

filename = sys.argv[1] if len(sys.argv) > 1 else "universe_scan_batch_1_20260122_183032.csv"

with open(filename, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

potential = [r for r in rows if r['Status'].startswith('POTENTIAL')]
wait = [r for r in rows if r['Status'] == 'WAIT']
no_setup = [r for r in rows if r['Status'] == 'NO SETUP']

print(f"Results from: {filename}")
print(f"Total instruments: {len(rows)}")
print(f"  POTENTIAL: {len(potential)}")
print(f"  WAIT: {len(wait)}")
print(f"  NO SETUP: {len(no_setup)}")

if potential:
    print(f"\n🎯 TOP POTENTIAL SETUPS:")
    print("-"*100)
    
    sorted_potential = sorted(potential, key=lambda x: float(x['Score']), reverse=True)
    
    for i, r in enumerate(sorted_potential[:10], 1):
        pattern_name = r['Pattern_Name'][:45]
        print(f"{i}. {r['Ticker']:8} | Score: {r['Score']:5} | {pattern_name:45}")
        print(f"   Edge 63d: {r['Edge_63d%']:>6}% | WR: {r['Win_Rate_63d%']:>5}% | "
              f"RRR: {r['RRR']:>5} | EV: {r['Expected_Value%']:>6}%")
        print(f"   Decline: {r['Decline%']:>6}% | Context: {r['Context_Valid']:5} | "
              f"Volume: {r['Volume_Confirmed']:5} | Earnings: {r['Earnings_Risk']:6}")
        print()
