import json
import os    
from config import INJURIES_DIR
from date_helper import is_data_up_to_date
from fetchers import fetch_players_for_fixture
from config import PLAYERS_DIR

def get_player_data(fixture_id):
    filename = os.path.join(PLAYERS_DIR, f'players_data_{fixture_id}.json')

    if is_data_up_to_date(filename):
        with open(filename, 'r') as f:
            players = json.load(f)
    else:
        print(f"Fetching new player data for fixture {fixture_id}...")
        players = fetch_players_for_fixture(fixture_id)
        with open(filename, 'w') as f:
            json.dump(players, f, indent=4)
    
    # Extract home and away team players
    home_team_players = players.get('home_team_players', [])
    away_team_players = players.get('away_team_players', [])

    return home_team_players, away_team_players

def get_key_players_by_team(player_data, rating_threshold=7.0):
    home_team_players = []
    away_team_players = []

    # Ensure 'response' exists in the data
    if 'response' not in player_data:
        print("No 'response' field found in player data.")
        return home_team_players, away_team_players

    # Traverse the response structure to access player statistics
    for team_data in player_data['response']:
        team_name = team_data['team']['name']
        players = team_data.get('players', [])
        
        for player in players:
            player_id = player['player']['id']
            player_name = player['player']['name']
            # Assuming rating is the first element in statistics list
            player_rating = float(player['statistics'][0]['games']['rating']) if 'rating' in player['statistics'][0]['games'] else 0.0
            
            if player_rating >= rating_threshold:
                player_info = {
                    'id': player_id,
                    'name': player_name,
                    'rating': player_rating
                }
                
                if team_name == player_data['response'][0]['team']['name']:
                    home_team_players.append(player_info)
                else:
                    away_team_players.append(player_info)

    return home_team_players, away_team_players
