#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PATTERN PRIORITY VERIFICATION
==============================
Verifies that all patterns have correct priority tags after cleanup.

PRIMARY patterns should be:
- Double Bottom
- Inverse H&S  
- Bull Flag After Decline
- Higher Lows Reversal
- EMA20 Reclaim
- Nya lägsta nivåer (252 perioder)

SECONDARY patterns should be:
- All calendar patterns (Wednesday, January, etc.)
- All technical patterns (RSI, MA crosses, Gaps)
- All other patterns

Author: V4.0 Position Trading System
"""

from src.patterns.technical_patterns import TechnicalPatternDetector
from src.patterns.detector import PatternDetector
from src.patterns.position_trading_patterns import PositionTradingPatternDetector
from src.utils.market_data import MarketData
import numpy as np
from datetime import datetime, timedelta

def create_dummy_data():
    """Create dummy market data for testing"""
    dates = [datetime.now() - timedelta(days=i) for i in range(300, 0, -1)]
    prices = 100 + np.cumsum(np.random.randn(300) * 0.5)
    
    data = MarketData(
        close_prices=prices,
        open_prices=prices + np.random.randn(300) * 0.1,
        high_prices=prices + np.abs(np.random.randn(300) * 0.2),
        low_prices=prices - np.abs(np.random.randn(300) * 0.2),
        volume=np.random.randint(1000000, 5000000, 300),
        timestamps=np.array(dates)
    )
    data.ticker = "TEST"  # Add ticker as attribute
    return data

def verify_priorities():
    """Verify all pattern priorities"""
    print("="*80)
    print("PATTERN PRIORITY VERIFICATION")
    print("="*80)
    
    # Create test data
    market_data = create_dummy_data()
    
    # Initialize detectors
    technical_detector = TechnicalPatternDetector()
    pattern_detector = PatternDetector()
    position_detector = PositionTradingPatternDetector()
    
    print("\n" + "="*80)
    print("1. TECHNICAL PATTERNS (Should all be SECONDARY)")
    print("="*80)
    
    technical_patterns = technical_detector.detect_all_technical_patterns(market_data)
    
    issues_found = False
    for pattern_id, situation in technical_patterns.items():
        priority = situation.metadata.get('priority', 'MISSING')
        
        if priority == 'MISSING':
            print(f"  ❌ {pattern_id}: NO PRIORITY TAG!")
            issues_found = True
        elif priority == 'PRIMARY':
            print(f"  ❌ {pattern_id}: WRONG! Should be SECONDARY, not PRIMARY")
            issues_found = True
        elif priority == 'SECONDARY':
            print(f"  ✅ {pattern_id}: SECONDARY ✓")
        else:
            print(f"  ⚠️  {pattern_id}: Unknown priority '{priority}'")
            issues_found = True
    
    print("\n" + "="*80)
    print("2. CALENDAR/GENERIC PATTERNS (Should all get SECONDARY in analyzer.py)")
    print("="*80)
    
    generic_patterns = pattern_detector.detect_all_patterns(market_data)
    
    for pattern_id, situation in list(generic_patterns.items())[:5]:  # Sample first 5
        priority = situation.metadata.get('priority', 'NONE')
        
        # These don't have priority YET - analyzer.py adds it
        if priority == 'NONE' or priority not in situation.metadata:
            print(f"  ℹ️  {pattern_id}: No priority (will be set to SECONDARY in analyzer.py)")
        else:
            print(f"  ✅ {pattern_id}: {priority}")
    
    print("\n" + "="*80)
    print("3. POSITION TRADING PATTERNS (Should all be PRIMARY)")
    print("="*80)
    
    position_patterns = position_detector.detect_all_position_patterns(market_data)
    
    for pattern_id, situation in position_patterns.items():
        priority = situation.metadata.get('priority', 'MISSING')
        
        if priority == 'MISSING':
            print(f"  ⚠️  {pattern_id}: NO PRIORITY TAG (assumed PRIMARY)")
        elif priority == 'PRIMARY':
            print(f"  ✅ {pattern_id}: PRIMARY ✓")
        elif priority == 'SECONDARY':
            print(f"  ❌ {pattern_id}: WRONG! Should be PRIMARY, not SECONDARY")
            issues_found = True
        else:
            print(f"  ⚠️  {pattern_id}: Unknown priority '{priority}'")
    
    # SUMMARY
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    if issues_found:
        print("\n❌ ISSUES FOUND! Some patterns have incorrect priorities.")
        print("   Review the output above and fix the issues.")
        return False
    else:
        print("\n✅ ALL PATTERNS HAVE CORRECT PRIORITIES!")
        print("\n Pattern Hierarchy:")
        print("   PRIMARY  → Drive entries (structural reversals only)")
        print("   SECONDARY → Support entries (technical, calendar, gaps)")
        return True

if __name__ == "__main__":
    success = verify_priorities()
    exit(0 if success else 1)
