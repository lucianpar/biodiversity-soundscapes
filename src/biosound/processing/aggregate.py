"""
Aggregation step: Compute per-year, per-species summaries.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from biosound.utils.io import ensure_dir, get_parquet_paths


def aggregate_by_year_species(
    config: Dict[str, Any],
    observations_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Aggregate observations by year and species.
    
    Computes:
    - species_obs: sum of obs_count per (year, species_id)
    - species_name: first non-null name
    - effort_year: sum of effort per year
    
    Args:
        config: Configuration dictionary
        observations_df: Input observations (loads from parquet if None)
        output_path: Override output path
        
    Returns:
        Aggregated DataFrame with columns:
        [year, species_id, species_name, species_obs, effort_year]
    """
    # Load observations if not provided
    if observations_df is None:
        paths = get_parquet_paths(config)
        observations_df = pd.read_parquet(paths["observations"])
    
    print(f"Aggregating {len(observations_df)} observations...")
    
    # Group by year and species
    year_species = observations_df.groupby(["year", "species_id"]).agg({
        "species_name": "first",
        "obs_count": "sum",
        "effort": "sum",  # NaN propagates if all NaN
    }).reset_index()
    
    # Rename for clarity
    year_species = year_species.rename(columns={
        "obs_count": "species_obs",
    })
    
    # Compute year-level effort
    year_effort = observations_df.groupby("year")["effort"].sum().reset_index()
    year_effort = year_effort.rename(columns={"effort": "effort_year"})
    
    # Merge effort back
    year_species = year_species.merge(year_effort, on="year", how="left")
    
    # Drop the per-row effort column (now have effort_year)
    year_species = year_species.drop(columns=["effort"], errors="ignore")
    
    # Sort for reproducibility
    year_species = year_species.sort_values(["year", "species_id"]).reset_index(drop=True)
    
    # Determine output path
    if output_path is None:
        paths = get_parquet_paths(config)
        output_path = paths["year_species"]
    
    # Write parquet
    ensure_dir(output_path.parent)
    year_species.to_parquet(output_path, index=False)
    
    n_years = year_species["year"].nunique()
    n_species = year_species["species_id"].nunique()
    print(f"Wrote {len(year_species)} year-species combinations ({n_years} years, {n_species} species) to {output_path}")
    
    return year_species
