import os
from datetime import datetime

def get_timestamp():
    """
    Returns a timestamp string in the format 'YYYYMMDD_HHMMSS'.
    """
    now = datetime.now()
    date_str = f"{now.year}{now.month:02d}{now.day:02d}"
    time_str = f"{now.hour:02d}{now.minute:02d}{now.second:02d}"
    return date_str + "_" + time_str

def get_path_from_timestamp(timestamp, data_folder):
    """
    Given a timestamp and a data folder path, returns the path to the corresponding folder if exists.
    """
    target_folder = timestamp.split("_")[0]  # Extract the folder name from the timestamp
    target_file = timestamp.split("_")[1]  # Extract the file name from the timestamp 

    folder_path = os.path.join(data_folder, target_folder)
    all_dirs = os.listdir(folder_path)
    matching_dirs = [this_dir for this_dir in all_dirs if target_file in this_dir]

    # more than one directory matching the timestamp
    assert len(matching_dirs)<2
    if len(matching_dirs)==1:
        if os.path.isdir(os.path.join(data_folder,matching_dirs[0])):
            return folder_path
    return None

def get_timestamp_from_file(path):
    """
    Given a file path, extracts and returns the timestamp associated with it.
    """
    parent_dir = os.path.dirname(path)
    splitted = parent_dir.split('/')
    splitted[-1]
    return splitted[-2][-8:] + '_' + splitted[-1][:6]

def get_last_folder(directory):
    """
    Returns the name of the last folder in the specified directory.
    """
    folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    folders.sort()
    last_folder = folders[-1] if folders else None
    return last_folder

def get_last_data_folder(directory):
    last_day_folder = get_last_folder(directory)
    last_data_folder = get_last_folder(directory+'/'+last_day_folder)
    return directory+'/'+last_day_folder+'/'+last_data_folder

def get_last_timestamp(data_folder):
    """
    Returns the timestamp string corresponding to the last experiment in the data folder.
    """
    last_day_folder = get_last_folder(data_folder)
    full_day_path = os.path.join(data_folder, last_day_folder)
    last_exp_folder = get_last_folder(full_day_path)
    timestamp_string = last_day_folder + '_' + last_exp_folder[:6]
    return timestamp_string

def get_last_results(data_folder):
    """
    Returns the path to the results file of the last experiment in the data folder.
    """
    last_day_folder = get_last_folder(data_folder)
    full_day_path = os.path.join(data_folder, last_day_folder)
    last_exp_folder = get_last_folder(full_day_path)
    full_exp_path = os.path.join(data_folder, last_day_folder, last_exp_folder)
    file_path = os.path.join(full_exp_path, "results.yml")
    if not os.path.isfile(file_path):
        print(f'Results file does not exist! {file_path}')
        return None
    return file_path
