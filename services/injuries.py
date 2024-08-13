import json
import os 

from helpers.date_helper import is_data_up_to_date
from fetchers import fetch_injuries_for_fixture

from config import INJURIES_DIR

def get_injury_data(fixture_id):
    filename = os.path.join(INJURIES_DIR, f'injuries_data_{fixture_id}.json')

    if is_data_up_to_date(filename):
        with open(filename, 'r') as f:
            injuries = json.load(f)
    else:
        injuries = fetch_injuries_for_fixture(fixture_id)
        with open(filename, 'w') as f:
            json.dump(injuries, f, indent=4)
        print("Injury data fetched and stored successfully.")
    
    # Extract home and away team injuries
    home_team_injuries = injuries.get('home_team_injuries', [])
    away_team_injuries = injuries.get('away_team_injuries', [])

    return home_team_injuries, away_team_injuries

def filter_injuries_to_player_ids(injury_data, player_ids):
    injured_players = set()
    for injury in injury_data.get('response', []):
        player_id = injury['player']['id']
        if player_id in player_ids:
            injured_players.add(player_id)
    return injured_players