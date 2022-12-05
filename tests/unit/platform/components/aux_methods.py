""" Auxiliary methods """
import copy
from unittest.mock import MagicMock, patch

from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import KeithleyChannel

from qililab import build_platform
from qililab.platform import Buses

from ....data import Galadriel


def buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform.buses


def mock_instruments(mock_rs: MagicMock, mock_pulsar: MagicMock, mock_keithley: MagicMock):
    """Mock dynamically created attributes."""
    mock_rs_instance = mock_rs.return_value
    mock_rs_instance.mock_add_spec(["power", "frequency"])
    mock_pulsar_instance = mock_pulsar.return_value
    mock_pulsar_instance.get_acquisitions.side_effect = lambda sequencer: copy.deepcopy(
        {
            "single": {
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
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "sequencers",
            "scope_acq_sequencer_select",
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
