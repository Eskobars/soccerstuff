import os

from datetime import datetime

def find_latest_rated_fixtures(directory):
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    files = [f for f in os.listdir(directory) if f.startswith('rated_fixtures_') and f.endswith('.json')]
    matching_files = [f for f in files if f[len('rated_fixtures_'): -len('.json')] == current_date_str]
    
    if matching_files:
        return matching_files[0]
    else:
        return None
    
def find_latest_file(directory):
    # Get all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    # Filter out any files that do not match a specific pattern if needed
    if not files:
        return None

    # Get the latest file based on the modification time
    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))

    return latest_file