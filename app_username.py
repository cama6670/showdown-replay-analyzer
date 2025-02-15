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

    print(f"🔍 Checking username: {username}")

    while True:
        full_url = f"{base_url}&page={page}"
        print(f"🔍 Fetching URL: {full_url}")  # Debugging print

        response = requests.get(full_url)
        if response.status_code != 200:
            print(f"❌ API request failed! Status Code: {response.status_code}")
            return pd.DataFrame()  # Return empty DataFrame

        try:
            data = response.json()
            print(f"✅ API Response (Page {page}): {json.dumps(data, indent=2)[:500]}")  # Show first 500 chars for debugging
        except json.JSONDecodeError:
            print("❌ Failed to parse JSON response from Showdown API")
            return pd.DataFrame()

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

    if "replay_url" not in df_input.columns and "id" not in df_input.columns:
        print("❌ CSV file is missing both 'replay_url' and 'id' columns!")
        return pd.DataFrame(), pd.DataFrame()

    # Construct replay URLs if they are missing
    if "replay_url" not in df_input.columns:
        df_input["replay_url"] = "https://replay.pokemonshowdown.com/" + df_input["id"]

    replay_urls = df_input["replay_url"].dropna().tolist()
    print(f"🔍 Found {len(replay_urls)} replay URLs for processing.")

    results = []
    for url in replay_urls:
        data = get_showdown_replay_data(username, url)
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

def get_showdown_replay_data(username, replay_url):
    """Fetch and parse replay data from Pokémon Showdown replay URL."""
    print(f"🔄 Fetching replay data: {replay_url}")

    response = requests.get(replay_url + ".json")
    if response.status_code != 200:
        print(f"❌ Failed to fetch replay JSON! Status Code: {response.status_code}")
        return None

    try:
        data = response.json()
    except json.JSONDecodeError:
        print("❌ JSON decode error while parsing replay data.")
        return None

    if "id" not in data or "format" not in data or "players" not in data:
        print("❌ Invalid replay JSON structure.")
        return None

    match_title = f"{data['format']}: {data['players'][0]} vs. {data['players'][1]}"
    match_date = format_upload_time(data.get("uploadtime", 0))

    # Determine if the username is an exact match for one of the players
    exact_match = "Yes" if username.lower() in [p.lower() for p in data["players"]] else "No"

    # Extract the Pokémon team (if available)
    teams = []
    for log in data.get("log", "").split("\n"):
        if "|poke|" in log:
            parts = log.split("|")
            if len(parts) > 3:
                teams.append(parts[3].split(",")[0])

    unique_team = sorted(set(teams))  # Ensure unique Pokémon per team

    return {
        "Match Title": match_title,
        "Match Date": match_date,
        "Replay URL": replay_url,
        "Exact User Name Match": exact_match,
        "Team": ", ".join(unique_team) if unique_team else "Unknown"
    }
