"""
Tests for metrics computation.
"""

import pandas as pd
import pytest

from biosound.processing.metrics import (
    jaccard_similarity,
    compute_turnover,
    compute_confidence,
    compute_year_metrics,
)


class TestJaccardSimilarity:
    """Tests for Jaccard similarity computation."""
    
    def test_identical_sets(self):
        """Test similarity of identical sets."""
        a = {"robin", "jay", "sparrow"}
        b = {"robin", "jay", "sparrow"}
        assert jaccard_similarity(a, b) == 1.0
    
    def test_disjoint_sets(self):
        """Test similarity of completely different sets."""
        a = {"robin", "jay"}
        b = {"hawk", "eagle"}
        assert jaccard_similarity(a, b) == 0.0
    
    def test_partial_overlap(self):
        """Test similarity with partial overlap."""
        a = {"robin", "jay", "sparrow"}  # 3 elements
        b = {"robin", "jay", "hawk"}      # 3 elements, 2 shared
        # Intersection = 2, Union = 4
        assert jaccard_similarity(a, b) == 0.5
    
    def test_empty_sets(self):
        """Test similarity of empty sets."""
        assert jaccard_similarity(set(), set()) == 1.0
    
    def test_one_empty(self):
        """Test when one set is empty."""
        a = {"robin", "jay"}
        assert jaccard_similarity(a, set()) == 0.0
        assert jaccard_similarity(set(), a) == 0.0


class TestComputeTurnover:
    """Tests for turnover computation."""
    
    def test_no_turnover(self):
        """Test zero turnover when sets are identical."""
        current = {"robin", "jay", "sparrow"}
        previous = {"robin", "jay", "sparrow"}
        assert compute_turnover(current, previous) == 0.0
    
    def test_complete_turnover(self):
        """Test complete turnover when sets are disjoint."""
        current = {"hawk", "eagle", "falcon"}
        previous = {"robin", "jay", "sparrow"}
        assert compute_turnover(current, previous) == 1.0
    
    def test_partial_turnover(self):
        """Test partial turnover."""
        current = {"robin", "jay", "hawk"}
        previous = {"robin", "jay", "sparrow"}
        # Jaccard = 2/4 = 0.5, so turnover = 0.5
        assert compute_turnover(current, previous) == 0.5


class TestComputeConfidence:
    """Tests for confidence score computation."""
    
    def test_high_effort(self):
        """Test confidence with high effort."""
        all_efforts = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        # p95 of log1p(all_efforts) ≈ log1p(5) ≈ 1.79
        # log1p(5) / log1p(5) = 1.0
        conf = compute_confidence(5.0, all_efforts)
        assert conf >= 0.9  # Should be high
    
    def test_low_effort(self):
        """Test confidence with low effort."""
        all_efforts = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        # Very low effort compared to distribution
        conf = compute_confidence(1.0, all_efforts)
        assert conf < 0.5  # Should be low
    
    def test_missing_effort(self):
        """Test confidence when effort is NaN."""
        all_efforts = pd.Series([1.0, 2.0, 3.0])
        conf = compute_confidence(float("nan"), all_efforts)
        assert conf == 1.0  # Default to full confidence
    
    def test_all_nan_efforts(self):
        """Test confidence when all efforts are NaN."""
        all_efforts = pd.Series([float("nan"), float("nan")])
        conf = compute_confidence(5.0, all_efforts)
        assert conf == 1.0  # Default to full confidence


class TestComputeYearMetrics:
    """Tests for full year metrics computation."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return {
            "run_id": "test_run",
            "time": {
                "start_year": 2020,
                "end_year": 2022,
            },
            "mapping": {
                "top_k_species_pool": 10,
            },
        }
    
    @pytest.fixture
    def sample_year_species(self):
        """Create sample year-species data."""
        # Year 2020: 5 species
        # Year 2021: 4 species (1 lost, 0 new)
        # Year 2022: 6 species (2 new, 0 lost)
        return pd.DataFrame([
            # 2020
            {"year": 2020, "species_id": "robin", "species_name": "Robin", "species_obs": 10, "effort_year": 5.0},
            {"year": 2020, "species_id": "jay", "species_name": "Jay", "species_obs": 8, "effort_year": 5.0},
            {"year": 2020, "species_id": "sparrow", "species_name": "Sparrow", "species_obs": 15, "effort_year": 5.0},
            {"year": 2020, "species_id": "hawk", "species_name": "Hawk", "species_obs": 3, "effort_year": 5.0},
            {"year": 2020, "species_id": "eagle", "species_name": "Eagle", "species_obs": 2, "effort_year": 5.0},
            # 2021 (eagle is gone)
            {"year": 2021, "species_id": "robin", "species_name": "Robin", "species_obs": 12, "effort_year": 6.0},
            {"year": 2021, "species_id": "jay", "species_name": "Jay", "species_obs": 7, "effort_year": 6.0},
            {"year": 2021, "species_id": "sparrow", "species_name": "Sparrow", "species_obs": 20, "effort_year": 6.0},
            {"year": 2021, "species_id": "hawk", "species_name": "Hawk", "species_obs": 4, "effort_year": 6.0},
            # 2022 (eagle back + 2 new)
            {"year": 2022, "species_id": "robin", "species_name": "Robin", "species_obs": 15, "effort_year": 7.0},
            {"year": 2022, "species_id": "jay", "species_name": "Jay", "species_obs": 9, "effort_year": 7.0},
            {"year": 2022, "species_id": "sparrow", "species_name": "Sparrow", "species_obs": 18, "effort_year": 7.0},
            {"year": 2022, "species_id": "hawk", "species_name": "Hawk", "species_obs": 5, "effort_year": 7.0},
            {"year": 2022, "species_id": "eagle", "species_name": "Eagle", "species_obs": 3, "effort_year": 7.0},
            {"year": 2022, "species_id": "owl", "species_name": "Owl", "species_obs": 2, "effort_year": 7.0},
        ])
    
    def test_richness_calculation(self, sample_config, sample_year_species, tmp_path):
        """Test that richness is calculated correctly."""
        # Set output to temp path
        output_path = tmp_path / "test_metrics.parquet"
        
        metrics = compute_year_metrics(
            sample_config,
            sample_year_species,
            output_path=output_path,
        )
        
        # Check richness per year
        assert metrics[metrics["year"] == 2020].iloc[0]["richness"] == 5
        assert metrics[metrics["year"] == 2021].iloc[0]["richness"] == 4
        assert metrics[metrics["year"] == 2022].iloc[0]["richness"] == 6
    
    def test_turnover_calculation(self, sample_config, sample_year_species, tmp_path):
        """Test that turnover is calculated correctly."""
        output_path = tmp_path / "test_metrics.parquet"
        
        metrics = compute_year_metrics(
            sample_config,
            sample_year_species,
            output_path=output_path,
        )
        
        # First year has no turnover (no previous year)
        assert metrics[metrics["year"] == 2020].iloc[0]["turnover"] == 0.0
        
        # 2021: lost eagle. Jaccard = 4/5 = 0.8, turnover = 0.2
        turnover_2021 = metrics[metrics["year"] == 2021].iloc[0]["turnover"]
        assert abs(turnover_2021 - 0.2) < 0.01
        
        # 2022: gained eagle and owl. Jaccard = 4/6 ≈ 0.67, turnover ≈ 0.33
        turnover_2022 = metrics[metrics["year"] == 2022].iloc[0]["turnover"]
        assert abs(turnover_2022 - 0.333) < 0.01
    
    def test_new_lost_species(self, sample_config, sample_year_species, tmp_path):
        """Test new and lost species tracking."""
        output_path = tmp_path / "test_metrics.parquet"
        
        metrics = compute_year_metrics(
            sample_config,
            sample_year_species,
            output_path=output_path,
        )
        
        # 2021: lost eagle
        row_2021 = metrics[metrics["year"] == 2021].iloc[0]
        assert row_2021["lost_species_count"] == 1
        assert "eagle" in row_2021["lost_species"]
        
        # 2022: gained eagle and owl
        row_2022 = metrics[metrics["year"] == 2022].iloc[0]
        assert row_2022["new_species_count"] == 2
        assert "eagle" in row_2022["new_species"]
        assert "owl" in row_2022["new_species"]


# Synthetic data generators for testing

def generate_stable_scenario(num_years: int = 5, base_richness: int = 20) -> pd.DataFrame:
    """
    Generate a stable ecosystem scenario.
    
    Same species every year with similar abundances.
    """
    species = [f"species_{i}" for i in range(base_richness)]
    records = []
    
    for year in range(2020, 2020 + num_years):
        for i, sp in enumerate(species):
            records.append({
                "year": year,
                "species_id": sp,
                "species_name": sp.replace("_", " ").title(),
                "species_obs": 10 + i,
                "effort_year": 5.0,
            })
    
    return pd.DataFrame(records)


def generate_decline_scenario(num_years: int = 5, initial_richness: int = 30) -> pd.DataFrame:
    """
    Generate a declining ecosystem scenario.
    
    Species are progressively lost each year.
    """
    records = []
    
    for year_idx in range(num_years):
        year = 2020 + year_idx
        # Lose some species each year
        current_richness = initial_richness - (year_idx * 5)
        species = [f"species_{i}" for i in range(current_richness)]
        
        for i, sp in enumerate(species):
            records.append({
                "year": year,
                "species_id": sp,
                "species_name": sp.replace("_", " ").title(),
                "species_obs": max(1, 10 - year_idx),  # Declining abundance
                "effort_year": 5.0,
            })
    
    return pd.DataFrame(records)


def generate_recovery_scenario(num_years: int = 5, min_richness: int = 10) -> pd.DataFrame:
    """
    Generate a recovering ecosystem scenario.
    
    Species are progressively gained each year.
    """
    records = []
    
    for year_idx in range(num_years):
        year = 2020 + year_idx
        # Gain species each year
        current_richness = min_richness + (year_idx * 4)
        species = [f"species_{i}" for i in range(current_richness)]
        
        for i, sp in enumerate(species):
            records.append({
                "year": year,
                "species_id": sp,
                "species_name": sp.replace("_", " ").title(),
                "species_obs": 5 + year_idx + i,  # Increasing abundance
                "effort_year": 5.0 + year_idx,
            })
    
    return pd.DataFrame(records)
