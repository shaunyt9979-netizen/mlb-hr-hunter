import streamlit as st
import pandas as pd
from pybaseball import statcast_batter_expected_stats

st.set_page_config(layout="wide")
st.title("⚾ Data Scout")
st.write("Printing raw Statcast data to find the exact column names...")

@st.cache_data
def load_raw_data():
    # Pull the live 2026 Statcast expected stats
    stats = statcast_batter_expected_stats(2026, minPA=100)
    return stats

# Load the raw data
df = load_raw_data()

# 1. Print a list of every single column name at the top of the app
st.write("### 📋 Available Column Headers:")
st.write(df.columns.tolist())

# 2. Print the raw, unformatted table
st.write("### 📊 Raw Data Table:")
st.dataframe(df, use_container_width=True)
