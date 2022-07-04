"""Load method used to load experiment and results data."""
import glob
import os
from pathlib import Path
from typing import Tuple

import yaml

from qililab.constants import DATA
from qililab.experiment import Experiment
from qililab.result import Results


def load(path: str | None = None) -> Tuple[Experiment | None, Results | None]:
    """Load Experiment and Results from yaml data.

    Args:
        path (str): Path to folder.

    Returns:
        Tuple(Experiment | None, Results | None): Return Experiment and Results objects, or None.
    """
    if path is None:
        folderpath = os.environ.get(DATA, None)
        if folderpath is None:
            raise ValueError("Environment variable DATA is not set.")
        files_list = glob.glob(os.path.join(folderpath, "*"))
        if not files_list:
            return None, None
        path = max(files_list, key=os.path.getctime)
    experiment = None
    results = None
    if os.path.exists(Path(path) / "experiment.yml"):
        with open(Path(path) / "experiment.yml", mode="r", encoding="utf-8") as experiment_file:
            experiment = Experiment.from_dict(yaml.safe_load(stream=experiment_file))

    if os.path.exists(Path(path) / "results.yml"):
        with open(Path(path) / "results.yml", mode="r", encoding="utf-8") as results_file:
            results = Results(**yaml.safe_load(stream=results_file))

    return experiment, results
