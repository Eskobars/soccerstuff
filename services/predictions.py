import json

from date_helper import is_data_up_to_date
from fetchers import fetch_match_predictions

def get_fixture_prediction(fixture_id):
    filename = f'predictions_data_{fixture_id}.json'
    
    if is_data_up_to_date(filename):
        with open(filename, 'r') as f:
            predictions = json.load(f)
    else:
        predictions = fetch_match_predictions(fixture_id)
        with open(filename, 'w') as f:
            json.dump(predictions, f, indent=4)
        print("Predictions data fetched and stored successfully.")
    
    if predictions and 'response' in predictions and isinstance(predictions['response'], list) and len(predictions['response']) > 0:
        return predictions['response'][0]  # Adjust if the structure is different
    else:
        print(f"No predictions available or incorrect format for fixture {fixture_id}.")
        return {}
    
def rate_fixture(predictions, team_data):
    """
    Rate a fixture based on its prediction and return the winning team and comment.
    """
    # Default values
    default_comment = "No comments"

    try:
        # Initialize points for the current fixture
        points = 0

        # Extract prediction data or use defaults
        percent_home = int(predictions.get('percent', {}).get('home', 0))
        percent_draw = int(predictions.get('percent', {}).get('draw', 0))
        percent_away = int(predictions.get('percent', {}).get('away', 0))
        winner_name = predictions.get('winner', {}).get('name', 'Unknown')

        # Check both fields for the comment
        comment = predictions.get('winner', {}).get('comment', '')
        advice = predictions.get('winner', {}).get('advice', '')
        comment = f"{comment} {'| ' if comment and advice else ''}{advice}".strip() or default_comment

        # Add points based on percentage values
        if percent_home > 70 or percent_away > 70:
            points += 3
        elif percent_home > 60 or percent_away > 60:
            points += 2
        elif percent_home > 45 and percent_draw > 45:
            points += 1
        else:
            points += 0

        # Add additional points based on other criteria (assuming they are part of the predictions)
        ## These arent in predictions, they are in match info
        if team_data.get('goals', {}).get('for', {}).get('total', {}).get('total', 0) > \
           team_data.get('goals', {}).get('against', {}).get('total', {}).get('total', 0):
            points += 1

        if team_data.get('fixtures', {}).get('wins', {}).get('total', 0) > \
           team_data.get('fixtures', {}).get('loses', {}).get('total', 0):
            points += 1

        if team_data.get('fixtures', {}).get('played', {}).get('total', 0) < 10:
            points -= 1

        form = team_data.get('form', '')
        if form.endswith('WWWWW'):
            points += 2
        elif form.endswith('WWW'):
            points += 1
        elif form.endswith('LLLLL'):
            points -= 2
        elif form.endswith('LLL'):
            points -= 1

        # Determine rating based on points
        if points >= 3:
            rating = 'three_star'
        elif points == 2:
            rating = 'two_star'
        elif points == 1:
            rating = 'one_star'
        else:
            rating = 'no_star'

        # Debug output for points and rating
        print(f"Fixture: {winner_name}, Points: {points}, Rating: {rating}, Comment: {comment}")
        print(points, rating)

        return rating, winner_name, comment
    

    except (KeyError, ValueError, TypeError) as e:
        # Print the structure of predictions for debugging
        print(f"Error processing predictions: {e}")
        print(f"Predictions data: {predictions}")
        return 'no_star', None, "Error retrieving comment"
