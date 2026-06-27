import streamlit as st
import pandas as pd
from pybaseball import statcast_batter_expected_stats

# 1. Setup the Dashboard
st.set_page_config(layout="wide")
st.title("⚾ Live Home Run Hunter Dashboard")
st.write("Pulling real-time 2026 Statcast data (Bypassing FanGraphs!)...")

# 2. The Data Engine (Hitting Baseball Savant directly)
@st.cache_data
def load_statcast_data():
    # Pull the live 2026 Statcast expected stats (minimum 100 plate appearances)
    stats = statcast_batter_expected_stats(2026, minPA=100)
    
    # Select the Statcast columns we care about
    # (est_woba = Expected wOBA, est_slg = Expected Slugging for power)
    my_hitters = stats[['last_name', 'first_name', 'pa', 'est_woba', 'est_slg', 'est_ba']]
    
    # Sort by highest expected slugging (est_slg) to find the biggest power threats
    my_hitters = my_hitters.sort_values(by='est_slg', ascending=False).head(25)
    
    # Clean up the names so they look nice
    my_hitters['Player'] = my_hitters['first_name'] + ' ' + my_hitters['last_name']
    
    # Reorder columns and drop the separated names
    return my_hitters[['Player', 'pa', 'est_woba', 'est_slg', 'est_ba']]

# 3. Load the Data
df = load_statcast_data()

# 4. Paint the Heatmap (Green = Good, Red = Bad)
styled_df = df.style.background_gradient(cmap='RdYlGn', subset=['est_woba', 'est_slg', 'est_ba'])

# 5. Render the table to the screen
st.dataframe(styled_df, use_container_width=True)
