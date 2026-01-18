"""
I/O utilities for configuration loading and file management.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and validate a YAML configuration file.
    
    Args:
        config_path: Path to the YAML config file
        
    Returns:
        Dictionary of configuration values
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config is invalid YAML
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Validate required sections
    required_sections = ["run_id", "park", "time", "data", "mapping", "render"]
    missing = [s for s in required_sections if s not in config]
    if missing:
        raise ValueError(f"Config missing required sections: {missing}")
    
    return config


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Walks up from current file to find pyproject.toml.
    
    Returns:
        Path to project root
    """
    current = Path(__file__).resolve()
    
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    
    # Fallback to current working directory
    return Path.cwd()


def resolve_path(path: Union[str, Path], base: Optional[Path] = None) -> Path:
    """
    Resolve a path, making it absolute relative to base or project root.
    
    Args:
        path: Path to resolve (can be relative)
        base: Base directory for relative paths (defaults to project root)
        
    Returns:
        Absolute Path object
    """
    path = Path(path)
    
    if path.is_absolute():
        return path
    
    if base is None:
        base = get_project_root()
    
    return (base / path).resolve()


def get_output_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Generate all output paths from config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with keys: processed_dir, run_dir, midi_dir, meta_dir, audio_dir
    """
    root = get_project_root()
    run_id = config["run_id"]
    park_id = config["park"]["park_id"]
    
    return {
        "processed_dir": root / "data" / "processed",
        "run_dir": root / "outputs" / "runs" / run_id,
        "midi_dir": root / "outputs" / "runs" / run_id / "midi",
        "meta_dir": root / "outputs" / "runs" / run_id / "meta",
        "audio_dir": root / "outputs" / "runs" / run_id / "audio" / park_id,
    }


def get_parquet_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Generate parquet file paths from config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with keys: observations, year_species, year_features
    """
    root = get_project_root()
    run_id = config["run_id"]
    start = config["time"]["start_year"]
    end = config["time"]["end_year"]
    
    processed_dir = root / "data" / "processed"
    
    return {
        "observations": processed_dir / f"{run_id}_observations_{start}_{end}.parquet",
        "year_species": processed_dir / f"{run_id}_year_species_{start}_{end}.parquet",
        "year_features": processed_dir / f"{run_id}_year_features_{start}_{end}.parquet",
    }
