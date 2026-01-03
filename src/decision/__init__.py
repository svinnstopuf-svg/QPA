"""
Decision support module.

Traffic light decision model for translating quant analysis into actionable guidance.
"""

from .traffic_light import (
    TrafficLightEvaluator,
    TrafficLightResult,
    Signal,
    format_traffic_light_report
)

__all__ = [
    'TrafficLightEvaluator',
    'TrafficLightResult', 
    'Signal',
    'format_traffic_light_report'
]
