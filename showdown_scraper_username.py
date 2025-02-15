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
    """Fetch all replay URLs for a given username using the Pokémon Showdown API."""
    base_url = f"https://replay.pokemonshowdown.com/search.json?user={username}"
    all_replays = []

    page = 1
    while True:
        response = requests.get(f"{base_url}&page={page}")
        if response.status_code != 200:
            break
        
        data = response.json()
        if not data or "replays" not in data:
            break

        all_replays.extend(data["replays"])
        if len(data["replays"]) < 50:
            break  # Stop if less than 50 replays are found on the current page

        page += 1  # Move to next page

    if not all_replays:
        return pd.DataFrame()

    # Convert to DataFrame
    replay_df = pd.DataFrame(all_replays)
    replay_df['uploadtime'] = replay_df['uploadtime'].apply(format_upload_time)
    return replay_df

def generate_team_id(team, existing_teams):
    """Assign a simple numerical ID for unique teams."""
    if not team:
        return "Unknown_Team"

    sorted_team = ",".join(sorted(team))
    if sorted_team in existing_teams:
        return existing_teams[sorted_team]
    else:
        new_id = len(existing_teams) + 1
        existing_teams[sorted_team] = new_id
        return new_id

def process_replay_csv(username, csv_file, output_file="processed_replays.csv", team_stats_file="team_statistics.csv"):
    """Process fetched replay URLs, extract data, and generate statistics."""
    df_input = pd.read_csv(csv_file)

    if "replay_url" not in df_input.columns:
        print("❌ CSV file is missing 'replay_url' column!")
        return pd.DataFrame(), pd.DataFrame()

    replay_urls = df_input["replay_url"].dropna().tolist()
    existing_teams = {}

    results = []
    for url in replay_urls:
        data = get_showdown_replay_data(username, url, existing_teams)
        if data:
            results.append(data)

    if not results:
        return pd.DataFrame(), pd.DataFrame()

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)

    df_output['Match Date'] = pd.to_datetime(df_output['Match Date'], format="%m-%d-%Y", errors='coerce')
    df_output['Last Used'] = df_output.groupby('Team ID')['Match Date'].transform('max')

    team_stats = df_output.groupby(['Team ID', 'Team']).agg(
        Count=('Match Title', 'count'),
        Last_Used=('Last Used', 'max')
    ).reset_index()

    team_stats.to_csv(team_stats_file, index=False)
    return df_output, team_stats
