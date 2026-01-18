"""
Mapping rules v0: Deterministic species-to-MIDI parameter assignment.

This module defines how biodiversity metrics map to musical elements:
- Species identity → pitch, pan, program
- Richness → number of voices
- Turnover → drone pitch shift, shimmer density
- Confidence → velocity and brightness modulation
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from biosound.utils.hashing import stable_int, stable_float01, stable_shuffle_key
from biosound.utils.timebins import TimeGrid, get_time_grid


# Scale definitions (semitone offsets from root)
SCALES = {
    "d_dorian": [0, 2, 3, 5, 7, 9, 10],        # D E F G A B C
    "c_minor_pentatonic": [0, 3, 5, 7, 10],     # C Eb F G Bb
    "a_minor": [0, 2, 3, 5, 7, 8, 10],          # A B C D E F G
    "c_major_pentatonic": [0, 2, 4, 7, 9],       # C D E G A
}


def get_scale(mode: str) -> List[int]:
    """Get scale intervals for a mode name."""
    if mode not in SCALES:
        raise ValueError(f"Unknown mode: {mode}. Available: {list(SCALES.keys())}")
    return SCALES[mode]


@dataclass
class SpeciesVoice:
    """Stable musical identity for a species."""
    
    species_id: str
    species_name: str
    pitch: int              # MIDI note number
    octave: int             # Octave (3-5)
    degree: int             # Scale degree index
    pan: int                # CC10 value (0-127)
    program: int            # MIDI program number
    
    @classmethod
    def from_species_id(
        cls,
        species_id: str,
        species_name: str,
        scale: List[int],
        root_midi: int,
        programs: List[int],
    ) -> "SpeciesVoice":
        """
        Create a stable voice assignment for a species.
        
        Args:
            species_id: Stable species identifier
            species_name: Display name
            scale: Scale intervals
            root_midi: Root note MIDI number
            programs: Available program numbers
            
        Returns:
            SpeciesVoice with deterministic assignments
        """
        # Pitch assignment
        degree = stable_int(species_id, len(scale))
        octave = 3 + stable_int(f"{species_id}:oct", 3)  # 3, 4, or 5
        
        # Calculate pitch from root pitch class, scale degree, and octave
        root_pc = root_midi % 12  # Pitch class of root
        pitch = root_pc + scale[degree] + (12 * octave)
        
        # Pan (0-127, centered at 64)
        pan = stable_int(f"{species_id}:pan", 128)
        
        # Program selection
        program = programs[stable_int(f"{species_id}:prog", len(programs))]
        
        return cls(
            species_id=species_id,
            species_name=species_name,
            pitch=pitch,
            octave=octave,
            degree=degree,
            pan=pan,
            program=program,
        )


@dataclass
class NoteEvent:
    """A single MIDI note event."""
    
    pitch: int
    velocity: int
    start_beat: float
    duration_beats: float
    channel: int
    species_id: Optional[str] = None
    layer: str = "pads"


@dataclass
class CCEvent:
    """A MIDI CC event."""
    
    cc_number: int
    value: int
    time_beat: float
    channel: int


@dataclass
class YearMusic:
    """Musical events for a single year."""
    
    year: int
    notes: List[NoteEvent] = field(default_factory=list)
    cc_events: List[CCEvent] = field(default_factory=list)
    selected_species: List[str] = field(default_factory=list)


class MappingRulesV0:
    """
    V0 mapping rules for ambient biodiversity sonification.
    
    Three-layer approach:
    - Drone: Structural anchor tied to turnover
    - Pads: Species voices representing ecosystem body
    - Shimmer: Change texture highlighting turnover
    """
    
    # Channel assignments
    CHANNEL_DRONE = 0
    CHANNEL_PADS = 1
    CHANNEL_SHIMMER = 2
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mapping_config = config["mapping"]
        
        # Musical parameters
        self.mode = self.mapping_config.get("mode", "d_dorian")
        self.scale = get_scale(self.mode)
        self.root_midi = self.mapping_config.get("base_root_midi", 62)  # D4
        
        # Voice parameters
        self.max_voices = self.mapping_config.get("max_voices", 16)
        self.min_voices = self.mapping_config.get("min_voices", 6)
        self.top_k = self.mapping_config.get("top_k_species_pool", 40)
        
        # Programs for pads
        self.pad_programs = self.mapping_config.get("pad_programs", [89, 90, 91, 92, 94])
        
        # Layer toggles
        layers = self.mapping_config.get("layers", {})
        self.drone_enabled = layers.get("drone", True)
        self.pads_enabled = layers.get("pads", True)
        self.shimmer_enabled = layers.get("shimmer", True)
        
        # Time grid
        self.grid = get_time_grid(config)
        
        # Species voice cache
        self._voice_cache: Dict[str, SpeciesVoice] = {}
    
    def get_species_voice(
        self,
        species_id: str,
        species_name: str,
    ) -> SpeciesVoice:
        """Get or create stable voice for a species."""
        if species_id not in self._voice_cache:
            self._voice_cache[species_id] = SpeciesVoice.from_species_id(
                species_id=species_id,
                species_name=species_name,
                scale=self.scale,
                root_midi=self.root_midi,
                programs=self.pad_programs,
            )
        return self._voice_cache[species_id]
    
    def compute_drone_root(self, turnover: float) -> int:
        """
        Compute drone root pitch based on turnover.
        
        Higher turnover shifts root down (darker), lower shifts up (brighter).
        """
        # semitone_shift = round(turnover*6) - 3  → range [-3, +3]
        semitone_shift = round(turnover * 6) - 3
        return self.root_midi + semitone_shift
    
    def compute_nvoices(self, richness: int) -> int:
        """
        Compute number of voices based on richness.
        
        nvoices = clamp(round(sqrt(richness)*2), min_voices, max_voices)
        """
        nvoices = round(np.sqrt(richness) * 2)
        return max(self.min_voices, min(self.max_voices, nvoices))
    
    def select_year_species(
        self,
        year: int,
        year_species_df: pd.DataFrame,
        metrics_df: pd.DataFrame,
    ) -> List[Tuple[str, str, float]]:
        """
        Select species to voice for a year (deterministic).
        
        1. Filter to this year's top_k species by obs count
        2. Sort by stable hash key for this year
        3. Take first nvoices
        
        Returns:
            List of (species_id, species_name, species_obs) tuples
        """
        # Filter to this year
        year_data = year_species_df[year_species_df["year"] == year].copy()
        
        if len(year_data) == 0:
            return []
        
        # Get richness from metrics
        year_metrics = metrics_df[metrics_df["year"] == year]
        if len(year_metrics) == 0:
            richness = len(year_data)
        else:
            richness = int(year_metrics.iloc[0]["richness"])
        
        # Top K by observations
        top_species = year_data.nlargest(self.top_k, "species_obs")
        
        # Add stable sort key
        top_species = top_species.copy()
        top_species["sort_key"] = top_species["species_id"].apply(
            lambda sid: stable_shuffle_key(year, sid)
        )
        
        # Sort and select
        top_species = top_species.sort_values("sort_key")
        nvoices = self.compute_nvoices(richness)
        selected = top_species.head(nvoices)
        
        return [
            (row["species_id"], row["species_name"], row["species_obs"])
            for _, row in selected.iterrows()
        ]
    
    def generate_drone_layer(
        self,
        year: int,
        turnover: float,
        confidence: float,
        richness: int,
        median_richness: float,
    ) -> List[NoteEvent]:
        """
        Generate drone layer notes for a year.
        
        Drone = root + fifth, optionally ninth if richness > median.
        """
        if not self.drone_enabled:
            return []
        
        notes = []
        start_beat, end_beat = self.grid.year_to_beat_range(year)
        duration = end_beat - start_beat
        
        # Compute drone root
        root = self.compute_drone_root(turnover)
        
        # Velocity based on confidence (35-60)
        base_vel = int(35 + 25 * confidence)
        
        # Root note
        notes.append(NoteEvent(
            pitch=root,
            velocity=base_vel,
            start_beat=start_beat,
            duration_beats=duration,
            channel=self.CHANNEL_DRONE,
            layer="drone",
        ))
        
        # Fifth
        notes.append(NoteEvent(
            pitch=root + 7,
            velocity=base_vel - 5,
            start_beat=start_beat,
            duration_beats=duration,
            channel=self.CHANNEL_DRONE,
            layer="drone",
        ))
        
        # Ninth if richness > median
        if richness > median_richness:
            notes.append(NoteEvent(
                pitch=root + 14,
                velocity=base_vel - 10,
                start_beat=start_beat,
                duration_beats=duration,
                channel=self.CHANNEL_DRONE,
                layer="drone",
            ))
        
        return notes
    
    def generate_pads_layer(
        self,
        year: int,
        selected_species: List[Tuple[str, str, float]],
        max_obs: float,
        confidence: float,
    ) -> Tuple[List[NoteEvent], List[CCEvent]]:
        """
        Generate pad layer notes for selected species.
        
        Each species gets deterministic note placements on a 4-beat grid.
        """
        if not self.pads_enabled:
            return [], []
        
        notes = []
        cc_events = []
        start_beat, end_beat = self.grid.year_to_beat_range(year)
        
        for species_id, species_name, species_obs in selected_species:
            voice = self.get_species_voice(species_id, species_name)
            
            # Normalized observation weight
            norm_obs = species_obs / max_obs if max_obs > 0 else 0.5
            
            # Velocity (25-95 scaled by norm_obs and confidence)
            vel = int((25 + 70 * norm_obs) * confidence)
            vel = max(25, min(100, vel))
            
            # Number of notes (2-4)
            nn = 2 + stable_int(f"{year}:{species_id}:nn", 3)
            
            # Duration (8 or 16 beats)
            dur = 8 if stable_int(f"{year}:{species_id}:dur", 2) == 0 else 16
            
            # Place notes on 4-beat grid
            grid_positions = list(range(int(start_beat), int(end_beat), 4))
            
            # Select positions deterministically
            for i in range(nn):
                if not grid_positions:
                    break
                
                # Pick position by hash
                pos_idx = stable_int(f"{year}:{species_id}:{i}", len(grid_positions))
                beat = grid_positions[pos_idx]
                
                # Small micro-offset for humanization
                offset = stable_float01(f"{year}:{species_id}:{i}:off") * 0.25
                
                notes.append(NoteEvent(
                    pitch=voice.pitch,
                    velocity=vel,
                    start_beat=beat + offset,
                    duration_beats=min(dur, end_beat - beat - offset),
                    channel=self.CHANNEL_PADS,
                    species_id=species_id,
                    layer="pads",
                ))
            
            # CC events at start of year
            # CC10 Pan
            cc_events.append(CCEvent(
                cc_number=10,
                value=voice.pan,
                time_beat=start_beat,
                channel=self.CHANNEL_PADS,
            ))
            
            # CC74 Brightness (40-100 based on confidence)
            cc_events.append(CCEvent(
                cc_number=74,
                value=int(40 + 60 * confidence),
                time_beat=start_beat,
                channel=self.CHANNEL_PADS,
            ))
            
            # CC91 Reverb (40-100, inverse of confidence)
            cc_events.append(CCEvent(
                cc_number=91,
                value=int(40 + 60 * (1 - confidence)),
                time_beat=start_beat,
                channel=self.CHANNEL_PADS,
            ))
        
        return notes, cc_events
    
    def generate_shimmer_layer(
        self,
        year: int,
        turnover: float,
        confidence: float,
        new_species: List[str],
        top_species: List[Tuple[str, str, float]],
    ) -> List[NoteEvent]:
        """
        Generate shimmer layer for change texture.
        
        Higher turnover = denser shimmer.
        Uses new species if available, else top species.
        """
        if not self.shimmer_enabled:
            return []
        
        # Skip if low turnover
        if turnover <= 0.2:
            return []
        
        notes = []
        start_beat, end_beat = self.grid.year_to_beat_range(year)
        
        # Step size: higher turnover = smaller step = denser
        step = max(1, round(4 - 3 * turnover))
        
        # Source species for shimmer - handle numpy arrays from parquet
        new_species_list = list(new_species) if hasattr(new_species, '__iter__') and not isinstance(new_species, str) else []
        top_species_list = list(top_species) if hasattr(top_species, '__iter__') and not isinstance(top_species, str) else []
        
        if len(new_species_list) > 0:
            source_ids = new_species_list[:5]  # Up to 5 new species
        elif len(top_species_list) > 0:
            source_ids = [s[0] if isinstance(s, (list, tuple)) else s for s in top_species_list[:5]]
        else:
            return []
        
        # Generate shimmer notes
        beat = start_beat
        note_idx = 0
        
        while beat < end_beat:
            # Select species by rotating through source
            species_id = source_ids[note_idx % len(source_ids)]
            
            # Get voice (may not be cached, create minimal version)
            pitch_degree = stable_int(species_id, len(self.scale))
            base_pitch = self.root_midi + self.scale[pitch_degree]
            shimmer_pitch = base_pitch + 24  # Two octaves up
            
            # Velocity (15-45 scaled by turnover and confidence)
            vel = int((15 + 30 * turnover) * confidence)
            vel = max(15, min(50, vel))
            
            # Small deterministic offset
            offset = stable_float01(f"{year}:shimmer:{note_idx}") * 0.25
            
            notes.append(NoteEvent(
                pitch=shimmer_pitch,
                velocity=vel,
                start_beat=beat + offset,
                duration_beats=2.0,
                channel=self.CHANNEL_SHIMMER,
                species_id=species_id,
                layer="shimmer",
            ))
            
            beat += step
            note_idx += 1
        
        return notes
    
    def generate_year_music(
        self,
        year: int,
        year_species_df: pd.DataFrame,
        metrics_df: pd.DataFrame,
    ) -> YearMusic:
        """
        Generate all musical events for a year.
        
        Args:
            year: Year to generate
            year_species_df: Year-species aggregation
            metrics_df: Year-level metrics
            
        Returns:
            YearMusic with all notes and CC events
        """
        # Get metrics for this year
        year_metrics = metrics_df[metrics_df["year"] == year]
        
        if len(year_metrics) == 0:
            return YearMusic(year=year)
        
        row = year_metrics.iloc[0]
        richness = int(row["richness"])
        turnover = float(row["turnover"])
        confidence = float(row["confidence"])
        new_species = row.get("new_species", [])
        if isinstance(new_species, str):
            new_species = []  # Handle serialization edge case
        
        # Median richness for drone decisions
        median_richness = metrics_df["richness"].median()
        
        # Select species for this year
        selected = self.select_year_species(year, year_species_df, metrics_df)
        
        # Max observation for normalization
        year_data = year_species_df[year_species_df["year"] == year]
        max_obs = year_data["species_obs"].max() if len(year_data) > 0 else 1.0
        
        # Generate layers
        drone_notes = self.generate_drone_layer(
            year, turnover, confidence, richness, median_richness
        )
        
        pads_notes, pads_cc = self.generate_pads_layer(
            year, selected, max_obs, confidence
        )
        
        shimmer_notes = self.generate_shimmer_layer(
            year, turnover, confidence, new_species, selected
        )
        
        return YearMusic(
            year=year,
            notes=drone_notes + pads_notes + shimmer_notes,
            cc_events=pads_cc,
            selected_species=[s[0] for s in selected],
        )
    
    def generate_all_years(
        self,
        year_species_df: pd.DataFrame,
        metrics_df: pd.DataFrame,
    ) -> Dict[int, YearMusic]:
        """
        Generate music for all years in the timeline.
        
        Returns:
            Dict mapping year to YearMusic
        """
        results = {}
        
        for year in self.grid.years():
            results[year] = self.generate_year_music(
                year, year_species_df, metrics_df
            )
        
        return results
