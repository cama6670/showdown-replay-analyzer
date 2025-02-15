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

# Step 1: Fetch Replays from Showdown
if st.button("Fetch Replays"):
    if username.strip() == "":
        st.error("❌ Please enter a username.")
    else:
        with st.status(f"🔄 Fetching replays for **{username}**...", expanded=True):
            fetched_replays = fetch_replays_by_username(username)

        if fetched_replays.empty:
            st.error("❌ No replays found for this username.")
        else:
            # Apply format filtering
            if format_option == "Reg G":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("Reg G", case=False, na=False)]
            elif format_option == "Reg H":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("Reg H", case=False, na=False)]

            # Display number of replays found
            st.success(f"✅ Found {len(fetched_replays)} replays for {username}.")

            # Save fetched replays for processing
            fetched_csv_file = "fetched_replays.csv"
            fetched_replays.to_csv(fetched_csv_file, index=False)

            # Step 2: Ask for CSV Upload (Optional)
            st.subheader("📂 (Optional) Upload Additional Replay URLs")
            uploaded_file = st.file_uploader("Upload a CSV containing additional replay URLs", type=["csv"])

            if uploaded_file:
                uploaded_replays = pd.read_csv(uploaded_file)
                if 'replay_url' not in uploaded_replays.columns:
                    st.error("❌ CSV must contain a 'replay_url' column.")
                else:
                    # Remove duplicates
                    all_replays = pd.concat([fetched_replays, uploaded_replays], ignore_index=True).drop_duplicates(subset=['replay_url'])
                    st.success(f"✅ After removing duplicates, {len(all_replays)} unique replays remain.")

                    # Save combined replays for processing
                    final_csv_file = "final_replays.csv"
                    all_replays.to_csv(final_csv_file, index=False)
            else:
                all_replays = fetched_replays
                final_csv_file = fetched_csv_file

            # Step 3: Process All Replays
            if st.button("Process Replays"):
                output_file = "processed_replays.csv"
                team_stats_file = "team_statistics.csv"

                with st.status("🔄 Processing replays...", expanded=True):
                    df, team_stats = process_replay_csv(username, final_csv_file, output_file, team_stats_file)

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
