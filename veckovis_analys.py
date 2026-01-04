"""
VECKOVIS ANALYS
Kör varje söndag för att se vad som ändrats sedan förra veckan.
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.reporting.weekly_report import WeeklyReportGenerator
from src.exit.exit_checker import ExitChecker
from src.config import Config

def main():
    print("=" * 80)
    print("📈 VECKOVIS ANALYS")
    print("=" * 80)
    print()
    
    config = Config()
    generator = WeeklyReportGenerator(config)
    
    # 1. Weekly report (what changed)
    try:
        report = generator.generate_report()
        
        if report:
            print(report)
            
            # Spara rapport
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            report_file = report_dir / f"weekly_report_{datetime.now().strftime('%Y-%m-%d')}.txt"
            report_file.write_text(report, encoding='utf-8')
            print()
            print(f"✅ Rapport sparad: {report_file}")
        else:
            print("⚠️  Kunde inte generera veckorapport.")
            print("   Kör 'python daglig_analys.py' först för att bygga tracking data.")
    
    except Exception as e:
        print(f"❌ Fel vid generering av veckorapport: {e}")
        print()
        print("💡 Tips: Kör 'python daglig_analys.py' några gånger först")
        print("   för att bygga upp historisk data.")
    
    print()
    print()
    
    # 2. Exit checks (profit-targeting)
    try:
        checker = ExitChecker()
        positions_file = Path("my_positions.json")
        
        signals = checker.check_all_positions(positions_file)
        exit_report = checker.format_exit_report(signals)
        
        print(exit_report)
        
        # Spara exit rapport
        if signals:
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            exit_file = report_dir / f"exit_checks_{datetime.now().strftime('%Y-%m-%d')}.txt"
            exit_file.write_text(exit_report, encoding='utf-8')
            print()
            print(f"✅ Exit rapport sparad: {exit_file}")
    
    except Exception as e:
        print(f"⚠️  Kunde inte köra exit checks: {e}")
        print("   Se till att 'my_positions.json' existerar och innehåller dina positioner.")

if __name__ == "__main__":
    main()
