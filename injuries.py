import http.client
import json
from config import API_KEY

def fetch_injuries_for_fixture(fixture_id):
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    url = f"/injuries?fixture={fixture_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def get_injured_players(injury_data, player_ids):
    injured_players = set()
    for injury in injury_data.get('response', []):
        player_id = injury['player']['id']
        if player_id in player_ids:
            injured_players.add(player_id)
    return injured_players
