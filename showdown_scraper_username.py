import requests
import pandas as pd
import time

def fetch_replays_by_username(username):
    """Fetch all available replays for a given Pokémon Showdown username using pagination."""
    all_replays = []
    page = 1  # Start from page 1
    per_page = 50  # Showdown API defaults to 50 per page

    while True:
        url = f"https://replay.pokemonshowdown.com/search.json?user={username}&page={page}"
        print(f"Fetching from: {url}")  # DEBUG: See the API request URL

        try:
            response = requests.get(url)
            response.raise_for_status()
            replays = response.json()

            if not replays:
                break  # Stop if there are no more replays to fetch

            all_replays.extend(replays)
            print(f"✅ Fetched {len(replays)} replays from page {page}")

            # If the number of replays fetched is less than the per_page limit, we are at the last page
            if len(replays) < per_page:
                break  

            page += 1  # Go to the next page
            time.sleep(1)  # Avoid hitting rate limits

        except requests.exceptions.RequestException as e:
            print(f"❌ API Request Failed: {e}")  # DEBUG
            break

    if not all_replays:
        return pd.DataFrame()  # Return an empty DataFrame if no replays found

    # Convert to DataFrame
    replay_data = pd.DataFrame(all_replays)
    return replay_data
