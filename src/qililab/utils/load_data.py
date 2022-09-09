"""Load method used to load experiment and results data."""
import glob
import os
from copy import deepcopy
from pathlib import Path
from typing import List, Tuple

import yaml

from qililab.constants import (
    DATA,
    EXPERIMENT,
    EXPERIMENT_FILENAME,
    PLATFORM,
    PULSE,
    QBLOXRESULT,
    RESULTS_FILENAME,
    RUNCARD,
)
from qililab.experiment import Experiment
from qililab.result import Results
from qililab.typings.enums import PulseShapeSettingsName

RESULTS_FILENAME_BACKUP = "results_bak.yml"
EXPERIMENT_FILENAME_BACKUP = "experiment_bak.yml"
DEFAULT_PULSE_LENGTH = 8000.0
DEFAULT_MASTER_DRAG_COEFFICIENT = 0


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


def load(path: str | None = None) -> Tuple[Experiment | None, Results | None]:
    """Load Experiment and Results from yaml data.

    Args:
        path (str): Path to folder.

    Returns:
        Tuple(Experiment | None, Results | None): Return Experiment and Results objects, or None.
    """
    parsed_path = Path(path) if isinstance(path, str) else _get_last_created_experiment_path()
    experiment, results = None, None
    if os.path.exists(parsed_path / EXPERIMENT_FILENAME):
        with open(parsed_path / EXPERIMENT_FILENAME, mode="r", encoding="utf-8") as experiment_file:
            experiment = Experiment.from_dict(yaml.safe_load(stream=experiment_file))

    if os.path.exists(parsed_path / RESULTS_FILENAME):
        with open(parsed_path / RESULTS_FILENAME, mode="r", encoding="utf-8") as results_file:
            results = Results(**yaml.safe_load(stream=results_file))

    return experiment, results


def _fix_loop_keyword(yaml_loaded: dict) -> dict:
    """from a loaded yaml fixes that loop keyword is changed by loops"""
    if "loop" in yaml_loaded:
        print("fixing loop key")
        loop_value = yaml_loaded["loop"]
        del yaml_loaded["loop"]
        yaml_loaded["loops"] = [loop_value]

    return yaml_loaded


def _load_backup_results_file(path: str) -> dict:
    """Load Results generated from the versionless qililab yaml data.

    Args:
        path (str): Path to folder.
    """
    parsed_path = Path(path)
    if not os.path.exists(parsed_path / RESULTS_FILENAME_BACKUP):
        raise ValueError(f"results file {parsed_path}{RESULTS_FILENAME_BACKUP} not found!")

    with open(parsed_path / RESULTS_FILENAME_BACKUP, mode="r", encoding="utf-8") as results_file:
        return yaml.safe_load(stream=results_file)


def _load_backup_experiment_file(path: str) -> dict | None:
    """Load Experiment yaml file.

    Args:
        path (str): Path to folder.

    Returns:
        dict | None: Return an experiment data dictionary or None.
    """
    parsed_path = Path(path)
    if os.path.exists(parsed_path / EXPERIMENT_FILENAME_BACKUP):
        with open(parsed_path / EXPERIMENT_FILENAME_BACKUP, mode="r", encoding="utf-8") as experiment_file:
            return yaml.safe_load(stream=experiment_file)
    return None


def _save_file(path: str, data: dict, filename: str) -> None:
    """Save to disk the file.

    Args:
        path (str): Path to folder.
        data (dict): dictornary data to be saved
    """
    parsed_path = Path(path)
    with open(file=parsed_path / filename, mode="w", encoding="utf-8") as file:
        yaml.dump(data=data, stream=file, sort_keys=False)


def _save_experiment(path: str, data: dict) -> None:
    """Save to disk the fixed experiment file.

    Args:
        path (str): Path to folder.
        data (dict): Fixed experiment dictionary data
    """
    _save_file(path=path, data=data, filename=EXPERIMENT_FILENAME)


def _save_results(path: str, data: dict) -> None:
    """Save to disk the fixed results.

    Args:
        path (str): Path to folder.
        data (dict): Fixed results dictionary data

    Returns:
        Results: Loaded dictionary results.
    """
    _save_file(path=path, data=data, filename=RESULTS_FILENAME)


def _get_pulse_length_from_experiment_dict(experiment: dict) -> float:
    """get pulse length from the experiment dictionary"""
    if RUNCARD.PLATFORM not in experiment:
        return DEFAULT_PULSE_LENGTH
    if RUNCARD.SETTINGS not in experiment[RUNCARD.PLATFORM]:
        return DEFAULT_PULSE_LENGTH
    if RUNCARD.GATES not in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        return DEFAULT_PULSE_LENGTH
    gates: List[dict] = experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][RUNCARD.GATES]
    measurement_gates = [gate for gate in gates if gate[PULSE.NAME] == "M"]
    if len(measurement_gates) <= 0:
        return DEFAULT_PULSE_LENGTH
    measurement_gate = measurement_gates.pop()
    if PULSE.DURATION not in measurement_gate:
        return DEFAULT_PULSE_LENGTH
    return measurement_gate[PULSE.DURATION]


def _get_missing_pulse_length(path: str) -> float:
    """get the missing pulse length from either the experiment dictionary or the default one: 8000"""
    loaded_experiment = _load_backup_results_file(path=path)
    if loaded_experiment is None:
        return DEFAULT_PULSE_LENGTH
    return _get_pulse_length_from_experiment_dict(experiment=loaded_experiment)


def _one_result_pulse_length_fix(result_to_fix: dict, path: str) -> dict:
    """from a loaded results checks that pulse length exist, and fixes it when does not.
    It takes the pulse length of the measurement gate from the experiment file.
    """
    if QBLOXRESULT.PULSE_LENGTH in result_to_fix:
        return result_to_fix

    result_fixed = deepcopy(result_to_fix)
    result_fixed[QBLOXRESULT.PULSE_LENGTH] = _get_missing_pulse_length(path=path)

    return result_fixed


def _one_result_pulse_length_integration(result_to_fix: dict) -> dict:
    """from a loaded results checks that integration exist, and fixes it when does not."""
    if QBLOXRESULT.BINS not in result_to_fix:
        return result_to_fix
    if isinstance(result_to_fix[QBLOXRESULT.BINS], list):
        return result_to_fix
    if not isinstance(result_to_fix[QBLOXRESULT.BINS], dict):
        raise ValueError("bins has a type not recognized. Only list or dict are admitted.")

    result_fixed = deepcopy(result_to_fix)
    result_fixed[QBLOXRESULT.BINS] = [result_to_fix[QBLOXRESULT.BINS]]

    return result_fixed


def _fix_one_result(result_to_fix: dict, path: str) -> dict:
    """from a given result, fix the pulse length and the integration"""
    pulse_length_fixed = _one_result_pulse_length_fix(result_to_fix=result_to_fix, path=path)
    return _one_result_pulse_length_integration(result_to_fix=pulse_length_fixed)


def _fix_pulse_length(results_to_fix: dict, path: str) -> dict:
    """from a loaded results checks that pulse length exist, and fixes it when does not.
    It takes the pulse length of the measurement gate from the experiment file.
    """
    print("fixing pulse_length and integration of each result")
    if EXPERIMENT.RESULTS not in results_to_fix:
        return results_to_fix
    if results_to_fix[EXPERIMENT.RESULTS] is None or len(results_to_fix[EXPERIMENT.RESULTS]) <= 0:
        return results_to_fix
    results_fixed = deepcopy(results_to_fix)
    results_fixed[EXPERIMENT.RESULTS] = [
        _fix_one_result(result_to_fix=result_to_fix, path=path) for result_to_fix in results_to_fix[EXPERIMENT.RESULTS]
    ]
    return results_fixed


def _update_results_file_format(path: str) -> None:
    """Load and fix Results generated from the versionless qililab yaml data to the current format.

    Args:
        path (str): Path to folder.
    """

    loaded_results = _load_backup_results_file(path=path)
    results_fixed_loop = _fix_loop_keyword(yaml_loaded=loaded_results)
    results_fixed_pulse_length = _fix_pulse_length(results_to_fix=results_fixed_loop, path=path)
    _save_results(path=path, data=results_fixed_pulse_length)


def _update_experiments_file_format(path: str) -> None:
    """Load and fix Experiments generated from the versionless qililab yaml data to the current format.

    Args:
        path (str): Path to folder.
    """

    loaded_experiment = _load_backup_experiment_file(path=path)
    if loaded_experiment is None:
        return
    fixed_experiment = deepcopy(loaded_experiment)
    fixed_beta_experiment = _fix_beta_to_drag_coefficient(experiment_to_fix=fixed_experiment)
    _save_experiment(path=path, data=fixed_beta_experiment)


def _backup_results_and_experiments_files(path: str) -> None:
    """from a given result, create a backup files from results and experiment files"""
    parsed_path = Path(path)
    if os.path.exists(parsed_path / RESULTS_FILENAME):
        os.rename(parsed_path / RESULTS_FILENAME, parsed_path / RESULTS_FILENAME_BACKUP)
    if os.path.exists(parsed_path / EXPERIMENT_FILENAME):
        os.rename(parsed_path / EXPERIMENT_FILENAME, parsed_path / EXPERIMENT_FILENAME_BACKUP)


def _fix_beta_to_drag_coefficient(experiment_to_fix: dict) -> dict:
    """from a experiment data, rename beta to drag_coefficient"""
    print("fixing beta to drag_coefficient experiment")
    experiment = deepcopy(experiment_to_fix)

    if RUNCARD.PLATFORM not in experiment:
        return experiment
    if RUNCARD.SETTINGS not in experiment[RUNCARD.PLATFORM]:
        return experiment
    if "master_beta_pulse_shape" in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][PLATFORM.MASTER_DRAG_COEFFICIENT] = experiment[RUNCARD.PLATFORM][
            RUNCARD.SETTINGS
        ]["master_beta_pulse_shape"]
        del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]["master_beta_pulse_shape"]
    if PLATFORM.MASTER_DRAG_COEFFICIENT not in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][
            PLATFORM.MASTER_DRAG_COEFFICIENT
        ] = DEFAULT_MASTER_DRAG_COEFFICIENT

    if RUNCARD.GATES not in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        return experiment
    gates: List[dict] = experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][RUNCARD.GATES]
    for gate in gates:
        if EXPERIMENT.SHAPE in gate and "beta" in gate[EXPERIMENT.SHAPE]:
            gate[EXPERIMENT.SHAPE][PulseShapeSettingsName.DRAG_COEFFICIENT.value] = gate[EXPERIMENT.SHAPE]["beta"]
            del gate[EXPERIMENT.SHAPE]["beta"]
        if PulseShapeSettingsName.DRAG_COEFFICIENT.value not in gate[EXPERIMENT.SHAPE]:
            gate[EXPERIMENT.SHAPE][PulseShapeSettingsName.DRAG_COEFFICIENT.value] = PLATFORM.MASTER_DRAG_COEFFICIENT
    return experiment


def update_results_files_format(path: str) -> None:
    """Load and fix Results and Experiments to the latest library format

    Args:
        path (str): Path to folder.
    """
    _backup_results_and_experiments_files(path=path)
    _update_experiments_file_format(path=path)
    _update_results_file_format(path=path)
