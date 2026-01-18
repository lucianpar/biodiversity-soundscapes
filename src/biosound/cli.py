"""
Command-line interface for Biodiversity Soundscapes.

Commands:
- biosound run: Run full pipeline
- biosound demo: Launch Streamlit demo
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="biosound",
    help="Convert biodiversity observations into ambient MIDI timelines.",
    add_completion=False,
)

console = Console()


def get_project_root() -> Path:
    """Get project root directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


@app.command()
def run(
    config: str = typer.Option(
        "config/v0_yosemite.yaml",
        "--config", "-c",
        help="Path to YAML configuration file",
    ),
    skip_render: bool = typer.Option(
        False,
        "--skip-render",
        help="Skip audio rendering (MIDI only)",
    ),
    skip_midi: bool = typer.Option(
        False,
        "--skip-midi",
        help="Skip MIDI generation (processing only)",
    ),
):
    """
    Run the full biodiversity sonification pipeline.
    
    Steps:
    1. Standardize: Load and validate observations
    2. Aggregate: Compute per-year, per-species summaries
    3. Metrics: Calculate richness, turnover, confidence
    4. MIDI: Generate musical timeline
    5. Render: Convert to WAV audio
    """
    from biosound.utils.io import load_config, resolve_path, get_output_paths, get_parquet_paths
    
    # Resolve config path
    root = get_project_root()
    config_path = resolve_path(config, root)
    
    console.print(Panel(
        f"[bold blue]Biodiversity Soundscapes[/]\n"
        f"Config: {config_path}",
        title="Starting Pipeline",
    ))
    
    # Load config
    try:
        cfg = load_config(config_path)
    except Exception as e:
        console.print(f"[red]Error loading config:[/] {e}")
        raise typer.Exit(1)
    
    run_id = cfg["run_id"]
    park_name = cfg["park"]["park_name"]
    start_year = cfg["time"]["start_year"]
    end_year = cfg["time"]["end_year"]
    
    console.print(f"Run ID: [cyan]{run_id}[/]")
    console.print(f"Park: [cyan]{park_name}[/]")
    console.print(f"Years: [cyan]{start_year}-{end_year}[/]")
    console.print()
    
    # Step 1: Standardize
    console.print("[bold]Step 1: Standardizing observations...[/]")
    try:
        from biosound.processing.standardize import standardize_observations
        obs_df = standardize_observations(cfg)
        console.print(f"  ✓ {len(obs_df)} observations standardized")
    except Exception as e:
        console.print(f"[red]Error in standardization:[/] {e}")
        raise typer.Exit(1)
    
    # Step 2: Aggregate
    console.print("[bold]Step 2: Aggregating by year and species...[/]")
    try:
        from biosound.processing.aggregate import aggregate_by_year_species
        year_species_df = aggregate_by_year_species(cfg, obs_df)
        n_years = year_species_df["year"].nunique()
        n_species = year_species_df["species_id"].nunique()
        console.print(f"  ✓ {n_years} years, {n_species} species")
    except Exception as e:
        console.print(f"[red]Error in aggregation:[/] {e}")
        raise typer.Exit(1)
    
    # Step 3: Metrics
    console.print("[bold]Step 3: Computing metrics...[/]")
    try:
        from biosound.processing.metrics import compute_year_metrics
        metrics_df = compute_year_metrics(cfg, year_species_df)
        mean_richness = metrics_df["richness"].mean()
        mean_turnover = metrics_df["turnover"].mean()
        console.print(f"  ✓ Mean richness: {mean_richness:.1f}, Mean turnover: {mean_turnover:.2%}")
    except Exception as e:
        console.print(f"[red]Error computing metrics:[/] {e}")
        raise typer.Exit(1)
    
    if skip_midi:
        console.print("[yellow]Skipping MIDI generation (--skip-midi)[/]")
    else:
        # Step 4: MIDI
        console.print("[bold]Step 4: Generating MIDI...[/]")
        try:
            from biosound.mapping.rules_v0 import MappingRulesV0
            from biosound.mapping.midi_writer import generate_midi
            from biosound.mapping.metadata import generate_mapping_metadata
            
            # Load data from parquet (ensure consistency)
            import pandas as pd
            parquet_paths = get_parquet_paths(cfg)
            year_species_df = pd.read_parquet(parquet_paths["year_species"])
            metrics_df = pd.read_parquet(parquet_paths["year_features"])
            
            # Generate music
            rules = MappingRulesV0(cfg)
            year_music_dict = rules.generate_all_years(year_species_df, metrics_df)
            
            # Write MIDI
            midi_path = generate_midi(cfg, year_music_dict)
            
            # Write metadata
            meta_path = generate_mapping_metadata(
                cfg, year_music_dict, rules, year_species_df, metrics_df
            )
            
            total_notes = sum(len(ym.notes) for ym in year_music_dict.values())
            console.print(f"  ✓ {total_notes} notes generated")
            console.print(f"  ✓ MIDI: {midi_path}")
            console.print(f"  ✓ Metadata: {meta_path}")
            
        except Exception as e:
            console.print(f"[red]Error generating MIDI:[/] {e}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(1)
        
        if skip_render:
            console.print("[yellow]Skipping audio rendering (--skip-render)[/]")
        else:
            # Step 5: Render
            console.print("[bold]Step 5: Rendering audio...[/]")
            try:
                from biosound.render.fluidsynth_render import render_full_pipeline
                
                result = render_full_pipeline(cfg, midi_path)
                
                console.print(f"  ✓ Full WAV: {result['full_wav']}")
                if 'year_wavs' in result:
                    console.print(f"  ✓ {len(result['year_wavs'])} year clips generated")
                    
            except FileNotFoundError as e:
                console.print(f"[yellow]Warning: {e}[/]")
                console.print("[yellow]Audio rendering skipped. Install FluidSynth and add a SoundFont to enable.[/]")
            except Exception as e:
                console.print(f"[red]Error rendering audio:[/] {e}")
                console.print("[yellow]Audio rendering failed but pipeline otherwise complete.[/]")
    
    # Summary
    console.print()
    paths = get_output_paths(cfg)
    parquet_paths = get_parquet_paths(cfg)
    
    console.print(Panel(
        f"[bold green]Pipeline Complete![/]\n\n"
        f"[bold]Output files:[/]\n"
        f"  • Observations: {parquet_paths['observations']}\n"
        f"  • Year features: {parquet_paths['year_features']}\n"
        f"  • MIDI: {paths['midi_dir']}/\n"
        f"  • Audio: {paths['audio_dir']}/\n\n"
        f"[bold]Next steps:[/]\n"
        f"  • Launch demo: [cyan]biosound demo --config {config}[/]\n"
        f"  • Or run: [cyan]streamlit run src/biosound/demo/app_streamlit.py[/]",
        title="Complete",
    ))


@app.command()
def demo(
    config: str = typer.Option(
        "config/v0_yosemite.yaml",
        "--config", "-c",
        help="Path to YAML configuration file",
    ),
    port: int = typer.Option(
        8501,
        "--port", "-p",
        help="Port for Streamlit server",
    ),
):
    """
    Launch the Streamlit demo UI.
    """
    import subprocess
    
    root = get_project_root()
    app_path = root / "src" / "biosound" / "demo" / "app_streamlit.py"
    
    if not app_path.exists():
        console.print(f"[red]Demo app not found at {app_path}[/]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"[bold blue]Launching Biodiversity Soundscapes Demo[/]\n"
        f"Config: {config}\n"
        f"Port: {port}",
        title="Streamlit Demo",
    ))
    
    # Launch Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(port),
        "--",
        config,
    ]
    
    console.print(f"Running: {' '.join(cmd)}")
    console.print()
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo stopped.[/]")


@app.command()
def info(
    config: str = typer.Option(
        "config/v0_yosemite.yaml",
        "--config", "-c",
        help="Path to YAML configuration file",
    ),
):
    """
    Show information about a run's outputs.
    """
    from biosound.utils.io import load_config, resolve_path, get_output_paths, get_parquet_paths
    
    root = get_project_root()
    config_path = resolve_path(config, root)
    
    try:
        cfg = load_config(config_path)
    except Exception as e:
        console.print(f"[red]Error loading config:[/] {e}")
        raise typer.Exit(1)
    
    run_id = cfg["run_id"]
    paths = get_output_paths(cfg)
    parquet_paths = get_parquet_paths(cfg)
    
    console.print(Panel(
        f"[bold]Run ID:[/] {run_id}\n"
        f"[bold]Park:[/] {cfg['park']['park_name']}\n"
        f"[bold]Years:[/] {cfg['time']['start_year']}-{cfg['time']['end_year']}",
        title="Run Information",
    ))
    
    console.print("\n[bold]Data files:[/]")
    for name, path in parquet_paths.items():
        status = "✓" if path.exists() else "✗"
        color = "green" if path.exists() else "red"
        console.print(f"  [{color}]{status}[/] {name}: {path}")
    
    console.print("\n[bold]Output directories:[/]")
    for name, path in paths.items():
        status = "✓" if path.exists() else "✗"
        color = "green" if path.exists() else "red"
        console.print(f"  [{color}]{status}[/] {name}: {path}")
    
    # Check for audio files
    audio_dir = paths["audio_dir"]
    if audio_dir.exists():
        wav_files = list(audio_dir.glob("*.wav"))
        console.print(f"\n[bold]Audio files:[/] {len(wav_files)} WAV files")


if __name__ == "__main__":
    app()
