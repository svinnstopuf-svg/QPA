"""
Exit Checker - Profit-Targeting for Active Positions
Checks if your positions hit +2σ or +3σ levels (time to take profits)
"""
from dataclasses import dataclass
from typing import List, Optional
import yfinance as yf
import json
from pathlib import Path


@dataclass
class ExitSignal:
    """Exit signal for a position"""
    ticker: str
    entry_price: float
    current_price: float
    profit_pct: float
    sigma_level: float
    sigma_2_price: float
    sigma_3_price: float
    recommendation: str  # "HOLD", "SELL_50", "SELL_100"
    reason: str


class ExitChecker:
    """
    Checks active positions for profit-targeting exits
    """
    
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
    
    def load_positions(self, positions_file: Path) -> List[dict]:
        """Load positions from JSON file"""
        if not positions_file.exists():
            return []
        
        with open(positions_file, 'r') as f:
            data = json.load(f)
            return data.get('positions', [])
    
    def check_position(self, ticker: str, entry_price: float) -> Optional[ExitSignal]:
        """
        Check if a position should be exited based on sigma levels
        
        Args:
            ticker: Stock ticker (e.g. 'AAPL')
            entry_price: Your entry price
            
        Returns:
            ExitSignal with recommendation, or None if data unavailable
        """
        try:
            # Download recent price data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
            if hist.empty or len(hist) < self.lookback_period:
                return None
            
            # Get prices for calculation
            recent_prices = hist['Close'].tail(self.lookback_period)
            current_price = hist['Close'].iloc[-1]
            
            # Calculate mean and std dev
            mean_price = recent_prices.mean()
            std_dev = recent_prices.std()
            
            # Calculate sigma levels
            sigma_2_price = mean_price + (2 * std_dev)
            sigma_3_price = mean_price + (3 * std_dev)
            
            # Calculate current sigma level
            sigma_level = (current_price - mean_price) / std_dev if std_dev > 0 else 0
            
            # Calculate profit %
            profit_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Determine recommendation
            if current_price >= sigma_3_price:
                recommendation = "SELL_100"
                reason = f"+3σ hit (${sigma_3_price:.2f}) - statistiskt extremt, sälj allt"
            elif current_price >= sigma_2_price:
                recommendation = "SELL_50"
                reason = f"+2σ hit (${sigma_2_price:.2f}) - ta hem 50% vinst"
            elif sigma_level > 1.5:
                recommendation = "WATCH"
                reason = f"+{sigma_level:.1f}σ - närmar sig +2σ (${sigma_2_price:.2f})"
            else:
                recommendation = "HOLD"
                reason = f"+{sigma_level:.1f}σ - håll position"
            
            return ExitSignal(
                ticker=ticker,
                entry_price=entry_price,
                current_price=current_price,
                profit_pct=profit_pct,
                sigma_level=sigma_level,
                sigma_2_price=sigma_2_price,
                sigma_3_price=sigma_3_price,
                recommendation=recommendation,
                reason=reason
            )
            
        except Exception as e:
            print(f"⚠️  Kunde inte hämta data för {ticker}: {e}")
            return None
    
    def check_all_positions(self, positions_file: Path) -> List[ExitSignal]:
        """
        Check all positions in portfolio file
        
        Args:
            positions_file: Path to my_positions.json
            
        Returns:
            List of ExitSignals for all positions
        """
        positions = self.load_positions(positions_file)
        signals = []
        
        for pos in positions:
            ticker = pos.get('ticker')
            entry_price = pos.get('entry_price')
            
            if not ticker or not entry_price:
                continue
            
            signal = self.check_position(ticker, entry_price)
            if signal:
                signals.append(signal)
        
        return signals
    
    def format_exit_report(self, signals: List[ExitSignal]) -> str:
        """
        Format exit signals as readable report
        
        Args:
            signals: List of ExitSignals
            
        Returns:
            Formatted string report
        """
        if not signals:
            return "📭 Inga aktiva positioner att kolla"
        
        report = []
        report.append("=" * 80)
        report.append("🎯 EXIT CHECKS - Profit-Targeting")
        report.append("=" * 80)
        report.append("")
        
        # Sort by recommendation priority (SELL_100 > SELL_50 > WATCH > HOLD)
        priority = {"SELL_100": 0, "SELL_50": 1, "WATCH": 2, "HOLD": 3}
        sorted_signals = sorted(signals, key=lambda s: priority.get(s.recommendation, 4))
        
        for signal in sorted_signals:
            # Icon based on recommendation
            if signal.recommendation == "SELL_100":
                icon = "🔴"
            elif signal.recommendation == "SELL_50":
                icon = "🟡"
            elif signal.recommendation == "WATCH":
                icon = "🟠"
            else:
                icon = "🟢"
            
            report.append(f"{icon} {signal.ticker}")
            report.append(f"   Entry: ${signal.entry_price:.2f}")
            report.append(f"   Current: ${signal.current_price:.2f} ({signal.profit_pct:+.1f}%)")
            report.append(f"   Sigma: {signal.sigma_level:+.1f}σ")
            report.append(f"   +2σ level: ${signal.sigma_2_price:.2f}")
            report.append(f"   +3σ level: ${signal.sigma_3_price:.2f}")
            report.append(f"   → {signal.reason}")
            report.append("")
        
        # Summary
        sell_100 = sum(1 for s in signals if s.recommendation == "SELL_100")
        sell_50 = sum(1 for s in signals if s.recommendation == "SELL_50")
        watch = sum(1 for s in signals if s.recommendation == "WATCH")
        
        report.append("=" * 80)
        report.append("SAMMANFATTNING")
        report.append("=" * 80)
        if sell_100 > 0:
            report.append(f"🔴 {sell_100} position(er) att sälja 100% (3σ hit)")
        if sell_50 > 0:
            report.append(f"🟡 {sell_50} position(er) att sälja 50% (2σ hit)")
        if watch > 0:
            report.append(f"🟠 {watch} position(er) att bevaka (närmar sig 2σ)")
        if sell_100 == 0 and sell_50 == 0 and watch == 0:
            report.append("🟢 Alla positioner inom normala nivåer")
        
        return "\n".join(report)


if __name__ == "__main__":
    # Test with positions file
    checker = ExitChecker()
    positions_file = Path(__file__).parent.parent.parent / "my_positions.json"
    
    signals = checker.check_all_positions(positions_file)
    print(checker.format_exit_report(signals))
