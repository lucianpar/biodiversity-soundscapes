"""
Tests for mapping determinism.

Ensures that identical inputs produce identical musical outputs.
"""

import hashlib
import json
from typing import Dict, List

import pandas as pd
import pytest

from biosound.utils.hashing import stable_int, stable_float01, stable_shuffle_key
from biosound.mapping.rules_v0 import (
    MappingRulesV0,
    SpeciesVoice,
    get_scale,
    SCALES,
)


class TestStableHashing:
    """Tests for deterministic hashing utilities."""
    
    def test_stable_int_consistency(self):
        """Test that stable_int returns same value for same input."""
        key = "american_robin"
        mod = 128
        
        result1 = stable_int(key, mod)
        result2 = stable_int(key, mod)
        
        assert result1 == result2
    
    def test_stable_int_different_keys(self):
        """Test that different keys produce different values (usually)."""
        results = set()
        for i in range(100):
            results.add(stable_int(f"species_{i}", 1000))
        
        # Should have high diversity (not all same value)
        assert len(results) > 50
    
    def test_stable_int_range(self):
        """Test that stable_int output is in expected range."""
        for _ in range(100):
            import random
            key = f"test_key_{random.random()}"
            mod = 128
            result = stable_int(key, mod)
            assert 0 <= result < mod
    
    def test_stable_float01_consistency(self):
        """Test that stable_float01 returns same value for same input."""
        key = "stellers_jay:velocity"
        
        result1 = stable_float01(key)
        result2 = stable_float01(key)
        
        assert result1 == result2
    
    def test_stable_float01_range(self):
        """Test that stable_float01 output is in [0, 1)."""
        for i in range(100):
            result = stable_float01(f"key_{i}")
            assert 0.0 <= result < 1.0
    
    def test_stable_shuffle_key_consistency(self):
        """Test that shuffle keys are consistent."""
        year = 2020
        species_id = "american_robin"
        
        key1 = stable_shuffle_key(year, species_id)
        key2 = stable_shuffle_key(year, species_id)
        
        assert key1 == key2
    
    def test_stable_shuffle_key_varies_by_year(self):
        """Test that shuffle keys vary by year."""
        species_id = "american_robin"
        
        keys = [stable_shuffle_key(year, species_id) for year in range(2020, 2030)]
        
        # All keys should be unique (with very high probability)
        assert len(set(keys)) == len(keys)


class TestSpeciesVoice:
    """Tests for species voice assignment."""
    
    def test_voice_determinism(self):
        """Test that same species always gets same voice."""
        scale = get_scale("d_dorian")
        root = 62
        programs = [89, 90, 91]
        
        voice1 = SpeciesVoice.from_species_id(
            "american_robin", "American Robin", scale, root, programs
        )
        voice2 = SpeciesVoice.from_species_id(
            "american_robin", "American Robin", scale, root, programs
        )
        
        assert voice1.pitch == voice2.pitch
        assert voice1.pan == voice2.pan
        assert voice1.program == voice2.program
        assert voice1.octave == voice2.octave
    
    def test_different_species_different_voices(self):
        """Test that different species get different voices."""
        scale = get_scale("d_dorian")
        root = 62
        programs = [89, 90, 91, 92, 94]
        
        voices = {}
        species_list = [
            ("american_robin", "American Robin"),
            ("stellers_jay", "Steller's Jay"),
            ("western_bluebird", "Western Bluebird"),
            ("mountain_chickadee", "Mountain Chickadee"),
        ]
        
        for species_id, species_name in species_list:
            voices[species_id] = SpeciesVoice.from_species_id(
                species_id, species_name, scale, root, programs
            )
        
        # Check that not all pitches are the same
        pitches = [v.pitch for v in voices.values()]
        assert len(set(pitches)) > 1
        
        # Check that not all pans are the same
        pans = [v.pan for v in voices.values()]
        assert len(set(pans)) > 1


class TestMappingDeterminism:
    """Tests for full mapping determinism."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return {
            "run_id": "test_run",
            "park": {
                "park_id": "yose",
                "park_name": "Yosemite",
            },
            "time": {
                "start_year": 2020,
                "end_year": 2022,
                "bars_per_year": 8,
                "bpm": 60,
            },
            "mapping": {
                "mode": "d_dorian",
                "base_root_midi": 62,
                "max_voices": 8,
                "min_voices": 4,
                "top_k_species_pool": 20,
                "pad_programs": [89, 90, 91],
                "layers": {
                    "drone": True,
                    "pads": True,
                    "shimmer": True,
                },
            },
        }
    
    @pytest.fixture
    def sample_data(self):
        """Create sample year-species and metrics data."""
        year_species = pd.DataFrame([
            {"year": 2020, "species_id": "robin", "species_name": "Robin", "species_obs": 10, "effort_year": 5.0},
            {"year": 2020, "species_id": "jay", "species_name": "Jay", "species_obs": 8, "effort_year": 5.0},
            {"year": 2020, "species_id": "sparrow", "species_name": "Sparrow", "species_obs": 15, "effort_year": 5.0},
            {"year": 2021, "species_id": "robin", "species_name": "Robin", "species_obs": 12, "effort_year": 6.0},
            {"year": 2021, "species_id": "jay", "species_name": "Jay", "species_obs": 7, "effort_year": 6.0},
            {"year": 2021, "species_id": "hawk", "species_name": "Hawk", "species_obs": 5, "effort_year": 6.0},
            {"year": 2022, "species_id": "robin", "species_name": "Robin", "species_obs": 15, "effort_year": 7.0},
            {"year": 2022, "species_id": "jay", "species_name": "Jay", "species_obs": 9, "effort_year": 7.0},
            {"year": 2022, "species_id": "sparrow", "species_name": "Sparrow", "species_obs": 18, "effort_year": 7.0},
            {"year": 2022, "species_id": "owl", "species_name": "Owl", "species_obs": 3, "effort_year": 7.0},
        ])
        
        metrics = pd.DataFrame([
            {"year": 2020, "richness": 3, "turnover": 0.0, "confidence": 0.8, "total_obs": 33, "new_species": [], "lost_species": []},
            {"year": 2021, "richness": 3, "turnover": 0.5, "confidence": 0.9, "total_obs": 24, "new_species": ["hawk"], "lost_species": ["sparrow"]},
            {"year": 2022, "richness": 4, "turnover": 0.4, "confidence": 1.0, "total_obs": 45, "new_species": ["sparrow", "owl"], "lost_species": ["hawk"]},
        ])
        
        return year_species, metrics
    
    def test_full_mapping_determinism(self, sample_config, sample_data):
        """Test that full mapping produces identical results on repeated runs."""
        year_species, metrics = sample_data
        
        # Run mapping twice
        rules1 = MappingRulesV0(sample_config)
        result1 = rules1.generate_all_years(year_species, metrics)
        
        rules2 = MappingRulesV0(sample_config)
        result2 = rules2.generate_all_years(year_species, metrics)
        
        # Compare results
        for year in result1.keys():
            ym1 = result1[year]
            ym2 = result2[year]
            
            # Same number of notes
            assert len(ym1.notes) == len(ym2.notes), f"Note count mismatch for year {year}"
            
            # Same selected species
            assert ym1.selected_species == ym2.selected_species, f"Selected species mismatch for year {year}"
            
            # Compare individual notes
            for i, (n1, n2) in enumerate(zip(ym1.notes, ym2.notes)):
                assert n1.pitch == n2.pitch, f"Pitch mismatch for note {i} in year {year}"
                assert n1.velocity == n2.velocity, f"Velocity mismatch for note {i} in year {year}"
                assert abs(n1.start_beat - n2.start_beat) < 0.001, f"Start beat mismatch for note {i} in year {year}"
    
    def test_note_hash_determinism(self, sample_config, sample_data):
        """Test that note sequence hash is deterministic."""
        year_species, metrics = sample_data
        
        def compute_notes_hash(year_music_dict: Dict) -> str:
            """Compute hash of all notes."""
            note_data = []
            for year in sorted(year_music_dict.keys()):
                ym = year_music_dict[year]
                for note in ym.notes:
                    # Round floats to avoid floating point issues
                    note_data.append((
                        year,
                        note.pitch,
                        note.velocity,
                        round(note.start_beat, 3),
                        round(note.duration_beats, 3),
                        note.channel,
                    ))
            
            data_str = json.dumps(note_data, sort_keys=True)
            return hashlib.sha256(data_str.encode()).hexdigest()[:16]
        
        # Run mapping twice
        rules1 = MappingRulesV0(sample_config)
        result1 = rules1.generate_all_years(year_species, metrics)
        hash1 = compute_notes_hash(result1)
        
        rules2 = MappingRulesV0(sample_config)
        result2 = rules2.generate_all_years(year_species, metrics)
        hash2 = compute_notes_hash(result2)
        
        assert hash1 == hash2, "Note hashes should be identical"
    
    def test_species_selection_determinism(self, sample_config, sample_data):
        """Test that species selection is deterministic."""
        year_species, metrics = sample_data
        
        # Run selection multiple times
        selections = []
        for _ in range(5):
            rules = MappingRulesV0(sample_config)
            result = rules.generate_all_years(year_species, metrics)
            
            year_selections = {
                year: tuple(ym.selected_species)
                for year, ym in result.items()
            }
            selections.append(year_selections)
        
        # All selections should be identical
        for i in range(1, len(selections)):
            assert selections[i] == selections[0], f"Selection {i} differs from selection 0"


class TestScales:
    """Tests for scale definitions."""
    
    def test_dorian_intervals(self):
        """Test D Dorian scale intervals."""
        scale = get_scale("d_dorian")
        # D E F G A B C = 0 2 3 5 7 9 10
        assert scale == [0, 2, 3, 5, 7, 9, 10]
    
    def test_minor_pentatonic_intervals(self):
        """Test C minor pentatonic scale intervals."""
        scale = get_scale("c_minor_pentatonic")
        # C Eb F G Bb = 0 3 5 7 10
        assert scale == [0, 3, 5, 7, 10]
    
    def test_unknown_scale_raises(self):
        """Test that unknown scale raises error."""
        with pytest.raises(ValueError):
            get_scale("unknown_scale")
