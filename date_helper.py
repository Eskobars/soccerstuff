import os
from datetime import datetime, timedelta
import pandas as pd

def get_current_day_epoch_range():
    now = pd.Timestamp.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)    
    end_of_day = start_of_day + timedelta(days=1)  # End of the day is start of next day

    epoch_time = datetime(1970, 1, 1)
    start_epoch = int((start_of_day - epoch_time).total_seconds())
    end_epoch = int((end_of_day - epoch_time).total_seconds())

    return start_epoch, end_epoch

def is_data_up_to_date(filename):
    if not os.path.exists(filename):
        return False
    
    file_mod_time = os.path.getmtime(filename)
    start_epoch, end_epoch = get_current_day_epoch_range()

    # Check if the file modification time is within the current day's epoch range
    return start_epoch <= file_mod_time <= end_epoch
