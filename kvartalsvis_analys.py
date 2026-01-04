"""
KVARTALSVIS ANALYS
Kör varje kvartal (mars, juni, september, december) för att validera systemet.
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.reporting.quarterly_audit import QuarterlyAuditor
from src.config import Config

def main():
    print("=" * 80)
    print("🎯 KVARTALSVIS ANALYS")
    print("=" * 80)
    print()
    
    config = Config()
    auditor = QuarterlyAuditor(config)
    
    try:
        report = auditor.generate_audit()
        
        if report:
            print(report)
            
            # Spara rapport
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            report_file = report_dir / f"quarterly_audit_{datetime.now().strftime('%Y-%m-%d')}.txt"
            report_file.write_text(report, encoding='utf-8')
            print()
            print(f"✅ Rapport sparad: {report_file}")
            print()
            print("=" * 80)
            print("💡 NÄSTA STEG")
            print("=" * 80)
            print()
            print("1. Läs pattern performance ovan")
            print("2. Kör Monte Carlo för risk-validering:")
            print()
            print("   python -c \"from src.analysis.monte_carlo import *; \\")
            print("   stats = TradingStats(win_rate=0.55, avg_win=2.5, avg_loss=-1.2, num_trades=50, kelly_fraction=0.25); \\")
            print("   sim = MonteCarloSimulator(); \\")
            print("   result = sim.run_simulation(stats, 10000); \\")
            print("   print(f'Risk för 20% drawdown: {result.prob_20pct_dd*100:.1f}%')\"")
            print()
            print("3. Justera Kelly-faktor baserat på Monte Carlo resultat")
        else:
            print("⚠️  Kunde inte generera kvartalsrapport.")
            print("   Det finns inte tillräckligt med historisk data (behöver 3+ månaders trades).")
    
    except Exception as e:
        print(f"❌ Fel vid generering av kvartalsrapport: {e}")
        print()
        print("💡 Tips: Systemet behöver 3 månaders tracking data.")
        print("   Kör 'python daglig_analys.py' regelbundet för att bygga upp data.")

if __name__ == "__main__":
    main()
