# Biodiversity Soundscapes - Developer Guide

Technical architecture and extension guide for developers.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM ARCHITECTURE                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                              CLI LAYER                                   │   │
│  │                          src/biosound/cli.py                             │   │
│  │                     [run] [demo] [info] commands                         │   │
│  └───────────────────────────────┬─────────────────────────────────────────┘   │
│                                  │                                              │
│  ┌───────────────────────────────▼─────────────────────────────────────────┐   │
│  │                           CORE PIPELINE                                  │   │
│  │                                                                          │   │
│  │   ┌──────────┐    ┌───────────┐    ┌─────────┐    ┌───────────────┐    │   │
│  │   │ ADAPTERS │───►│PROCESSING │───►│ MAPPING │───►│    RENDER     │    │   │
│  │   │          │    │           │    │         │    │               │    │   │
│  │   │• NPS CSV │    │•Standardize│   │•Rules V0│    │• FluidSynth   │    │   │
│  │   │• eBird   │    │•Aggregate │    │•MIDI    │    │• WAV slicing  │    │   │
│  │   │• iNat    │    │•Metrics   │    │•Metadata│    │               │    │   │
│  │   └──────────┘    └───────────┘    └─────────┘    └───────────────┘    │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                  │                                              │
│  ┌───────────────────────────────▼─────────────────────────────────────────┐   │
│  │                           UTILITIES                                      │   │
│  │              hashing.py │ io.py │ timebins.py                            │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           DEMO LAYER                                     │   │
│  │                   src/biosound/demo/app_streamlit.py                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          MODULE DEPENDENCIES                                    │
│                                                                                 │
│                              ┌─────────┐                                        │
│                              │   CLI   │                                        │
│                              └────┬────┘                                        │
│                                   │                                             │
│              ┌────────────────────┼────────────────────┐                        │
│              │                    │                    │                        │
│              ▼                    ▼                    ▼                        │
│        ┌──────────┐        ┌───────────┐        ┌──────────┐                   │
│        │ ADAPTERS │        │ PROCESSING│        │  RENDER  │                   │
│        └────┬─────┘        └─────┬─────┘        └────┬─────┘                   │
│             │                    │                   │                          │
│             │              ┌─────┴─────┐             │                          │
│             │              │           │             │                          │
│             │              ▼           ▼             │                          │
│             │        ┌─────────┐ ┌─────────┐        │                          │
│             │        │ MAPPING │ │ MAPPING │        │                          │
│             │        │ rules   │ │  midi   │        │                          │
│             │        └────┬────┘ └────┬────┘        │                          │
│             │             │           │             │                          │
│             └─────────────┼───────────┼─────────────┘                          │
│                           │           │                                         │
│                           ▼           ▼                                         │
│                        ┌─────────────────┐                                      │
│                        │     UTILS       │                                      │
│                        │ hashing│io│time │                                      │
│                        └─────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                          │
│                                                                                 │
│  ┌─────────────┐                                                                │
│  │  RAW DATA   │  CSV, API responses                                            │
│  │  (Various)  │  Various schemas                                               │
│  └──────┬──────┘                                                                │
│         │                                                                        │
│         ▼  DataAdapter.fetch_observations()                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    CANONICAL SCHEMA (DataFrame)                         │    │
│  │  ┌──────────┬───────────┬──────┬────────────┬────────────┬───────────┐ │    │
│  │  │ park_id  │ park_name │ year │ species_id │species_name│ obs_count │ │    │
│  │  │  str     │   str     │ int  │    str     │    str     │   float   │ │    │
│  │  └──────────┴───────────┴──────┴────────────┴────────────┴───────────┘ │    │
│  └──────┬──────────────────────────────────────────────────────────────────┘    │
│         │                                                                        │
│         ▼  standardize_observations()                                            │
│  ┌─────────────┐                                                                │
│  │ OBSERVATIONS│  {run_id}_observations_{start}_{end}.parquet                   │
│  │  (Parquet)  │  Validated, cleaned, typed                                     │
│  └──────┬──────┘                                                                │
│         │                                                                        │
│         ▼  aggregate_by_year_species()                                           │
│  ┌─────────────┐                                                                │
│  │YEAR_SPECIES │  {run_id}_year_species_{start}_{end}.parquet                   │
│  │  (Parquet)  │  Grouped by (year, species_id)                                 │
│  └──────┬──────┘                                                                │
│         │                                                                        │
│         ▼  compute_year_metrics()                                                │
│  ┌─────────────┐                                                                │
│  │YEAR_FEATURES│  {run_id}_year_features_{start}_{end}.parquet                  │
│  │  (Parquet)  │  richness, turnover, confidence, top_species                   │
│  └──────┬──────┘                                                                │
│         │                                                                        │
│         ▼  MappingRulesV0.generate_all_years()                                   │
│  ┌─────────────┐                                                                │
│  │ YEAR_MUSIC  │  Dict[int, YearMusic]                                          │
│  │  (Memory)   │  NoteEvents, CCEvents per year                                 │
│  └──────┬──────┘                                                                │
│         │                                                                        │
│         ├──────────────────────┐                                                 │
│         ▼                      ▼                                                 │
│  ┌─────────────┐        ┌─────────────┐                                         │
│  │    MIDI     │        │  METADATA   │                                         │
│  │   (.mid)    │        │   (.json)   │                                         │
│  └──────┬──────┘        └─────────────┘                                         │
│         │                                                                        │
│         ▼  render_midi_to_wav() + slice_per_year_wavs()                          │
│  ┌─────────────┐                                                                │
│  │  WAV FILES  │  {year}.wav for each year                                      │
│  │   (.wav)    │  Full timeline + per-year clips                                │
│  └─────────────┘                                                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Adapter Interface

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          ADAPTER PATTERN                                        │
│                                                                                 │
│                        ┌───────────────────┐                                    │
│                        │    DataAdapter    │  Abstract Base Class               │
│                        │      (ABC)        │                                    │
│                        ├───────────────────┤                                    │
│                        │ + list_parks()    │  → List[Dict]                      │
│                        │ + fetch_obs()     │  → DataFrame (canonical)           │
│                        │ + validate_output()│                                   │
│                        └─────────┬─────────┘                                    │
│                                  │                                              │
│            ┌─────────────────────┼─────────────────────┐                        │
│            │                     │                     │                        │
│            ▼                     ▼                     ▼                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ NPSLocalCSV     │  │  EBirdAPIStub   │  │  INatAPIStub    │                 │
│  │    Adapter      │  │    Adapter      │  │    Adapter      │                 │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤                 │
│  │ Reads local CSV │  │ TODO: eBird API │  │ TODO: iNat API  │                 │
│  │ Column mapping  │  │ API key auth    │  │ Place ID lookup │                 │
│  │ ✅ Implemented  │  │ ⏳ Stub only    │  │ ⏳ Stub only    │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
│                                                                                 │
│  CANONICAL OUTPUT SCHEMA:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ park_id: str │ park_name: str │ year: int │ taxon_group: str │          │   │
│  │ species_id: str │ species_name: str │ obs_count: float │ effort: float  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Mapping Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       SPECIES → MUSIC MAPPING                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     DETERMINISTIC HASHING                                │   │
│  │                                                                          │   │
│  │    species_id ──────► SHA-256 ──────► stable values                     │   │
│  │                                                                          │   │
│  │    "american_robin"  ──►  stable_int("american_robin", 7)  ──► 3        │   │
│  │                           stable_int("american_robin:oct", 3) ──► 1     │   │
│  │                           stable_int("american_robin:pan", 128) ──► 73  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      SPECIES VOICE ASSIGNMENT                            │   │
│  │                                                                          │   │
│  │   species_id ──────────────────────────────────────────► SpeciesVoice   │   │
│  │                                                                          │   │
│  │   ┌────────────────┐    ┌──────────────────────────────────────────┐    │   │
│  │   │ "american_     │    │  pitch: 67 (G4)                          │    │   │
│  │   │    robin"      │───►│  octave: 4                               │    │   │
│  │   │                │    │  pan: 73                                 │    │   │
│  │   │                │    │  program: 91 (Pad 4)                     │    │   │
│  │   └────────────────┘    └──────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         THREE LAYERS                                     │   │
│  │                                                                          │   │
│  │   LAYER A: DRONE (Channel 0)                                            │   │
│  │   ├── Root note shifts with turnover: [-3, +3] semitones                │   │
│  │   ├── Always plays: root + fifth                                        │   │
│  │   └── Velocity scaled by confidence                                     │   │
│  │                                                                          │   │
│  │   LAYER B: PADS (Channel 1)                                             │   │
│  │   ├── N voices where N = clamp(sqrt(richness)*2, min, max)              │   │
│  │   ├── Species selected by abundance + stable shuffle                    │   │
│  │   ├── Each species has unique pitch/pan/program                         │   │
│  │   └── Velocity = (25 + 70*norm_abundance) * confidence                  │   │
│  │                                                                          │   │
│  │   LAYER C: SHIMMER (Channel 2)                                          │   │
│  │   ├── Active only when turnover > 0.2                                   │   │
│  │   ├── Density increases with turnover                                   │   │
│  │   ├── Uses new_species or top_species as pitch source                   │   │
│  │   └── +24 semitones (2 octaves up)                                      │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Musical Time Model

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MUSICAL TIME GRID                                       │
│                                                                                 │
│   CONFIG:  bpm=60, bars_per_year=8, beats_per_bar=4                            │
│                                                                                 │
│   CALCULATIONS:                                                                 │
│   ├── beats_per_year = 8 × 4 = 32 beats                                        │
│   ├── seconds_per_beat = 60/60 = 1.0 second                                    │
│   └── seconds_per_year = 32 × 1.0 = 32 seconds                                 │
│                                                                                 │
│   TIMELINE (10 years = 320 beats = 320 seconds):                               │
│                                                                                 │
│   Beat:    0        32       64       96      128      ...     288     320     │
│            │        │        │        │        │                │       │      │
│   Year:   2016     2017     2018     2019     2020     ...     2024    2025    │
│            │        │        │        │        │                │       │      │
│            ├────────┼────────┼────────┼────────┼────────────────┼───────┤      │
│            │ 8 bars │ 8 bars │ 8 bars │ 8 bars │      ...       │8 bars │      │
│            └────────┴────────┴────────┴────────┴────────────────┴───────┘      │
│                                                                                 │
│   Time:   0:00     0:32     1:04     1:36     2:08     ...     4:48    5:20    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
biodiversity-soundscapes/
├── pyproject.toml                    # Package configuration
├── README.md                         # Project overview
├── config/
│   └── v0_yosemite.yaml             # Default config
├── data/
│   ├── raw/                          # Input data
│   │   ├── README.md                 # Data format docs
│   │   ├── yosemite_birds.csv       # User CSV data
│   │   └── soundfont.sf2            # SoundFont for rendering
│   └── processed/                    # Pipeline outputs (Parquet)
├── outputs/
│   └── runs/{run_id}/               # Run outputs
│       ├── midi/                     # MIDI files
│       ├── meta/                     # Mapping metadata JSON
│       └── audio/{park_id}/         # WAV files
├── scripts/
│   └── generate_sample_data.py      # Test data generator
├── src/biosound/
│   ├── __init__.py
│   ├── cli.py                        # Typer CLI commands
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                   # DataAdapter ABC
│   │   ├── nps_local_csv.py         # CSV file adapter
│   │   ├── ebird_api_stub.py        # eBird stub
│   │   └── inat_api_stub.py         # iNaturalist stub
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── standardize.py           # Raw → canonical
│   │   ├── aggregate.py             # Group by year/species
│   │   └── metrics.py               # Richness, turnover, etc.
│   ├── mapping/
│   │   ├── __init__.py
│   │   ├── rules_v0.py              # Mapping rules engine
│   │   ├── midi_writer.py           # pretty_midi wrapper
│   │   └── metadata.py              # JSON sidecar generation
│   ├── render/
│   │   ├── __init__.py
│   │   └── fluidsynth_render.py     # MIDI→WAV rendering
│   ├── demo/
│   │   ├── __init__.py
│   │   └── app_streamlit.py         # Streamlit UI
│   └── utils/
│       ├── __init__.py
│       ├── hashing.py               # Deterministic hashing
│       ├── io.py                    # Config loading, paths
│       └── timebins.py              # TimeGrid utilities
└── tests/
    ├── conftest.py                   # Pytest fixtures
    ├── test_schema.py               # Adapter schema tests
    ├── test_metrics.py              # Metrics computation tests
    └── test_mapping_determinism.py  # Determinism tests
```

## Adding a New Data Adapter

```python
# src/biosound/adapters/my_adapter.py

from biosound.adapters.base import DataAdapter, normalize_species_id

class MyCustomAdapter(DataAdapter):
    """Adapter for my custom data source."""
    
    def list_parks(self) -> List[Dict[str, str]]:
        # Return available parks
        return [{"park_id": "my_park", "park_name": "My Park"}]
    
    def fetch_observations(
        self,
        park_id: str,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        # Fetch data from your source
        raw_data = self._fetch_from_source(park_id, start_year, end_year)
        
        # Transform to canonical schema
        return pd.DataFrame({
            "park_id": park_id,
            "park_name": self.park_config["park_name"],
            "year": raw_data["observation_date"].dt.year,
            "taxon_group": "bird",
            "species_id": raw_data["scientific_name"].apply(normalize_species_id),
            "species_name": raw_data["common_name"],
            "obs_count": raw_data["count"].fillna(1.0),
            "effort": raw_data.get("effort", float("nan")),
        })

# Register in src/biosound/processing/standardize.py:
ADAPTERS = {
    "nps_local_csv": NPSLocalCSVAdapter,
    "my_adapter": MyCustomAdapter,  # Add here
}
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=biosound --cov-report=html

# Run specific test file
pytest tests/test_metrics.py -v

# Run specific test
pytest tests/test_mapping_determinism.py::TestMappingDeterminism::test_full_mapping_determinism -v
```

## Key Design Principles

1. **Determinism**: All mapping uses SHA-256 hashing, no random()
2. **Modularity**: Adapters, processing, mapping, render are independent
3. **Reproducibility**: Same input always produces same MIDI output
4. **Extensibility**: New adapters implement DataAdapter interface
5. **Transparency**: Mapping metadata JSON documents all decisions

## Configuration Reference

```yaml
run_id: "my_run"              # Unique identifier for outputs

park:
  park_id: "yose"             # Short park code
  park_name: "Yosemite"       # Display name

time:
  start_year: 2016            # First year (inclusive)
  end_year: 2025              # Last year (inclusive)
  bars_per_year: 8            # Musical bars per year
  bpm: 60                     # Tempo in beats per minute

data:
  adapter: "nps_local_csv"    # Adapter to use
  raw_path: "data/raw/file.csv"
  taxon_group: "bird"
  column_mapping:             # Map CSV columns to canonical
    year: "year"
    species_name: "species_name"
    obs_count: "count"
    effort: "hours"

mapping:
  mode: "d_dorian"            # Scale: d_dorian | c_minor_pentatonic
  base_root_midi: 62          # Root note (62 = D4)
  max_voices: 16              # Max species voices per year
  min_voices: 6               # Min species voices per year
  top_k_species_pool: 40      # Pool size for voice selection
  pad_programs: [89,90,91,92] # GM program numbers for species
  layers:
    drone: true               # Enable drone layer
    pads: true                # Enable species pads
    shimmer: true             # Enable change shimmer

render:
  soundfont_path: "data/raw/soundfont.sf2"
  sample_rate: 44100
  per_year_wav: true          # Generate per-year clips
  render_full: true           # Generate full timeline WAV

demo:
  enabled: true
  host: "localhost"
  port: 8501
```
