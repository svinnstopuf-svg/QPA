"""
VECKOVIS ANALYS - Strategic Decision Module
Kör varje söndag för att analysera veckan och få köprekommendationer.

Usage:
    python veckovis_analys.py              # Normal mode
    python veckovis_analys.py --backfill   # Use backfilled data
"""
import sys
import io
import argparse
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from weekly_analyzer import WeeklyAnalyzer
from src.exit.exit_checker import ExitChecker

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Veckovis Analys - Strategic Decision Report')
    parser.add_argument('--backfill', action='store_true', help='Use backfilled historical data')
    args = parser.parse_args()
    
    print("\n" + "📈 "*20)
    if args.backfill:
        print("          VECKOVIS ANALYS - Backfilled Historical Data")
    else:
        print("          VECKOVIS ANALYS - Strategic Decision Report")
    print("📈 "*20)
    print(f"\n📅 Datum: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if args.backfill:
        print("🎯 Mode: BACKFILL (Point-in-Time Analysis)")
    print()
    
    # Initialize Weekly Analyzer
    analyzer = WeeklyAnalyzer(reports_dir="reports", use_backfill=args.backfill)
    
    # 1. Run Weekly Analysis
    print("⌛ Analyserar senaste veckans dashboard-körningar...")
    print()
    
    try:
        analysis = analyzer.analyze_week(days_back=7)
        
        if 'error' in analysis:
            print(f"\n❌ {analysis['error']}")
            print("   Kör 'python dashboard.py' dagligen för att bygga upp veckodata.")
            return
        
        # 2. Generate and display markdown report
        markdown_report = analyzer.generate_markdown_report(analysis)
        
        print(markdown_report)
        
        # 3. Save markdown report
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f"weekly_decision_{datetime.now().strftime('%Y-%m-%d')}.md"
        report_file.write_text(markdown_report, encoding='utf-8')
        
        print(f"\n\n💾 Rapport sparad: {report_file}")
        
        # 4. Generate and save audit trail for quarterly review
        now = datetime.now()
        week_number = now.isocalendar()[1]
        year = now.year
        
        audit_trail = analyzer.generate_audit_trail(analysis, week_number, year)
        
        import json
        audit_file = report_dir / f"weekly_audit_{year}_W{week_number:02d}.json"
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_trail, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Audit trail sparad: {audit_file}")
    
    except Exception as e:
        print(f"\n❌ Fel vid veckoanalys: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print()
    
    # 4. Exit checks (profit-targeting) - only for real positions
    print("\n" + "="*80)
    print("🎯 EXIT CHECKS - Profit-Targeting")
    print("="*80)
    
    try:
        import json
        positions_file = Path("my_positions.json")
        
        if positions_file.exists():
            with open(positions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                positions = data.get('positions', [])
                
                # Filter out example positions
                real_positions = [p for p in positions if 'example' not in p.get('notes', '').lower()]
                
                if real_positions:
                    checker = ExitChecker()
                    signals = checker.check_all_positions(positions_file)
                    exit_report = checker.format_exit_report(signals)
                    
                    print(exit_report)
                    
                    # Spara exit rapport
                    if signals:
                        report_dir = Path("reports")
                        report_dir.mkdir(exist_ok=True)
                        exit_file = report_dir / f"exit_checks_{datetime.now().strftime('%Y-%m-%d')}.txt"
                        exit_file.write_text(exit_report, encoding='utf-8')
                        print(f"\n✅ Exit rapport sparad: {exit_file}")
                else:
                    print("\n📋 Inga aktiva positioner att kontrollera.")
                    print("   Lägg till dina positioner i my_positions.json (ta bort exempelraden).")
        else:
            print("\n📋 Inga aktiva positioner att kontrollera.")
            print("   Skapa my_positions.json och lägg till dina positioner.")
    
    except Exception as e:
        print(f"\n⚠️  Kunde inte köra exit checks: {e}")

if __name__ == "__main__":
    main()
