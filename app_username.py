import streamlit as st
import pandas as pd
from showdown_scraper_username import fetch_replays_by_username, process_replay_csv

# Streamlit UI
st.set_page_config(page_title="Pokémon Showdown Username-Based Replay Fetcher", page_icon="🎮")

st.title("🎮 Pokémon Showdown Username-Based Replay Fetcher")

# Username Input Field (with Placeholder)
username = st.text_input("Enter Pokémon Showdown Username:", placeholder="Wolfe Glick")

# Select Format Filter
format_option = st.radio("Select Format Filter:", ["All Matches", "Reg G", "Reg H"])

# Fetch and Process Replays Button
if st.button("Fetch and Process Replays"):
    if username.strip() == "":
        st.error("❌ Please enter a username.")
    else:
        with st.status(f"🔄 Fetching replays for **{username}**...", expanded=True):
            # Fetch replay data based on username
            fetched_replays = fetch_replays_by_username(username)

        if fetched_replays.empty:
            st.error("❌ No replays found for this username.")
        else:
            # Apply format filtering
            if format_option == "Reg G":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("Reg G", case=False, na=False)]
            elif format_option == "Reg H":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("Reg H", case=False, na=False)]

            # Save fetched replays for processing
            csv_file = "fetched_replays.csv"
            fetched_replays.to_csv(csv_file, index=False)

            # Process the replay data
            output_file = "processed_replays.csv"
            team_stats_file = "team_statistics.csv"

            with st.status("🔄 Processing replays...", expanded=True):
                df, team_stats = process_replay_csv(username, csv_file, output_file, team_stats_file)

            if df.empty:
                st.error("❌ No valid replay data found after processing.")
            else:
                # Display processed tables
                st.subheader("📊 Processed Replay Data")
                st.dataframe(df)

                st.subheader("📈 Team Statistics")
                st.dataframe(team_stats)

                # Provide download buttons
                st.download_button("📥 Download Processed Replays", data=df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
                st.download_button("📥 Download Team Statistics", data=team_stats.to_csv(index=False), file_name="team_statistics.csv", mime="text/csv")
                
                st.success(f"✅ Successfully processed {len(df)} replays!")
