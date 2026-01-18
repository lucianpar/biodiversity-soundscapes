"""
Data adapters for various biodiversity data sources.
"""

from biosound.adapters.base import DataAdapter, CANONICAL_SCHEMA
from biosound.adapters.nps_local_csv import NPSLocalCSVAdapter

__all__ = [
    "DataAdapter",
    "CANONICAL_SCHEMA",
    "NPSLocalCSVAdapter",
]
