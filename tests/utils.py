"""Module containing utilities for the tests."""
import copy
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import numpy as np
from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import KeithleyChannel

from qililab import build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.platform import Platform


def mock_instruments(mock_rs: MagicMock, mock_pulsar: MagicMock, mock_keithley: MagicMock):
    """Mock dynamically created attributes."""
    mock_rs_instance = mock_rs.return_value
    mock_rs_instance.mock_add_spec(["power", "frequency"])
    mock_pulsar_instance = mock_pulsar.return_value
    mock_pulsar_instance.get_acquisitions.side_effect = lambda sequencer: copy.deepcopy(
        {
            "default": {
                "index": 0,
                "acquisition": {
                    "scope": {
                        "path0": {"data": [1, 1, 1, 1, 1, 1, 1, 1], "out-of-range": False, "avg_cnt": 1000},
                        "path1": {"data": [0, 0, 0, 0, 0, 0, 0, 0], "out-of-range": False, "avg_cnt": 1000},
                    },
                    "bins": {
                        "integration": {"path0": [-0.08875841551660968], "path1": [-0.4252879595139228]},
                        "threshold": [0.48046875],
                        "avg_cnt": [1024],
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
        yield f"{base}_{str(next_id)}"
        next_id += 1


def compare_pair_of_arrays(
    pair_a: Tuple[List[float], List[float]],
    pair_b: Tuple[List[float], List[float]],
    tolerance: float,
) -> bool:
    """Compares two pairs of arrays of the same length up to a given tolerance.

    Args:
        pair_a (Tuple[List[float], List[float]]): First pair of arrays.
        pair_b (Tuple[List[float], List[float]]): Second pair of arrays.
        tolerance (float): Absolute amount up to which the arrays can differ to be considered equal.

    Returns:
        bool: True if the arrays are equal up to the given tolerance, False otherwise.
    """
    path0_ok = all(np.isclose(pair_a[0], pair_b[0], atol=tolerance))
    path1_ok = all(np.isclose(pair_a[1], pair_b[1], atol=tolerance))
    return path0_ok and path1_ok


def complete_array(array: List[float], filler: float, final_length: int) -> List[float]:
    """Fills a given array with the given float as a filler up to the final_length specified.

    Args:
        array (List[float]): Original array.
        filler (float): Number to use as a filler.
        final_length (int): Final length of the array.

    Returns:
        List[float]: List of length `final_length` where the first `len(array)` elements are those of the original
            array, and the remaining elements are are repetitions of `filler`.
    """
    return array + [filler] * (final_length - len(array))


dummy_qrm_name_generator = name_generator("dummy_qrm")
dummy_qcm_name_generator = name_generator("dummy_qcm")


def platform_db(runcard: dict) -> Platform:
    """Return PlatformBuilderDB instance with loaded platform."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name=DEFAULT_PLATFORM_NAME)
            mock_load.assert_called()
            mock_open.assert_called()
    return platform


def platform_yaml(runcard: dict) -> Platform:
    """Return PlatformBuilderYAML instance with loaded platform."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform
