"""
Abstract base class for data adapters.

All adapters must implement this interface and output data conforming
to the canonical observation schema.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd


# Canonical observation schema - all adapters must output this
CANONICAL_SCHEMA = {
    "park_id": "str",       # Park identifier (e.g., "yose")
    "park_name": "str",     # Full park name (e.g., "Yosemite")
    "year": "int",          # Observation year
    "taxon_group": "str",   # Taxonomic group (v0: always "bird")
    "species_id": "str",    # Stable species identifier (normalized scientific name)
    "species_name": "str",  # Display name
    "obs_count": "float",   # Observation count (default 1.0 if unavailable)
    "effort": "float",      # Sampling effort (NaN if unavailable)
}

REQUIRED_COLUMNS = ["park_id", "park_name", "year", "taxon_group", "species_id", "species_name"]


def normalize_species_id(name: str) -> str:
    """
    Create a stable species_id from a species name.
    
    Normalizes to lowercase, replaces spaces/special chars with underscores.
    
    Args:
        name: Species name (common or scientific)
        
    Returns:
        Normalized species identifier
    """
    if pd.isna(name) or not name:
        return ""
    
    # Lowercase and replace problematic characters
    normalized = str(name).lower().strip()
    
    # Replace spaces and special characters with underscores
    for char in [" ", "-", "'", ".", ",", "(", ")", "/"]:
        normalized = normalized.replace(char, "_")
    
    # Remove consecutive underscores
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    
    # Strip leading/trailing underscores
    normalized = normalized.strip("_")
    
    return normalized


def validate_schema(df: pd.DataFrame) -> List[str]:
    """
    Validate that a DataFrame matches the canonical schema.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check required columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    
    # Check all expected columns exist
    for col in CANONICAL_SCHEMA:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
    
    if errors:
        return errors
    
    # Type validations
    if not pd.api.types.is_integer_dtype(df["year"]):
        # Allow conversion
        try:
            df["year"].astype(int)
        except (ValueError, TypeError):
            errors.append("Column 'year' must be convertible to int")
    
    if not pd.api.types.is_float_dtype(df["obs_count"]):
        try:
            df["obs_count"].astype(float)
        except (ValueError, TypeError):
            errors.append("Column 'obs_count' must be convertible to float")
    
    return errors


class DataAdapter(ABC):
    """
    Abstract base class for biodiversity data adapters.
    
    Subclasses must implement:
    - list_parks(): Return available parks/regions
    - fetch_observations(): Fetch and transform observation data
    
    All adapters must output DataFrames conforming to CANONICAL_SCHEMA.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with configuration.
        
        Args:
            config: Configuration dictionary (full config, adapter uses 'data' section)
        """
        self.config = config
        self.data_config = config.get("data", {})
        self.park_config = config.get("park", {})
    
    @abstractmethod
    def list_parks(self) -> List[Dict[str, str]]:
        """
        List available parks/regions.
        
        Returns:
            List of dicts with at least 'park_id' and 'park_name'
        """
        pass
    
    @abstractmethod
    def fetch_observations(
        self,
        park_id: str,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Fetch observations for a park within a year range.
        
        Must return a DataFrame matching CANONICAL_SCHEMA.
        
        Args:
            park_id: Park identifier
            start_year: Start year (inclusive)
            end_year: End year (inclusive)
            
        Returns:
            DataFrame with canonical schema columns
        """
        pass
    
    def validate_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean adapter output.
        
        Args:
            df: Raw adapter output
            
        Returns:
            Validated DataFrame
            
        Raises:
            ValueError: If schema validation fails
        """
        errors = validate_schema(df)
        if errors:
            raise ValueError(f"Schema validation failed: {errors}")
        
        # Ensure correct dtypes
        df = df.copy()
        df["year"] = df["year"].astype(int)
        df["obs_count"] = df["obs_count"].astype(float)
        df["effort"] = df["effort"].astype(float)  # NaN preserved
        
        # Drop rows with missing required fields
        initial_len = len(df)
        df = df.dropna(subset=["year", "species_id", "species_name"])
        dropped = initial_len - len(df)
        
        if dropped > 0:
            print(f"Warning: Dropped {dropped} rows with missing required fields")
        
        return df
