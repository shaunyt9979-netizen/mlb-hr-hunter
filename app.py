import streamlit as st
import pandas as pd
from pybaseball import batting_stats

# 1. Setup the Dashboard
st.set_page_config(layout="wide")
st.title("⚾ Live Home Run Hunter Dashboard")
st.write("Pulling real-time 2026 Statcast data...")

# 2. The Data Engine (Caching prevents the app from crashing by saving the data memory)
@st.cache_data
def load_live_stats():
    # Pull the live 2026 MLB season stats (players with at least 100 Plate Appearances)
    # This automatically pulls all metrics FanGraphs has available!
    stats = batting_stats(2026, qual=100)
    
    # Select the specific columns we care about for Home Run Hunting
    # (ISO = Raw Power, wRC+ = Overall hitting rating)
    my_hitters = stats[['Name', 'Team', 'PA', 'HR', 'ISO', 'wOBA', 'wRC+']]
    
    # Sort by the highest ISO (Isolated Power) to find the biggest HR threats
    my_hitters = my_hitters.sort_values(by='ISO', ascending=False).head(25)
    return my_hitters

# 3. Load the Data
df = load_live_stats()

# 4. Paint the Heatmap (Green = Good, Red = Bad)
styled_df = df.style.background_gradient(cmap='RdYlGn', subset=['HR', 'ISO', 'wOBA', 'wRC+'])

# 5. Render the table to the screen
st.dataframe(styled_df, use_container_width=True)
