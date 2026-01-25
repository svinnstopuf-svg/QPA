#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PATTERN CONTRADICTION AUDITOR
==============================
Identifies patterns that contradict the core MEAN REVERSION / BOTTOM FISHING strategy.

Core Strategy:
- Buy after DECLINES (-10%+ from highs)
- Buy at BOTTOMS, not tops
- Hold 21-63 days (position trading)

Contradictory Patterns:
- Momentum patterns (Extended Rally, etc.)
- Breakout patterns (52-week highs, etc.)
- Short-term noise (day of week, calendar effects if used for entries)

Author: V4.0 Position Trading System
"""

from src.patterns.technical_patterns import TechnicalPatternDetector
from src.patterns.detector import PatternDetector
from src.patterns.position_trading_patterns import PositionTradingPatternDetector

# ============================================================================
# AUDIT CONFIGURATION
# ============================================================================

# Define what qualifies as "contradictory" to mean reversion strategy
CONTRADICTORY_PATTERNS = {
    # Pattern ID: (reason, severity, recommendation)
    "extended_rally": (
        "Buys after 7+ up days (momentum/breakout, not reversal)",
        "HIGH",
        "REMOVE - Contradicts bottom-fishing strategy"
    ),
    "extended_selloff": (
        "This is GOOD (buy after 7+ down days = reversal)",
        "OK",
        "KEEP - Aligns with strategy"
    ),
    "rsi_overbought": (
        "RSI >70 = overbought (contrarian SHORT, not BUY)",
        "HIGH",
        "REMOVE or INVERT - Use as sell signal, not buy"
    ),
    "rsi_oversold": (
        "RSI <30 = oversold (GOOD for mean reversion)",
        "OK",
        "KEEP - Aligns with strategy"
    ),
    "golden_cross": (
        "50MA crosses above 200MA = late-stage uptrend",
        "MEDIUM",
        "REVIEW - Trend-following, not reversal. May work for SOME trades but not core strategy"
    ),
    "death_cross": (
        "50MA crosses below 200MA = bearish (GOOD for bottom fishing IF followed by reversal)",
        "OK",
        "KEEP - Can signal bottoming process"
    ),
    "gap_up": (
        "Gap up >2% = strong buying (momentum, not reversal)",
        "MEDIUM",
        "REVIEW - Could be breakout continuation. Not aligned with bottom-fishing."
    ),
    "gap_down": (
        "Gap down >2% = panic selling (GOOD for reversal setup)",
        "OK",
        "KEEP - Can create oversold conditions"
    ),
    # Calendar/Day-of-week patterns
    "wednesday_effect": (
        "Day-of-week pattern (noise, not structural)",
        "LOW",
        "KEEP as SECONDARY only - Should not drive PRIMARY entries"
    ),
    "january_effect": (
        "Calendar pattern (noise, not structural)",
        "LOW",
        "KEEP as SECONDARY only - Should not drive PRIMARY entries"
    ),
}

# ============================================================================
# PATTERN ANALYSIS
# ============================================================================

def audit_patterns():
    """
    Audit all patterns in the system for contradictions.
    """
    print("="*80)
    print("PATTERN CONTRADICTION AUDIT")
    print("="*80)
    print("\nCore Strategy: MEAN REVERSION / BOTTOM FISHING")
    print("  - Buy after DECLINES (-10%+ from highs)")
    print("  - Buy at BOTTOMS, not tops")
    print("  - Hold 21-63 days (position trading)")
    print("\n" + "="*80)
    
    # Initialize detectors
    technical_detector = TechnicalPatternDetector()
    pattern_detector = PatternDetector()
    position_detector = PositionTradingPatternDetector()
    
    # Get all pattern detection methods
    technical_methods = [
        method for method in dir(technical_detector) 
        if method.startswith('detect_') and callable(getattr(technical_detector, method))
    ]
    
    position_methods = [
        method for method in dir(position_detector)
        if method.startswith('detect_') and callable(getattr(position_detector, method))
    ]
    
    print("\n📋 TECHNICAL PATTERNS (from TechnicalPatternDetector):")
    print("-" * 80)
    for method in technical_methods:
        pattern_name = method.replace('detect_', '')
        print(f"  • {pattern_name}")
        
        # Check if this is a known contradictory pattern
        for contra_id, (reason, severity, rec) in CONTRADICTORY_PATTERNS.items():
            if contra_id in pattern_name:
                emoji = "🚨" if severity == "HIGH" else "⚠️" if severity == "MEDIUM" else "ℹ️"
                print(f"    {emoji} {severity}: {reason}")
                print(f"       → {rec}")
    
    print("\n📋 POSITION TRADING PATTERNS (from PositionTradingPatternDetector):")
    print("-" * 80)
    for method in position_methods:
        pattern_name = method.replace('detect_', '').replace('_all_position_patterns', '')
        if pattern_name:
            print(f"  ✅ {pattern_name} (PRIMARY - structural reversal)")
    
    # Summary
    print("\n" + "="*80)
    print("🎯 RECOMMENDED ACTIONS")
    print("="*80)
    
    high_priority = [
        (pid, info) for pid, info in CONTRADICTORY_PATTERNS.items() 
        if info[1] == "HIGH"
    ]
    
    medium_priority = [
        (pid, info) for pid, info in CONTRADICTORY_PATTERNS.items() 
        if info[1] == "MEDIUM"
    ]
    
    print("\n🚨 HIGH PRIORITY (Immediate action needed):")
    for pid, (reason, severity, rec) in high_priority:
        print(f"\n  {pid.upper()}:")
        print(f"    Issue: {reason}")
        print(f"    Action: {rec}")
    
    print("\n⚠️  MEDIUM PRIORITY (Review recommended):")
    for pid, (reason, severity, rec) in medium_priority:
        print(f"\n  {pid.upper()}:")
        print(f"    Issue: {reason}")
        print(f"    Action: {rec}")
    
    print("\n" + "="*80)
    print("📝 IMPLEMENTATION GUIDE")
    print("="*80)
    print("""
To implement these changes:

1. REMOVE Extended Rally (HIGH PRIORITY):
   File: src/patterns/technical_patterns.py
   Action: Comment out or remove detect_trend_exhaustion() from detect_all_technical_patterns()
   
   # IN detect_all_technical_patterns():
   # exhaustion_patterns = self.detect_trend_exhaustion(market_data)  # REMOVED
   # all_patterns.update(exhaustion_patterns)  # REMOVED

2. REMOVE RSI Overbought (HIGH PRIORITY):
   File: src/patterns/technical_patterns.py
   Action: Remove overbought logic from detect_rsi_extremes()
   
   # Keep only oversold (<30), remove overbought (>70)

3. REVIEW Golden Cross (MEDIUM PRIORITY):
   File: src/patterns/technical_patterns.py
   Action: Either remove or demote to SECONDARY-only
   
   # Option A: Remove entirely
   # Option B: Add metadata['priority'] = 'SECONDARY'

4. REVIEW Gap Up (MEDIUM PRIORITY):
   File: src/patterns/technical_patterns.py
   Action: Either remove or demote to SECONDARY-only
   
After changes, run:
  python test_v4_watertight.py  # Verify system still works
  python sunday_dashboard.py    # Check new Top 5 results
""")

if __name__ == "__main__":
    audit_patterns()
