import streamlit as st
import pandas as pd
from showdown_scraper_username import fetch_replays_by_username, process_replay_csv

st.title("🎮 Pokémon Showdown Username-Based Replay Fetcher")

# 📝 Username Input
username = st.text_input("Enter Pokémon Showdown Username:", placeholder="Wolfe Glick")

# 🎛️ Select Format Filter
format_option = st.radio("Select Format Filter:", ["All Matches", "Reg G", "Reg H"])

# 🔄 Fetch and Process Replays Button
if st.button("Fetch and Process Replays"):
    if username.strip() == "":
        st.error("❌ Please enter a username.")
    else:
        st.info(f"🔄 Fetching replays for **{username}**...")

        # Fetch replay data based on username (with pagination)
        fetched_replays = fetch_replays_by_username(username)

        if fetched_replays.empty:
            st.error("❌ No replays found for this username.")
        else:
            # Apply format filtering
            if format_option == "Reg G":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("Reg G", case=False, na=False)]
            elif format_option == "Reg H":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("Reg H", case=False, na=False)]

            if fetched_replays.empty:
                st.error(f"❌ No replays found for {username} in **{format_option}**.")
            else:
                # Save fetched replays for processing
                csv_file = "fetched_replays.csv"
                fetched_replays.to_csv(csv_file, index=False)
                st.success(f"✅ Successfully fetched {len(fetched_replays)} replays!")

                # 🔄 Process the replay data
                output_file = "processed_replays.csv"
                team_stats_file = "team_statistics.csv"

                st.info("🔄 Processing replays, please wait...")
                df, team_stats = process_replay_csv(username, csv_file, output_file, team_stats_file)

                if df.empty:
                    st.error("❌ No valid replay data could be processed.")
                else:
                    st.success(f"✅ Successfully processed {len(df)} replays!")

                    # 📊 Display the processed tables
                    st.subheader("📊 Processed Replay Data")
                    st.dataframe(df)

                    st.subheader("📈 Team Statistics")
                    st.dataframe(team_stats)

                    # 📥 Provide Download Buttons
                    st.download_button("📥 Download Processed Replays", data=df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
                    st.download_button("📥 Download Team Statistics", data=team_stats.to_csv(index=False), file_name="team_statistics.csv", mime="text/csv")
