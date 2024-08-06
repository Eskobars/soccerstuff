import json
import os
from datetime import datetime
from config import PREDICTIONS_DIR
from fetchers import fetch_match_predictions
from services.teams import get_teams_data

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

        # Extract prediction data directly
        predictions_item = predictions['predictions']  # Access the predictions section
        teams_item = predictions['teams']
        home_team_item = teams_item['home']
        away_team_item = teams_item['away']
        league_item = predictions['league']

        # Convert percentage values to integers
        percent_home = int(predictions_item['percent']['home'].strip('%')) if 'home' in predictions_item['percent'] else 0
        percent_draw = int(predictions_item['percent']['draw'].strip('%')) if 'draw' in predictions_item['percent'] else 0
        percent_away = int(predictions_item['percent']['away'].strip('%')) if 'away' in predictions_item['percent'] else 0

        home_team_id = int(teams_item['home']['id'])
        away_team_id = int(teams_item['away']['id'])
        league_id = int(league_item['id'])

        # Access predicted winner's name with a default value if None
        predicted_winner_name = predictions_item['winner']['name'] if predictions_item['winner']['name'] is not None else 'Unknown'
        
        # Default team names if not provided
        home_team_name = home_team_data['team_name'] if 'team_name' in home_team_data else 'Unknown'
        away_team_name = away_team_data['team_name'] if 'team_name' in away_team_data else 'Unknown'
        
        # Form check
        home_form = home_team_data['form'] if 'form' in home_team_data else ''
        away_form = away_team_data['form'] if 'form' in away_team_data else ''

        # Ensure form has at least five characters
        if len(home_form) < 5 or len(away_form) < 5:
            return 0, 0, 'no_star', "None", "None", "Not enough recent matches, skipping"

        home_team_win_ratio, away_team_win_ratio = get_team_win_lose_ratios(home_team_item, away_team_item)
        home_team_goal_ratio, away_team_goal_ratio = get_team_goals_ratios(home_team_item, away_team_item)
        rank_difference = get_team_rank_difference(home_team_data, away_team_data)

        # Extract comment and advice directly
        winner_data = predictions_item['winner']
        comment = winner_data['comment'] if winner_data['comment'] is not None else default_comment
        advice = predictions['advice'] if 'advice' in predictions else default_comment
        comment = f"{comment} {'| ' if comment and advice else ''}{advice}".strip() or default_comment

        # Add points based on percentage values
        if percent_home >= 70:
            home_team_points += 2
        elif percent_home >= 60:
            home_team_points += 1
        elif percent_home >= 45 and percent_draw >= 45:
            home_team_points += 0

        if percent_away >= 70:
            away_team_points += 2
        elif percent_away >= 60:
            away_team_points += 1
        elif percent_away >= 45 and percent_draw >= 45:
            away_team_points += 0

        # Adjust points based on win-to-lose ratio
        if home_team_win_ratio >= 3:
            home_team_points += 2
        elif home_team_win_ratio >= 2:
            home_team_points += 1    
        elif home_team_win_ratio >= 1:
            home_team_points += 0
        elif home_team_win_ratio <= -1:
            home_team_points -= 1

        if away_team_win_ratio >= 3:
            home_team_points += 2
        elif away_team_win_ratio >= 2:
            away_team_points += 1
        elif away_team_win_ratio >= 1:
            away_team_points += 0
        elif away_team_win_ratio <= -1:
            away_team_points -= 1

        # Adjust points based on goals for/against ratio
        if home_team_goal_ratio >= 2:
            home_team_points += 2
        elif home_team_goal_ratio >= 1.5:
            home_team_points += 1
        elif home_team_goal_ratio >= 1:
            home_team_points += 0
        elif home_team_goal_ratio <= 1:
            home_team_points -= 1
        elif home_team_goal_ratio <= -1:
            home_team_points -= 2

        if away_team_goal_ratio >= 2:
            home_team_points += 2
        elif away_team_goal_ratio >= 1.5:
            home_team_points += 1
        elif away_team_goal_ratio >= 1:
            home_team_points += 0
        elif away_team_goal_ratio <= 1:
            home_team_points -= 1
        elif away_team_goal_ratio <= -1:
            home_team_points -= 2

        if rank_difference >= 10:
            home_team_points += 2
        elif rank_difference >= 5:
            home_team_points += 1
        elif rank_difference <= 5:
            away_team_points += 1
        elif rank_difference <= -5:
            away_team_points += 1
        elif rank_difference <= -10:
            away_team_points += 2

        # Use points and goalsDiff (goal difference) to rate the teams
        home_points = home_team_data['points'] if 'points' in home_team_data else 0
        away_points = away_team_data['points'] if 'points' in away_team_data else 0
        # home_goals_diff = home_team_data['goalsDiff'] if 'goalsDiff' in home_team_data else 0
        # away_goals_diff = away_team_data['goalsDiff'] if 'goalsDiff' in away_team_data else 0

        # Additional points based on points and goals difference
        if home_points >= (away_points + 30):
            home_team_points += 2
        elif home_points >= (away_points + 20):
            home_team_points += 1
        elif home_points >= (away_points + 10):
            home_team_points += 0

        if away_points >= (home_points + 30):
            away_team_points += 2
        elif away_points >= (home_points + 20):
            away_team_points += 1
        elif away_points >= (home_points + 10):
            away_team_points += 0

        # if home_goals_diff > 30:
        #     home_team_points += 3
        # elif home_goals_diff > 15:
        #     home_team_points += 2
        # elif home_goals_diff > 0:
        #     home_team_points += 1
        # elif home_goals_diff < 0:
        #     home_team_points -1 

        # if away_goals_diff > 30:
        #     away_team_points += 2
        # elif away_goals_diff > 15:
        #     away_team_points += 1
        # elif away_goals_diff > 0:
        #     away_team_points += 1
        # elif away_goals_diff < 0:
        #     away_team_points -= 1

        home_team_points += 1
        away_team_points -= 1

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

        if (rating != 'no_star') : 
            # home_team_stats = get_teams_data(home_team_id, league_id)
            # away_team_stats = get_teams_data(away_team_id, league_id)

            print("rating succesful")


        # Debug output for points and rating
        print(f"Fixture: {home_team_name} vs {away_team_name}, Home Team Points: {home_team_points}, Away Team Points: {away_team_points}, Comment: {comment}")
        print(f"Predicted Winner: {predicted_winner_name}, Winner in points: {points_winner_name}")

        return home_team_points, away_team_points, rating, predicted_winner_name, points_winner_name, comment

    except (KeyError, IndexError, ValueError) as e:
        # Print the structure of predictions for debugging
        print(f"Error processing predictions: {e}")

        return 0, 0, 'no_star', "None", "None", "Error retrieving comment"

    
def determine_rating(home_team_points, away_team_points):
    # Calculate the absolute difference between home team and away team points
    points_difference = abs(home_team_points - away_team_points)

    # Determine the rating based on the points difference
    if points_difference > 6:
        return 'three_star'
    elif points_difference > 4:
        return 'two_star'
    elif points_difference > 2:
        return 'one_star'
    else:
        return 'no_star'

def calculate_win_lose_ratio(wins, losses):
    # Convert inputs to integers and handle division by zero
    wins = int(wins)
    losses = int(losses)
    
    if losses == 0:
        return float('inf')  # or another indicator of an undefined ratio
    else:
        return wins / losses
    
def get_team_win_lose_ratios(home_team_item, away_team_item):
    # Extract home team stats
    home_total_wins = home_team_item['league']['fixtures']['wins']['total']
    home_total_losses = home_team_item['league']['fixtures']['loses']['total']
    
    home_win_lose_ratio = calculate_win_lose_ratio(home_total_wins, home_total_losses)
    
    away_total_wins = away_team_item['league']['fixtures']['wins']['total']
    away_total_losses = away_team_item['league']['fixtures']['loses']['total']
    
    away_win_lose_ratio = calculate_win_lose_ratio(away_total_wins, away_total_losses)
    
    return home_win_lose_ratio, away_win_lose_ratio

def get_team_goals_ratios (home_team_item, away_team_item): 
    home_total_goals_for = home_team_item['league']['goals']['for']['total']['total']
    home_total_goals_against = home_team_item['league']['goals']['against']['total']['total']

    if home_total_goals_against == 0:
        home_goals_ratio = home_total_goals_for  # To avoid division by zero
    else:
        home_goals_ratio = home_total_goals_for / home_total_goals_against

    away_total_goals_for = away_team_item['league']['goals']['for']['total']['total']
    away_total_goals_against = away_team_item['league']['goals']['against']['total']['total']

    if away_total_goals_against == 0:
        away_goals_ratio = away_total_goals_for  # To avoid division by zero
    else:
        away_goals_ratio = away_total_goals_for / away_total_goals_against

    return (home_goals_ratio, away_goals_ratio)

def get_team_rank_difference (home_team_data, away_team_data): 
    home_rank = home_team_data['rank']
    away_rank = away_team_data['rank']

    rank_difference = away_rank - home_rank

    return (rank_difference)