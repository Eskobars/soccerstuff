# import json
# import os    
# from date_helper import is_data_up_to_date
# from fetchers import fetch_teams_for_fixture
# from config import TEAMS_DIR

# def get_player_data(fixture_id):
#     filename = os.path.join(TEAMS_DIR, f'teams_data_{fixture_id}.json')

#     if is_data_up_to_date(filename):
#         with open(filename, 'r') as f:
#             players = json.load(f)
#     else:
#         print(f"Fetching new player data for fixture {fixture_id}...")
#         players = fetch_players_for_fixture(fixture_id)
#         with open(filename, 'w') as f:
#             json.dump(players, f, indent=4)
    
#     # Extract home and away team players
#     home_team_players = players.get('home_team_players', [])
#     away_team_players = players.get('away_team_players', [])

#     return home_team_players, away_team_players
