# Simplified function to add a fixed delay between each request
import functools
import time

def fetch_data_with_rate_limit(fetch_function, *args, delay_seconds=6.1):
    time.sleep(delay_seconds)
    @functools.wraps(fetch_function)
    def wrapper():
        while True:
            try:
                # Attempt to fetch data
                data = fetch_function(*args)
                return data  # Return data if no error is detected
            except Exception as e:
                print(f"Error fetching data: {e}")
                print("Retrying in 61 seconds...")
                time.sleep(61)  # Wait before retrying in case of error

    return wrapper()