"""This file contains the function ``prepare_results``."""
import os
from datetime import datetime
from pathlib import Path

from qililab.constants import DATA, EXPERIMENT, EXPERIMENT_FILENAME, RESULTS_FILENAME
from qililab.result.results import Results
from qililab.typings.experiment import ExperimentOptions
from qililab.typings.yaml_type import yaml
from qililab.utils.util_loops import compute_shapes_from_loops


def prepare_results(
    options: ExperimentOptions, num_schedules: int, experiment_serialized: dict
) -> tuple[Results, Path]:
    """Creates the ``Results`` class, creates the ``results.yml`` file where the results will be saved, and dumps
    the experiment data into this file.

    Args:
        options (ExperimentOptions): options of the experiment
        num_schedules (int): number of schedules
        experiment_serialized (dict): dictionary representing the current experiment

    Returns:
        tuple[Results, Path]: a tuple containing the ``Results`` class and the path to the ``results.yml`` file
    """
    # Create the ``Results`` class
    results = Results(
        software_average=options.settings.software_average, num_schedules=num_schedules, loops=options.loops
    )
    # Create the folders & files needed to save the results locally
    results_path = _path_to_results_folder(name=options.name)
    _create_results_file(options=options, num_schedules=num_schedules, path=results_path)

    # Dump the experiment data into the created file
    with open(file=results_path / EXPERIMENT_FILENAME, mode="w", encoding="utf-8") as experiment_file:
        yaml.dump(data=experiment_serialized, stream=experiment_file, sort_keys=False)

    return results, results_path


def _path_to_results_folder(name: str) -> Path:
    """Creates a folder for the current day (if needed), creates another folder for the current timestamp (if needed)
    and returns the path to this last folder.

    Args:
        name (str): name to identify the folder besides the timestamp

    Returns:
        Path: Path to folder.
    """
    # Timestamp
    now = datetime.now()

    # Get path to DATA folder from environment
    daily_path = os.environ.get(DATA, None)
    if daily_path is None:
        raise ValueError("Environment variable DATA is not set.")

    # Generate path to the daily folder
    daily_path = Path(daily_path) / f"{now.year}{now.month:02d}{now.day:02d}"  # type: ignore

    # Check if folder exists, if not create one
    if not os.path.exists(daily_path):
        os.makedirs(daily_path)

    # Generate path to the results folder
    now_path = daily_path / f"{now.hour:02d}{now.minute:02d}{now.second:02d}_{name}"  # type: ignore

    # Check if folder exists, if not create one
    if not os.path.exists(now_path):
        os.makedirs(now_path)

    return now_path


def _create_results_file(options: ExperimentOptions, num_schedules: int, path: Path):
    """Create 'results.yml' file that contains all the information about the current experiment.

    Args:
        path (Path): Path to data folder.
    """

    data = {
        EXPERIMENT.SOFTWARE_AVERAGE: options.settings.software_average,
        EXPERIMENT.NUM_SCHEDULES: num_schedules,
        EXPERIMENT.SHAPE: [] if options.loops is None else compute_shapes_from_loops(loops=options.loops),
        EXPERIMENT.LOOPS: [loop.to_dict() for loop in options.loops] if options.loops is not None else None,
        EXPERIMENT.RESULTS: None,
    }
    with open(file=path / RESULTS_FILENAME, mode="w", encoding="utf-8") as results_file:
        yaml.dump(data=data, stream=results_file, sort_keys=False)
