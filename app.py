# 1. Setup the Dashboard
st.set_page_config(layout="wide")
st.title("⚾ Live Home Run Hunter Dashboard")
st.write("Targeting weak pitchers with real-time Statcast data...")

# 2. Hitter Data Engine
@st.cache_data
def load_hitters():
    stats = statcast_batter_expected_stats(2026, minPA=100)
    hitters = stats[['last_name, first_name', 'pa', 'est_woba', 'est_slg', 'est_ba']]
    hitters = hitters.rename(columns={'last_name, first_name': 'Hitter'})
    hitters = hitters[hitters['pa'] >= 100]
    return hitters

# 3. Pitcher Data Engine
@st.cache_data
def load_pitchers():
    # Pull expected stats for pitchers
    stats = statcast_pitcher_expected_stats(2026, minPA=50) 
    pitchers = stats[['last_name, first_name', 'est_woba', 'est_slg']]
    pitchers = pitchers.rename(columns={'last_name, first_name': 'Pitcher'})
    return pitchers

df_hitters = load_hitters()
df_pitchers = load_pitchers()

# 4. The Sidebar Matchup Selector
st.sidebar.header("🎯 Matchup Settings")
# Create an alphabetical list of pitchers for the dropdown menu
pitcher_list = df_pitchers['Pitcher'].sort_values().tolist()
selected_pitcher = st.sidebar.selectbox("Select Today's Opposing Pitcher:", pitcher_list)

# 5. The Matchup Math
# Find the stats of the specific pitcher you selected
pitcher_stats = df_pitchers[df_pitchers['Pitcher'] == selected_pitcher].iloc[0]
pitcher_slg_allowed = pitcher_stats['est_slg']

# Create the new "Matchup Score" column (Hitter Power + Pitcher Power Allowed)
df_hitters['Matchup Score'] = df_hitters['est_slg'] + pitcher_slg_allowed

# Sort the board by the best Matchup Scores
df_hitters = df_hitters.sort_values(by='Matchup Score', ascending=False).head(25)

# Rearrange the columns to put the Matchup Score right next to the Hitter's name
df_hitters = df_hitters[['Hitter', 'Matchup Score', 'pa', 'est_woba', 'est_slg', 'est_ba']]

# 6. Paint the Heatmap
styled_df = df_hitters.style.background_gradient(
    cmap='RdYlGn', 
    subset=['Matchup Score', 'est_woba', 'est_slg', 'est_ba']
)

# 7. Render to screen
st.dataframe(styled_df, use_container_width=True)

