"""
Backtest Configuration - Research Mode

Purpose: Validate the CORE STRATEGY (bottom-fishing) without strict filters.

Philosophy:
- Live trading needs strict filters (EV > 0, RRR >= 3.0, volume confirmation)
- Backtesting needs DATA to validate the strategy itself
- We relax filters to see if "buy declines, hold 21-63 days" works

Differences from Live Trading:
┌─────────────────────────┬─────────────────┬─────────────────┐
│ Parameter               │ Live Trading    │ Backtest Mode   │
├─────────────────────────┼─────────────────┼─────────────────┤
│ Decline Threshold       │ -15%            │ -10%            │
│ Volume Confirmation     │ REQUIRED        │ OPTIONAL        │
│ EV Filter               │ > 0             │ DISABLED        │
│ RRR Filter              │ >= 3.0          │ DISABLED        │
│ Pattern Tolerance       │ 2% (strict)     │ 5% (fuzzy)      │
│ Earnings Check          │ ENABLED         │ DISABLED        │
└─────────────────────────┴─────────────────┴─────────────────┘

Goal: Generate enough trades to statistically validate the strategy.
"""

# Market Context (Vattenpasset)
BACKTEST_MIN_DECLINE_PCT = 10.0  # -10% from 90-day high (vs -15% live)
BACKTEST_LOOKBACK_HIGH = 90
BACKTEST_EMA_PERIOD = 200

# Pattern Detection
BACKTEST_PATTERN_TOLERANCE = 0.05  # 5% tolerance for "same" low (vs 2% live)
BACKTEST_MIN_BOUNCE_PCT = 0.05  # 5% minimum bounce
BACKTEST_MIN_DECLINE_FOR_PATTERN = 10.0  # Match context filter

# Volume Confirmation
BACKTEST_VOLUME_REQUIRED = False  # Don't reject patterns lacking volume
BACKTEST_VOLUME_LOG = True  # Log volume info for analysis

# Filters (Disabled for Research)
BACKTEST_EV_FILTER_ENABLED = False  # Calculate but don't filter
BACKTEST_RRR_FILTER_ENABLED = False  # Calculate but don't filter
BACKTEST_EARNINGS_CHECK_ENABLED = False  # Skip earnings API calls

# Pattern Priorities
BACKTEST_PRIMARY_PATTERNS = [
    'double_bottom',
    'inverse_head_shoulders',
    'bull_flag_after_decline',
    'higher_lows',
    'ema20_reclaim'  # NEW: Simple pattern for testing
]

BACKTEST_SECONDARY_PATTERNS = [
    'extended_rally',
    'extended_selloff',
    'quarter_end',
    'january_effect'
]

# Timeframes
BACKTEST_FORWARD_PERIODS = [21, 42, 63]  # Days to measure returns

# Test Universe
BACKTEST_TICKERS = [
    'SBB-B.ST',      # Real estate crash 2022-2023
    'NOLA-B.ST',     # Industrial company
    'INVE-B.ST',     # Investor B (stable large cap)
]

# Output Settings
BACKTEST_SHOW_SAMPLE_TRADES = 5
BACKTEST_MIN_TRADES_FOR_STATS = 3  # Need at least 3 trades for meaningful stats


def get_backtest_summary(ticker: str) -> str:
    """Generate summary header for backtest."""
    return f"""
{'='*80}
BACKTEST MODE: {ticker}
Mode: RESEARCH (Relaxed Filters)
{'='*80}

Configuration:
  Decline Threshold: -{BACKTEST_MIN_DECLINE_PCT}% (vs -15% live)
  Pattern Tolerance: {BACKTEST_PATTERN_TOLERANCE*100:.0f}% (vs 2% live)
  Volume Required: {'Yes' if BACKTEST_VOLUME_REQUIRED else 'No (logged only)'}
  EV Filter: {'Enabled' if BACKTEST_EV_FILTER_ENABLED else 'DISABLED'}
  RRR Filter: {'Enabled' if BACKTEST_RRR_FILTER_ENABLED else 'DISABLED'}

Goal: Validate core strategy (buy declines, hold 21-63 days)
"""


def should_reject_trade_for_volume(volume_declining: bool, high_volume_breakout: bool) -> bool:
    """
    Determine if trade should be rejected for volume reasons.
    
    In backtest mode, we DON'T reject - we just log.
    """
    if not BACKTEST_VOLUME_REQUIRED:
        return False  # Never reject in backtest mode
    
    # If volume IS required (strict mode), check conditions
    if not volume_declining:
        return True
    if not high_volume_breakout:
        return True
    
    return False


def should_apply_ev_filter(expected_value: float) -> bool:
    """Should we filter out negative EV trades?"""
    if not BACKTEST_EV_FILTER_ENABLED:
        return False  # Don't filter in backtest mode
    return expected_value <= 0


def should_apply_rrr_filter(risk_reward_ratio: float) -> bool:
    """Should we filter out poor RRR trades?"""
    if not BACKTEST_RRR_FILTER_ENABLED:
        return False  # Don't filter in backtest mode
    return risk_reward_ratio < 3.0
