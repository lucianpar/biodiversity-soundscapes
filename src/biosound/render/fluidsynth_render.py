"""
FluidSynth-based MIDI to WAV rendering.

Uses FluidSynth CLI to convert MIDI files to audio,
then slices into per-year WAV clips.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf

from biosound.utils.io import ensure_dir, get_output_paths, resolve_path
from biosound.utils.timebins import get_time_grid, TimeGrid


def check_fluidsynth() -> bool:
    """Check if FluidSynth is available on the system."""
    return shutil.which("fluidsynth") is not None


def render_midi_to_wav(
    midi_path: Path,
    output_path: Path,
    soundfont_path: Path,
    sample_rate: int = 44100,
) -> Path:
    """
    Render MIDI to WAV using FluidSynth.
    
    Args:
        midi_path: Path to input MIDI file
        output_path: Path for output WAV file
        soundfont_path: Path to SoundFont file
        sample_rate: Audio sample rate (default 44100)
        
    Returns:
        Path to rendered WAV file
        
    Raises:
        FileNotFoundError: If MIDI or SoundFont not found
        RuntimeError: If FluidSynth not available or fails
    """
    # Validate inputs
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")
    
    if not soundfont_path.exists():
        raise FileNotFoundError(
            f"SoundFont not found: {soundfont_path}\n"
            "Please place a SoundFont file in data/raw/\n"
            "See data/raw/README.md for download options."
        )
    
    if not check_fluidsynth():
        raise RuntimeError(
            "FluidSynth not found.\n"
            "Install it with:\n"
            "  macOS: brew install fluidsynth\n"
            "  Ubuntu: sudo apt-get install fluidsynth"
        )
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    
    # Build FluidSynth command
    # Note: -F and -r must come before soundfont/midi files in FluidSynth 2.x
    cmd = [
        "fluidsynth",
        "-ni",                          # Non-interactive mode
        "-F", str(output_path),         # Output file
        "-r", str(sample_rate),         # Sample rate
        str(soundfont_path),
        str(midi_path),
    ]
    
    print(f"Rendering MIDI to WAV...")
    print(f"  MIDI: {midi_path}")
    print(f"  SoundFont: {soundfont_path}")
    print(f"  Output: {output_path}")
    
    # Run FluidSynth
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"FluidSynth failed:\n"
            f"stdout: {e.stdout}\n"
            f"stderr: {e.stderr}"
        )
    
    if not output_path.exists():
        raise RuntimeError(f"FluidSynth completed but output file not found: {output_path}")
    
    print(f"Rendered WAV to {output_path}")
    return output_path


def get_year_time_ranges(
    config: Dict[str, Any],
) -> List[Tuple[int, float, float]]:
    """
    Get time ranges for each year.
    
    Returns:
        List of (year, start_seconds, end_seconds) tuples
    """
    grid = get_time_grid(config)
    
    ranges = []
    for year in grid.years():
        start_time, end_time = grid.year_to_time_range(year)
        ranges.append((year, start_time, end_time))
    
    return ranges


def slice_per_year_wavs(
    full_wav_path: Path,
    config: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> List[Path]:
    """
    Slice a full timeline WAV into per-year clips.
    
    Args:
        full_wav_path: Path to full timeline WAV
        config: Configuration dictionary
        output_dir: Directory for year WAV files
        
    Returns:
        List of paths to year WAV files
    """
    if not full_wav_path.exists():
        raise FileNotFoundError(f"WAV file not found: {full_wav_path}")
    
    # Determine output directory
    if output_dir is None:
        paths = get_output_paths(config)
        output_dir = paths["audio_dir"]
    
    ensure_dir(output_dir)
    
    # Load full WAV
    print(f"Loading {full_wav_path} for slicing...")
    data, sample_rate = sf.read(full_wav_path)
    
    # Get year time ranges
    year_ranges = get_year_time_ranges(config)
    
    output_paths = []
    
    for year, start_time, end_time in year_ranges:
        # Convert times to samples
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)
        
        # Handle edge cases
        start_sample = max(0, start_sample)
        end_sample = min(len(data), end_sample)
        
        if start_sample >= end_sample:
            print(f"Warning: Year {year} has no audio data (start={start_sample}, end={end_sample})")
            continue
        
        # Extract year audio
        year_data = data[start_sample:end_sample]
        
        # Write year WAV
        year_path = output_dir / f"{year}.wav"
        sf.write(year_path, year_data, sample_rate)
        output_paths.append(year_path)
        
        duration = (end_sample - start_sample) / sample_rate
        print(f"  {year}.wav: {duration:.1f}s")
    
    print(f"Sliced {len(output_paths)} year clips to {output_dir}")
    return output_paths


def render_full_pipeline(
    config: Dict[str, Any],
    midi_path: Optional[Path] = None,
    soundfont_path: Optional[Path] = None,
) -> Dict[str, Path]:
    """
    Run complete render pipeline: MIDI → Full WAV → Per-year WAVs.
    
    Args:
        config: Configuration dictionary
        midi_path: Path to MIDI file (default from config paths)
        soundfont_path: Path to SoundFont (default from config)
        
    Returns:
        Dict with keys 'full_wav' and 'year_wavs'
    """
    # Get paths
    paths = get_output_paths(config)
    park_name = config["park"]["park_name"].lower()
    park_id = config["park"]["park_id"]
    start = config["time"]["start_year"]
    end = config["time"]["end_year"]
    
    # MIDI path
    if midi_path is None:
        midi_path = paths["midi_dir"] / f"{park_name}_{start}_{end}.mid"
    
    # SoundFont path
    if soundfont_path is None:
        sf_path_str = config["render"].get("soundfont_path", "data/raw/soundfont.sf2")
        soundfont_path = resolve_path(sf_path_str)
    
    # Output paths
    sample_rate = config["render"].get("sample_rate", 44100)
    full_wav_path = paths["audio_dir"].parent / f"{park_id}_full.wav"
    
    # Render full WAV
    render_midi_to_wav(
        midi_path=midi_path,
        output_path=full_wav_path,
        soundfont_path=soundfont_path,
        sample_rate=sample_rate,
    )
    
    result = {"full_wav": full_wav_path}
    
    # Slice per-year if enabled
    if config["render"].get("per_year_wav", True):
        year_wavs = slice_per_year_wavs(
            full_wav_path=full_wav_path,
            config=config,
            output_dir=paths["audio_dir"],
        )
        result["year_wavs"] = year_wavs
    
    return result
