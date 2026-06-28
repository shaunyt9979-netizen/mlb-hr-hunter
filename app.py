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

# --- OFFICIAL MLB LIVE SCOREBOARD SECTION ---

# 1. Get today's date dynamically
today_date = datetime.datetime.today().strftime('%Y-%m-%d')

# 2. The Free MLB API Call (No keys needed!)
@st.cache_data(ttl=3600)
def get_live_schedule():
    # Official MLB endpoint - 100% free, no limits
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_date}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        games_list = []
        
        # Check if MLB returned games for today's date
        if 'dates' in data and len(data['dates']) > 0:
            games = data['dates'][0].get('games', [])
            for game in games:
                away_team = game['teams']['away']['team']['name']
                home_team = game['teams']['home']['team']['name']
                status = game['status']['detailedState'] # usually says "Scheduled", "In Progress", or "Final"
                
                games_list.append(f"⚾ {away_team} @ {home_team} ({status})")
            return games_list
        else:
            return ["No games scheduled for today."]
            
    except Exception as e:
        return ["Error loading MLB schedule..."]

# 3. Put it in the Sidebar for clean viewing
st.sidebar.markdown("---")
st.sidebar.header("📅 Today's Matchups")
todays_games = get_live_schedule()

for game in todays_games:
    st.sidebar.info(game)
