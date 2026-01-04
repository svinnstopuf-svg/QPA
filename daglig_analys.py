"""
DAGLIG ANALYS
Kör varje morgon för att se om det finns köpsignaler idag.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard import main

if __name__ == "__main__":
    print("=" * 80)
    print("📊 DAGLIG ANALYS")
    print("=" * 80)
    print()
    
    main()
