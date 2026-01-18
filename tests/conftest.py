"""
Pytest configuration and fixtures.
"""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return {
        "run_id": "test_run",
        "park": {
            "park_id": "test",
            "park_name": "Test Park",
        },
        "time": {
            "start_year": 2020,
            "end_year": 2022,
            "bars_per_year": 8,
            "bpm": 60,
        },
        "data": {
            "adapter": "nps_local_csv",
            "raw_path": "data/raw/test_birds.csv",
            "taxon_group": "bird",
            "column_mapping": {
                "year": "year",
                "species_name": "species_name",
                "obs_count": "obs_count",
            },
        },
        "mapping": {
            "mode": "d_dorian",
            "base_root_midi": 62,
            "max_voices": 16,
            "min_voices": 6,
            "top_k_species_pool": 40,
            "pad_programs": [89, 90, 91, 92, 94],
            "layers": {
                "drone": True,
                "pads": True,
                "shimmer": True,
            },
        },
        "render": {
            "soundfont_path": "data/raw/soundfont.sf2",
            "sample_rate": 44100,
            "per_year_wav": True,
        },
        "demo": {
            "enabled": True,
        },
    }
