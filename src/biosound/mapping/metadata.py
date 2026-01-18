"""
Metadata generation for MIDI mapping sidecar files.

Produces JSON files documenting:
- Configuration snapshot
- Per-year metrics
- Per-species assignments
- Warnings and diagnostics
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from biosound.mapping.rules_v0 import MappingRulesV0, YearMusic
from biosound.utils.io import ensure_dir, get_output_paths, get_parquet_paths
from biosound.utils.hashing import content_hash


def generate_mapping_metadata(
    config: Dict[str, Any],
    year_music_dict: Dict[int, YearMusic],
    rules: MappingRulesV0,
    year_species_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    warnings: Optional[List[str]] = None,
) -> Path:
    """
    Generate mapping metadata JSON file.
    
    Args:
        config: Configuration dictionary
        year_music_dict: Dict mapping year to YearMusic
        rules: MappingRulesV0 instance with voice cache
        year_species_df: Year-species aggregation DataFrame
        metrics_df: Year metrics DataFrame
        output_path: Override output path
        warnings: List of warning messages to include
        
    Returns:
        Path to generated JSON file
    """
    metadata: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "version": "v0",
    }
    
    # Config snapshot (excluding paths for portability)
    config_snapshot = {
        "run_id": config["run_id"],
        "park": config["park"],
        "time": config["time"],
        "mapping": config["mapping"],
    }
    metadata["config"] = config_snapshot
    
    # Summary statistics
    metadata["summary"] = {
        "total_years": len(year_music_dict),
        "year_range": [config["time"]["start_year"], config["time"]["end_year"]],
        "total_notes": sum(len(ym.notes) for ym in year_music_dict.values()),
        "total_species_voiced": len(rules._voice_cache),
        "scale": rules.mode,
        "root_midi": rules.root_midi,
    }
    
    # Per-year metrics
    year_data = []
    for year in sorted(year_music_dict.keys()):
        ym = year_music_dict[year]
        
        # Get metrics for this year
        year_metrics = metrics_df[metrics_df["year"] == year]
        if len(year_metrics) > 0:
            row = year_metrics.iloc[0]
            metrics_info = {
                "richness": int(row["richness"]),
                "turnover": float(row["turnover"]),
                "confidence": float(row["confidence"]),
                "total_obs": float(row["total_obs"]),
            }
        else:
            metrics_info = {}
        
        year_data.append({
            "year": year,
            "note_count": len(ym.notes),
            "selected_species_count": len(ym.selected_species),
            "selected_species": ym.selected_species,
            "metrics": metrics_info,
        })
    
    metadata["years"] = year_data
    
    # Per-species assignments
    species_assignments = []
    for species_id, voice in sorted(rules._voice_cache.items()):
        species_assignments.append({
            "species_id": species_id,
            "species_name": voice.species_name,
            "pitch": voice.pitch,
            "octave": voice.octave,
            "degree": voice.degree,
            "pan": voice.pan,
            "program": voice.program,
        })
    
    metadata["species_assignments"] = species_assignments
    
    # Warnings
    if warnings:
        metadata["warnings"] = warnings
    else:
        # Check for potential issues
        auto_warnings = []
        
        # Check for missing effort
        if metrics_df["effort_year"].isna().all():
            auto_warnings.append("No effort data available - confidence set to 1.0 for all years")
        
        # Check for years with low species
        for year_info in year_data:
            if year_info["metrics"].get("richness", 0) < 5:
                auto_warnings.append(f"Year {year_info['year']} has low richness ({year_info['metrics'].get('richness', 0)} species)")
        
        if auto_warnings:
            metadata["warnings"] = auto_warnings
    
    # Content hash for reproducibility verification
    metadata["content_hash"] = content_hash(json.dumps(metadata, sort_keys=True, default=str))
    
    # Determine output path
    if output_path is None:
        paths = get_output_paths(config)
        park_name = config["park"]["park_name"].lower()
        start = config["time"]["start_year"]
        end = config["time"]["end_year"]
        output_path = paths["meta_dir"] / f"{park_name}_{start}_{end}_mapping.json"
    
    # Write JSON
    ensure_dir(output_path.parent)
    
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print(f"Wrote mapping metadata to {output_path}")
    
    return output_path


def generate_metadata_from_parquet(
    config: Dict[str, Any],
    year_species_path: Optional[Path] = None,
    year_features_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate metadata from parquet files.
    
    Convenience function that loads data, runs mapping, and generates metadata.
    """
    # Load data
    parquet_paths = get_parquet_paths(config)
    
    if year_species_path is None:
        year_species_path = parquet_paths["year_species"]
    if year_features_path is None:
        year_features_path = parquet_paths["year_features"]
    
    year_species_df = pd.read_parquet(year_species_path)
    metrics_df = pd.read_parquet(year_features_path)
    
    # Run mapping
    rules = MappingRulesV0(config)
    year_music_dict = rules.generate_all_years(year_species_df, metrics_df)
    
    # Generate metadata
    return generate_mapping_metadata(
        config=config,
        year_music_dict=year_music_dict,
        rules=rules,
        year_species_df=year_species_df,
        metrics_df=metrics_df,
        output_path=output_path,
    )
