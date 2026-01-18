"""
Time binning utilities for musical time grid calculations.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TimeGrid:
    """Musical time grid parameters."""
    
    start_year: int
    end_year: int
    bars_per_year: int
    bpm: float
    beats_per_bar: int = 4
    
    @property
    def num_years(self) -> int:
        """Number of years in the timeline."""
        return self.end_year - self.start_year + 1
    
    @property
    def beats_per_year(self) -> int:
        """Total beats per year segment."""
        return self.bars_per_year * self.beats_per_bar
    
    @property
    def total_beats(self) -> int:
        """Total beats in entire timeline."""
        return self.num_years * self.beats_per_year
    
    @property
    def seconds_per_beat(self) -> float:
        """Duration of one beat in seconds."""
        return 60.0 / self.bpm
    
    @property
    def seconds_per_year(self) -> float:
        """Duration of one year segment in seconds."""
        return self.beats_per_year * self.seconds_per_beat
    
    @property
    def total_duration(self) -> float:
        """Total duration in seconds."""
        return self.total_beats * self.seconds_per_beat
    
    def year_to_beat_range(self, year: int) -> Tuple[float, float]:
        """
        Get beat range for a year.
        
        Args:
            year: Year value
            
        Returns:
            Tuple of (start_beat, end_beat)
        """
        year_index = year - self.start_year
        start_beat = year_index * self.beats_per_year
        end_beat = start_beat + self.beats_per_year
        return (float(start_beat), float(end_beat))
    
    def year_to_time_range(self, year: int) -> Tuple[float, float]:
        """
        Get time range in seconds for a year.
        
        Args:
            year: Year value
            
        Returns:
            Tuple of (start_time, end_time) in seconds
        """
        start_beat, end_beat = self.year_to_beat_range(year)
        return (
            start_beat * self.seconds_per_beat,
            end_beat * self.seconds_per_beat,
        )
    
    def beat_to_time(self, beat: float) -> float:
        """Convert beat position to time in seconds."""
        return beat * self.seconds_per_beat
    
    def time_to_beat(self, time: float) -> float:
        """Convert time in seconds to beat position."""
        return time / self.seconds_per_beat
    
    def years(self) -> List[int]:
        """Get list of all years in range."""
        return list(range(self.start_year, self.end_year + 1))


def get_time_grid(config: dict) -> TimeGrid:
    """
    Create a TimeGrid from configuration.
    
    Args:
        config: Configuration dictionary with 'time' section
        
    Returns:
        TimeGrid instance
    """
    time_cfg = config["time"]
    return TimeGrid(
        start_year=time_cfg["start_year"],
        end_year=time_cfg["end_year"],
        bars_per_year=time_cfg.get("bars_per_year", 8),
        bpm=time_cfg.get("bpm", 60),
    )


def year_to_beats(year: int, config: dict) -> Tuple[float, float]:
    """
    Convenience function to get beat range for a year.
    
    Args:
        year: Year value
        config: Configuration dictionary
        
    Returns:
        Tuple of (start_beat, end_beat)
    """
    grid = get_time_grid(config)
    return grid.year_to_beat_range(year)
