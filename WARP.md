# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A statistical observation tool for financial markets inspired by Jim Simons and Renaissance Technologies. The system identifies measurable market situations (X variables) and analyzes their historical outcomes (Y variables) without interpretation or narrative.

**Core Philosophy:**
- Measurable variables only
- Probabilities, not predictions
- No interpretation of narratives or company names
- Statistical robustness required (sufficient data and temporal stability)

## Commands

### Installation
```powershell
pip install -r requirements.txt
```

### Running the Application
```powershell
python main.py
```

### Testing
```powershell
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_market_data.py -v

# Run specific test
pytest tests/unit/test_market_data.py::TestMarketDataProcessor::test_calculate_returns -v
```

### Configuration
Edit `config/config.yaml` to adjust:
- Pattern evaluation thresholds (`min_occurrences`, `min_confidence`)
- Pattern detection parameters (volatility, momentum, volume thresholds)
- Analysis parameters (`forward_periods`, `lookback_window`)

## Architecture

### Data Flow
1. **MarketData** → Raw OHLCV data container
2. **PatternDetector** → Identifies market situations (X variables)
3. **OutcomeAnalyzer** → Calculates forward returns from identified situations
4. **PatternEvaluator** → Evaluates statistical robustness and significance
5. **InsightFormatter** → Presents results in user-friendly format

### Module Structure

**`src/analyzer.py`** - Main orchestrator that coordinates the entire analysis pipeline. This is the entry point for using the library programmatically.

**`src/utils/market_data.py`** - Contains `MarketData` dataclass and `MarketDataProcessor` for all market calculations (returns, volatility, momentum, volume profiles, etc.)

**`src/patterns/detector.py`** - Contains `PatternDetector` which identifies all market situations:
- Volatility regimes (high/low)
- Momentum regimes (positive/negative)
- Volume spikes
- Extreme price moves
- Range-bound periods
- Calendar effects (month-end, weekdays, etc.)

**`src/core/pattern_evaluator.py`** - Contains `PatternEvaluator` which determines if patterns are statistically significant based on:
- Sample size (min_occurrences threshold)
- Temporal stability (consistency across time periods)
- Confidence level (based on sample size and consistency)

**`src/analysis/outcome_analyzer.py`** - Contains `OutcomeAnalyzer` which calculates forward returns and outcome statistics for identified patterns.

**`src/communication/formatter.py`** - Contains `InsightFormatter` and `ConsoleFormatter` for user-friendly output formatting.

### Key Design Patterns

**Separation of X and Y:** Pattern detection (X variables) is completely separated from outcome analysis (Y variables). Detectors never "know" what happens after a pattern occurs.

**Statistical Rigor:** Patterns must meet multiple criteria to be considered significant:
- Minimum 30 occurrences (configurable)
- Temporal stability ≥ 70% (configurable)
- Confidence level ≥ 70% (configurable)

**No Forward-Looking Bias:** The system carefully handles indices to ensure forward returns don't leak into pattern detection.

## Development Guidelines

### Adding New Pattern Detectors

Add methods to `PatternDetector` class in `src/patterns/detector.py`:
1. Method should return `MarketSituation` dataclass
2. Include `timestamp_indices` - array of indices where pattern occurs
3. Provide clear `description` - what the pattern represents
4. Add metadata for debugging and analysis
5. Register in `detect_all_patterns()` method

### Testing Philosophy

Tests use pytest and focus on:
- Correctness of calculations (returns, volatility, momentum)
- Proper handling of edge cases (empty arrays, NaN values)
- Data structure integrity (array lengths match expectations)

Run tests before committing changes to ensure statistical calculations remain accurate.

### Code Style

- Docstrings in Swedish (following existing codebase convention)
- Type hints for all function parameters and returns
- Use numpy arrays for numerical data, not lists
- Prefer pandas for rolling window calculations
- Use dataclasses for structured data containers

### Important Constraints

**Never make predictions:** Output must describe historical tendencies, never future certainties. Use language like "historically tended to" not "will increase."

**No financial advice:** This tool is for research and education. Never generate buy/sell recommendations.

**Maintain statistical integrity:** 
- Don't reduce `min_occurrences` below 30 without strong justification
- Don't cherry-pick time periods for analysis
- Always report confidence levels alongside results

## Common Workflows

### Analyzing Custom Data
```python
from src import QuantPatternAnalyzer, MarketData
import numpy as np

# Create MarketData object with your data
market_data = MarketData(
    timestamps=your_timestamps,
    open_prices=your_open,
    high_prices=your_high,
    low_prices=your_low,
    close_prices=your_close,
    volume=your_volume
)

# Initialize analyzer
analyzer = QuantPatternAnalyzer(
    min_occurrences=30,
    min_confidence=0.70,
    forward_periods=1
)

# Run analysis
results = analyzer.analyze_market_data(market_data)

# Generate report
report = analyzer.generate_report(results)
print(report)
```

### Analyzing Specific Patterns Only
```python
# Analyze only momentum patterns
results = analyzer.analyze_market_data(
    market_data,
    patterns_to_analyze=['positive_momentum', 'negative_momentum']
)
```

### Checking Current Market Situation
```python
# Check what patterns are active in recent data
current = analyzer.get_current_market_situation(
    market_data,
    lookback_window=50
)

for situation in current['active_situations']:
    print(situation['description'])
```

## Dependencies

- **NumPy** (≥1.21.0) - Core numerical operations
- **Pandas** (≥1.3.0) - Time series analysis, rolling calculations
- **SciPy** (≥1.7.0) - Statistical functions (currently minimal usage)
- **pytest** - Testing framework (dev dependency)

Python 3.8+ required for dataclass support.
