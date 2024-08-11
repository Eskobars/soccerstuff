import os
import json

from config import STANDINGS_DIR

def load_standings_data(league_id):
    """Load standings data from a file and ensure it contains valid content."""
    file_path = os.path.join(STANDINGS_DIR, f'standings_{league_id}.json')
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                if data and 'response' in data and isinstance(data['response'], list) and len(data['response']) > 0:
                    return data
        except (FileNotFoundError, KeyError, IndexError, ValueError, json.JSONDecodeError) as e:
            print(f"Error reading standings data from {file_path}: {e}")
    
    return None

def save_standings_data(league_id, data):
    """Save standings data to a file."""
    file_path = os.path.join(STANDINGS_DIR, f'standings_{league_id}.json')
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
