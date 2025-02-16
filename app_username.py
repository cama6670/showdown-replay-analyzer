import streamlit as st
import pandas as pd
from showdown_scraper_username import fetch_replays_by_username, process_replay_csv

st.title("🎮 Pokémon Showdown Username-Based Replay Fetcher")

# Username Input
username = st.text_input("Enter Pokémon Showdown Username:", "")

# Select Format Filter
format_option = st.radio("Select Format Filter:", ["All Matches", "Reg G", "Reg F"])

# Fetch and Process Replays Button
if st.button("Fetch Replays"):
    if username.strip() == "":
        st.error("❌ Please enter a username.")
    else:
        st.info(f"🔍 Fetching replays for **{username}**...")
        fetched_replays = fetch_replays_by_username(username)

        if fetched_replays.empty:
            st.error("❌ No replays found for this username.")
        else:
            # Apply format filtering
            if format_option == "Reg G":
                fetched_replays = fetched_replays[
                    fetched_replays['format'].str.contains("VGC 2024 Reg G|VGC 2025 Reg G", case=False, na=False)
                ]
            elif format_option == "Reg F":
                fetched_replays = fetched_replays[
                    fetched_replays['format'].str.contains("VGC 2024 Reg F", case=False, na=False)
                ]

            # Save fetched replays for processing
            csv_file = "fetched_replays.csv"
            fetched_replays.to_csv(csv_file, index=False)

            st.success(f"✅ Found {len(fetched_replays)} replays for **{username}**.")

            # Optional CSV Upload
            st.subheader("📂 (Optional) Upload Additional Replay URLs")
            uploaded_file = st.file_uploader("Upload a CSV containing additional replay URLs", type=["csv"])
            if uploaded_file:
                csv_data = pd.read_csv(uploaded_file)
                if "id" in csv_data.columns:
                    existing_ids = set(fetched_replays["id"])
                    new_data = csv_data[~csv_data["id"].isin(existing_ids)]
                    num_new = len(new_data)
                    num_removed = len(csv_data) - num_new
                    fetched_replays = pd.concat([fetched_replays, new_data], ignore_index=True)

                    st.success(
                        f"✅ After merging: {len(fetched_replays)} unique replays found! "
                        f"({len(fetched_replays)-num_new} from Showdown, {num_new} from CSV). Removed {num_removed} duplicate(s)."
                    )

            # Process the replay data
            output_file = "processed_replays.csv"
            team_stats_file = "team_statistics.csv"
            df, team_stats = process_replay_csv(username, csv_file, output_file, team_stats_file)

            # Display the processed tables
            st.subheader("📊 Processed Replay Data")
            st.dataframe(df)

            st.subheader("📈 Team Statistics")
            if team_stats is not None and not team_stats.empty:
                st.dataframe(team_stats)
            else:
                st.warning("⚠ No team statistics were generated.")

            # Provide download buttons
            st.download_button("📥 Download Processed Replays", data=df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
            st.download_button("📥 Download Team Statistics", data=team_stats.to_csv(index=False), file_name="team_statistics.csv", mime="text/csv")
