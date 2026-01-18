"""
MIDI file writer using pretty_midi.

Converts NoteEvent/CCEvent objects to a MIDI file.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pretty_midi

from biosound.mapping.rules_v0 import MappingRulesV0, YearMusic, NoteEvent, CCEvent
from biosound.utils.io import ensure_dir, get_output_paths, get_parquet_paths
from biosound.utils.timebins import get_time_grid


class MIDIWriter:
    """
    Write musical events to a MIDI file.
    
    Handles conversion from beat-based timing to seconds,
    and organizes events into appropriate instruments/channels.
    """
    
    # Instrument names for each channel
    INSTRUMENT_NAMES = {
        0: "Drone",
        1: "Pads",
        2: "Shimmer",
    }
    
    # Default programs
    DEFAULT_PROGRAMS = {
        0: 89,   # Pad 2 (warm) for drone
        1: 91,   # Pad 4 (choir) for pads
        2: 98,   # FX 3 (crystal) for shimmer
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.grid = get_time_grid(config)
        
        # Create MIDI object
        self.midi = pretty_midi.PrettyMIDI(
            initial_tempo=self.grid.bpm
        )
        
        # Create instruments for each channel
        self.instruments: Dict[int, pretty_midi.Instrument] = {}
        
        for channel, name in self.INSTRUMENT_NAMES.items():
            program = self.DEFAULT_PROGRAMS.get(channel, 0)
            instrument = pretty_midi.Instrument(
                program=program,
                is_drum=False,
                name=name,
            )
            self.instruments[channel] = instrument
    
    def beat_to_time(self, beat: float) -> float:
        """Convert beat position to time in seconds."""
        return self.grid.beat_to_time(beat)
    
    def add_note(self, note: NoteEvent) -> None:
        """Add a note event to the appropriate instrument."""
        channel = note.channel
        
        if channel not in self.instruments:
            # Create new instrument if needed
            self.instruments[channel] = pretty_midi.Instrument(
                program=0,
                name=f"Channel_{channel}",
            )
        
        # Convert timing
        start_time = self.beat_to_time(note.start_beat)
        end_time = self.beat_to_time(note.start_beat + note.duration_beats)
        
        # Create MIDI note
        midi_note = pretty_midi.Note(
            velocity=max(1, min(127, note.velocity)),
            pitch=max(0, min(127, note.pitch)),
            start=start_time,
            end=end_time,
        )
        
        self.instruments[channel].notes.append(midi_note)
    
    def add_cc(self, cc: CCEvent) -> None:
        """Add a CC event to the appropriate instrument."""
        channel = cc.channel
        
        if channel not in self.instruments:
            return
        
        time = self.beat_to_time(cc.time_beat)
        
        # Create control change
        control_change = pretty_midi.ControlChange(
            number=cc.cc_number,
            value=max(0, min(127, cc.value)),
            time=time,
        )
        
        self.instruments[channel].control_changes.append(control_change)
    
    def add_year_music(self, year_music: YearMusic) -> None:
        """Add all events from a YearMusic object."""
        for note in year_music.notes:
            self.add_note(note)
        
        for cc in year_music.cc_events:
            self.add_cc(cc)
    
    def write(self, output_path: Path) -> None:
        """
        Write MIDI to file.
        
        Args:
            output_path: Path for output .mid file
        """
        # Add all instruments to MIDI object
        for channel in sorted(self.instruments.keys()):
            self.midi.instruments.append(self.instruments[channel])
        
        # Ensure directory exists
        ensure_dir(output_path.parent)
        
        # Write file
        self.midi.write(str(output_path))
        print(f"Wrote MIDI to {output_path}")
    
    def get_note_count(self) -> int:
        """Get total number of notes across all instruments."""
        return sum(len(inst.notes) for inst in self.instruments.values())


def generate_midi(
    config: Dict[str, Any],
    year_music_dict: Dict[int, YearMusic],
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate complete MIDI file from year music data.
    
    Args:
        config: Configuration dictionary
        year_music_dict: Dict mapping year to YearMusic
        output_path: Override output path
        
    Returns:
        Path to generated MIDI file
    """
    import pandas as pd
    
    # Create writer
    writer = MIDIWriter(config)
    
    # Add all years
    for year in sorted(year_music_dict.keys()):
        writer.add_year_music(year_music_dict[year])
    
    # Determine output path
    if output_path is None:
        paths = get_output_paths(config)
        park_name = config["park"]["park_name"].lower()
        start = config["time"]["start_year"]
        end = config["time"]["end_year"]
        output_path = paths["midi_dir"] / f"{park_name}_{start}_{end}.mid"
    
    # Write file
    writer.write(output_path)
    
    print(f"Generated {writer.get_note_count()} notes across {len(year_music_dict)} years")
    
    return output_path


def generate_midi_from_parquet(
    config: Dict[str, Any],
    year_species_path: Optional[Path] = None,
    year_features_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate MIDI file from parquet data files.
    
    Convenience function that loads parquet, runs mapping, and writes MIDI.
    
    Args:
        config: Configuration dictionary
        year_species_path: Path to year-species parquet (default from config)
        year_features_path: Path to year-features parquet (default from config)
        output_path: Override output path
        
    Returns:
        Path to generated MIDI file
    """
    import pandas as pd
    
    # Load data
    parquet_paths = get_parquet_paths(config)
    
    if year_species_path is None:
        year_species_path = parquet_paths["year_species"]
    if year_features_path is None:
        year_features_path = parquet_paths["year_features"]
    
    year_species_df = pd.read_parquet(year_species_path)
    metrics_df = pd.read_parquet(year_features_path)
    
    print(f"Loaded {len(year_species_df)} year-species records")
    print(f"Loaded {len(metrics_df)} year metrics")
    
    # Create mapping rules and generate
    rules = MappingRulesV0(config)
    year_music_dict = rules.generate_all_years(year_species_df, metrics_df)
    
    # Write MIDI
    return generate_midi(config, year_music_dict, output_path)
