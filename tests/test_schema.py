"""
Tests for adapter schema validation.
"""

import pandas as pd
import pytest

from biosound.adapters.base import (
    CANONICAL_SCHEMA,
    REQUIRED_COLUMNS,
    normalize_species_id,
    validate_schema,
)


class TestNormalizeSpeciesId:
    """Tests for species ID normalization."""
    
    def test_basic_normalization(self):
        """Test basic name normalization."""
        assert normalize_species_id("American Robin") == "american_robin"
        assert normalize_species_id("Steller's Jay") == "steller_s_jay"
    
    def test_special_characters(self):
        """Test handling of special characters."""
        assert normalize_species_id("Black-capped Chickadee") == "black_capped_chickadee"
        assert normalize_species_id("Wilson's Warbler") == "wilson_s_warbler"
    
    def test_scientific_name(self):
        """Test scientific name normalization."""
        assert normalize_species_id("Turdus migratorius") == "turdus_migratorius"
    
    def test_empty_values(self):
        """Test handling of empty/null values."""
        assert normalize_species_id("") == ""
        assert normalize_species_id(None) == ""
    
    def test_consecutive_underscores(self):
        """Test that consecutive underscores are collapsed."""
        assert normalize_species_id("Bird  Name") == "bird_name"
        assert normalize_species_id("Bird - Name") == "bird_name"


class TestValidateSchema:
    """Tests for schema validation."""
    
    def test_valid_schema(self):
        """Test validation of a correct schema."""
        df = pd.DataFrame({
            "park_id": ["yose"],
            "park_name": ["Yosemite"],
            "year": [2020],
            "taxon_group": ["bird"],
            "species_id": ["american_robin"],
            "species_name": ["American Robin"],
            "obs_count": [5.0],
            "effort": [2.5],
        })
        
        errors = validate_schema(df)
        assert len(errors) == 0
    
    def test_missing_required_column(self):
        """Test detection of missing required columns."""
        df = pd.DataFrame({
            "park_id": ["yose"],
            "park_name": ["Yosemite"],
            # Missing 'year'
            "taxon_group": ["bird"],
            "species_id": ["american_robin"],
            "species_name": ["American Robin"],
            "obs_count": [5.0],
            "effort": [2.5],
        })
        
        errors = validate_schema(df)
        assert len(errors) > 0
        assert any("year" in str(e) for e in errors)
    
    def test_missing_optional_column(self):
        """Test that missing optional columns are detected."""
        df = pd.DataFrame({
            "park_id": ["yose"],
            "park_name": ["Yosemite"],
            "year": [2020],
            "taxon_group": ["bird"],
            "species_id": ["american_robin"],
            "species_name": ["American Robin"],
            # Missing obs_count and effort
        })
        
        errors = validate_schema(df)
        assert len(errors) > 0  # obs_count and effort are in CANONICAL_SCHEMA


class TestCanonicalSchema:
    """Tests for canonical schema definition."""
    
    def test_required_columns_subset(self):
        """Test that required columns are subset of canonical schema."""
        for col in REQUIRED_COLUMNS:
            assert col in CANONICAL_SCHEMA
    
    def test_schema_types(self):
        """Test that schema defines expected types."""
        assert CANONICAL_SCHEMA["year"] == "int"
        assert CANONICAL_SCHEMA["obs_count"] == "float"
        assert CANONICAL_SCHEMA["species_id"] == "str"


def create_test_dataframe(num_records: int = 10, num_years: int = 3) -> pd.DataFrame:
    """
    Create a synthetic test DataFrame with valid schema.
    
    Helper for other tests.
    """
    import random
    
    species = [
        ("american_robin", "American Robin"),
        ("western_bluebird", "Western Bluebird"),
        ("stellers_jay", "Steller's Jay"),
        ("mountain_chickadee", "Mountain Chickadee"),
        ("white_headed_woodpecker", "White-headed Woodpecker"),
    ]
    
    records = []
    for _ in range(num_records):
        species_id, species_name = random.choice(species)
        year = 2020 + random.randint(0, num_years - 1)
        
        records.append({
            "park_id": "yose",
            "park_name": "Yosemite",
            "year": year,
            "taxon_group": "bird",
            "species_id": species_id,
            "species_name": species_name,
            "obs_count": random.uniform(1, 50),
            "effort": random.uniform(0.5, 5.0),
        })
    
    return pd.DataFrame(records)
