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
            break
        
        try:
            data = response.json()
            print(f"✅ API Response (Page {page}): {json.dumps(data, indent=2)[:500]}")  # Show first 500 chars for debugging
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
