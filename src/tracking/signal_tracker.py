"""
Signal Tracker - Historisk loggning och validering

Loggar alla signals och outcomes för att validera system-prestanda över tid.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd


@dataclass
class SignalEntry:
    """En loggad signal med metadata."""
    timestamp: str
    ticker: str
    signal: str  # GREEN, YELLOW, ORANGE, RED
    edge: float
    score: float
    price_at_signal: float
    
    # Outcome (fylls i senare)
    price_after_1w: Optional[float] = None
    price_after_1m: Optional[float] = None
    price_after_3m: Optional[float] = None
    return_1w: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    
    # Metadata
    signal_confidence: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self):
        """Konvertera till dictionary för JSON."""
        return asdict(self)


class SignalTracker:
    """Tracker för att logga och analysera signals över tid."""
    
    def __init__(self, log_dir: str = "signal_logs"):
        """
        Initiera tracker.
        
        Args:
            log_dir: Directory för att spara loggar
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "signal_history.jsonl"
    
    def log_signal(
        self,
        ticker: str,
        signal: str,
        edge: float,
        score: float,
        price: float,
        confidence: str = None,
        category: str = None
    ):
        """
        Logga en signal.
        
        Args:
            ticker: Ticker symbol
            signal: GREEN/YELLOW/ORANGE/RED
            edge: Statistical edge (%)
            score: Overall score (0-100)
            price: Current price
            confidence: Signal confidence
            category: Instrument category
        """
        entry = SignalEntry(
            timestamp=datetime.now().isoformat(),
            ticker=ticker,
            signal=signal,
            edge=edge,
            score=score,
            price_at_signal=price,
            signal_confidence=confidence,
            category=category
        )
        
        # Append till log-fil (JSONL format)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
    
    def load_history(self) -> List[SignalEntry]:
        """Ladda all signal-historik."""
        if not self.log_file.exists():
            return []
        
        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                entries.append(SignalEntry(**data))
        
        return entries
    
    def update_outcomes(self, price_data: Dict[str, pd.DataFrame]):
        """
        Uppdatera outcomes för gamla signals.
        
        Args:
            price_data: Dict av {ticker: price_dataframe}
        """
        entries = self.load_history()
        updated_entries = []
        
        for entry in entries:
            if entry.ticker not in price_data:
                updated_entries.append(entry)
                continue
            
            df = price_data[entry.ticker]
            signal_date = datetime.fromisoformat(entry.timestamp)
            
            # Hämta priser 1w, 1m, 3m efter signal
            try:
                date_1w = signal_date + timedelta(days=7)
                date_1m = signal_date + timedelta(days=30)
                date_3m = signal_date + timedelta(days=90)
                
                # Hitta närmaste datum i data
                if entry.price_after_1w is None:
                    price_1w = self._get_price_at_date(df, date_1w)
                    if price_1w:
                        entry.price_after_1w = price_1w
                        entry.return_1w = (price_1w / entry.price_at_signal - 1) * 100
                
                if entry.price_after_1m is None:
                    price_1m = self._get_price_at_date(df, date_1m)
                    if price_1m:
                        entry.price_after_1m = price_1m
                        entry.return_1m = (price_1m / entry.price_at_signal - 1) * 100
                
                if entry.price_after_3m is None:
                    price_3m = self._get_price_at_date(df, date_3m)
                    if price_3m:
                        entry.price_after_3m = price_3m
                        entry.return_3m = (price_3m / entry.price_at_signal - 1) * 100
            
            except Exception as e:
                pass  # Skip om data saknas
            
            updated_entries.append(entry)
        
        # Skriv tillbaka uppdaterad data
        with open(self.log_file, 'w') as f:
            for entry in updated_entries:
                f.write(json.dumps(entry.to_dict()) + '\n')
    
    def _get_price_at_date(self, df: pd.DataFrame, target_date: datetime) -> Optional[float]:
        """Hämta pris vid specifikt datum (eller närmaste tillgängliga)."""
        try:
            # Konvertera till pandas Timestamp
            target_ts = pd.Timestamp(target_date)
            
            # Hitta närmaste datum
            idx = df.index.get_indexer([target_ts], method='nearest')[0]
            if idx >= 0 and idx < len(df):
                return float(df.iloc[idx]['Close'])
        except:
            pass
        
        return None
    
    def generate_performance_report(self) -> str:
        """Generera performance-rapport baserat på historik."""
        entries = self.load_history()
        
        if not entries:
            return "Ingen signal-historik att analysera."
        
        lines = []
        lines.append("=" * 80)
        lines.append("SIGNAL PERFORMANCE REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Overall statistik
        total_signals = len(entries)
        signals_with_1m_outcome = len([e for e in entries if e.return_1m is not None])
        
        lines.append(f"Total signals logged: {total_signals}")
        lines.append(f"Signals with 1-month outcome: {signals_with_1m_outcome}")
        lines.append("")
        
        # Performance per signal type
        lines.append("-" * 80)
        lines.append("PERFORMANCE PER SIGNAL TYPE (1-month returns)")
        lines.append("-" * 80)
        lines.append("")
        
        for signal_type in ["GREEN", "YELLOW", "ORANGE", "RED"]:
            signal_entries = [e for e in entries if e.signal == signal_type and e.return_1m is not None]
            
            if signal_entries:
                returns = [e.return_1m for e in signal_entries]
                avg_return = sum(returns) / len(returns)
                win_rate = len([r for r in returns if r > 0]) / len(returns)
                
                lines.append(f"{signal_type}:")
                lines.append(f"  Count: {len(signal_entries)}")
                lines.append(f"  Avg Return (1m): {avg_return:+.2f}%")
                lines.append(f"  Win Rate: {win_rate:.1%}")
                lines.append("")
        
        # Edge validation
        lines.append("-" * 80)
        lines.append("EDGE VALIDATION")
        lines.append("-" * 80)
        lines.append("")
        
        # Gruppera efter edge-nivå
        high_edge = [e for e in entries if e.edge >= 1.0 and e.return_1m is not None]
        med_edge = [e for e in entries if 0.5 <= e.edge < 1.0 and e.return_1m is not None]
        low_edge = [e for e in entries if 0.1 <= e.edge < 0.5 and e.return_1m is not None]
        
        for label, group in [("High Edge (>=1.0%)", high_edge), 
                             ("Medium Edge (0.5-1.0%)", med_edge),
                             ("Low Edge (0.1-0.5%)", low_edge)]:
            if group:
                returns = [e.return_1m for e in group]
                avg_return = sum(returns) / len(returns)
                lines.append(f"{label}: Avg {avg_return:+.2f}% ({len(group)} signals)")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def get_summary_stats(self) -> Dict:
        """Returnera sammanfattande statistik."""
        entries = self.load_history()
        
        stats = {
            "total_signals": len(entries),
            "by_signal_type": {},
            "avg_edge": 0,
            "signals_with_outcomes": 0
        }
        
        # Count per signal type
        for signal_type in ["GREEN", "YELLOW", "ORANGE", "RED"]:
            count = len([e for e in entries if e.signal == signal_type])
            stats["by_signal_type"][signal_type] = count
        
        # Average edge
        if entries:
            stats["avg_edge"] = sum(e.edge for e in entries) / len(entries)
        
        # Outcomes available
        stats["signals_with_outcomes"] = len([e for e in entries if e.return_1m is not None])
        
        return stats


def create_tracker_example():
    """Example usage av SignalTracker."""
    tracker = SignalTracker()
    
    # Logga några exempel-signals
    tracker.log_signal("AAPL", "YELLOW", 0.96, 58.2, 150.0, "MÅTTLIG", "stock_us_tech")
    tracker.log_signal("MSFT", "RED", 0.89, 51.5, 380.0, "MÅTTLIG", "stock_us_tech")
    tracker.log_signal("META", "YELLOW", 0.87, 76.0, 350.0, "MÅTTLIG", "stock_us_tech")
    
    print("Signals logged successfully!")
    print(tracker.generate_performance_report())


if __name__ == "__main__":
    create_tracker_example()
