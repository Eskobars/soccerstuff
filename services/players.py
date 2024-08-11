import json
import os    
from services.date_helper import is_data_up_to_date
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

def get_key_players_by_team(home_team_players, away_team_players, rating_threshold=7.0):
    home_key_players = []
    away_key_players = []

    # Function to filter players based on rating threshold
    def filter_key_players(players, team_key_players):
        for player in players:
            player_id = player['player']['id']
            player_name = player['player']['name']
            player_rating = float(player['statistics'][0]['games']['rating']) if 'rating' in player['statistics'][0]['games'] else 0.0
            
            if player_rating >= rating_threshold:
                player_info = {
                    'id': player_id,
                    'name': player_name,
                    'rating': player_rating
                }
                team_key_players.append(player_info)
    
    # Filter key players for home and away teams
    filter_key_players(home_team_players, home_key_players)
    filter_key_players(away_team_players, away_key_players)

    return home_key_players, away_key_players