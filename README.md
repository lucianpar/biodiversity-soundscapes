# Biodiversity Soundscapes

Convert biodiversity observations into ambient, structurally legible MIDI timelines.

## Overview

This project transforms ecological observation data (birds, plants, etc.) into musical compositions that sonify biodiversity patterns over time. The v0 prototype focuses on **Yosemite bird observations** across **10 yearly bins (2016-2025)**.

### Features

- **Modular adapter architecture** for multiple data sources (NPS, eBird, iNaturalist)
- **Deterministic mapping** from species/metrics to musical parameters
- **Three-layer ambient composition**:
  - **Drone**: Structural anchor reflecting ecosystem turnover
  - **Pads**: Species voices representing ecosystem body
  - **Shimmer**: Change texture highlighting biodiversity shifts
- **Per-year WAV rendering** for interactive exploration
- **Streamlit demo UI** with year scrubbing and layer toggles

## Installation

```bash
# Clone and install
cd biodiversity-soundscapes
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Install FluidSynth (required for audio rendering)
# macOS:
brew install fluidsynth
# Ubuntu:
sudo apt-get install fluidsynth
```

## Quick Start

1. **Prepare data** (see `data/raw/README.md`):
   - Place `yosemite_birds.csv` in `data/raw/`
   - Place a SoundFont file (`soundfont.sf2`) in `data/raw/`

2. **Run the pipeline**:
   ```bash
   biosound run --config config/v0_yosemite.yaml
   ```

3. **Launch the demo**:
   ```bash
   biosound demo --config config/v0_yosemite.yaml
   ```

## Pipeline Outputs

After running `biosound run`, you'll find:

```
data/processed/
  yosemite_v0_observations_2016_2025.parquet
  yosemite_v0_year_species_2016_2025.parquet
  yosemite_v0_year_features_2016_2025.parquet

outputs/runs/yosemite_v0/
  midi/yosemite_2016_2025.mid
  meta/yosemite_2016_2025_mapping.json
  audio/yose/
    2016.wav
    2017.wav
    ...
    2025.wav
```

## Configuration

Edit `config/v0_yosemite.yaml` to customize:

- Time range and resolution
- Musical mode (D Dorian, C minor pentatonic)
- Voice counts and species pool size
- Layer toggles
- Rendering parameters

## Architecture

```
src/biosound/
├── adapters/      # Data source connectors
├── processing/    # Standardize → Aggregate → Metrics
├── mapping/       # Species → MIDI rules
├── render/        # MIDI → WAV via FluidSynth
├── demo/          # Streamlit UI
└── utils/         # Hashing, I/O, time bins
```

## Adding New Data Sources

1. Create an adapter in `src/biosound/adapters/` implementing `DataAdapter`
2. Map source columns to the canonical schema
3. Update config to use your adapter

See `adapters/base.py` for the interface specification.

## Tests

```bash
pytest tests/ -v
```

## License

MIT
