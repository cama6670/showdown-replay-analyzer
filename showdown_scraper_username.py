import requests
import pandas as pd
import json
import time
import ast 

SHOWDOWN_API_URL = "https://replay.pokemonshowdown.com/search.json"

def fetch_replays_by_username(username):
    """Fetch replays for a given username using Showdown's API"""
    all_replays = []
    page = 1

    print(f"🔍 Searching for replays of '{username}'...")

    while True:
        params = {"user": username, "page": page}
        print(f"🌐 Fetching page {page} from {SHOWDOWN_API_URL} with params: {params}")

        response = requests.get(SHOWDOWN_API_URL, params=params)
        if response.status_code != 200:
            print(f"❌ Error fetching page {page}: {response.status_code}")
            break

        replays = response.json()
        if not replays:
            print("✅ Pagination Complete: No more replays found.")
            break

        for replay in replays:
            replay_id = replay["id"]
            replay_data_json = fetch_team_from_replay(replay_id, username)
            
            # Parse the JSON string back into a dictionary
            replay_data = json.loads(replay_data_json)
            
            # Store the team data, opponent name, and player slot in the replay object
            replay["teams"] = json.dumps(replay_data["teams"])  # Store teams as JSON string
            replay["opponent"] = replay_data["opponent"]  # Store opponent's name
            replay["player_slot"] = replay_data["player_slot"]  # Store which slot is the player

        all_replays.extend(replays)
        print(f"✅ Fetched {len(replays)} replays from page {page}")

        page += 1
        time.sleep(1)  # Avoid excessive requests

    if not all_replays:
        return pd.DataFrame()

    df = pd.DataFrame(all_replays)
    df.to_csv("fetched_replays.csv", index=False)
    print(f"✅ Saved {len(df)} replays to fetched_replays.csv")
    return df


def fetch_team_from_replay(replay_id, username):
    """Fetches a replay and extracts full teams + opponent's name + player's slot"""
    replay_url = f"https://replay.pokemonshowdown.com/{replay_id}.json"
    response = requests.get(replay_url)

    if response.status_code != 200:
        print(f"❌ Error fetching replay {replay_id}")
        return "{}", "Unknown", "p1"  # Default to p1 if not found

    data = response.json()
    replay_log = data.get("log", "")

    print(f"🔍 Debug: Raw Replay Log for {replay_id}")
    print(replay_log[:500])  # Print first 500 characters to check log structure

    teams, opponent, player_slot = extract_teams_and_opponent(replay_log, username)

    # Store the complete information in a dictionary
    result = {
        "teams": teams,
        "opponent": opponent,
        "player_slot": player_slot
    }

    return json.dumps(result)  # Return all data as a JSON string


def extract_teams_and_opponent(replay_log, username):
    """Extracts full teams and finds opponent's name and player's slot from the replay log."""
    teams = {"p1": [], "p2": []}
    opponent = "Unknown"
    player_slot = None  # Will store which slot (p1/p2) belongs to the input username
    lines = replay_log.split("\n")

    player_dict = {}  # Store player mapping (p1 -> player1, p2 -> player2)
    for line in lines:
        parts = line.split("|")
        if len(parts) < 4:  # Ensure there are at least 4 parts
            continue  # Skip this line if it's too short

        if parts[1] == "player":
            slot, player_name = parts[2], parts[3]
            player_dict[slot] = player_name
            if player_name.lower() == username.lower():
                player_slot = slot  # Found the slot for our player

        if parts[1] == "poke" and len(parts) >= 4:  # Check that parts[3] exists
            player, pokemon = parts[2], parts[3].split(",")[0]
            if player in teams:
                teams[player].append(pokemon)

    # Determine opponent based on who isn't the searched username
    for slot, player_name in player_dict.items():
        if player_name.lower() != username.lower():
            opponent = player_name
            break

    # If we couldn't determine the player's slot, default to p1
    if player_slot is None:
        player_slot = "p1"
        print(f"⚠ Warning: Could not determine player slot for {username} in replay, defaulting to p1")

    return teams, opponent, player_slot


def assign_sequential_team_ids(team_list):
    """Assigns a unique numeric ID to each unique set of six Pokémon."""
    team_id_map = {}
    current_id = 1  # Start numbering from 1

    def get_team_id(team):
        """Returns existing ID if team is found, otherwise assigns a new one."""
        nonlocal current_id
        sorted_team = tuple(sorted(team))  # Ensure consistent order
        if sorted_team not in team_id_map:
            team_id_map[sorted_team] = current_id
            current_id += 1
        return team_id_map[sorted_team]

    return get_team_id


def process_replay_csv(username, input_csv, output_csv, team_stats_csv):
    """Processes replay data and generates team statistics"""
    df_input = pd.read_csv(input_csv)

    if df_input.empty:
        print("❌ No data to process.")
        return pd.DataFrame(), pd.DataFrame()

    # ✅ Debug: Print existing columns
    print(f"🔍 Existing Columns in Dataframe: {df_input.columns.tolist()}")

    # Ensure 'teams', 'opponent', and 'player_slot' columns exist
    if "teams" not in df_input.columns:
        print("⚠ Warning: 'teams' column missing in CSV. Adding empty column.")
        df_input["teams"] = "{}"  # Default empty JSON

    if "opponent" not in df_input.columns:
        df_input["opponent"] = "Unknown"
        
    if "player_slot" not in df_input.columns:
        print("⚠ Warning: 'player_slot' column missing in CSV. Defaulting to 'p1'.")
        df_input["player_slot"] = "p1"  # Default to p1 if not found

    # Convert stored JSON strings into dictionaries
    df_input["teams"] = df_input["teams"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)

    # ✅ Ensure 'players' column is properly parsed
    if "players" in df_input.columns:
        df_input["players"] = df_input["players"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
        )

        # ✅ Construct Match Titles using API data
        df_input["Match Title"] = df_input.apply(
            lambda row: f"{row['format']}: {row['players'][0]} vs. {row['players'][1]}"
            if isinstance(row["players"], list) and len(row["players"]) == 2 
            else f"{row['format']}: ??? vs. ???",
            axis=1
        )
    else:
        df_input["Match Title"] = df_input['format'] + ": ??? vs. ???"  # Fallback

    # ✅ Debug: Check missing titles
    df_missing_titles = df_input[df_input["Match Title"].str.contains("\?\?\?")]
    if not df_missing_titles.empty:
        print(f"⚠ Warning: Some replays are missing Match Titles! Here are a few:")
        print(df_missing_titles[["format", "players"]].head(5))

    # Convert timestamp to readable format
    df_input['Match Date'] = pd.to_datetime(df_input['uploadtime'], unit='s').dt.strftime("%m-%d-%Y")

    # ✅ Ensure 'Replay URL' column exists
    if "Replay URL" not in df_input.columns:
        df_input['Replay URL'] = "https://replay.pokemonshowdown.com/" + df_input['id'].astype(str)

    # ✅ Use the player's team based on their slot (p1 or p2), not always p1
    # This is the key fix that was missing before
    def get_player_team(row):
        """Extract the team for the player based on their slot"""
        player_slot = row["player_slot"]
        teams = row["teams"]
        # Return the player's team or an empty list if not found
        return teams.get(player_slot, [])
    
    # Assign unique Team IDs based on the player's actual team
    get_team_id = assign_sequential_team_ids(df_input.apply(get_player_team, axis=1))
    
    # Store team as string using the player's team
    df_input["Team"] = df_input.apply(lambda row: ", ".join(get_player_team(row)), axis=1)
    
    # Assign Team ID using the player's team
    df_input["Team ID"] = df_input.apply(lambda row: get_team_id(get_player_team(row)), axis=1)

    # ✅ Check for missing columns before proceeding
    required_columns = ['Team ID', 'Match Title', 'Match Date', 'Replay URL', 'Team']
    missing_columns = [col for col in required_columns if col not in df_input.columns]

    if missing_columns:
        print(f"❌ Missing Columns: {missing_columns}")
        print(f"🔍 Existing Columns: {df_input.columns.tolist()}")
        raise KeyError(f"Missing columns in dataframe: {missing_columns}")

    # ✅ Processed Replay Data Table
    df_output = df_input[required_columns]
    df_output.to_csv(output_csv, index=False)

    # ✅ Team Statistics Table
    team_stats_df = df_input.groupby(["Team ID", "Team"]).agg(
        Times_Used=("Team ID", "count"),
        Last_Used=("Match Date", "max")  # Get most recent date team was used
    ).reset_index()

    team_stats_df.to_csv(team_stats_csv, index=False)

    return df_output, team_stats_df
