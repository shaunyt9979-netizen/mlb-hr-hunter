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

# --- PLAYER SPLIT STAT BOX ---

# 1. Change 'batter_id' to whatever variable name your app uses for the selected player's ID
# 2. Change 'pitcher_hand' to whatever variable name your app uses for the pitcher's throwing hand ('L' or 'R')
batter_id = "592450"  # This is a placeholder ID. Swap this out with your actual player selector variable!
pitcher_hand = "R"    # This is a placeholder hand. Swap this out with your pitcher hand variable!
@st.cache_data
def get_batter_splits(player_id, pitcher_hand):
    # 'vl' means vs Left, 'vr' means vs Right in the MLB database
    sit_code = 'vl' if pitcher_hand == 'L' else 'vr'
    
    # The actual, official MLB endpoint for batter splits
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=statSplits&group=hitting&sitCodes={sit_code}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'stats' in data and len(data['stats']) > 0:
            splits = data['stats'][0].get('splits', [])
            if len(splits) > 0:
                stats = splits[0].get('stat', {})
                return {
                    "AVG": stats.get("avg", ".000"),
                    "HR": stats.get("homeRuns", 0),
                    "OPS": stats.get("ops", ".000"),
                    "At Bats": stats.get("atBats", 0)
                }
    except Exception as e:
        pass
        
    # Fallback if the player has no data for that split yet
    return {"AVG": ".000", "HR": 0, "OPS": ".000", "At Bats": 0}

if batter_id:
    with st.spinner("Loading split data..."):
        splits = get_batter_splits(batter_id, pitcher_hand)
    
    st.markdown(f"### 📊 Batter Performance vs {pitcher_hand}HP")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Batting Avg (AVG)", value=str(splits["AVG"]))
    with col2:
        st.metric(label="On-Base + Slugging (OPS)", value=str(splits["OPS"]))
    with col3:
        st.metric(label="Home Runs (HR)", value=int(splits["HR"]))
    with col4:
        st.metric(label="Sample Size (AB)", value=int(splits["At Bats"]))
        
    st.markdown("---")
    
@st.cache_data(ttl=3600)
def get_live_schedule():
    # Official MLB endpoint
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        games_list = []
        if 'dates' in data and len(data['dates']) > 0:
            games = data['dates'][0].get('games', [])
            for game in games:
                away_team = game['teams']['away']['team']['name']
                home_team = game['teams']['home']['team']['name']
                game_id = game.get('gamePk')
                status = game['status']['detailedState']
                
                # We save this as a dictionary so we keep the ID attached to the text
                games_list.append({
                    "label": f"⚪ {away_team} @ {home_team} ({status})",
                    "game_id": game_id,
                    "away_name": away_team,
                    "home_name": home_team
                })
        return games_list
    except Exception as e:
        return []



# In your sidebar section:
st.sidebar.header("🗓️ Today's Matchups")
todays_games = get_live_schedule()

if todays_games:
    # This turns your games into a selectable dropdown list
    selected_game = st.sidebar.selectbox(
        "Select Game to Model:",
        options=todays_games,
        format_func=lambda x: x["label"]
    )
    
    # These variables now hold the active game data!
    active_game_id = selected_game["game_id"]
    away_team_name = selected_game["away_name"]
    home_team_name = selected_game["home_name"]
else:
    st.sidebar.warning("No games found for today.")
    active_game_id = None
@st.cache_data(ttl=300)
def get_starting_lineups(game_id):
    if not game_id:
        return [], []
        
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    try:
        response = requests.get(url)
        data = response.json()
        
        # The MLB API returns 'battingOrder' as a list of player IDs (e.g. [592450, 605141...])
        away_batters = data['teams']['away'].get('battingOrder', [])
        home_batters = data['teams']['home'].get('battingOrder', [])
        
        return away_batters, home_batters
    except Exception as e:
        return [], []
