"""Test experiment."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.pulse import Pulse, PulseSequences, ReadoutPulse
from qililab.pulse.pulse_shape import Drag
from qililab.result import QbloxResult

from ..utils.side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="experiment")
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_experiment(mock_load: MagicMock):
    """Return Experiment object."""
    pulse_sequence = PulseSequences(delay_between_pulses=0, delay_before_readout=50)
    pulse_sequence.add(Pulse(amplitude=1, phase=0, pulse_shape=Drag(num_sigmas=4, beta=1), duration=50, qubit_ids=[0]))
    pulse_sequence.add(ReadoutPulse(amplitude=1, phase=0, duration=50, qubit_ids=[0]))

    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=[pulse_sequence, pulse_sequence])
    mock_load.assert_called()
    return experiment


class TestExperiment:
    """Unit tests checking the Experiment attributes and methods"""

    def test_platform_attribute_instance(self, experiment: Experiment):
        """Test platform attribute instance."""
        assert isinstance(experiment.platform, Platform)

    def test_execution_attribute_instance(self, experiment: Experiment):
        """Test execution attribute instance."""
        assert isinstance(experiment.execution, Execution)

    @patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
    @patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
    def test_execute_method(self, mock_rs: MagicMock, mock_pulsar: MagicMock, experiment: Experiment):
        """Test run method."""
        # add dynamically created attributes
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
                            "integration": {"path0": [1, 1, 1, 1], "path1": [0, 0, 0, 0]},
                            "threshold": [0.5, 0.5, 0.5, 0.5],
                            "avg_cnt": [1000, 1000, 1000, 1000],
                        },
                    },
                }
            }
        )
        mock_pulsar_instance.mock_add_spec(
            [
                "reference_source",
                "sequencer0",
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
            ]
        )
        experiment.add_parameter_to_loop(
            category="signal_generator", id_=1, parameter="frequency", start=3544000000, stop=3744000000, num=500
        )
        results = experiment.execute()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, list)
        assert isinstance(results[0][0], QbloxResult)
        assert isinstance(results[0][0].results[0], QbloxResult.QbloxAcquisitions)

    def test_draw_method(self, experiment: Experiment):
        """Test draw method"""
        experiment.draw()
