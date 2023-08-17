import os
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

from qililab.platform import Platform


def save_results(results: np.ndarray, path: str, name: str | None = None, platform: Platform | None = None):
    """Save the given results and the platform.

    A timestamp is used to create a folder to save the data. The data will be saved within the folder located in:
    `path/year-month-day/hour-minute-second_name/`.

    Args:
        results (np.ndarray): Array containing the results to be saved.
        path (str): Path to the top data folder.
        name (str | None, optional): Name of the experiment. If given, the name is added to the name of the folder.
        platform (Platform | None, optional): Platform class. If given, the platform is serialized and saved together
            with the results. Defaults to None.
    """
    now = datetime.now()

    # Generate path to the daily folder
    daily_path = Path(path) / f"{now.year}{now.month:02d}{now.day:02d}"  # type: ignore

    # Check if folder exists, if not create one
    if not os.path.exists(daily_path):
        os.makedirs(daily_path)

    # Generate path to the results folder
    now_path = daily_path / f"{now.hour:02d}{now.minute:02d}{now.second:02d}_{name}"  # type: ignore

    # Check if folder exists, if not create one
    if not os.path.exists(now_path):
        os.makedirs(now_path)

    np.save(file=f"{now_path}/results.npy", arr=results)

    if platform:
        with open(file=f"{now_path}/platform.yml", mode="w", encoding="utf-8") as platform_file:
            yaml.dump(stream=platform_file, data=platform.to_dict(), sort_keys=False)

    return now_path
