"""
Configuration module for Quant Pattern Analyzer
"""
from pathlib import Path

class Config:
    """Configuration for analysis parameters."""
    
    def __init__(self):
        # File paths
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.reports_dir = self.project_root / "reports"
        self.tracking_dir = self.data_dir / "tracking"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.tracking_dir.mkdir(exist_ok=True)
        
        # Analysis parameters
        self.min_occurrences = 5
        self.min_confidence = 0.40
        self.forward_periods = 1
        
        # Risk parameters
        self.kelly_fraction = 0.5  # Half-Kelly for safety
        self.max_position_size = 0.25  # Max 25% per position
        self.min_edge = 0.001  # 0.1% min edge
        
        # Data parameters
        self.min_data_years = 5.0
        self.min_avg_volume = 50000
        
        # V2.2 filters
        self.enable_v22_filters = True
