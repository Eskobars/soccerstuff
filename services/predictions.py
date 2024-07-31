import json
import os
from datetime import datetime
from config import PREDICTIONS_DIR
from fetchers import fetch_match_predictions

def is_data_up_to_date(filename):
    """
    Check if the data in the file is valid and not empty.
    
    :param filename: Path to the JSON file.
    :return: True if data is valid and not empty, False otherwise.
    """
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                # Check if data is not empty
                return bool(data and 'response' in data and isinstance(data['response'], list) and len(data['response']) > 0)
        except (FileNotFoundError, KeyError, IndexError, ValueError, json.JSONDecodeError):
            return False
    return False

def get_fixture_prediction(fixture_id):
    # Define the file path using PREDICTIONS_DIR from the config
    filename = os.path.join(PREDICTIONS_DIR, f'predictions_data_{fixture_id}.json')

    # Use the is_data_up_to_date function to check if the file is valid
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
    
def determine_rating(home_team_points, away_team_points):
    points_difference = abs(home_team_points - away_team_points)
    if points_difference > 6:
        return 'three_star'
    elif points_difference > 4:
        return 'two_star'
    elif points_difference > 2:
        return 'one_star'
    else:
        return 'no_star'

def rate_fixture(predictions, home_team_data, away_team_data):
    """
    Rate a fixture based on its prediction and return the points and rating for home and away teams, 
    along with the winning team and comment.
    """
    # Default values
    default_comment = "No comments"

    try:
        # Initialize points for the home and away teams
        home_team_points = 0
        away_team_points = 0

        # Extract prediction data or use defaults
        percent_home = int(predictions.get('percent', {}).get('home', 0))
        percent_draw = int(predictions.get('percent', {}).get('draw', 0))
        percent_away = int(predictions.get('percent', {}).get('away', 0))
        predicted_winner_name = predictions.get('winner', {}).get('name', 'Unknown')
        points_winner_name = ""
        home_team_name = home_team_data.get('team_name', 'Unknown')
        away_team_name = away_team_data.get('team_name', 'Unknown')

        # Check both fields for the comment
        comment = predictions.get('winner', {}).get('comment', '')
        advice = predictions.get('winner', {}).get('advice', '')
        comment = f"{comment} {'| ' if comment and advice else ''}{advice}".strip() or default_comment

        # Add points based on percentage values
        if percent_home > 70:
            home_team_points += 3
        elif percent_home > 60:
            home_team_points += 2
        elif percent_home > 45 and percent_draw > 45:
            home_team_points += 1

        if percent_away > 70:
            away_team_points += 3
        elif percent_away > 60:
            away_team_points += 2
        elif percent_away > 45 and percent_draw > 45:
            away_team_points += 1

        # Use points and goalsDiff (goal difference) to rate the teams
        home_points = home_team_data.get('points', 0)
        away_points = away_team_data.get('points', 0)
        home_goals_diff = home_team_data.get('goalsDiff', 0)
        away_goals_diff = away_team_data.get('goalsDiff', 0)

        # Additional points based on points and goals difference
        if home_points > (away_points + 30):
            home_team_points += 3
        elif home_points > (away_points + 20):
            home_team_points += 2
        elif home_points > (away_points + 10):
            home_team_points += 1

        if away_points > (home_points + 30):
            away_team_points += 3
        elif away_points > (home_points + 20):
            away_team_points += 2
        elif away_points > (home_points + 10):
            away_team_points += 1

        if home_goals_diff > 30:
            home_team_points += 3
        elif home_goals_diff > 15:
            home_team_points += 2
        elif home_goals_diff > 0:
            home_team_points += 1

        if away_goals_diff > 30:
            away_team_points += 3
        elif away_goals_diff > 15:
            away_team_points += 2
        elif away_goals_diff > 0:
            away_team_points += 1
        
        home_team_points += 1
        away_team_points -= 1

        # Form check
        home_form = home_team_data.get('form', '')
        away_form = away_team_data.get('form', '')

        if home_form:
            if home_form.endswith('WWWWW'):
                home_team_points += 2
            elif home_form.endswith('WWW'):
                home_team_points += 1
            elif home_form.endswith('LLLLL'):
                home_team_points -= 2
            elif home_form.endswith('LLL'):
                home_team_points -= 1

        if away_form:
            if away_form.endswith('WWWWW'):
                away_team_points += 2
            elif away_form.endswith('WWW'):
                away_team_points += 1
            elif away_form.endswith('LLLLL'):
                away_team_points -= 2
            elif away_form.endswith('LLL'):
                away_team_points -= 1

        # Determine which team has more points
        if home_team_points > away_team_points:
            points_winner_name = home_team_name
        elif away_team_points > home_team_points:
            points_winner_name = away_team_name
        else:
            points_winner_name = "Draw"

        rating = determine_rating(home_team_points, away_team_points)

        # Debug output for points and rating
        print(f"Fixture: {home_team_name} vs {away_team_name}, Home Team Points: {home_team_points}, Away Team Points: {away_team_points}, Comment: {comment}")
        print(f"Predicted Winner: {predicted_winner_name}, Winner in points: {points_winner_name}")

        return home_team_points, away_team_points, rating, predicted_winner_name, points_winner_name, comment

    except (KeyError, ValueError, TypeError) as e:
        # Print the structure of predictions for debugging
        print(f"Error processing predictions: {e}")
        print(f"Predictions data: {predictions}")
        return 0, 0, 'no_star', None, "Error retrieving comment"