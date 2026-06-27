import streamlit as st
import pandas as pd

# Set wide layout like Kasper's app
st.set_page_config(layout="wide")

st.title("⚾ Home Run Hunter Dashboard")
st.write("Data pipeline test...")

# Mocking up Kasper's hitter look
data = {
    'Hitter': ['TJ Rumfield', 'Edouard Julien', 'Spencer Horwitz'],
    'Team': ['COL', 'COL', 'PIT'],
    'Matchup Score': [63.028, 62.838, 62.815],
    'Test Score': [61.496, 61.464, 60.606],
    'xwOBA': [0.328, 0.337, 0.333],
    'SweetSpot%': [41.9, 40.3, 37.9],
    'LA (Launch Angle)': [19.1, 14.2, 20.2]
}
df = pd.DataFrame(data)

# Apply the green-to-red color heatmap
styled_df = df.style.background_gradient(cmap='RdYlGn', subset=['Matchup Score', 'Test Score', 'xwOBA', 'SweetSpot%'])

# Render the table nicely
st.dataframe(styled_df, use_container_width=True)
