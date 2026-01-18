"""
Streamlit demo app for Biodiversity Soundscapes.

Interactive exploration of sonified biodiversity data:
- Year slider for temporal navigation
- Layer toggles (informational in v0)
- Richness and turnover visualizations
- Per-year audio playback
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

# Import after streamlit to avoid import order issues
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML config file."""
    import yaml
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def find_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def load_year_features(config: Dict[str, Any]) -> pd.DataFrame:
    """Load year features parquet."""
    root = find_project_root()
    run_id = config["run_id"]
    start = config["time"]["start_year"]
    end = config["time"]["end_year"]
    
    path = root / "data" / "processed" / f"{run_id}_year_features_{start}_{end}.parquet"
    
    if not path.exists():
        st.error(f"Year features not found at {path}")
        st.info("Run `biosound run --config <config.yaml>` first to generate data.")
        return pd.DataFrame()
    
    return pd.read_parquet(path)


def load_mapping_metadata(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load mapping metadata JSON."""
    root = find_project_root()
    run_id = config["run_id"]
    park_name = config["park"]["park_name"].lower()
    start = config["time"]["start_year"]
    end = config["time"]["end_year"]
    
    path = root / "outputs" / "runs" / run_id / "meta" / f"{park_name}_{start}_{end}_mapping.json"
    
    if not path.exists():
        return {}
    
    with open(path, "r") as f:
        return json.load(f)


def get_year_wav_path(config: Dict[str, Any], year: int) -> Optional[Path]:
    """Get path to WAV file for a year."""
    root = find_project_root()
    run_id = config["run_id"]
    park_id = config["park"]["park_id"]
    
    path = root / "outputs" / "runs" / run_id / "audio" / park_id / f"{year}.wav"
    
    if path.exists():
        return path
    return None


def plot_richness_turnover(df: pd.DataFrame, selected_year: int):
    """Create richness and turnover plot."""
    if HAS_PLOTLY:
        # Create dual-axis plot with Plotly
        fig = go.Figure()
        
        # Richness bars
        colors = ['#2ecc71' if y == selected_year else '#3498db' 
                  for y in df['year']]
        
        fig.add_trace(go.Bar(
            x=df['year'],
            y=df['richness'],
            name='Species Richness',
            marker_color=colors,
            yaxis='y',
        ))
        
        # Turnover line
        fig.add_trace(go.Scatter(
            x=df['year'],
            y=df['turnover'],
            name='Turnover',
            mode='lines+markers',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8),
            yaxis='y2',
        ))
        
        fig.update_layout(
            title='Species Richness and Turnover Over Time',
            xaxis=dict(title='Year', tickmode='linear'),
            yaxis=dict(title='Species Richness', side='left'),
            yaxis2=dict(title='Turnover', side='right', overlaying='y', range=[0, 1]),
            legend=dict(x=0.01, y=0.99),
            height=400,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback to matplotlib-style via streamlit
        st.subheader("Species Richness")
        richness_data = df.set_index('year')['richness']
        st.bar_chart(richness_data)
        
        st.subheader("Turnover")
        turnover_data = df.set_index('year')['turnover']
        st.line_chart(turnover_data)


def main(config_path: str = "config/v0_yosemite.yaml"):
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Biodiversity Soundscapes",
        page_icon="🎵",
        layout="wide",
    )
    
    st.title("🎵 Biodiversity Soundscapes")
    st.markdown("*Listening to ecosystem change through ambient sonification*")
    
    # Load config
    root = find_project_root()
    full_config_path = root / config_path
    
    if not full_config_path.exists():
        st.error(f"Config not found: {full_config_path}")
        return
    
    config = load_config(str(full_config_path))
    
    # Sidebar - Configuration info
    with st.sidebar:
        st.header("Configuration")
        st.write(f"**Run ID:** {config['run_id']}")
        st.write(f"**Park:** {config['park']['park_name']}")
        st.write(f"**Years:** {config['time']['start_year']}-{config['time']['end_year']}")
        st.write(f"**Mode:** {config['mapping']['mode']}")
        
        st.divider()
        
        # Layer toggles (informational in v0)
        st.header("Layers")
        st.info("Layer stems not available in v0. These show which layers are active in the mix.")
        
        layers = config['mapping'].get('layers', {})
        drone_enabled = st.checkbox("🎹 Drone", value=layers.get('drone', True), disabled=True)
        pads_enabled = st.checkbox("🎶 Pads", value=layers.get('pads', True), disabled=True)
        shimmer_enabled = st.checkbox("✨ Shimmer", value=layers.get('shimmer', True), disabled=True)
    
    # Load data
    features_df = load_year_features(config)
    
    if features_df.empty:
        st.warning("No data loaded. Please run the pipeline first.")
        st.code("biosound run --config config/v0_yosemite.yaml")
        return
    
    metadata = load_mapping_metadata(config)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Year selector
        years = sorted(features_df['year'].tolist())
        
        selected_year = st.select_slider(
            "Select Year",
            options=years,
            value=years[len(years) // 2] if years else years[0],
        )
        
        # Audio playback
        wav_path = get_year_wav_path(config, selected_year)
        
        if wav_path:
            st.audio(str(wav_path), format='audio/wav')
        else:
            st.warning(f"No audio file found for {selected_year}")
            st.info("Run `biosound run` to generate audio files.")
        
        # Visualization
        st.subheader("Biodiversity Metrics")
        plot_richness_turnover(features_df, selected_year)
    
    with col2:
        # Year details
        st.subheader(f"Year {selected_year}")
        
        year_data = features_df[features_df['year'] == selected_year]
        
        if not year_data.empty:
            row = year_data.iloc[0]
            
            # Metrics cards
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Species Richness", int(row['richness']))
            with m2:
                st.metric("Turnover", f"{row['turnover']:.2%}")
            
            m3, m4 = st.columns(2)
            with m3:
                st.metric("Total Observations", f"{int(row['total_obs']):,}")
            with m4:
                st.metric("Confidence", f"{row['confidence']:.2%}")
            
            # Species changes
            st.divider()
            
            new_count = row.get('new_species_count', 0)
            lost_count = row.get('lost_species_count', 0)
            
            if new_count > 0 or lost_count > 0:
                st.write("**Species Changes:**")
                if new_count > 0:
                    st.success(f"➕ {new_count} new species")
                if lost_count > 0:
                    st.error(f"➖ {lost_count} lost species")
        
        # Mapping info from metadata
        if metadata:
            st.divider()
            st.subheader("Sonification Info")
            
            summary = metadata.get('summary', {})
            st.write(f"**Total Notes:** {summary.get('total_notes', 'N/A'):,}")
            st.write(f"**Species Voiced:** {summary.get('total_species_voiced', 'N/A')}")
            st.write(f"**Scale:** {summary.get('scale', 'N/A')}")
            
            # Show selected species for this year
            year_info = None
            for yd in metadata.get('years', []):
                if yd['year'] == selected_year:
                    year_info = yd
                    break
            
            if year_info:
                st.write(f"**Notes this year:** {year_info.get('note_count', 'N/A')}")
                
                with st.expander("Selected Species"):
                    for species_id in year_info.get('selected_species', [])[:10]:
                        st.write(f"• {species_id}")
                    if len(year_info.get('selected_species', [])) > 10:
                        st.write(f"*...and {len(year_info['selected_species']) - 10} more*")
    
    # Footer
    st.divider()
    st.markdown(
        "*Biodiversity Soundscapes v0 — "
        "Converting ecological observations into ambient music*"
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
