"""Methods to manage results data """
import os
from datetime import datetime
from pathlib import Path

from qililab.constants import DATA


def _get_folder_path():
    """Results data 'path'.

    Returns:
        Path: Path to the results data folder.
    """
    folderpath = os.environ.get(DATA, None)
    if folderpath is None:
        raise ValueError("Environment variable DATA is not set.")
    return folderpath


def _create_daily_results_folder(now: datetime) -> Path:
    """Create a folder for the current day (if not exist)
       where the daily results data will be saved.

    Args:
        now (datetime): The current datetime

    Returns:
        Path: Path to folder.
    """
    # create folder
    path = Path(_get_folder_path()) / f"{now.year}{now.month:02d}{now.day:02d}"
    _create_directory_if_not_exists(path=path)

    return path


def _get_current_time():
    """Get the current time"""
    return datetime.now()


def create_results_folder(name: str) -> Path:
    """Create folder where the results data will be saved.

    Args:
        name (str): name to identify the folder besides the timestamp
    Returns:
        Path: Path to folder.
    """
    now = _get_current_time()

    daily_path = _create_daily_results_folder(now=now)

    path = daily_path / f"{now.hour:02d}{now.minute:02d}{now.second:02d}_{name}"
    _create_directory_if_not_exists(path=path)

    return path


def _create_directory_if_not_exists(path: Path):
    """create directory if it not exists"""
    if not os.path.exists(path):
        os.makedirs(path)
