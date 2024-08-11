import os

from datetime import datetime

def find_latest_file(directory):
    # Get the current date as a string in the format 'YYYY-MM-DD'
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    
    # List all files in the directory that match the pattern
    files = [f for f in os.listdir(directory) if f.startswith('rated_fixtures_') and f.endswith('.json')]
    
    # Filter files that match the current date
    matching_files = [f for f in files if f[len('rated_fixtures_'): -len('.json')] == current_date_str]
    
    # Return the file if found, otherwise return None
    if matching_files:
        return matching_files[0]
    else:
        return None
    