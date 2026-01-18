# Raw Data Directory

Place your source data files here before running the pipeline.

## Required Files

### 1. Bird Observations CSV (`yosemite_birds.csv`)

A CSV file containing bird observation records with at minimum:

| Column | Required | Description |
|--------|----------|-------------|
| `year` | **Yes** | Observation year (integer, e.g., 2016) |
| `species_name` | **Yes** | Common or scientific name of the bird species |
| `species_id` | No | Stable identifier (if absent, derived from species_name) |
| `obs_count` | No | Number of individuals observed (defaults to 1.0) |
| `effort` | No | Sampling effort metric (e.g., hours, party-miles) |

**Example CSV format:**
```csv
year,species_name,obs_count,effort
2016,American Robin,15,2.5
2016,Western Bluebird,8,2.5
2016,Steller's Jay,12,2.5
2017,American Robin,22,3.0
2017,Western Bluebird,5,3.0
...
```

**Column mapping:**
If your CSV has different column names, update the `column_mapping` section in your config YAML:

```yaml
data:
  column_mapping:
    year: "observation_year"        # Map your column name
    species_name: "common_name"
    obs_count: "count"
    effort: "survey_hours"
```

### 2. SoundFont File (`soundfont.sf2`)

A SoundFont file for FluidSynth rendering. Recommended options:

- **FluidR3_GM.sf2** - Free General MIDI soundfont (~150MB)
  - Download: https://member.keymusician.com/Member/FluidR3_GM/index.html
  
- **MuseScore_General.sf3** - High quality, compressed (~40MB)
  - Included with MuseScore installation
  
- **TimGM6mb.sf2** - Smaller alternative (~6MB)
  - Good for testing, less fidelity

Place the soundfont file here and update `render.soundfont_path` in your config if using a different filename.

## Data Sources

### NPS Species Lists
- https://irma.nps.gov/NPSpecies/
- Export park species lists with observation data

### eBird
- https://ebird.org/data/download
- Request custom dataset for park boundaries

### iNaturalist
- https://www.inaturalist.org/observations/export
- Filter by place and taxon

## Validation

The pipeline will validate your data on load and report:
- Missing required columns
- Invalid year ranges
- Species with no observations

Records with missing `year` or `species_name` are automatically dropped with a warning.
