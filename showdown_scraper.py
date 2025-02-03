import requests
import json
from datetime import datetime
import pandas as pd

def format_upload_time(timestamp):
    """Convert Unix timestamp to human-readable format."""
    if isinstance(timestamp, int):
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "Unknown Date"

def get_showdown_replay_data(username, replay_url):
    if replay_url.endswith('/'):
        replay_url = replay_url[:-1]
    json_url = replay_url + ".json"

    response = requests.get(json_url)
    if response.status_code != 200:
        return None

    try:
        replay_data = response.json()
    except json.JSONDecodeError:
        return None

    match_format = replay_data.get('format', 'Unknown Format')
    players = replay_data.get("players", [])
    match_title = f"{match_format}: {' vs. '.join(players)}" if len(players) >= 2 else "Unknown Title"

    upload_time = replay_data.get('uploadtime', None)
    match_date = format_upload_time(upload_time)  # Convert timestamp to readable date

    # Determine player slot and exact match
    exact_user_match = "Yes" if username in players else "No"

    return {
        'Match Title': match_title,
        'Match Date': match_date,
        'Replay URL': replay_url,
        'Exact User Name Match': exact_user_match
    }

def process_replay_csv(username, csv_file, output_file="processed_replays.csv", team_stats_file="team_statistics.csv"):
    print(f"📂 Loading CSV: {csv_file}")  # Debugging log

    df_input = pd.read_csv(csv_file)

    if "replay_url" not in df_input.columns:
        print("❌ CSV file is missing 'replay_url' column!")
        return None, None

    replay_urls = df_input["replay_url"].dropna().tolist()
    print(f"🔍 Found {len(replay_urls)} replay URLs for processing.")  # Debug log

    results = [get_showdown_replay_data(username, url) for url in replay_urls if get_showdown_replay_data(username, url)]

    if not results:
        print("❌ No valid replay data found!")
        return None, None

    df_output = pd.DataFrame(results)
    df_output.to_csv(output_file, index=False)
    print(f"✅ Processed replay data saved to {output_file}")

    return df_output, None  # Team stats removed for simplicity
