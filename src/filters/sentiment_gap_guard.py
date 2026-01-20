"""
Sentiment Gap Guard - Detect Sentiment-Momentum Divergence

Quantitative Principle:
Price and sentiment should align. When they diverge, it signals:
- Distribution phase: High sentiment + weak momentum = trap
- Capitulation trap: Low sentiment + strong momentum = miss

Methodology:
1. Sentiment: RSI (0-100) - measures overbought/oversold
2. Momentum: Rate of Change (ROC) - measures price acceleration
3. Detect gaps where sentiment and momentum disagree

Divergence Types:
- DISTRIBUTION: RSI > 70 (euphoric) BUT ROC < 0 (price falling)
  → Block: Smart money selling into optimism
  
- CAPITULATION TRAP: RSI < 30 (panic) BUT ROC > 5% (price rising fast)
  → Block: Bounce in downtrend, not reversal
  
- ALIGNED: RSI and momentum agree
  → Allow: Normal market behavior
"""
from typing import List
import numpy as np
from dataclasses import dataclass


@dataclass
class SentimentGapAnalysis:
    """Results from sentiment-momentum divergence analysis."""
    ticker: str
    
    # Sentiment (RSI)
    rsi: float  # 0-100
    rsi_regime: str  # OVERSOLD, NEUTRAL, OVERBOUGHT
    
    # Momentum (ROC)
    roc_pct: float  # % change over period
    momentum_regime: str  # FALLING, NEUTRAL, RISING
    
    # Gap detection
    divergence_detected: bool
    divergence_type: str  # DISTRIBUTION, CAPITULATION_TRAP, NONE
    tradable: bool  # Can we trade?
    
    # Recommendation
    recommendation: str


class SentimentGapGuard:
    """
    Detects divergence between sentiment (RSI) and momentum (ROC).
    
    Philosophy: Only trade when price and sentiment align.
    """
    
    def __init__(
        self,
        rsi_period: int = 14,
        roc_period: int = 10,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        roc_rising_threshold: float = 5.0,
        roc_falling_threshold: float = -2.0
    ):
        """
        Initialize sentiment gap guard.
        
        Args:
            rsi_period: Period for RSI calculation
            roc_period: Period for ROC calculation
            rsi_overbought: RSI threshold for overbought
            rsi_oversold: RSI threshold for oversold
            roc_rising_threshold: ROC % for "rising" momentum
            roc_falling_threshold: ROC % for "falling" momentum
        """
        self.rsi_period = rsi_period
        self.roc_period = roc_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.roc_rising_threshold = roc_rising_threshold
        self.roc_falling_threshold = roc_falling_threshold
    
    def calculate_rsi(self, prices: np.ndarray) -> float:
        """
        Calculate RSI (Relative Strength Index).
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        
        Args:
            prices: Array of prices
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < self.rsi_period + 1:
            return 50.0  # Neutral default
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gain and loss (using SMA for first, then EMA)
        avg_gain = np.mean(gains[:self.rsi_period])
        avg_loss = np.mean(losses[:self.rsi_period])
        
        # Calculate RS and RSI
        if avg_loss == 0:
            return 100.0  # No losses = max RSI
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_roc(self, prices: np.ndarray) -> float:
        """
        Calculate Rate of Change (ROC).
        
        ROC = ((Current - Past) / Past) * 100
        
        Args:
            prices: Array of prices
            
        Returns:
            ROC percentage
        """
        if len(prices) < self.roc_period + 1:
            return 0.0  # Neutral default
        
        current_price = prices[-1]
        past_price = prices[-(self.roc_period + 1)]
        
        if past_price == 0:
            return 0.0
        
        roc = ((current_price - past_price) / past_price) * 100
        return roc
    
    def analyze(
        self,
        ticker: str,
        prices: np.ndarray
    ) -> SentimentGapAnalysis:
        """
        Analyze sentiment-momentum divergence.
        
        Args:
            ticker: Instrument ticker
            prices: Array of close prices
            
        Returns:
            SentimentGapAnalysis with results
        """
        # 1. Calculate RSI (sentiment)
        rsi = self.calculate_rsi(prices)
        
        if rsi >= self.rsi_overbought:
            rsi_regime = "OVERBOUGHT"
        elif rsi <= self.rsi_oversold:
            rsi_regime = "OVERSOLD"
        else:
            rsi_regime = "NEUTRAL"
        
        # 2. Calculate ROC (momentum)
        roc_pct = self.calculate_roc(prices)
        
        if roc_pct >= self.roc_rising_threshold:
            momentum_regime = "RISING"
        elif roc_pct <= self.roc_falling_threshold:
            momentum_regime = "FALLING"
        else:
            momentum_regime = "NEUTRAL"
        
        # 3. Detect divergence
        divergence_detected = False
        divergence_type = "NONE"
        tradable = True
        recommendation = "ALLOW - Sentiment and momentum aligned"
        
        # DISTRIBUTION: High sentiment + weak/falling momentum
        if rsi_regime == "OVERBOUGHT" and momentum_regime in ["FALLING", "NEUTRAL"]:
            if roc_pct < 0:  # Actually falling
                divergence_detected = True
                divergence_type = "DISTRIBUTION"
                tradable = False
                recommendation = "BLOCK - Distribution phase (euphoria + selling)"
        
        # CAPITULATION TRAP: Low sentiment + strong rising momentum
        elif rsi_regime == "OVERSOLD" and momentum_regime == "RISING":
            if roc_pct > self.roc_rising_threshold:
                divergence_detected = True
                divergence_type = "CAPITULATION_TRAP"
                tradable = False
                recommendation = "BLOCK - Capitulation trap (panic bounce in downtrend)"
        
        # OVERBOUGHT + RISING: Also risky (late to party)
        elif rsi_regime == "OVERBOUGHT" and momentum_regime == "RISING":
            # Not a hard block, but flag as risky
            recommendation = "CAUTION - Overbought with momentum (late entry risk)"
        
        return SentimentGapAnalysis(
            ticker=ticker,
            rsi=rsi,
            rsi_regime=rsi_regime,
            roc_pct=roc_pct,
            momentum_regime=momentum_regime,
            divergence_detected=divergence_detected,
            divergence_type=divergence_type,
            tradable=tradable,
            recommendation=recommendation
        )
    
    def format_analysis_report(self, analysis: SentimentGapAnalysis) -> str:
        """Generate formatted analysis report."""
        report = f"""
{'='*70}
SENTIMENT GAP ANALYSIS: {analysis.ticker}
{'='*70}

Sentiment (RSI-{self.rsi_period}):
  RSI:                 {analysis.rsi:.1f}
  Regime:              {analysis.rsi_regime}

Momentum (ROC-{self.roc_period}):
  ROC:                 {analysis.roc_pct:+.2f}%
  Regime:              {analysis.momentum_regime}

Divergence Detection:
  Divergence:          {'⚠️ YES' if analysis.divergence_detected else '✅ NO'}
  Type:                {analysis.divergence_type}
  
Trading Decision:
  Tradable:            {'✅ YES' if analysis.tradable else '❌ BLOCK'}
  Recommendation:      {analysis.recommendation}

Interpretation:
  {'Smart money distribution - high sentiment but price falling' if analysis.divergence_type == 'DISTRIBUTION' else ''}
  {'Dead cat bounce - panic selling but temporary bounce' if analysis.divergence_type == 'CAPITULATION_TRAP' else ''}
  {'Sentiment and momentum aligned - normal market behavior' if analysis.divergence_type == 'NONE' else ''}
{'='*70}
"""
        return report


if __name__ == "__main__":
    # Test module
    print("Testing Sentiment Gap Guard...")
    
    guard = SentimentGapGuard()
    
    # Test Case 1: DISTRIBUTION (high RSI, falling price)
    print("\n1. Distribution Phase Test:")
    # Simulate: Price rising to 100, then falling to 95 (euphoria fading)
    prices_distribution = np.array([
        80, 82, 85, 88, 90, 92, 95, 97, 99, 100,  # Rising
        100, 99, 98, 97, 96, 95  # Falling (but RSI still high)
    ])
    
    analysis = guard.analyze("DIST.ST", prices_distribution)
    print(guard.format_analysis_report(analysis))
    
    # Test Case 2: CAPITULATION TRAP (low RSI, rising price)
    print("\n2. Capitulation Trap Test:")
    # Simulate: Price crashing to 50, then bouncing to 60 (dead cat bounce)
    prices_capitulation = np.array([
        100, 95, 90, 85, 80, 75, 70, 65, 60, 55,  # Crashing
        50, 52, 55, 58, 60, 63  # Bouncing (but still in downtrend)
    ])
    
    analysis = guard.analyze("CAP.ST", prices_capitulation)
    print(guard.format_analysis_report(analysis))
    
    # Test Case 3: ALIGNED (neutral RSI, neutral momentum)
    print("\n3. Aligned (Healthy) Test:")
    prices_aligned = np.array([
        100, 101, 102, 101, 102, 103, 102, 103, 104, 103,
        104, 105, 104, 105, 106, 105  # Steady uptrend
    ])
    
    analysis = guard.analyze("ALIGN.ST", prices_aligned)
    print(guard.format_analysis_report(analysis))
    
    print("\n✅ Sentiment Gap Guard - Tests Complete")
