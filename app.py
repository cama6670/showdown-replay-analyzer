import streamlit as st
import pandas as pd
from showdown_scraper import process_replay_csv

st.title("🎮 Pokémon Showdown Replay Analyzer")

# Username Input for Player Selection
username = st.text_input("Enter the Pokémon Showdown Username to Extract Team From:")

# Upload CSV File
uploaded_file = st.file_uploader("Upload CSV with Replay URLs", type=["csv"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    csv_file = "uploaded_replays.csv"
    with open(csv_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Process the replay data
    output_file = "processed_replays.csv"
    team_stats_file = "team_statistics.csv"

    df, team_stats = process_replay_csv(username, csv_file, output_file, team_stats_file)

    # Display the processed tables
    st.subheader("📊 Processed Replay Data")
    st.dataframe(df)

    st.subheader("📈 Team Statistics")
    st.dataframe(team_stats)

    # Provide download buttons
    st.download_button("📥 Download Processed Replays", data=df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
    st.download_button("📥 Download Team Statistics", data=team_stats.to_csv(index=False), file_name="team_statistics.csv", mime="text/csv")
