import requests
import json
import pandas as pd
from datetime import datetime

def format_upload_time(timestamp):
    """Convert Unix timestamp to MM-DD-YYYY format."""
    if isinstance(timestamp, int):
        return datetime.utcfromtimestamp(timestamp).strftime('%m-%d-%Y')
    return "Unknown Date"

def fetch_replays_by_username(username):
    """Fetch all replay URLs for a given username using Pokémon Showdown API."""
    username = username.strip()  # Remove spaces
    base_url = f"https://replay.pokemonshowdown.com/search.json?user={username}"
    all_replays = []
    page = 1

    while True:
        full_url = f"{base_url}&page={page}"
        print(f"🔍 Fetching: {full_url}")  # Debugging print
        
        response = requests.get(full_url)
        if response.status_code != 200:
            print(f"❌ API request failed with status {response.status_code}")
            break
        
        try:
            data = response.json()
            print(f"✅ API Response (Page {page}): {json.dumps(data, indent=2)[:500]}")  # Print first 500 characters for debugging
        except json.JSONDecodeError:
            print("❌ Failed to parse JSON response from Showdown API")
            break

        if not data or "replays" not in data or len(data["replays"]) == 0:
            print(f"✅ No more replays found after page {page}. Stopping search.")
            break

        all_replays.extend(data["replays"])
        print(f"✅ Fetched {len(data['replays'])} replays from page {page}")

        if len(data["replays"]) < 50:
            break  # Stop if less than 50 replays found (end of list)

        page += 1  # Move to next page

    if not all_replays:
        print(f"❌ No replays found for username: {username}. Check if it's correct.")
        return pd.DataFrame()

    # Convert to DataFrame
    replay_df = pd.DataFrame(all_replays)
    replay_df['uploadtime'] = replay_df['uploadtime'].apply(format_upload_time)

    print(f"✅ Total replays fetched: {len(replay_df)}")
    return replay_df

def process_replay_csv(username, csv_file, output_file="processed_replays.csv", team_stats_file="team_statistics.csv"):
    """Process fetched replay URLs, extract data, and generate statistics."""
    print(f"📂 Loading CSV: {csv_file}")

    df_input = pd.read_csv(csv_file)

    if "replay_url" not in df_input.columns:
        print("❌ CSV file is missing 'replay_url' column!")
        return pd.DataFrame(), pd.DataFrame()

    replay_urls = df_input["replay_url"].dropna().tolist()
    print(f"🔍 Found {len(replay_urls)} replay URLs for processing.")

    existing_teams = {}
    results = []
    for url in replay_urls:
        data = get_showdown_replay_data(username, url, existing_teams)
        if data:
            results.append(data)

    if not results:
        print("❌ No valid replay data found!")
        return pd.DataFrame(), pd.DataFrame()

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)
    print(f"✅ Processed replay data saved to {output_file}")

    # Generate team statistics based on unique Team ID
    df_output['Match Date'] = pd.to_datetime(df_output['Match Date'], format="%m-%d-%Y", errors='coerce')
    df_output['Last Used'] = df_output.groupby('Team ID')['Match Date'].transform('max')

    team_stats = df_output.groupby(['Team ID', 'Team', 'Exact User Name Match']).agg(
        Count=('Match Title', 'count'),
        Last_Used=('Last Used', 'max')
    ).reset_index()

    team_stats.to_csv(team_stats_file, index=False)
    print(f"✅ Team stats saved to {team_stats_file}")

    return df_output, team_stats
