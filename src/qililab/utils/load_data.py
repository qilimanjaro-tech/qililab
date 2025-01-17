# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Load method used to load experiment and results data."""
import glob
import os
from pathlib import Path

from ruamel.yaml import YAML

from qililab.constants import DATA, EXPERIMENT_FILENAME, RESULTS_FILENAME
from qililab.experiment.experiment import Experiment
from qililab.result.results import Results


def _get_last_created_path(folderpath: Path) -> Path:
    """Get the last created path for files in a directory"""
    files_list = glob.glob(os.path.join(folderpath, "*"))
    if not files_list:
        raise ValueError("No previous experiment data found.")
    path = max(files_list, key=os.path.getctime)
    return Path(path)


def _get_last_created_experiment_path() -> Path:
    """Get the last created path for the experiment"""
    folderpath = os.environ.get(DATA, None)
    if folderpath is None:
        raise ValueError("Environment variable DATA is not set.")
    last_daily_directory_path = _get_last_created_path(folderpath=Path(folderpath))
    return _get_last_created_path(folderpath=last_daily_directory_path)


def load(path: str | None = None, load_experiment: bool = False) -> tuple[Experiment | None, Results | None]:
    """Load Experiment and Results from yaml data.

    Args:
        path (str): Path to folder.

    Returns:
        Tuple(Experiment | None, Results | None): Return Experiment and Results objects, or None.
    """
    parsed_path = Path(path) if isinstance(path, str) else _get_last_created_experiment_path()
    experiment, results = None, None
    if load_experiment and os.path.exists(parsed_path / EXPERIMENT_FILENAME):
        with open(parsed_path / EXPERIMENT_FILENAME, mode="r", encoding="utf-8") as experiment_file:
            yaml = YAML(typ="safe")
            experiment = Experiment.from_dict(yaml.load(stream=experiment_file))

    if os.path.exists(parsed_path / RESULTS_FILENAME):
        with open(parsed_path / RESULTS_FILENAME, mode="r", encoding="utf-8") as results_file:
            yaml = YAML(typ="safe")
            results = Results(**yaml.load(stream=results_file))

    if experiment is not None and results is not None:
        experiment.results = results

    return experiment, results
