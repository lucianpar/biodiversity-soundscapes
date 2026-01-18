"""
Processing pipeline modules.
"""

from biosound.processing.standardize import standardize_observations
from biosound.processing.aggregate import aggregate_by_year_species
from biosound.processing.metrics import compute_year_metrics

__all__ = [
    "standardize_observations",
    "aggregate_by_year_species",
    "compute_year_metrics",
]
