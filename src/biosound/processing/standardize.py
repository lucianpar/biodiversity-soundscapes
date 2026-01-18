"""
Standardization step: Load raw data via adapter and produce canonical parquet.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from biosound.adapters.base import DataAdapter, validate_schema
from biosound.adapters.nps_local_csv import NPSLocalCSVAdapter
from biosound.utils.io import ensure_dir, get_parquet_paths


# Adapter registry
ADAPTERS = {
    "nps_local_csv": NPSLocalCSVAdapter,
}


def get_adapter(config: Dict[str, Any]) -> DataAdapter:
    """
    Get the appropriate adapter based on config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Instantiated DataAdapter
    """
    adapter_name = config["data"].get("adapter", "nps_local_csv")
    
    if adapter_name not in ADAPTERS:
        available = list(ADAPTERS.keys())
        raise ValueError(
            f"Unknown adapter: {adapter_name}. Available: {available}"
        )
    
    adapter_class = ADAPTERS[adapter_name]
    return adapter_class(config)


def standardize_observations(
    config: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load observations via adapter and write standardized parquet.
    
    Args:
        config: Configuration dictionary
        output_path: Override output path (default from config)
        
    Returns:
        Standardized observations DataFrame
    """
    # Get adapter
    adapter = get_adapter(config)
    
    # Extract parameters
    park_id = config["park"]["park_id"]
    start_year = config["time"]["start_year"]
    end_year = config["time"]["end_year"]
    
    print(f"Fetching observations for {park_id} ({start_year}-{end_year})...")
    
    # Fetch data
    df = adapter.fetch_observations(park_id, start_year, end_year)
    
    # Validate schema
    errors = validate_schema(df)
    if errors:
        raise ValueError(f"Schema validation failed: {errors}")
    
    # Determine output path
    if output_path is None:
        paths = get_parquet_paths(config)
        output_path = paths["observations"]
    
    # Ensure directory exists
    ensure_dir(output_path.parent)
    
    # Write parquet
    df.to_parquet(output_path, index=False)
    print(f"Wrote {len(df)} observations to {output_path}")
    
    return df
