"""
Local CSV adapter for NPS-style bird observation data.

This adapter reads a local CSV file and transforms it to the canonical schema.
Designed for flexibility with various CSV column layouts via column mapping.
"""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from biosound.adapters.base import DataAdapter, normalize_species_id, CANONICAL_SCHEMA


class NPSLocalCSVAdapter(DataAdapter):
    """
    Adapter for loading bird observations from a local CSV file.
    
    Configuration (in data section):
        raw_path: Path to CSV file
        taxon_group: Taxonomic group (default "bird")
        column_mapping: Dict mapping canonical names to CSV column names
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Get paths
        self.raw_path = Path(self.data_config.get("raw_path", ""))
        self.taxon_group = self.data_config.get("taxon_group", "bird")
        
        # Column mapping: canonical_name -> csv_column_name
        self.column_mapping = self.data_config.get("column_mapping", {
            "year": "year",
            "species_name": "species_name",
            "species_id": "species_id",
            "obs_count": "obs_count",
            "effort": "effort",
        })
    
    def list_parks(self) -> List[Dict[str, str]]:
        """Return the configured park as the only available park."""
        return [{
            "park_id": self.park_config.get("park_id", "unknown"),
            "park_name": self.park_config.get("park_name", "Unknown Park"),
        }]
    
    def fetch_observations(
        self,
        park_id: str,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Load observations from CSV and transform to canonical schema.
        
        Args:
            park_id: Park identifier (used for output, not filtering)
            start_year: Start year (inclusive)
            end_year: End year (inclusive)
            
        Returns:
            DataFrame with canonical schema
        """
        # Resolve path relative to project root
        from biosound.utils.io import resolve_path
        csv_path = resolve_path(self.raw_path)
        
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {csv_path}\n"
                f"Please place your bird observation data at this location.\n"
                f"See data/raw/README.md for format requirements."
            )
        
        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows from {csv_path}")
        
        # Validate required columns exist in source
        year_col = self.column_mapping.get("year", "year")
        species_name_col = self.column_mapping.get("species_name", "species_name")
        
        if year_col not in df.columns:
            raise ValueError(
                f"Required column '{year_col}' not found in CSV.\n"
                f"Available columns: {list(df.columns)}\n"
                f"Update column_mapping in config if your column has a different name."
            )
        
        if species_name_col not in df.columns:
            raise ValueError(
                f"Required column '{species_name_col}' not found in CSV.\n"
                f"Available columns: {list(df.columns)}\n"
                f"Update column_mapping in config if your column has a different name."
            )
        
        # Build canonical DataFrame
        canonical_df = pd.DataFrame()
        
        # Required columns from config
        canonical_df["park_id"] = park_id
        canonical_df["park_name"] = self.park_config.get("park_name", "Unknown")
        canonical_df["taxon_group"] = self.taxon_group
        
        # Year
        canonical_df["year"] = pd.to_numeric(df[year_col], errors="coerce")
        
        # Species name
        canonical_df["species_name"] = df[species_name_col].astype(str)
        
        # Species ID (derive from name if not present)
        species_id_col = self.column_mapping.get("species_id")
        if species_id_col and species_id_col in df.columns:
            canonical_df["species_id"] = df[species_id_col].apply(normalize_species_id)
        else:
            canonical_df["species_id"] = df[species_name_col].apply(normalize_species_id)
        
        # Observation count (default to 1.0 if missing)
        obs_count_col = self.column_mapping.get("obs_count")
        if obs_count_col and obs_count_col in df.columns:
            canonical_df["obs_count"] = pd.to_numeric(df[obs_count_col], errors="coerce").fillna(1.0)
        else:
            canonical_df["obs_count"] = 1.0
            print("Note: No obs_count column found, defaulting to 1.0 per record")
        
        # Effort (optional, NaN if missing)
        effort_col = self.column_mapping.get("effort")
        if effort_col and effort_col in df.columns:
            canonical_df["effort"] = pd.to_numeric(df[effort_col], errors="coerce")
        else:
            canonical_df["effort"] = float("nan")
            print("Note: No effort column found, setting to NaN")
        
        # Filter year range
        canonical_df = canonical_df[
            (canonical_df["year"] >= start_year) & 
            (canonical_df["year"] <= end_year)
        ].copy()
        
        # Drop invalid rows
        initial_len = len(canonical_df)
        canonical_df = canonical_df.dropna(subset=["year", "species_id"])
        canonical_df = canonical_df[canonical_df["species_id"] != ""]
        dropped = initial_len - len(canonical_df)
        
        if dropped > 0:
            print(f"Warning: Dropped {dropped} rows with invalid year or species")
        
        # Ensure year is int
        canonical_df["year"] = canonical_df["year"].astype(int)
        
        print(f"Returning {len(canonical_df)} observations for years {start_year}-{end_year}")
        
        return canonical_df.reset_index(drop=True)
