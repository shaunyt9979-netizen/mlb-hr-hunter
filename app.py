import streamlit as st
import pandas as pd
import requests
import datetime

from pybaseball import statcast_batter_expected_stats, statcast_pitcher_expected_stats, statcast_batter_exitvelo_barrels

# 1. Setup the Dashboard
st.set_page_config(layout="wide")
st.title("⚾ Live Home Run Hunter Dashboard")
st.write("Targeting weak pitchers with real-time Statcast data...")

# 2. Hitter Data Engine (Now with Launch Angle & Sweet Spot!)
@st.cache_data
def load_hitters():
    # Pull expected stats database
    exp_stats = statcast_batter_expected_stats(2026, minPA=100)
    
    # Pull exit velocity / batted ball database
    ev_stats = statcast_batter_exitvelo_barrels(2026, minBBE=50)
    
    # Clean up the batted ball data using the EXACT API column names
    ev_stats_clean = ev_stats[['player_id', 'avg_hit_angle', 'anglesweetspotpercent']]
    
    # MERGE: Combine both datasets using their unique player_id
    stats = pd.merge(exp_stats, ev_stats_clean, on='player_id', how='inner')
    
    # Select our new master list of columns (using the exact API name)
    hitters = stats[['last_name, first_name', 'pa', 'est_woba', 'est_slg', 'est_ba', 'avg_hit_angle', 'anglesweetspotpercent']]
    
    # Rename columns so they look clean on the dashboard
    hitters = hitters.rename(columns={
        'last_name, first_name': 'Hitter',
        'avg_hit_angle': 'Launch Angle',
        'anglesweetspotpercent': 'Sweet Spot %'
    })
    
    return hitters

# 3. Pitcher Data Engine
@st.cache_data
def load_pitchers():
    stats = statcast_pitcher_expected_stats(2026, minPA=50) 
    pitchers = stats[['last_name, first_name', 'est_woba', 'est_slg']]
    pitchers = pitchers.rename(columns={'last_name, first_name': 'Pitcher'})
    return pitchers

# Download all the data
df_hitters = load_hitters()
df_pitchers = load_pitchers()

# 4. The Sidebar Matchup Selector
st.sidebar.header("🎯 Matchup Settings")
pitcher_list = df_pitchers['Pitcher'].sort_values().tolist()
selected_pitcher = st.sidebar.selectbox("Select Today's Opposing Pitcher:", pitcher_list)

# 5. The Matchup Math
pitcher_stats = df_pitchers[df_pitchers['Pitcher'] == selected_pitcher].iloc[0]
pitcher_slg_allowed = pitcher_stats['est_slg']

# Hitter Slugging + Pitcher Slugging Allowed
df_hitters['Matchup Score'] = df_hitters['est_slg'] + pitcher_slg_allowed
df_hitters = df_hitters.sort_values(by='Matchup Score', ascending=False).head(25)

# Rearrange columns for maximum visual impact
df_hitters = df_hitters[['Hitter', 'Matchup Score', 'Launch Angle', 'Sweet Spot %', 'pa', 'est_woba', 'est_slg', 'est_ba']]

# 6. Paint and Format the Table
format_dict = {
    'Matchup Score': '{:.3f}',
    'Launch Angle': '{:.1f}°',
    'Sweet Spot %': '{:.1f}%',
    'est_woba': '{:.3f}',
    'est_slg': '{:.3f}',
    'est_ba': '{:.3f}'
}

styled_df = df_hitters.style.format(format_dict).background_gradient(
    cmap='RdYlGn', 
    subset=['Matchup Score', 'Sweet Spot %', 'est_woba', 'est_slg']
)

# 7. Render to screen
st.dataframe(styled_df, use_container_width=True)

# --- LIVE SCOREBOARD SECTION ---

# 1. Get today's date dynamically
today_date = datetime.datetime.today().strftime('%Y-%m-%d')
current_year = datetime.datetime.today().year

# 2. The Armored API Call (Caches data for 1 hour)
@st.cache_data(ttl=3600)
def get_live_schedule():
    # MLB is League ID 1 in API-Sports
    url = f"https://v1.baseball.api-sports.io/games?league=1&season={current_year}&date={today_date}"
    
    # Securely pulling your key from the Streamlit vault
    headers = {
        'x-apisports-key': st.secrets["API_SPORTS_KEY"]
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # ADD THIS LINE RIGHT HERE:
        st.sidebar.write("DEBUG DATA:", data)
        
        games_list = []

        games_list = []
        # Parse the JSON response
        if 'response' in data and len(data['response']) > 0:
            for game in data['response']:
                home_team = game['teams']['home']['name']
                away_team = game['teams']['away']['name']
                # Clean up the time formatting if needed
                status = game['status']['long']
                
                games_list.append(f"⚾ {away_team} @ {home_team} ({status})")
            return games_list
        else:
            return ["No games scheduled for today yet."]
    except Exception as e:
        return ["Waiting for schedule data..."]

# 3. Put it in the Sidebar for clean viewing
st.sidebar.markdown("---")
st.sidebar.header("📅 Today's Matchups")
todays_games = get_live_schedule()

for game in todays_games:
    st.sidebar.info(game)

