#!/usr/bin/env python3
"""
Generate synthetic Yosemite bird data for testing.

This creates a realistic-looking dataset with:
- 50+ bird species typical of Yosemite
- 10 years of observations (2016-2025)
- Seasonal patterns in abundance
- Some species turnover year-to-year
- Varying sampling effort

Usage:
    python scripts/generate_sample_data.py

Output:
    data/raw/yosemite_birds.csv
"""

import csv
import random
from pathlib import Path
from typing import List, Tuple

# Seed for reproducibility
random.seed(42)

# Yosemite bird species (common residents and visitors)
YOSEMITE_BIRDS = [
    # Woodpeckers
    ("White-headed Woodpecker", "resident", 0.8),
    ("Acorn Woodpecker", "resident", 0.9),
    ("Hairy Woodpecker", "resident", 0.7),
    ("Pileated Woodpecker", "resident", 0.4),
    ("Red-breasted Sapsucker", "resident", 0.6),
    
    # Jays and Corvids
    ("Steller's Jay", "resident", 0.95),
    ("Mountain Chickadee", "resident", 0.9),
    ("Clark's Nutcracker", "resident", 0.5),
    ("Common Raven", "resident", 0.8),
    ("American Crow", "resident", 0.6),
    
    # Raptors
    ("Red-tailed Hawk", "resident", 0.7),
    ("Cooper's Hawk", "resident", 0.5),
    ("Golden Eagle", "resident", 0.3),
    ("Great Horned Owl", "resident", 0.4),
    ("Northern Pygmy-Owl", "resident", 0.3),
    
    # Songbirds - Residents
    ("American Robin", "resident", 0.9),
    ("Western Bluebird", "resident", 0.7),
    ("Dark-eyed Junco", "resident", 0.85),
    ("White-breasted Nuthatch", "resident", 0.75),
    ("Red-breasted Nuthatch", "resident", 0.7),
    ("Brown Creeper", "resident", 0.5),
    ("Golden-crowned Kinglet", "resident", 0.6),
    ("Hermit Thrush", "resident", 0.5),
    ("Townsend's Solitaire", "resident", 0.4),
    
    # Songbirds - Summer visitors
    ("Western Tanager", "summer", 0.7),
    ("Black-headed Grosbeak", "summer", 0.65),
    ("Lazuli Bunting", "summer", 0.4),
    ("Warbling Vireo", "summer", 0.6),
    ("Yellow Warbler", "summer", 0.5),
    ("Wilson's Warbler", "summer", 0.5),
    ("MacGillivray's Warbler", "summer", 0.4),
    ("Nashville Warbler", "summer", 0.45),
    ("Orange-crowned Warbler", "summer", 0.5),
    ("Yellow-rumped Warbler", "summer", 0.7),
    ("Olive-sided Flycatcher", "summer", 0.35),
    ("Western Wood-Pewee", "summer", 0.5),
    ("Hammond's Flycatcher", "summer", 0.4),
    ("Dusky Flycatcher", "summer", 0.4),
    ("Pacific-slope Flycatcher", "summer", 0.45),
    
    # Hummingbirds
    ("Anna's Hummingbird", "resident", 0.6),
    ("Calliope Hummingbird", "summer", 0.4),
    ("Rufous Hummingbird", "summer", 0.35),
    
    # Other
    ("Band-tailed Pigeon", "resident", 0.5),
    ("Mourning Dove", "resident", 0.6),
    ("Wild Turkey", "resident", 0.5),
    ("California Quail", "resident", 0.55),
    ("Spotted Towhee", "resident", 0.6),
    ("Fox Sparrow", "resident", 0.5),
    ("Song Sparrow", "resident", 0.6),
    ("Lincoln's Sparrow", "summer", 0.35),
    ("Chipping Sparrow", "summer", 0.5),
]


def generate_yearly_presence(
    species_name: str,
    season: str,
    base_prob: float,
    year: int,
) -> bool:
    """Determine if a species is present in a given year."""
    # Add some year-to-year variation
    year_factor = 0.9 + 0.2 * random.random()
    
    # Climate trend: slight decline for some species
    trend_factor = 1.0 - (year - 2016) * 0.01 * random.random()
    
    effective_prob = base_prob * year_factor * trend_factor
    
    return random.random() < effective_prob


def generate_observation_count(
    species_name: str,
    season: str,
    base_prob: float,
    year: int,
) -> int:
    """Generate observation count for a species-year."""
    # Base count related to commonness
    base_count = int(base_prob * 50)
    
    # Add variability
    count = max(1, int(base_count * (0.5 + random.random())))
    
    # Summer visitors have higher counts in good years
    if season == "summer":
        if random.random() > 0.3:
            count = int(count * 1.5)
    
    return count


def generate_effort(year: int) -> float:
    """Generate sampling effort for a year."""
    # Base effort increases slightly over time (more observers)
    base_effort = 100 + (year - 2016) * 5
    
    # Add yearly variation
    effort = base_effort * (0.8 + 0.4 * random.random())
    
    return round(effort, 1)


def generate_data() -> List[Tuple]:
    """Generate full dataset."""
    records = []
    
    for year in range(2016, 2026):  # 2016-2025
        effort = generate_effort(year)
        
        for species_name, season, base_prob in YOSEMITE_BIRDS:
            # Check if species present this year
            if generate_yearly_presence(species_name, season, base_prob, year):
                count = generate_observation_count(species_name, season, base_prob, year)
                records.append((
                    year,
                    species_name,
                    count,
                    effort,
                ))
        
        # Add some rare/vagrant species occasionally
        if random.random() > 0.7:
            vagrant_species = [
                "Varied Thrush",
                "Evening Grosbeak",
                "Pine Grosbeak",
                "Red Crossbill",
                "Cassin's Finch",
            ]
            species = random.choice(vagrant_species)
            records.append((year, species, random.randint(1, 5), effort))
    
    return records


def main():
    """Generate and write sample data."""
    # Determine output path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_path = project_root / "data" / "raw" / "yosemite_birds.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    print("Generating synthetic Yosemite bird data...")
    records = generate_data()
    
    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "species_name", "obs_count", "effort"])
        writer.writerows(records)
    
    print(f"Wrote {len(records)} records to {output_path}")
    
    # Print summary
    years = set(r[0] for r in records)
    species = set(r[1] for r in records)
    print(f"  Years: {min(years)}-{max(years)}")
    print(f"  Unique species: {len(species)}")
    print(f"  Records per year: {len(records) // len(years):.0f} avg")


if __name__ == "__main__":
    main()
