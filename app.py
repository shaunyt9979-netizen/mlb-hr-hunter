import streamlit as st
import pandas as pd
from pybaseball import statcast_batter_expected_stats

# 1. Setup the Dashboard
st.set_page_config(layout="wide")
st.title("⚾ Live Home Run Hunter Dashboard")
st.write("Pulling real-time 2026 Statcast data...")

# 2. The Data Engine
@st.cache_data
def load_statcast_data():
    # Pull the live 2026 Statcast expected stats
    stats = statcast_batter_expected_stats(2026, minPA=100)
    
    # 1. CREATE the variable by grabbing the exact columns we scouted (You accidentally deleted this line!)
    my_hitters = stats[['last_name, first_name', 'pa', 'est_woba', 'est_slg', 'est_ba']]
    
    # 2. Rename that ugly combined column to just 'Player'
    my_hitters = my_hitters.rename(columns={'last_name, first_name': 'Player'})
    
    # 3. Force Pandas to drop the minor leaguers (The 5-second fix)
    my_hitters = my_hitters[my_hitters['pa'] >= 100]
    
    # 4. Sort by highest expected slugging (est_slg) to find the biggest power threats
    my_hitters = my_hitters.sort_values(by='est_slg', ascending=False).head(25)
    
    return my_hitters


# 3. Load the Data
df = load_statcast_data()

# 4. Paint the Heatmap (Green = Good, Red = Bad)
# We only apply the color gradient to the actual stat numbers, not the Player name or PA
styled_df = df.style.background_gradient(cmap='RdYlGn', subset=['est_woba', 'est_slg', 'est_ba'])

# 5. Render the table to the screen
st.dataframe(styled_df, use_container_width=True)
