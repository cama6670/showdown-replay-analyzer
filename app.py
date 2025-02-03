import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from showdown_scraper import process_replay_csv

st.title("🎮 Pokémon Showdown Replay Analyzer")

# User Input for Username
username = st.text_input("Enter Pokémon Showdown Username:", "GTheDon")

# 🎯 Match Format Filtering
match_format = st.radio("Filter by Format:", ["All", "Reg G", "Reg H"])

# Variable to store replay file
replay_csv = "fetched_replays.csv"

def fetch_replays(username):
    """Fetch all replay URLs using the pagination method from PsReplayDownloader."""
    base_url = f"https://replay.pokemonshowdown.com/search.json?user={username}"
    all_replays = []
    seen_ids = set()  # Track unique replay IDs
    page = 1  # Start from page 1

    while True:
        url = f"{base_url}&page={page}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"❌ API Error: Failed to fetch data on page {page}.")
            break  # Stop if an error occurs

        replays = response.json()
        print(f"✅ Fetched {len(replays)} replays from page {page}")

        if not replays:
            break  # Stop if no more replays are returned

        # Remove duplicates by checking the 'id' field
        for replay in replays[:-1]:  # Ignore the last item to prevent duplication
            if replay["id"] not in seen_ids:
                all_replays.append(replay)
                seen_ids.add(replay["id"])

        if len(replays) < 51:  # If fewer than 51 results, stop (last page reached)
            print(f"✅ Pagination Complete: Fetched {len(all_replays)} total replays.")
            break

        page += 1  # Move to the next page

    return all_replays

def filter_replays(replays, match_format):
    """Apply filtering AFTER fetching all replays."""
    if match_format == "All":
        return replays
    return [r for r in replays if match_format in r["format"]]

def convert_upload_time(timestamp):
    """Convert Unix timestamp to human-readable format."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp, int) else "Unknown Date"

if st.button("Fetch Replays for Username"):
    print("🔄 Button Clicked: Fetching replays...")  # Debugging log

    with st.spinner("Fetching replays..."):
        replays = fetch_replays(username)
        if replays:
            # Apply filtering **after** fetching all replays
            filtered_replays = filter_replays(replays, match_format)
            replay_df = pd.DataFrame(filtered_replays)

            # Convert upload time to readable format
            replay_df["uploadtime"] = replay_df["uploadtime"].apply(convert_upload_time)

            # Save filtered replays to CSV for processing
            replay_df.to_csv(replay_csv, index=False)

            st.subheader(f"🔗 Found {len(filtered_replays)} Replays")
            st.dataframe(replay_df)
        else:
            st.error("No replays found or an error occurred.")

# 🚀 FIX: Move "Process These Replays" Button Outside the Fetch Condition
if st.button("Process These Replays"):
    print("🔄 Button Clicked: Processing replays...")  # Debug log
    output_file = "processed_replays.csv"
    team_stats_file = "team_statistics.csv"

    with st.spinner("🔄 Processing Replay Data..."):
        try:
            df, team_stats = process_replay_csv(username, replay_csv, output_file, team_stats_file)

            if df is None or df.empty:
                st.error("⚠️ No valid replay data was processed.")
                print("❌ No valid replay data found in CSV.")
            else:
                print(f"✅ Successfully processed {len(df)} replays!")  # Debugging output
                print(f"✅ Generated {len(team_stats)} team stats!")

                st.subheader("📊 Processed Replay Data")
                st.dataframe(df)

                st.subheader("📈 Team Statistics")
                st.dataframe(team_stats)

                st.download_button("📥 Download Processed Replays", data=df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
                st.download_button("📥 Download Team Statistics", data=team_stats.to_csv(index=False), file_name="team_statistics.csv")

        except Exception as e:
            print(f"❌ Error Processing Replays: {e}")  # Debug error
            st.error(f"An error occurred while processing replays: {e}")
