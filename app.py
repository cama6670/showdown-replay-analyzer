import streamlit as st
import pandas as pd
import requests
from showdown_scraper import process_replay_csv

st.title("🎮 Pokémon Showdown Replay Analyzer")

# User Input for Username
username = st.text_input("Enter Pokémon Showdown Username:", "GTheDon")

# 🎯 Match Format Filtering
match_format = st.radio("Filter by Format:", ["All", "Reg G", "Reg H"])

def fetch_replays(username):
    """Fetch replay URLs from Pokémon Showdown API"""
    url = f"https://replay.pokemonshowdown.com/search.json?user={username}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def filter_replays(replays, match_format):
    """Filter replays by Reg G, Reg H, or All"""
    if match_format == "All":
        return replays
    return [r for r in replays if match_format.lower().replace(" ", "") in r["format"].lower()]

if st.button("Fetch Replays for Username"):
    with st.spinner("Fetching replays..."):
        replays = fetch_replays(username)
        if replays:
            filtered_replays = filter_replays(replays, match_format)
            replay_df = pd.DataFrame(filtered_replays)

            # Save to CSV for processing
            replay_csv = "fetched_replays.csv"
            replay_df.to_csv(replay_csv, index=False)

            st.subheader(f"🔗 Found {len(filtered_replays)} Replays")
            st.dataframe(replay_df)

            # 📤 Option to Process Downloaded CSV
            if st.button("Process These Replays"):
                output_file = "processed_replays.csv"
                team_stats_file = "team_statistics.csv"
                with st.spinner("🔄 Processing Replay Data..."):
                    df, team_stats = process_replay_csv(username, replay_csv, output_file, team_stats_file)

                st.subheader("📊 Processed Replay Data")
                st.dataframe(df)

                st.subheader("📈 Team Statistics")
                st.dataframe(team_stats)

                st.download_button("📥 Download Processed Replays", data=df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
                st.download_button("📥 Download Team Statistics", data=team_stats.to_csv(index=False), file_name="team_statistics.csv", mime="text/csv")
        else:
            st.error("No replays found or an error occurred.")
