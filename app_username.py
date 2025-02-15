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
        with st.spinner(f"Fetching replays for **{username}**..."):
            fetched_replays = fetch_replays_by_username(username)
        
        if fetched_replays.empty:
            st.error("❌ No replays found for this username.")
        else:
            # Apply format filtering
            if format_option == "Reg G":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("RegG", case=False, na=False)]
            elif format_option == "Reg H":
                fetched_replays = fetched_replays[fetched_replays['format'].str.contains("RegH", case=False, na=False)]

            # Store fetched replays
            st.session_state["fetched_replays"] = fetched_replays
            st.session_state["final_replays"] = fetched_replays  # Default before CSV upload
            fetched_count = len(fetched_replays)
            st.success(f"✅ Found **{fetched_count}** replays from Showdown!")

# CSV Upload Section (Optional)
st.subheader("📂 (Optional) Upload Additional Replay URLs")
uploaded_file = st.file_uploader("Upload a CSV containing additional replay URLs", type=["csv"])

if uploaded_file:
    uploaded_replays = pd.read_csv(uploaded_file)

    if "replay_url" in uploaded_replays.columns:
        search_replays_count = len(st.session_state["fetched_replays"])
        csv_replays_count = len(uploaded_replays)

        # Merge & find duplicates
        merged_replays = pd.concat([st.session_state["fetched_replays"], uploaded_replays], ignore_index=True)
        duplicates = merged_replays.duplicated(subset=['replay_url'], keep=False)
        num_duplicates = duplicates.sum()

        # Remove duplicates
        final_replays = merged_replays.drop_duplicates(subset=['replay_url'])
        st.session_state["final_replays"] = final_replays

        # Display detailed summary
        st.success(f"✅ After merging: {len(final_replays)} unique replays found! "
                   f"({search_replays_count} from Showdown, {csv_replays_count} from CSV). "
                   f"Removed {num_duplicates} duplicate(s).")
    else:
        st.error("❌ Uploaded CSV is missing 'replay_url' column.")

# Process Replays Button
if st.button("Process Replays") and "final_replays" in st.session_state:
    final_csv_file = "merged_replays.csv"
    st.session_state["final_replays"].to_csv(final_csv_file, index=False)

    output_file = "processed_replays.csv"
    team_stats_file = "team_statistics.csv"

    with st.spinner("Processing replay data..."):
        df, team_stats = process_replay_csv(username, final_csv_file, output_file, team_stats_file)

    if df is not None and not df.empty:
        st.subheader("📊 Processed Replay Data")
        st.dataframe(df)
        st.download_button("📥 Download Processed Replays", data=df.to_csv(index=False), file_name="processed_replays.csv", mime="text/csv")
    else:
        st.error("❌ Error processing replays. Please check CSV format.")
