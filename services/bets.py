import os
import json

from services.fixtures import get_fixture_score
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

def check_bets_success_rate(new_bets):
    successful_bets = 0
    total_bets = 0

    # Load old bets from bets.json
    old_bets = load_saved_bets()
    
    # Create a dictionary to store unique bets by fixture_id
    unique_bets = {bet['fixture_id']: bet for bet in old_bets}

    for bet in new_bets:
        fixture_id = bet['fixture_id']
        if fixture_id in unique_bets:
            # Update existing bet if it doesn't have a result yet
            if 'correct' not in unique_bets[fixture_id]:
                unique_bets[fixture_id].update(bet)
        else:
            # Add new bet
            unique_bets[fixture_id] = bet

    for bet in unique_bets.values():
        if 'correct' in bet:
            total_bets += 1
            if bet['correct']:
                successful_bets += 1
        else:
            # Process bets without results
            predicted_winner = bet['predicted_winner'].split(": ")[1]
            print(f"Checking bet for fixture {bet['fixture_id']}: predicted winner - {predicted_winner}")

            actual_home_score, actual_away_score = get_fixture_score(bet['fixture_id'])
            print(f"Actual score for {bet['team_name']}: {actual_home_score} - {actual_away_score}")

            if actual_home_score is None or actual_away_score is None:
                print(f"Score data not available for fixture {bet['fixture_id']}. Skipping this bet.")
                continue

            if actual_home_score > actual_away_score:
                actual_winner = bet['team_name'].split(" vs ")[0]
            elif actual_away_score > actual_home_score:
                actual_winner = bet['team_name'].split(" vs ")[1]
            else:
                actual_winner = "Draw"

            print(f"Actual winner: {actual_winner}")
            success = (predicted_winner == actual_winner)
            print(f"Was the bet correct? {'Yes' if success else 'No'}")

            bet['home_team_goals'] = actual_home_score
            bet['away_team_goals'] = actual_away_score
            bet['correct'] = success

            total_bets += 1
            if success:
                successful_bets += 1
                print(f"Bet for {bet['team_name']} was successful!")
            else:
                print(f"Bet for {bet['team_name']} failed.")

    success_rate = (successful_bets / total_bets) * 100 if total_bets > 0 else 0
    print(f"\nTotal bets: {total_bets}")
    print(f"Successful bets: {successful_bets}")
    print(f"Success rate: {success_rate:.2f}%")

    # Save updated bets back to bets.json
    save_updated_bets(list(unique_bets.values()))

def save_updated_bets(bets):
    latest_file = find_latest_file(BETS_DIR)
    file_path = os.path.join(BETS_DIR, latest_file)

    with open(file_path, 'w') as file:
        json.dump(bets, file, indent=4)
