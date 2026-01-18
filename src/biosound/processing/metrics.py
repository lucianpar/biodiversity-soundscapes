"""
Metrics computation: Richness, turnover, confidence, and derived features.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from biosound.utils.io import ensure_dir, get_parquet_paths


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Compute Jaccard similarity between two sets.
    
    Args:
        set_a: First set
        set_b: Second set
        
    Returns:
        Jaccard similarity in [0, 1]
    """
    if not set_a and not set_b:
        return 1.0  # Both empty = identical
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    return intersection / union if union > 0 else 0.0


def compute_turnover(set_current: Set[str], set_previous: Set[str]) -> float:
    """
    Compute turnover between consecutive years.
    
    Turnover = 1 - Jaccard similarity
    
    Args:
        set_current: Species set for current year
        set_previous: Species set for previous year
        
    Returns:
        Turnover in [0, 1] (0 = identical, 1 = completely different)
    """
    return 1.0 - jaccard_similarity(set_current, set_previous)


def compute_confidence(
    effort_year: float,
    all_efforts: pd.Series,
) -> float:
    """
    Compute confidence score based on sampling effort.
    
    confidence = clip(log1p(effort_year) / p95(log1p(all_efforts)), 0, 1)
    
    Args:
        effort_year: Effort for this year
        all_efforts: Series of all year efforts
        
    Returns:
        Confidence score in [0, 1]
    """
    if pd.isna(effort_year) or all_efforts.isna().all():
        return 1.0  # Default to full confidence if no effort data
    
    log_effort = np.log1p(effort_year)
    log_all = np.log1p(all_efforts.dropna())
    
    if len(log_all) == 0:
        return 1.0
    
    p95 = np.percentile(log_all, 95)
    
    if p95 == 0:
        return 1.0
    
    return float(np.clip(log_effort / p95, 0.0, 1.0))


def compute_year_metrics(
    config: Dict[str, Any],
    year_species_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Compute per-year biodiversity metrics.
    
    Computes:
    - richness: Number of unique species
    - total_obs: Total observations
    - turnover: 1 - Jaccard(S_y, S_{y-1})
    - new_species: Species in S_y but not S_{y-1}
    - lost_species: Species in S_{y-1} but not S_y
    - confidence: Based on sampling effort
    - top_species: Top K species by observation count
    
    Args:
        config: Configuration dictionary
        year_species_df: Year-species aggregation (loads if None)
        output_path: Override output path
        
    Returns:
        DataFrame with year-level metrics
    """
    # Load year-species if not provided
    if year_species_df is None:
        paths = get_parquet_paths(config)
        year_species_df = pd.read_parquet(paths["year_species"])
    
    # Get parameters
    start_year = config["time"]["start_year"]
    end_year = config["time"]["end_year"]
    top_k = config["mapping"].get("top_k_species_pool", 40)
    
    # Ensure all years are present
    all_years = list(range(start_year, end_year + 1))
    
    # Build species sets per year
    species_by_year: Dict[int, Set[str]] = {}
    for year in all_years:
        year_data = year_species_df[year_species_df["year"] == year]
        species_by_year[year] = set(year_data["species_id"].tolist())
    
    # Compute year-level effort
    effort_by_year = year_species_df.groupby("year")["effort_year"].first()
    
    # Build metrics for each year
    records: List[Dict[str, Any]] = []
    
    for year in all_years:
        year_data = year_species_df[year_species_df["year"] == year]
        species_set = species_by_year[year]
        
        # Basic metrics
        richness = len(species_set)
        total_obs = year_data["species_obs"].sum() if len(year_data) > 0 else 0.0
        
        # Turnover (compared to previous year)
        prev_year = year - 1
        if prev_year in species_by_year:
            prev_set = species_by_year[prev_year]
            turnover = compute_turnover(species_set, prev_set)
            new_species = list(species_set - prev_set)
            lost_species = list(prev_set - species_set)
        else:
            # First year has no turnover
            turnover = 0.0
            new_species = list(species_set)
            lost_species = []
        
        # Confidence from effort
        effort = effort_by_year.get(year, float("nan"))
        confidence = compute_confidence(effort, effort_by_year)
        
        # Top species by observation count
        if len(year_data) > 0:
            top_species = (
                year_data.nlargest(top_k, "species_obs")["species_id"].tolist()
            )
        else:
            top_species = []
        
        records.append({
            "year": year,
            "richness": richness,
            "total_obs": total_obs,
            "turnover": turnover,
            "new_species": new_species,
            "lost_species": lost_species,
            "new_species_count": len(new_species),
            "lost_species_count": len(lost_species),
            "effort_year": effort if not pd.isna(effort) else None,
            "confidence": confidence,
            "top_species": top_species,
        })
    
    metrics_df = pd.DataFrame(records)
    
    # Determine output path
    if output_path is None:
        paths = get_parquet_paths(config)
        output_path = paths["year_features"]
    
    # Write parquet
    ensure_dir(output_path.parent)
    metrics_df.to_parquet(output_path, index=False)
    
    print(f"Computed metrics for {len(metrics_df)} years:")
    print(f"  Richness range: {metrics_df['richness'].min()}-{metrics_df['richness'].max()}")
    print(f"  Mean turnover: {metrics_df['turnover'].mean():.3f}")
    print(f"Wrote to {output_path}")
    
    return metrics_df
