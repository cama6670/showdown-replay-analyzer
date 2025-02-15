import streamlit as st
import pandas as pd
from showdown_scraper_username import fetch_replays_by_username, process_replay_csv

st.title("🎮 Pokémon Showdown Username-Based Replay Fetcher")

# Username Input
username = st.text_input("Enter Pokémon Showdown Username:", "")

# Select Format Filter
format_option = st.radio("Select Format Filter:", ["All Matches", "Reg G", "Reg H"])

# Fetch Replays Button
if st.button("Fetch Replays"):
    if not username.strip():
        st.error("❌ Please enter a username.")
    else:
        st.info(f"🔄 Fetching replays for **{username}**...")
        fetched_replays = fetch_replays_by_username(username)

        if fetched_replays.empty:
            st.error("❌ No replays found for this username.")
        else:
            if format_option == "Reg G":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("RegG", case=False, na=False)]
            elif format_option == "Reg H":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("RegH", case=False, na=False)]

            fetched_replays["Replay URL"] = "https://replay.pokemonshowdown.com/" + fetched_replays["id"]
            fetched_replays = fetched_replays[["Replay URL"]]

            # Save fetched replays
            fetched_replays.to_csv("fetched_replays.csv", index=False)
            st.success(f"✅ Fetched {len(fetched_replays)} replays!")

            # Optional CSV Upload
            st.subheader("📂 (Optional) Upload Additional Replay URLs")
            uploaded_file = st.file_uploader("Upload a CSV containing additional replay URLs", type=["csv"])

            if uploaded_file is not None:
                uploaded_replays = pd.read_csv(uploaded_file)

                if "Replay URL" not in uploaded_replays.columns:
                    st.error("❌ The uploaded CSV must contain a 'Replay URL' column.")
                else:
                    combined_replays = pd.concat([fetched_replays, uploaded_replays]).drop_duplicates()
                    duplicates_removed = len(fetched_replays) + len(uploaded_replays) - len(combined_replays)
                    unique_from_csv = len(uploaded_replays) - duplicates_removed
                    st.success(f"✅ After merging: {len(combined_replays)} unique replays found! ({len(fetched_replays)} from Showdown, {unique_from_csv} from CSV). Removed {duplicates_removed} duplicate(s).")
                    
                    # Save merged data
                    combined_replays.to_csv("final_replays.csv", index=False)

            # Process Replays Button
            if st.button("Process Replays"):
                st.info("🔄 Processing replays...")
                df, team_stats = process_replay_csv(username, "final_replays.csv", "processed_replays.csv", "team_statistics.csv")

                st.subheader("📊 Processed Replay Data")
                st.dataframe(df)

                st.subheader("📈 Team Statistics")
                st.dataframe(team_stats)

                st.download_button("📥 Download Processed Replays", df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
                st.download_button("📥 Download Team Statistics", team_stats.to_csv(index=False), file_name="team_statistics.csv", mime="text/csv")
