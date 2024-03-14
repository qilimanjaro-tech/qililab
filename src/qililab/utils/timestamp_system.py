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
    Given a timestamp and a data folder path, returns the path to the corresponding result file.
    """
    target_folder = timestamp.split("_")[0]  # Extract the folder name from the timestamp
    target_file = timestamp.split("_")[1]  # Extract the file name from the timestamp 

    folder_path = os.path.join(data_folder, target_folder) 

    if os.path.isdir(data_folder):
        for root, dirs, files in os.walk(folder_path):
            for folder in dirs:
                desired_part = folder.split("_")[0]

                if desired_part == target_file:
                    path = os.path.join(root, folder)
                    files = os.listdir(path)
                    if files:
                        return os.path.join(path, "results.yml")
    return None

def get_timestamp_from_file(path):
    """
    Given a file path, extracts and returns the timestamp associated with it.
    """
    parent_dir = os.path.dirname(path)
    desired_part = os.path.basename(parent_dir)
    first_part, second_part = os.path.split(path)
    return desired_part + '_' + second_part[:6]

def get_last_folder(directory):
    """
    Returns the name of the last folder in the specified directory.
    """
    folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    folders.sort()
    last_folder = folders[-1] if folders else None
    return last_folder

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
