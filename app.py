import streamlit as st
import pandas as pd
import requests
import time
from showdown_scraper import process_replay_csv

st.title("🎮 Pokémon Showdown Replay Analyzer")

# User Input for Username
username = st.text_input("Enter Pokémon Showdown Username:", "GTheDon")

# 🎯 Match Format Filtering
match_format = st.radio("Filter by Format:", ["All", "Reg G", "Reg H"])

def fetch_replays(username):
    """Fetch all replay URLs from Pokémon Showdown API by paginating results safely."""
    base_url = f"https://replay.pokemonshowdown.com/search.json?user={username}"
    all_replays = []
    offset = 0
    max_retries = 3  # Number of retries if Showdown API fails
    max_pages = 20   # Hard limit (20 * 50 = 1000 replays max)

    while True:
        url = f"{base_url}&offset={offset}"
        response = requests.get(url)

        if response.status_code != 200:
            max_retries -= 1
            if max_retries == 0:
                break  # Stop if too many failures
            time.sleep(2)  # Wait before retrying
            continue

        replays = response.json()
        if not replays:
            break  # Stop if no more replays are returned

        all_replays.extend(replays)
        offset += 50  # Move to the next set of 50 replays

        if offset >= max_pages * 50:  # Stop after max_pages (1000 replays)
            break

    return all_replays

def filter_replays(replays, match_format):
    """Apply filtering AFTER fetching all replays."""
    if match_format == "All":
        return replays
    return [r for r in replays if match_format.lower().replace(" ", "") in r["format"].lower()]

if st.button("Fetch Replays for Username"):
    with st.spinner("Fetching replays..."):
        replays = fetch_replays(username)
        if replays:
            # Apply filtering **after** fetching all replays
            filtered_replays = filter_replays(replays, match_format)
            replay_df = pd.DataFrame(filtered_replays)

            # Save filtered replays to CSV for processing
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
