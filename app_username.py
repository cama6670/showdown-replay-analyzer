import streamlit as st
import pandas as pd
import re
from showdown_scraper_username import fetch_replays_by_username, process_replay_csv, fetch_team_from_replay

st.title("🎮 Pokémon Showdown Username-Based Replay Fetcher")

# Username Input
username = st.text_input("Enter Pokémon Showdown Username:", "")

# Select Format Filter
format_option = st.radio("Select Format Filter:", ["All Matches", "Reg G", "Reg F"])

# Function to extract replay ID from URL
def extract_replay_id(url):
    # Extract the replay ID from a URL like https://replay.pokemonshowdown.com/gen9vgc2024regf-2016073916
    match = re.search(r'pokemonshowdown\.com/([^/]+)$', url)
    if match:
        return match.group(1)
    return None

# Fetch and Process Replays Button
if st.button("Fetch Replays"):
    if username.strip() == "":
        st.error("❌ Please enter a username.")
    else:
        st.info(f"🔍 Fetching replays for **{username}**...")
        fetched_replays = fetch_replays_by_username(username)

        if fetched_replays.empty:
            st.warning("⚠️ No replays found through the Showdown API. You can still upload a CSV with replay URLs.")
            fetched_replays = pd.DataFrame(columns=['id', 'format', 'uploadtime', 'teams', 'opponent', 'player_slot'])
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

            st.success(f"✅ Found {len(fetched_replays)} replays for **{username}** via the Showdown API.")

        # Optional CSV Upload - Now with support for 'replay_url' column
        st.subheader("📂 (Optional) Upload Additional Replay URLs")
        uploaded_file = st.file_uploader("Upload a CSV containing additional replay URLs", type=["csv"])
        
        if uploaded_file:
            csv_data = pd.read_csv(uploaded_file)
            
            # Check if the CSV has the expected format
            if "replay_url" in csv_data.columns:
                # Extract replay IDs from URLs
                csv_data['id'] = csv_data['replay_url'].apply(extract_replay_id)
                
                # Remove rows with invalid URLs
                invalid_urls = csv_data[csv_data['id'].isna()]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ {len(invalid_urls)} invalid URLs found in CSV and ignored.")
                
                csv_data = csv_data.dropna(subset=['id'])
                
                # Check which replays are not already fetched
                existing_ids = set(fetched_replays["id"]) if "id" in fetched_replays.columns else set()
                new_replay_ids = [id for id in csv_data['id'] if id not in existing_ids]
                
                st.info(f"🔍 Found {len(new_replay_ids)} new replays in CSV to process.")
                
                # For each new replay, fetch details
                new_replays_data = []
                for idx, replay_id in enumerate(new_replay_ids):
                    st.text(f"Processing additional replay {idx+1}/{len(new_replay_ids)}: {replay_id}")
                    try:
                        # We need to fetch each replay's data
                        replay_data_json = fetch_team_from_replay(replay_id, username)
                        import json
                        replay_data = json.loads(replay_data_json)
                        
                        # Create a record similar to what we get from the API
                        new_replay = {
                            "id": replay_id,
                            "format": "unknown",  # We can't easily determine this
                            "uploadtime": pd.Timestamp.now().timestamp(),  # Use current time as fallback
                            "teams": json.dumps(replay_data["teams"]),
                            "opponent": replay_data["opponent"],
                            "player_slot": replay_data["player_slot"],
                            # Add any other fields needed
                        }
                        new_replays_data.append(new_replay)
                    except Exception as e:
                        st.error(f"❌ Error processing replay {replay_id}: {str(e)}")
                
                # Add the new replays to our dataset
                if new_replays_data:
                    new_replays_df = pd.DataFrame(new_replays_data)
                    fetched_replays = pd.concat([fetched_replays, new_replays_df], ignore_index=True)
                
                st.success(
                    f"✅ After merging: {len(fetched_replays)} unique replays found! "
                    f"({len(fetched_replays) - len(new_replays_data)} from Showdown API, "
                    f"{len(new_replays_data)} from CSV)."
                )
            else:
                st.error("❌ CSV format not recognized. Expected a column named 'replay_url'.")

        # Save fetched replays for processing
        if not fetched_replays.empty:
            csv_file = "fetched_replays.csv"
            fetched_replays.to_csv(csv_file, index=False)

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
        else:
            st.error("❌ No replays to process after filtering and CSV upload.")
