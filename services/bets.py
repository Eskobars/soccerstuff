import os
import json

from helpers.data.latest_file import find_latest_file

from config import BETS_DIR

def save_bets(bets):
    file_path = os.path.join(BETS_DIR, 'bets.json')
    os.makedirs(BETS_DIR, exist_ok=True)

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                existing_bets = json.load(file)
        else:
            existing_bets = []

        existing_bets.extend(bets)
        with open(file_path, 'w') as file:
            json.dump(existing_bets, file, indent=4)

    except Exception as e:
        print(f"Error saving bets: {e}")

def load_saved_bets():
    latest_file = find_latest_file(BETS_DIR)
    if latest_file is None:
        return [] 
    
    file_path = os.path.join(BETS_DIR, latest_file)
    with open(file_path, 'r') as file:
        bets_data = json.load(file)
        return bets_data 
    