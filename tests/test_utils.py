"""Module containing utilities for the tests."""

import copy
import math
from unittest.mock import MagicMock, patch

import numpy as np
from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import KeithleyChannel
from qpysequence import Sequence as QPySequence
from qpysequence.program import Program as QPyProgram
from ruamel.yaml import YAML

import qililab as ql
from qililab.platform import Platform


def mock_instruments(mock_rs: MagicMock, mock_pulsar: MagicMock, mock_keithley: MagicMock):
    """Mock dynamically created attributes."""
    mock_rs_instance = mock_rs.return_value
    mock_rs_instance.mock_add_spec(["power", "frequency", "ref_osc_source"])
    mock_pulsar_instance = mock_pulsar.return_value
    mock_pulsar_instance.get_acquisitions.side_effect = lambda sequencer: copy.deepcopy(
        {
            "acq_q0_0": {
                "index": 0,
                "acquisition": {
                    "scope": {
                        "path0": {"data": [1, 1, 1, 1, 1, 1, 1, 1], "out-of-range": False, "avg_cnt": 1},
                        "path1": {"data": [0, 0, 0, 0, 0, 0, 0, 0], "out-of-range": False, "avg_cnt": 1},
                    },
                    "bins": {
                        "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                        "threshold": [0],
                        "avg_cnt": [1],
                    },
                },
            }
        }
    )
    mock_pulsar_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "out0_offset",
            "out1_offset",
            "out2_offset",
            "out3_offset",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "sequencers",
            "scope_acq_sequencer_select",
            "get_acquisitions",
            "disconnect_outputs",
            "disconnect_inputs",
        ]
    )
    mock_pulsar_instance.sequencer0.mock_add_spec(
        [
            "sync_en",
            "gain_awg_path0",
            "gain_awg_path1",
            "sequence",
            "mod_en_awg",
            "nco_freq",
            "scope_acq_sequencer_select",
            "channel_map_path0_out0_en",
            "channel_map_path1_out1_en",
            "demod_en_acq",
            "integration_length_acq",
            "mixer_corr_phase_offset_degree",
            "mixer_corr_gain_ratio",
        ]
    )
    mock_keithley_instance = mock_keithley.return_value
    mock_keithley_instance.smua = MagicMock(KeithleyChannel)
    mock_keithley_instance.smua.mock_add_spec(["limiti", "limitv", "doFastSweep"])


def name_generator(base: str):
    """Unique name generator
    Args:
        base (str): common name for all the elements.
    Yields:
        str: Unique name in the format base_id.
    """
    next_id = 0
    while True:
        yield f"{base}_{next_id!s}"
        next_id += 1


def compare_pair_of_arrays(
    pair_a: tuple[list[float], list[float]],
    pair_b: tuple[list[float], list[float]],
    tolerance: float,
) -> bool:
    """Compares two pairs of arrays of the same length up to a given tolerance.

    Args:
        pair_a (tuple[list[float], list[float]]): First pair of arrays.
        pair_b (tuple[list[float], list[float]]): Second pair of arrays.
        tolerance (float): Absolute amount up to which the arrays can differ to be considered equal.

    Returns:
        bool: True if the arrays are equal up to the given tolerance, False otherwise.
    """
    path0_ok = all(np.isclose(pair_a[0], pair_b[0], atol=tolerance))
    path1_ok = all(np.isclose(pair_a[1], pair_b[1], atol=tolerance))
    return path0_ok and path1_ok


def compare_objects(obj1, obj2, path="root", depth=0, max_depth=10) -> tuple[bool, list[str]]:
    """Recursively compare two objects' properties up to a maximum depth.

    Args:
        obj1: First object.
        obj2: Second object.
        path (str): Path of the current branch, used to locate differences in the report.
        depth (int): Current recursion depth.
        max_depth (int): Depth beyond which branches are considered equal.

    Returns:
        tuple[bool, list[str]]: True if the objects are equal, and the list of differences found.
    """
    differences = []

    if depth > max_depth:
        return True, []

    if type(obj1) is not type(obj2):
        differences.append(f"{path}: type mismatch ({type(obj1).__name__} vs {type(obj2).__name__})")
        return False, differences

    # Numpy arrays would reach the fallback below as element-wise comparisons and raise on `!=`.
    if isinstance(obj1, np.ndarray):
        if obj1.dtype != obj2.dtype:
            differences.append(f"{path}: dtype mismatch ({obj1.dtype} vs {obj2.dtype})")
        if obj1.shape != obj2.shape:
            differences.append(f"{path}: shape mismatch ({obj1.shape} vs {obj2.shape})")
        elif not np.array_equal(obj1, obj2, equal_nan=np.issubdtype(obj1.dtype, np.floating)):
            differences.append(f"{path}: {obj1!r} != {obj2!r}")
        return len(differences) == 0, differences

    if isinstance(obj1, (int, float, complex, str, bool, bytes, type(None))):
        if isinstance(obj1, float) and math.isnan(obj1) and math.isnan(obj2):
            return True, differences
        if obj1 != obj2:
            differences.append(f"{path}: {obj1!r} != {obj2!r}")
        return obj1 == obj2, differences

    if isinstance(obj1, (list, tuple)):
        if len(obj1) != len(obj2):
            differences.append(f"{path}: length mismatch ({len(obj1)} vs {len(obj2)})")
        for i, (a, b) in enumerate(zip(obj1, obj2)):
            _, diffs = compare_objects(a, b, path=f"{path}[{i}]", depth=depth + 1, max_depth=max_depth)
            differences.extend(diffs)
        return len(differences) == 0, differences

    if isinstance(obj1, dict):
        keys1, keys2 = set(obj1.keys()), set(obj2.keys())
        for k in keys1 - keys2:
            differences.append(f"{path}[{k!r}]: key only in first object")
        for k in keys2 - keys1:
            differences.append(f"{path}[{k!r}]: key only in second object")
        for k in keys1 & keys2:
            _, diffs = compare_objects(obj1[k], obj2[k], path=f"{path}[{k!r}]", depth=depth + 1, max_depth=max_depth)
            differences.extend(diffs)
        return len(differences) == 0, differences

    if hasattr(obj1, "__dict__"):
        attrs1, attrs2 = set(vars(obj1).keys()), set(vars(obj2).keys())
        for attr in attrs1 - attrs2:
            differences.append(f"{path}.{attr}: attribute only in first object")
        for attr in attrs2 - attrs1:
            differences.append(f"{path}.{attr}: attribute only in second object")
        for attr in attrs1 & attrs2:
            _, diffs = compare_objects(
                getattr(obj1, attr), getattr(obj2, attr), path=f"{path}.{attr}", depth=depth + 1, max_depth=max_depth
            )
            differences.extend(diffs)
        return len(differences) == 0, differences

    if obj1 != obj2:
        differences.append(f"{path}: {obj1!r} != {obj2!r}")
    return obj1 == obj2, differences


def complete_array(array: list[float], filler: float, final_length: int) -> list[float]:
    """Fills a given array with the given float as a filler up to the final_length specified.

    Args:
        array (list[float]): Original array.
        filler (float): Number to use as a filler.
        final_length (int): Final length of the array.

    Returns:
        list[float]: List of length `final_length` where the first `len(array)` elements are those of the original
            array, and the remaining elements are are repetitions of `filler`.
    """
    return array + [filler] * (final_length - len(array))


dummy_qrm_name_generator = name_generator("dummy_qrm")
dummy_qcm_name_generator = name_generator("dummy_qcm")


def build_platform(runcard: dict) -> Platform:
    """Return PlatformBuilderDB instance with loaded platform."""
    runcard_copy = copy.deepcopy(runcard)
    real_yaml_load = YAML.load

    def patched_yaml_load(self, stream):
        # Only intercept the runcard file load; let other YAML deserializations run normally
        if isinstance(stream, MagicMock):
            return runcard_copy
        return real_yaml_load(self, stream)

    with patch("ruamel.yaml.YAML.load", side_effect=patched_yaml_load, autospec=True) as mock_load:
        with patch("qililab.data_management.open") as mock_open:
            pl = ql.build_platform(runcard="_")
            mock_load.assert_called()
            mock_open.assert_called()
    return pl


def is_q1asm_equal(a: str | QPySequence | QPyProgram, b: str | QPySequence | QPyProgram) -> bool:
    if isinstance(a, QPySequence):
        a = str(a._program)
    elif isinstance(a, QPyProgram):
        a = str(a)

    if isinstance(b, QPySequence):
        b = str(b._program)
    elif isinstance(b, QPyProgram):
        b = str(b)
    return "".join(a.strip().split()) == "".join(b.strip().split())
