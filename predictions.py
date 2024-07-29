import json
import http.client
from config import API_KEY
from date_helper import is_data_up_to_date

def fetch_match_predictions(fixture_id):
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_KEY
    }
    url = f"/predictions?fixture={fixture_id}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def get_fixture_prediction(fixture_id):
    filename = f'predictions_data_{fixture_id}.json'
    
    if is_data_up_to_date(filename):
        print(f"Predictions data for fixture {fixture_id} is up to date, loading from file.")
        with open(filename, 'r') as f:
            predictions = json.load(f)
    else:
        print(f"Fetching new predictions data for fixture {fixture_id}...")
        predictions = fetch_match_predictions(fixture_id)
        with open(filename, 'w') as f:
            json.dump(predictions, f, indent=4)
        print("Predictions data fetched and stored successfully.")
    
    if predictions and 'response' in predictions and isinstance(predictions['response'], list) and len(predictions['response']) > 0:
        return predictions['response'][0]  # Adjust if the structure is different
    else:
        print(f"No predictions available or incorrect format for fixture {fixture_id}.")
        return {}