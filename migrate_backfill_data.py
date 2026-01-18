"""
Migration Script: Add entry_recommendation to Backfill Data
============================================================

Adds missing 'entry_recommendation' field to watchlist items in existing
backfill JSON files. This enables Weekly Analyzer to correctly count
1500 SEK floor positions as investable days.

Logic:
- If position > 0: ENTER (would get 1500 SEK floor in new system)
- Otherwise: BLOCK - Cost blocked
"""

import json
from pathlib import Path

def infer_entry_recommendation(item):
    """
    Infer entry_recommendation based on position.
    
    Conservative assumption: Any position > 0 would have been approved
    with 1500 SEK floor in the new systematic overlay.
    """
    position = item.get('position', 0.0)
    
    if position > 0:
        # Would get 1500 SEK floor enforcement
        return "ENTER"
    else:
        # Blocked by screener
        return "BLOCK - Cost blocked"

def migrate_file(filepath):
    """Migrate a single JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Track changes
    updated_watchlist = 0
    
    # Update watchlist items
    for item in data.get('watchlist', []):
        if 'entry_recommendation' not in item:
            item['entry_recommendation'] = infer_entry_recommendation(item)
            updated_watchlist += 1
    
    # Save back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return updated_watchlist

def main():
    backfill_dir = Path("reports/backfill")
    
    if not backfill_dir.exists():
        print(f"❌ Backfill directory not found: {backfill_dir}")
        return
    
    # Find all actionable JSON files
    files = sorted(backfill_dir.glob("actionable_*.json"))
    
    if not files:
        print(f"❌ No actionable files found in {backfill_dir}")
        return
    
    print(f"🔧 MIGRATING {len(files)} BACKFILL FILES")
    print("=" * 60)
    
    total_updated = 0
    
    for filepath in files:
        date = filepath.stem.replace("actionable_", "")
        updated = migrate_file(filepath)
        total_updated += updated
        
        status = "✅" if updated > 0 else "⏭️"
        print(f"{status} {date}: {updated} watchlist items updated")
    
    print()
    print("=" * 60)
    print(f"✅ MIGRATION COMPLETE")
    print(f"   Files processed: {len(files)}")
    print(f"   Watchlist items updated: {total_updated}")
    print()
    print("🚀 Ready to run weekly analysis:")
    print("   python veckovis_analys.py")

if __name__ == "__main__":
    main()
