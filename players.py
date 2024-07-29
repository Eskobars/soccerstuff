import http.client
import json
from config import API_KEY

def fetch_players_for_fixture(fixture_id):
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")

    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }

    url = f"/fixtures/players?fixture={fixture_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    
    if res.status != 200:
        print(f"Error fetching players: {res.status} - {res.reason}")
        return None
    
    # Decode the JSON data
    parsed_data = json.loads(data.decode("utf-8"))
    
    return parsed_data

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
