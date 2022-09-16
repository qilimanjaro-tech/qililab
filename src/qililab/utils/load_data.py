"""Load method used to load experiment and results data."""
import glob
import os
from copy import deepcopy
from pathlib import Path
from typing import List, Tuple

import numpy as np
import yaml
from tqdm import tqdm

from qililab.constants import (
    DATA,
    EXPERIMENT,
    EXPERIMENT_FILENAME,
    PLATFORM,
    PULSE,
    PULSESEQUENCE,
    PULSESEQUENCES,
    QBLOXRESULT,
    RESULTS_FILENAME,
    RUNCARD,
    SCHEMA,
)
from qililab.experiment import Experiment
from qililab.result import Results
from qililab.typings.enums import (
    Category,
    GateName,
    InstrumentControllerName,
    InstrumentName,
    NodeName,
    Parameter,
    PulseName,
    PulseShapeName,
    PulseShapeSettingsName,
    ReferenceClock,
)

RESULTS_FILENAME_BACKUP = "results_bak.yml"
EXPERIMENT_FILENAME_BACKUP = "experiment_bak.yml"
DEFAULT_PULSE_LENGTH = 8000.0
DEFAULT_MASTER_DRAG_COEFFICIENT = 0
DEFAULT_MASTER_AMPLITUDE_GATE = 1
DEFAULT_MASTER_DURATION_GATE = 100
PATH0 = "path0"
PATH1 = "path1"
THRESHOLD = "threshold"
AVG_CNT = "avg_cnt"
NUMBER_SEQUENCERS = "num_sequencers"
MAX_FILE_SIZE_200_MB = 200


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
    # print("_fix_loop_keyword")
    if "loop" in yaml_loaded:
        print("fixing loop key")
        loop_value = yaml_loaded["loop"]
        del yaml_loaded["loop"]
        yaml_loaded["loops"] = [loop_value]

    if EXPERIMENT.LOOPS in yaml_loaded:
        if isinstance(yaml_loaded[EXPERIMENT.LOOPS], list):
            return yaml_loaded
        if not isinstance(yaml_loaded[EXPERIMENT.LOOPS], dict):
            raise ValueError("loops has a type not recognized. Only list or dict are admitted.")
        print("fixing loops key")
        yaml_loaded[EXPERIMENT.LOOPS] = [yaml_loaded[EXPERIMENT.LOOPS]]

    return yaml_loaded


def _fix_bad_beta_and_amplitude_serialized(in_path: Path, in_filename: str, out_path: Path, out_filename: str) -> None:
    """fix bad beta serialized and save the file with the correct format to be loaded correctly"""
    with open(in_path / in_filename, mode="r", encoding="utf-8") as input_file, open(
        out_path / out_filename, mode="w", encoding="utf-8"
    ) as output_file:
        line_to_remove = False
        beta_found = False
        amplitude_found = False
        duration_found = False
        shape_found = False
        phase_found = False
        lines_removed = 0
        for line in input_file:
            text = line.strip("\n")
            if (beta_found or amplitude_found or duration_found) and lines_removed == 0:
                line_to_remove = True
            if beta_found and lines_removed > 0:
                line_to_remove = False
                beta_found = False
                lines_removed = 0
            if amplitude_found and "phase" in text:
                phase_found = True
            if duration_found and "shape" in text:
                shape_found = True
            if amplitude_found and phase_found:
                line_to_remove = False
                amplitude_found = False
                phase_found = False
                lines_removed = 0
            if duration_found and shape_found:
                line_to_remove = False
                duration_found = False
                shape_found = False
                lines_removed = 0
            if "beta" in text and "!!python/object/apply:qililab.typings.enums.MasterPulseShapeSettingsName" in text:
                out_text = text.replace(
                    "!!python/object/apply:qililab.typings.enums.MasterPulseShapeSettingsName",
                    "master_beta_pulse_shape",
                )
                beta_found = True
                text = out_text
            if "amplitude" in text and "!!python/object/apply:numpy.core.multiarray.scalar" in text:
                out_text = text.replace(
                    "!!python/object/apply:numpy.core.multiarray.scalar",
                    "1",
                )
                amplitude_found = True
                text = out_text
            if "duration" in text and "!!python/object/apply:numpy.core.multiarray.scalar" in text:
                out_text = text.replace(
                    "!!python/object/apply:numpy.core.multiarray.scalar",
                    "100",
                )
                duration_found = True
                text = out_text
            if not line_to_remove:
                output_file.write(text + "\n")
            if line_to_remove:
                lines_removed += 1


def _load_backup_experiment_file(path: str) -> dict:
    """Load Experiment yaml file.

    Args:
        path (str): Path to folder.

    Returns:
        dict : Return an experiment data dictionary.
    """
    # print("_load_backup_experiment_file")
    parsed_path = Path(path)
    if os.path.exists(parsed_path / EXPERIMENT_FILENAME_BACKUP):
        try:
            return _yaml_load_file(path=parsed_path, filename=EXPERIMENT_FILENAME_BACKUP)
        except yaml.constructor.ConstructorError:
            _fix_bad_beta_and_amplitude_serialized(
                in_path=parsed_path,
                in_filename=EXPERIMENT_FILENAME_BACKUP,
                out_path=parsed_path,
                out_filename="experiment_fixed.yml",
            )
            os.rename(parsed_path / EXPERIMENT_FILENAME_BACKUP, parsed_path / "experiment_original.yml")
            os.rename(parsed_path / "experiment_fixed.yml", parsed_path / EXPERIMENT_FILENAME_BACKUP)
            return _yaml_load_file(path=parsed_path, filename=EXPERIMENT_FILENAME_BACKUP)

    raise ValueError("No experiment file found")


def _fix_bad_results_serialized(in_path: Path, in_filename: str, out_path: Path, out_filename: str) -> None:
    """fix bad results serialized and save the file with the correct format to be loaded correctly"""
    with open(in_path / in_filename, mode="r", encoding="utf-8") as input_file, open(
        out_path / out_filename, mode="w", encoding="utf-8"
    ) as output_file:
        for line in input_file:
            text = line.strip("\n")
            if "-0" in text:
                print("\n ***** fixing -0\n")
                out_text = text.replace(
                    "-0",
                    "- 0",
                )
                text = out_text
            # if "0.08402540302882266" in text and "-" not in text:
            #     print("\n ***** FOUND ELEMENT\n")
            #     print(f"{text.startswith('0')}")
            #     print(f"{text.startswith('0.')}")
            #     print(text)
            #     print(text[0])
            #     print(text[1])
            if text.startswith(" 0."):
                print("\n ***** fixing starts with 0.\n")
                out_text = text.replace(
                    " 0.",
                    "      - 0.",
                )
                text = out_text
            if text.startswith(" - 0."):
                print("\n ***** fixing starts with ' - 0.'\n")
                out_text = text.replace(
                    " - 0.",
                    "      - 0.",
                )
                text = out_text
            output_file.write(text + "\n")


def _load_backup_results_file(path: str) -> dict:
    """Load Results yaml file.

    Args:
        path (str): Path to folder.

    Returns:
        dict : Return a results data dictionary.
    """

    parsed_path = Path(path)
    if os.path.exists(parsed_path / RESULTS_FILENAME_BACKUP):
        try:
            return _yaml_load_file(path=parsed_path, filename=RESULTS_FILENAME_BACKUP)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            print("\n ***** YAML ERROR **** .\n")
            _fix_bad_results_serialized(
                in_path=parsed_path,
                in_filename=RESULTS_FILENAME_BACKUP,
                out_path=parsed_path,
                out_filename="results_fixed.yml",
            )
            os.rename(parsed_path / RESULTS_FILENAME_BACKUP, parsed_path / "results_original.yml")
            os.rename(parsed_path / "results_fixed.yml", parsed_path / RESULTS_FILENAME_BACKUP)
            return _yaml_load_file(path=parsed_path, filename=RESULTS_FILENAME_BACKUP)

    raise ValueError("No results file found")


def _yaml_load_file(path: Path, filename: str) -> dict:
    """yaml load file"""
    with open(path / filename, mode="r", encoding="utf-8") as stream_file:
        return yaml.safe_load(stream=stream_file)


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
    # print(f"saving {path}/{EXPERIMENT_FILENAME}")
    _save_file(path=path, data=data, filename=EXPERIMENT_FILENAME)


def _save_results(path: str, data: dict) -> None:
    """Save to disk the fixed results.

    Args:
        path (str): Path to folder.
        data (dict): Fixed results dictionary data

    Returns:
        Results: Loaded dictionary results.
    """
    # print(f"saving {path}/{RESULTS_FILENAME}")
    _save_file(path=path, data=data, filename=RESULTS_FILENAME)


def _get_pulse_length_from_experiment_dict(experiment: dict) -> float:
    """get pulse length from the experiment dictionary"""
    # print("_get_pulse_length_from_experiment_dict")
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


def _one_result_pulse_length_fix(result_to_fix: dict, experiment_pulse_length: float) -> dict:
    """from a loaded results checks that pulse length exist, and fixes it when does not.
    It takes the pulse length of the measurement gate from the experiment file.
    """
    # print("_one_result_pulse_length_fix")
    if QBLOXRESULT.PULSE_LENGTH in result_to_fix:
        return result_to_fix

    result_fixed = result_to_fix
    result_fixed[QBLOXRESULT.PULSE_LENGTH] = experiment_pulse_length

    return result_fixed


def _one_result_pulse_length_integration(result_to_fix: dict) -> dict:
    """from a loaded results checks that integration exist, and fixes it when does not."""
    if QBLOXRESULT.BINS not in result_to_fix:
        if Parameter.INTEGRATION.value not in result_to_fix:
            return result_to_fix
        result_to_fix[QBLOXRESULT.BINS] = [
            {
                Parameter.INTEGRATION.value: result_to_fix[Parameter.INTEGRATION.value],
                "threshold": result_to_fix["threshold"],
                "avg_cnt": result_to_fix["avg_cnt"],
            },
        ]
        del result_to_fix[Parameter.INTEGRATION.value]
        del result_to_fix["threshold"]
        del result_to_fix["avg_cnt"]
        return result_to_fix

    if isinstance(result_to_fix[QBLOXRESULT.BINS], list):
        return result_to_fix
    if not isinstance(result_to_fix[QBLOXRESULT.BINS], dict):
        raise ValueError("bins has a type not recognized. Only list or dict are admitted.")

    result_fixed = result_to_fix
    result_fixed[QBLOXRESULT.BINS] = [result_to_fix[QBLOXRESULT.BINS]]

    return result_fixed


def _fix_one_result(result_to_fix: dict, experiment_pulse_length: float) -> dict:
    """from a given result, fix the pulse length, the integration and nans"""
    # print("_fix_one_result")
    pulse_length_fixed = _one_result_pulse_length_fix(
        result_to_fix=result_to_fix, experiment_pulse_length=experiment_pulse_length
    )
    integration_fixed = _one_result_pulse_length_integration(result_to_fix=pulse_length_fixed)
    return _remove_result_nans(result_to_fix=integration_fixed)


def _fix_pulse_length(results_to_fix: dict, experiment: dict) -> dict:
    """from a loaded results checks that pulse length exist, and fixes it when does not.
    It takes the pulse length of the measurement gate from the experiment file.
    """
    print("fixing pulse_length and integration of each result")

    if EXPERIMENT.RESULTS not in results_to_fix:
        return results_to_fix
    if results_to_fix[EXPERIMENT.RESULTS] is None or len(results_to_fix[EXPERIMENT.RESULTS]) <= 0:
        return results_to_fix
    results_fixed = results_to_fix

    experiment_pulse_length = _get_pulse_length_from_experiment_dict(experiment=experiment)

    results_fixed[EXPERIMENT.RESULTS] = [
        _fix_one_result(result_to_fix=result_to_fix, experiment_pulse_length=experiment_pulse_length)
        for result_to_fix in tqdm(results_to_fix[EXPERIMENT.RESULTS])
    ]
    return results_fixed


def _remove_nans_one_bin(one_bin_to_fix: dict) -> dict:
    """remove nans in one bin"""
    # print("_remove_nans_one_bin")
    one_bin_fixed = one_bin_to_fix
    if Parameter.INTEGRATION.value in one_bin_to_fix:
        if PATH0 in one_bin_to_fix[Parameter.INTEGRATION.value]:
            one_bin_fixed[Parameter.INTEGRATION.value][PATH0] = [
                value for value in one_bin_to_fix[Parameter.INTEGRATION.value][PATH0] if not np.isnan(value)
            ]
        if PATH1 in one_bin_to_fix[Parameter.INTEGRATION.value]:
            one_bin_fixed[Parameter.INTEGRATION.value][PATH1] = [
                value for value in one_bin_to_fix[Parameter.INTEGRATION.value][PATH1] if not np.isnan(value)
            ]
    if THRESHOLD in one_bin_to_fix:
        one_bin_fixed[THRESHOLD] = [value for value in one_bin_to_fix[THRESHOLD] if not np.isnan(value)]
    if AVG_CNT in one_bin_to_fix:
        one_bin_fixed[AVG_CNT] = [value for value in one_bin_to_fix[AVG_CNT] if not np.isnan(value)]
    return one_bin_fixed


def _remove_result_nans(result_to_fix: dict) -> dict:
    """remove all nans in result bins"""
    # print("_remove_result_nans")
    if QBLOXRESULT.BINS not in result_to_fix:
        return result_to_fix
    result_fixed = result_to_fix
    result_fixed[QBLOXRESULT.BINS] = [
        _remove_nans_one_bin(one_bin_to_fix=one_bin_to_fix) for one_bin_to_fix in result_to_fix[QBLOXRESULT.BINS]
    ]
    return result_fixed


def _file_greater_than_200_mb(path: str) -> bool:
    """check if file is greater than 200MB"""
    parsed_path = Path(path)
    filename = parsed_path / RESULTS_FILENAME_BACKUP
    return int(filename.stat().st_size / 1024 / 1024) > MAX_FILE_SIZE_200_MB


def _update_results_file_format(path: str, experiment: dict) -> None:
    """Load and fix Results generated from the versionless qililab yaml data to the current format.

    Args:
        path (str): Path to folder.
    """
    # print("_update_results_file_format")

    if _file_greater_than_200_mb(path=path):
        print(f"File {path}/{RESULTS_FILENAME_BACKUP} NOT PROCESSED: It is greater than 200MB.")
        return
    loaded_results = _load_backup_results_file(path=path)
    results_fixed_loop = _fix_loop_keyword(yaml_loaded=loaded_results)
    results_fixed_pulse_length = _fix_pulse_length(results_to_fix=results_fixed_loop, experiment=experiment)
    _save_results(path=path, data=results_fixed_pulse_length)


def _fix_platform_to_settings(experiment: dict) -> dict:
    """fix platform structure to contain settings"""
    if RUNCARD.PLATFORM not in experiment:
        return experiment
    if RUNCARD.PLATFORM not in experiment[RUNCARD.PLATFORM]:
        return experiment
    if RUNCARD.SETTINGS in experiment[RUNCARD.PLATFORM]:
        return experiment

    # update experiment[platform][platform]
    experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS] = experiment[RUNCARD.PLATFORM][RUNCARD.PLATFORM]
    del experiment[RUNCARD.PLATFORM][RUNCARD.PLATFORM]

    # update experiment[platform][settings][settings]
    if RUNCARD.SETTINGS not in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        return experiment
    experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS] |= experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][RUNCARD.SETTINGS]
    del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][RUNCARD.SETTINGS]

    settings: dict = experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]
    # change readout_duration, readout_amplitude and readout_phase
    if "readout_duration" in settings and "readout_amplitude" in settings and "readout_phase" in settings:
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][RUNCARD.GATES] = [
            {
                RUNCARD.NAME: GateName.M.value,
                Parameter.AMPLITUDE.value: settings["readout_amplitude"],
                Parameter.DURATION.value: settings["readout_duration"],
                Parameter.PHASE.value: settings["readout_phase"],
                EXPERIMENT.SHAPE: {RUNCARD.NAME: PulseShapeName.RECTANGULAR.value},
            }
        ]
        del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]["readout_amplitude"]
        del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]["readout_duration"]
        del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]["readout_phase"]

    # change gate_duration and drag_coefficient
    if "gate_duration" in settings and PulseShapeSettingsName.DRAG_COEFFICIENT.value in settings:
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][PLATFORM.MASTER_DURATION_GATE] = settings["gate_duration"]
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][PLATFORM.MASTER_AMPLITUDE_GATE] = settings[
            PulseShapeSettingsName.DRAG_COEFFICIENT.value
        ]
        del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]["gate_duration"]
        del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][PulseShapeSettingsName.DRAG_COEFFICIENT.value]

    # change num_sigmas
    if PulseShapeSettingsName.NUM_SIGMAS.value in settings:
        sigmas = settings[PulseShapeSettingsName.NUM_SIGMAS.value]
        del experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][PulseShapeSettingsName.NUM_SIGMAS.value]
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][RUNCARD.GATES] += [
            {
                RUNCARD.NAME: GateName.I.value,
                Parameter.AMPLITUDE.value: 0,
                Parameter.DURATION.value: PLATFORM.MASTER_DURATION_GATE,
                Parameter.PHASE.value: 0,
                EXPERIMENT.SHAPE: {RUNCARD.NAME: PulseShapeName.RECTANGULAR.value},
            },
            {
                RUNCARD.NAME: GateName.X.value,
                Parameter.AMPLITUDE.value: PLATFORM.MASTER_AMPLITUDE_GATE,
                Parameter.DURATION.value: PLATFORM.MASTER_DURATION_GATE,
                Parameter.PHASE.value: 0,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: PulseShapeName.DRAG.value,
                    PulseShapeSettingsName.NUM_SIGMAS.value: sigmas,
                    PulseShapeSettingsName.DRAG_COEFFICIENT.value: PLATFORM.MASTER_DRAG_COEFFICIENT,
                },
            },
            {
                RUNCARD.NAME: GateName.Y.value,
                Parameter.AMPLITUDE.value: PLATFORM.MASTER_AMPLITUDE_GATE,
                Parameter.DURATION.value: PLATFORM.MASTER_DURATION_GATE,
                Parameter.PHASE.value: 1.5708,
                EXPERIMENT.SHAPE: {
                    RUNCARD.NAME: PulseShapeName.DRAG.value,
                    PulseShapeSettingsName.NUM_SIGMAS.value: sigmas,
                    PulseShapeSettingsName.DRAG_COEFFICIENT.value: PLATFORM.MASTER_DRAG_COEFFICIENT,
                },
            },
        ]
    return experiment


def _fix_bus(bus: dict) -> dict:
    """fix bus structure"""
    # == BusSubcategory.CONTROL.value:
    fixed_bus = deepcopy(bus)
    if RUNCARD.AWG in bus[RUNCARD.SYSTEM_CONTROL] and RUNCARD.NAME in bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.AWG]:
        if bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.AWG][RUNCARD.NAME] == "qblox_qcm":
            fixed_bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.AWG] = InstrumentName.QBLOX_QCM.value
        if bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.AWG][RUNCARD.NAME] == "qblox_qrm":
            fixed_bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.AWG] = InstrumentName.QBLOX_QRM.value
    if (
        RUNCARD.SIGNAL_GENERATOR in bus[RUNCARD.SYSTEM_CONTROL]
        and RUNCARD.NAME in bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.SIGNAL_GENERATOR]
        and bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.SIGNAL_GENERATOR][RUNCARD.NAME] == RUNCARD.SIGNAL_GENERATOR
    ):
        if bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.SIGNAL_GENERATOR][RUNCARD.ID] == 0:
            fixed_bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.SIGNAL_GENERATOR] = "rs_0"
        if bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.SIGNAL_GENERATOR][RUNCARD.ID] == 1:
            fixed_bus[RUNCARD.SYSTEM_CONTROL][RUNCARD.SIGNAL_GENERATOR] = "rs_1"
    if (
        RUNCARD.ATTENUATOR in bus
        and RUNCARD.NAME in bus[RUNCARD.ATTENUATOR]
        and bus[RUNCARD.ATTENUATOR][RUNCARD.NAME] == InstrumentName.MINI_CIRCUITS.value
    ):
        fixed_bus[RUNCARD.ATTENUATOR] = InstrumentName.QBLOX_QCM.value
    return fixed_bus


def _fix_buses(experiment: dict) -> dict:
    """fix buses structure"""
    if RUNCARD.PLATFORM not in experiment:
        return experiment
    if RUNCARD.SCHEMA not in experiment[RUNCARD.PLATFORM]:
        return experiment
    fixed_experiment = deepcopy(experiment)
    if SCHEMA.BUSES not in experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA]:
        return experiment
    buses = experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.BUSES]
    fixed_experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.BUSES] = [_fix_bus(bus=bus) for bus in buses]
    return fixed_experiment


def _fix_pulse(pulse: dict) -> dict:
    """fix pulse structure"""
    if RUNCARD.NAME in pulse and pulse[RUNCARD.NAME] == "ReadoutPulse":
        pulse[RUNCARD.NAME] = PulseName.READOUT_PULSE.value
    if "qubit_ids" in pulse:
        del pulse["qubit_ids"]
    return pulse


def _fix_pulses_port(pulses: List[dict]) -> int:
    """fix pulses port"""
    if len(pulses) <= 0:
        return 0
    return 0 if pulses[0][RUNCARD.NAME] == PulseName.PULSE.value else 1


def _fix_sequence(sequence: dict) -> dict:
    """fix sequences structure"""
    if PULSESEQUENCES.ELEMENTS not in sequence:
        if PULSESEQUENCE.PULSES not in sequence:
            return {PULSESEQUENCES.ELEMENTS: []}
        fixed_pulses = [_fix_pulse(pulse=pulse) for pulse in sequence[PULSESEQUENCE.PULSES]]
        return {
            PULSESEQUENCES.ELEMENTS: [
                {PULSESEQUENCE.PULSES: fixed_pulses, PULSESEQUENCE.PORT: _fix_pulses_port(pulses=fixed_pulses)},
            ]
        }
    return sequence


def _fix_sequences(experiment: dict) -> dict:
    """fix sequences structure"""
    fixed_experiment = deepcopy(experiment)
    if EXPERIMENT.SEQUENCES not in experiment:
        fixed_experiment[EXPERIMENT.SEQUENCES] = []
        return fixed_experiment
    fixed_experiment[EXPERIMENT.SEQUENCES] = [
        _fix_sequence(sequence=sequence) for sequence in fixed_experiment[EXPERIMENT.SEQUENCES]
    ]
    return fixed_experiment


def _update_experiments_file_format(path: str) -> dict:
    """Load and fix Experiments generated from the versionless qililab yaml data to the current format.

    Args:
        path (str): Path to folder.
    """

    loaded_experiment = _load_backup_experiment_file(path=path)
    # print("updating experiments file")
    fixed_experiment = deepcopy(loaded_experiment)
    fixed_platform_to_settings = _fix_platform_to_settings(experiment=fixed_experiment)
    fixed_beta_experiment = _fix_beta_to_drag_coefficient(experiment_to_fix=fixed_platform_to_settings)
    fixed_master_gate_experiment = _fix_master_gate_on_platform(experiment=fixed_beta_experiment)
    fixed_instruments_experiment = _fix_instruments(experiment=fixed_master_gate_experiment)
    fixed_instrument_controllers_experiment = _fix_instrument_controllers(experiment=fixed_instruments_experiment)
    fixed_chip = _fix_chip(experiment=fixed_instrument_controllers_experiment)
    fixed_loops_experiment = _fix_loop_keyword(yaml_loaded=fixed_chip)
    fixed_buses = _fix_buses(experiment=fixed_loops_experiment)
    fixed_sequences = _fix_sequences(experiment=fixed_buses)
    _save_experiment(path=path, data=fixed_sequences)
    return fixed_experiment


def _fix_instrument_controller(instrument_controller: dict) -> dict:
    """fix an instrument_controller so it is loadable"""
    # print("_fix_instrument_controller")
    fixed_instrument_controller = instrument_controller
    if (
        fixed_instrument_controller[RUNCARD.NAME]
        in [
            InstrumentControllerName.QBLOX_PULSAR.value,
            InstrumentControllerName.QBLOX_CLUSTER.value,
        ]
        and Parameter.REFERENCE_CLOCK.value not in fixed_instrument_controller
    ):
        fixed_instrument_controller = _add_reference_clock(
            qxm_controller=fixed_instrument_controller, value=ReferenceClock.INTERNAL.value
        )
    return fixed_instrument_controller


def _add_chip_nodes_one_qubit() -> List[dict]:
    """create a chip nodes structure for a single qubit"""
    return [
        {
            RUNCARD.NAME: NodeName.PORT.value,
            RUNCARD.ID: 0,
            RUNCARD.CATEGORY: Category.NODE.value,
            RUNCARD.ALIAS: "",
            "nodes": [3],
        },
        {
            RUNCARD.NAME: NodeName.PORT.value,
            RUNCARD.ID: 1,
            RUNCARD.CATEGORY: Category.NODE.value,
            RUNCARD.ALIAS: "",
            "nodes": [2],
        },
        {
            RUNCARD.NAME: NodeName.RESONATOR.value,
            RUNCARD.ID: 2,
            RUNCARD.CATEGORY: Category.NODE.value,
            RUNCARD.ALIAS: NodeName.RESONATOR.value,
            "nodes": [1, 3],
            Parameter.FREQUENCY.value: 7.32644e09,
        },
        {
            RUNCARD.NAME: NodeName.QUBIT.value,
            RUNCARD.ID: 3,
            RUNCARD.CATEGORY: Category.NODE.value,
            RUNCARD.ALIAS: NodeName.QUBIT.value,
            "nodes": [0, 2],
            Parameter.FREQUENCY.value: 3.351e09,
            "qubit_idx": 0,
        },
    ]


def _fix_chip(experiment: dict) -> dict:
    """fix the chip section so it is loadable"""
    if RUNCARD.PLATFORM not in experiment:
        return experiment
    if RUNCARD.SCHEMA not in experiment[RUNCARD.PLATFORM]:
        return experiment
    fixed_experiment = deepcopy(experiment)
    if SCHEMA.CHIP not in fixed_experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA]:
        fixed_experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.CHIP] = {
            RUNCARD.ID: 0,
            RUNCARD.CATEGORY: SCHEMA.CHIP,
            "nodes": _add_chip_nodes_one_qubit(),
        }
        return fixed_experiment
    return fixed_experiment


def _fix_instrument_controllers(experiment: dict) -> dict:
    """fix the instrument controllers section so it is loadable"""
    # print("_fix_instrument_controllers")
    if RUNCARD.PLATFORM not in experiment:
        return experiment
    if RUNCARD.SCHEMA not in experiment[RUNCARD.PLATFORM]:
        return experiment
    fixed_experiment = deepcopy(experiment)
    if SCHEMA.INSTRUMENT_CONTROLLERS not in fixed_experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA]:
        fixed_experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.INSTRUMENT_CONTROLLERS] = []
        return fixed_experiment

    instrument_controllers: List[dict] = experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.INSTRUMENT_CONTROLLERS]
    fixed_experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.INSTRUMENT_CONTROLLERS] = [
        _fix_instrument_controller(instrument_controller=instrument_controller)
        for instrument_controller in instrument_controllers
    ]
    return fixed_experiment


def _backup_results_and_experiments_files(path: str) -> None:
    """from a given result, create a backup files from results and experiment files"""
    # print("_backup_results_and_experiments_files")
    parsed_path = Path(path)
    if os.path.exists(parsed_path / RESULTS_FILENAME) and not os.path.exists(parsed_path / RESULTS_FILENAME_BACKUP):
        os.rename(parsed_path / RESULTS_FILENAME, parsed_path / RESULTS_FILENAME_BACKUP)
    if os.path.exists(parsed_path / EXPERIMENT_FILENAME) and not os.path.exists(
        parsed_path / EXPERIMENT_FILENAME_BACKUP
    ):
        os.rename(parsed_path / EXPERIMENT_FILENAME, parsed_path / EXPERIMENT_FILENAME_BACKUP)


def _add_num_bins(qxm: dict) -> dict:
    """add num bins on a QCM or QRM instrument"""
    if Parameter.NUM_BINS.value not in qxm:
        qxm[Parameter.NUM_BINS.value] = 1
    return qxm


def _add_integration(qxm: dict) -> dict:
    """add integration on a QRM instrument"""
    if Parameter.INTEGRATION_LENGTH.value in qxm and Parameter.INTEGRATION.value not in qxm:
        qxm[Parameter.INTEGRATION.value] = True
    return qxm


def _add_reference_clock(qxm_controller: dict, value: str) -> dict:
    """add reference clock on a QCM or QRM instrument controller"""
    # print("_add_reference_clock")
    qxm_controller[Parameter.REFERENCE_CLOCK.value] = value
    return qxm_controller


def _remove_reference_clock(qxm: dict) -> dict:
    """remove reference clock on a QCM or QRM instrument"""
    # print("_remove_reference_clock")
    if Parameter.REFERENCE_CLOCK.value in qxm:
        del qxm[Parameter.REFERENCE_CLOCK.value]
    return qxm


def _update_sequencer_number(qxm: dict) -> dict:
    """updates sequencer number reference"""
    # print("_update_sequencer_number")
    if "sequencer" in qxm:
        qxm[NUMBER_SEQUENCERS] = 1
        del qxm["sequencer"]
    return qxm


def _update_acquire_trigger_mode(qxm: dict) -> dict:
    """updates acquire trigger mode reference"""
    # print("_update_acquire_trigger_mode")
    if "acquire_trigger_mode" in qxm:
        qxm["scope_acquire_trigger_mode"] = qxm["acquire_trigger_mode"]
        del qxm["acquire_trigger_mode"]
    return qxm


def _update_hardware_averaging(qxm: dict) -> dict:
    """updates hardware_averaging reference"""
    # print("_update_hardware_averaging")
    if "hardware_averaging" in qxm:
        qxm["scope_hardware_averaging"] = qxm["hardware_averaging"]
        del qxm["hardware_averaging"]
    return qxm


def _update_delay_time(qxm: dict) -> dict:
    """updates delay time reference"""
    if "delay_time" in qxm:
        qxm[Parameter.ACQUISITION_DELAY_TIME.value] = qxm["delay_time"]
        del qxm["delay_time"]
    return qxm


def _update_scope_acquisition_averaging(qxm: dict) -> dict:
    """updates scope_acquisition_averaging reference"""
    if "scope_acquisition_averaging" in qxm:
        qxm["scope_hardware_averaging"] = qxm["scope_acquisition_averaging"]
        del qxm["scope_acquisition_averaging"]
    return qxm


def _remove_connection_ip(instrument: dict) -> dict:
    """remove connection ip from an instrument"""
    # print("_remove_connection_ip")
    if "ip" in instrument:
        del instrument["ip"]
    return instrument


def _remove_frequency(instrument: dict) -> dict:
    """remove frequency reference"""
    if Parameter.FREQUENCY.value in instrument:
        del instrument[Parameter.FREQUENCY.value]
    return instrument


def _remove_acquisition_name(qxm: dict) -> dict:
    """remove acquisition_name reference"""
    if "acquisition_name" in qxm:
        del qxm["acquisition_name"]
    return qxm


def _update_sequencer_params(qxm: dict, key: str) -> dict:
    """update sequencer params: gain, epsilon, delta, offset_i, offset_q"""
    # print("_update_sequencer_params")
    if key in qxm and not isinstance(qxm[key], list):
        qxm[key] = [qxm[key]]
    return qxm


def _fix_instrument_alias(instrument: dict, alias: str) -> dict:
    """add instrument alias when not set"""
    if RUNCARD.ALIAS not in instrument:
        instrument[RUNCARD.ALIAS] = alias
    return instrument


def _fix_instrument(instrument: dict) -> dict:
    """fix an instrument so it is loadable"""
    # print("_fix_instrument")
    fixed_instrument = instrument
    if fixed_instrument[RUNCARD.NAME] == "qblox_qcm":
        fixed_instrument[RUNCARD.NAME] = InstrumentName.QBLOX_QCM.value
    if fixed_instrument[RUNCARD.NAME] == "qblox_qrm":
        fixed_instrument[RUNCARD.NAME] = InstrumentName.QBLOX_QRM.value
    if fixed_instrument[RUNCARD.NAME] in [
        InstrumentName.QBLOX_QCM.value,
        InstrumentName.QBLOX_QRM.value,
    ]:
        fixed_instrument = _remove_reference_clock(qxm=fixed_instrument)
        fixed_instrument = _update_sequencer_number(qxm=fixed_instrument)
        fixed_instrument = _update_acquire_trigger_mode(qxm=fixed_instrument)
        fixed_instrument = _update_hardware_averaging(qxm=fixed_instrument)
        fixed_instrument = _update_sequencer_params(qxm=fixed_instrument, key="gain")
        fixed_instrument = _update_sequencer_params(qxm=fixed_instrument, key="epsilon")
        fixed_instrument = _update_sequencer_params(qxm=fixed_instrument, key="delta")
        fixed_instrument = _update_sequencer_params(qxm=fixed_instrument, key="offset_i")
        fixed_instrument = _update_sequencer_params(qxm=fixed_instrument, key="offset_q")
        fixed_instrument = _add_num_bins(qxm=fixed_instrument)
        fixed_instrument = _update_delay_time(qxm=fixed_instrument)
        fixed_instrument = _update_scope_acquisition_averaging(qxm=fixed_instrument)
        fixed_instrument = _remove_acquisition_name(qxm=fixed_instrument)
        fixed_instrument = _add_integration(qxm=fixed_instrument)
        fixed_instrument = _fix_instrument_alias(instrument=fixed_instrument, alias=fixed_instrument[RUNCARD.NAME])
    if fixed_instrument[RUNCARD.NAME] == InstrumentName.ROHDE_SCHWARZ.value:
        fixed_instrument = _remove_frequency(instrument=fixed_instrument)
        fixed_instrument = _fix_instrument_alias(
            instrument=fixed_instrument, alias=f"rs_{fixed_instrument[RUNCARD.ID]}"
        )
    if fixed_instrument[RUNCARD.NAME] == InstrumentName.MINI_CIRCUITS.value:
        fixed_instrument = _fix_instrument_alias(instrument=fixed_instrument, alias=RUNCARD.ATTENUATOR)
    fixed_instrument = _remove_connection_ip(instrument=fixed_instrument)
    return fixed_instrument


def _fix_instruments(experiment: dict) -> dict:
    """fix the instrument section so it is loadable"""
    # print("_fix_instruments")
    if RUNCARD.PLATFORM not in experiment:
        return experiment
    if RUNCARD.SCHEMA not in experiment[RUNCARD.PLATFORM]:
        return experiment
    if SCHEMA.INSTRUMENTS not in experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA]:
        return experiment
    fixed_experiment = deepcopy(experiment)
    instruments: List[dict] = experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.INSTRUMENTS]
    fixed_experiment[RUNCARD.PLATFORM][RUNCARD.SCHEMA][SCHEMA.INSTRUMENTS] = [
        _fix_instrument(instrument=instrument) for instrument in instruments
    ]
    return fixed_experiment


def _fix_master_gate_on_platform(experiment: dict) -> dict:
    """from a experiment data, add master amplitude and duration on the platform section"""
    # print("_fix_master_gate_on_platform")
    if RUNCARD.PLATFORM not in experiment:
        return experiment
    if RUNCARD.SETTINGS not in experiment[RUNCARD.PLATFORM]:
        return experiment
    if PLATFORM.MASTER_AMPLITUDE_GATE not in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][PLATFORM.MASTER_AMPLITUDE_GATE] = DEFAULT_MASTER_AMPLITUDE_GATE
    if PLATFORM.MASTER_DURATION_GATE not in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][PLATFORM.MASTER_DURATION_GATE] = DEFAULT_MASTER_DURATION_GATE
    return experiment


def _fix_beta_to_drag_coefficient_on_platform(experiment: dict) -> dict:
    """from a experiment data, rename beta to drag_coefficient on the platform section"""
    # print("_fix_beta_to_drag_coefficient_on_platform")
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
    return experiment


def _fix_beta_to_drag_coefficient_on_gates(experiment: dict) -> dict:
    """from a experiment data, rename beta to drag_coefficient on the gates section"""
    # print("_fix_beta_to_drag_coefficient_on_gates")
    if RUNCARD.GATES not in experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS]:
        return experiment
    gates: List[dict] = experiment[RUNCARD.PLATFORM][RUNCARD.SETTINGS][RUNCARD.GATES]
    for gate in gates:
        if EXPERIMENT.SHAPE in gate and "beta" in gate[EXPERIMENT.SHAPE]:
            if isinstance(gate[EXPERIMENT.SHAPE]["beta"], str) and "beta" in gate[EXPERIMENT.SHAPE]["beta"]:
                gate[EXPERIMENT.SHAPE]["beta"] = PLATFORM.MASTER_DRAG_COEFFICIENT
            gate[EXPERIMENT.SHAPE][PulseShapeSettingsName.DRAG_COEFFICIENT.value] = gate[EXPERIMENT.SHAPE]["beta"]
            del gate[EXPERIMENT.SHAPE]["beta"]
        if (
            EXPERIMENT.SHAPE in gate
            and gate[EXPERIMENT.SHAPE][RUNCARD.NAME] == PulseShapeName.DRAG.value
            and PulseShapeSettingsName.DRAG_COEFFICIENT.value not in gate[EXPERIMENT.SHAPE]
        ):
            gate[EXPERIMENT.SHAPE][PulseShapeSettingsName.DRAG_COEFFICIENT.value] = PLATFORM.MASTER_DRAG_COEFFICIENT
    return experiment


def _fix_beta_to_drag_coefficient_on_pulses(experiment: dict) -> dict:
    """from a experiment data, rename beta to drag_coefficient on the pulses section"""
    # print("_fix_beta_to_drag_coefficient_on_pulses")
    if EXPERIMENT.SEQUENCES not in experiment:
        return experiment
    pulse_sequences: List[dict] = experiment[EXPERIMENT.SEQUENCES]
    for pulse_sequence in pulse_sequences:
        if PULSESEQUENCES.ELEMENTS not in pulse_sequence:
            continue
        elements: List[dict] = pulse_sequence[PULSESEQUENCES.ELEMENTS]
        for element in elements:
            if PULSESEQUENCE.PULSES not in element:
                continue
            pulses: List[dict] = element[PULSESEQUENCE.PULSES]
            for pulse in pulses:
                if PULSE.PULSE_SHAPE in pulse and "beta" in pulse[PULSE.PULSE_SHAPE]:
                    if isinstance(pulse[PULSE.PULSE_SHAPE]["beta"], str) and "beta" in pulse[PULSE.PULSE_SHAPE]["beta"]:
                        pulse[PULSE.PULSE_SHAPE]["beta"] = PLATFORM.MASTER_DRAG_COEFFICIENT
                    pulse[PULSE.PULSE_SHAPE][PulseShapeSettingsName.DRAG_COEFFICIENT.value] = pulse[PULSE.PULSE_SHAPE][
                        "beta"
                    ]
                    del pulse[PULSE.PULSE_SHAPE]["beta"]
                if (
                    PULSE.PULSE_SHAPE in pulse
                    and pulse[PULSE.PULSE_SHAPE][RUNCARD.NAME] == PulseShapeName.DRAG.value
                    and "master_beta_pulse_shape" in pulse[PULSE.PULSE_SHAPE]
                ):
                    pulse[PULSE.PULSE_SHAPE][PulseShapeSettingsName.DRAG_COEFFICIENT.value] = pulse[PULSE.PULSE_SHAPE][
                        "master_beta_pulse_shape"
                    ]
                    del pulse[PULSE.PULSE_SHAPE]["master_beta_pulse_shape"]
                if (
                    PULSE.PULSE_SHAPE in pulse
                    and pulse[PULSE.PULSE_SHAPE][RUNCARD.NAME] == PulseShapeName.DRAG.value
                    and "master_beta_pulse_shape" not in pulse[PULSE.PULSE_SHAPE]
                ):
                    pulse[PULSE.PULSE_SHAPE][PulseShapeSettingsName.DRAG_COEFFICIENT.value] = experiment[
                        RUNCARD.PLATFORM
                    ][RUNCARD.SETTINGS][PLATFORM.MASTER_DRAG_COEFFICIENT]
    return experiment


def _fix_beta_to_drag_coefficient(experiment_to_fix: dict) -> dict:
    """from a experiment data, rename beta to drag_coefficient"""
    print("fixing beta to drag_coefficient experiment")
    experiment = experiment_to_fix
    experiment = _fix_beta_to_drag_coefficient_on_platform(experiment=experiment)
    experiment = _fix_beta_to_drag_coefficient_on_gates(experiment=experiment)
    return _fix_beta_to_drag_coefficient_on_pulses(experiment=experiment)


def update_results_files_format(path: str) -> None:
    """Load and fix Results and Experiments to the latest library format

    Args:
        path (str): Path to folder.
    """
    _backup_results_and_experiments_files(path=path)
    fixed_experiment = _update_experiments_file_format(path=path)
    _update_results_file_format(path=path, experiment=fixed_experiment)
