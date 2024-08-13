import os
import json

from config import BETS_DIR

def save_bets(bets):
    """Save bets to a file."""
    
    ### To solve issue with saving when running from .exe
    ## file_path = r'C:\absolute\path\to\folder\data.txt'

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