# Biodiversity Soundscapes - User Guide

Transform ecological observation data into ambient musical compositions that reveal patterns of biodiversity change over time.

## Quick Start

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BIODIVERSITY SOUNDSCAPES                            │
│                                                                             │
│    Your Data              Pipeline                 Your Music               │
│   ┌─────────┐          ┌──────────┐            ┌─────────────┐             │
│   │  CSV    │  ─────►  │ biosound │  ─────►    │  MIDI + WAV │             │
│   │  file   │          │   run    │            │   files     │             │
│   └─────────┘          └──────────┘            └─────────────┘             │
│                              │                                              │
│                              ▼                                              │
│                        ┌──────────┐                                         │
│                        │ Streamlit│                                         │
│                        │   Demo   │                                         │
│                        └──────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# 1. Clone and enter the project
cd biodiversity-soundscapes

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install
pip install -e .

# 4. (Optional) Install FluidSynth for audio rendering
# macOS:
brew install fluidsynth
# Ubuntu:
sudo apt-get install fluidsynth
```

## Preparing Your Data

### Required: Bird Observation CSV

Place your CSV file at `data/raw/yosemite_birds.csv` with this structure:

| Column | Required | Description |
|--------|----------|-------------|
| `year` | ✅ Yes | Observation year (e.g., 2016, 2017...) |
| `species_name` | ✅ Yes | Bird species name |
| `obs_count` | Optional | Number observed (defaults to 1) |
| `effort` | Optional | Sampling effort metric |

**Example:**
```csv
year,species_name,obs_count,effort
2016,American Robin,15,2.5
2016,Steller's Jay,12,2.5
2017,American Robin,22,3.0
```

### Optional: SoundFont for Audio

For WAV audio output, place a SoundFont file at `data/raw/soundfont.sf2`.

Free options:
- [FluidR3_GM](https://member.keymusician.com/Member/FluidR3_GM/index.html) (~150MB)
- [TimGM6mb](https://packages.debian.org/sid/timgm6mb-soundfont) (~6MB)

## Running the Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE WORKFLOW                                 │
│                                                                             │
│  ┌──────────┐    ┌───────────┐    ┌─────────┐    ┌──────┐    ┌──────────┐  │
│  │   CSV    │───►│Standardize│───►│Aggregate│───►│Metrics│───►│   MIDI   │  │
│  │   Data   │    │           │    │         │    │       │    │          │  │
│  └──────────┘    └───────────┘    └─────────┘    └───────┘    └────┬─────┘  │
│                                                                     │       │
│                                                                     ▼       │
│                                                              ┌──────────┐   │
│                                                              │   WAV    │   │
│                                                              │  Audio   │   │
│                                                              └──────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Basic Command

```bash
biosound run --config config/v0_yosemite.yaml
```

### Command Options

```bash
# Skip audio rendering (MIDI only)
biosound run --config config/v0_yosemite.yaml --skip-render

# Skip MIDI generation (data processing only)
biosound run --config config/v0_yosemite.yaml --skip-midi

# Show run information
biosound info --config config/v0_yosemite.yaml
```

## Output Files

After running, you'll find:

```
data/processed/
├── yosemite_v0_observations_2016_2025.parquet   # Standardized observations
├── yosemite_v0_year_species_2016_2025.parquet   # Per-year species counts
└── yosemite_v0_year_features_2016_2025.parquet  # Biodiversity metrics

outputs/runs/yosemite_v0/
├── midi/
│   └── yosemite_2016_2025.mid                   # Full MIDI timeline
├── meta/
│   └── yosemite_2016_2025_mapping.json          # Mapping documentation
└── audio/yose/
    ├── 2016.wav                                  # Per-year audio clips
    ├── 2017.wav
    └── ...
```

## Interactive Demo

```bash
biosound demo --config config/v0_yosemite.yaml
```

Opens a web interface at `http://localhost:8501`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAMLIT DEMO UI                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     🎵 Biodiversity Soundscapes                      │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │   Year Slider:  ◄──────────●──────────►                             │   │
│  │                 2016      2020       2025                           │   │
│  │                                                                     │   │
│  │   🔊 [▶ Play Audio]                                                 │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────────────────────────────────────────┐   │   │
│  │   │  📊 Species Richness & Turnover Chart                       │   │   │
│  │   │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                 │   │   │
│  │   └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │   Year 2020 Details:                                               │   │
│  │   • Richness: 28 species                                           │   │
│  │   • Turnover: 45%                                                  │   │
│  │   • Confidence: 92%                                                │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Understanding the Music

### Three Musical Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MUSICAL LAYERS                                     │
│                                                                             │
│  LAYER              WHAT IT REPRESENTS              SOUND                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  🎹 DRONE           Ecosystem stability            Low sustained            │
│                     Root shifts with turnover      tones (bass)             │
│                                                                             │
│  🎶 PADS            Individual species             Mid-range pads           │
│                     Each species = unique voice    Layered voices           │
│                                                                             │
│  ✨ SHIMMER         Change & turnover              High sparkly             │
│                     New/lost species               textures                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How Data Maps to Sound

| Biodiversity Metric | Musical Parameter |
|---------------------|-------------------|
| **Species Richness** | Number of voices playing |
| **Abundance** | Note velocity (loudness) |
| **Turnover** | Drone root shift, shimmer density |
| **Confidence** (effort) | Brightness, reverb amount |
| **Species Identity** | Unique pitch, pan position |

## Configuration

Edit `config/v0_yosemite.yaml` to customize:

```yaml
# Time range
time:
  start_year: 2016
  end_year: 2025
  bpm: 60              # Tempo (beats per minute)
  bars_per_year: 8     # Musical length per year

# Musical settings
mapping:
  mode: "d_dorian"     # Scale: "d_dorian" or "c_minor_pentatonic"
  max_voices: 16       # Maximum simultaneous species
  min_voices: 6        # Minimum voices per year
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "CSV file not found" | Place your CSV at `data/raw/yosemite_birds.csv` |
| "SoundFont not found" | Add `.sf2` file to `data/raw/` for audio rendering |
| "FluidSynth not found" | Install FluidSynth or use `--skip-render` |
| "No audio in demo" | Run `biosound run` first to generate WAV files |

## Sample Data

Generate synthetic test data to try the system:

```bash
python scripts/generate_sample_data.py
```

Creates realistic Yosemite bird data with 50+ species across 10 years.
