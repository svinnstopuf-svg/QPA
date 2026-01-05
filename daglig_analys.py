"""
DAGLIG ANALYS
Kör varje morgon för att se om det finns köpsignaler idag.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard import main

if __name__ == "__main__":
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 80)
    print("📊 DAGLIG ANALYS")
    print("=" * 80)
    print()
    
    main()
