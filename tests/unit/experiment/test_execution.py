"""Test execution."""
from unittest.mock import MagicMock, patch

import pytest

from qililab.constants import DEFAULT_EXPERIMENT_NAME, DEFAULT_PLATFORM_NAME
from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.typings import Category

from ..utils.side_effect import yaml_safe_load_side_effect


@patch("qililab.settings.settings_manager.yaml.safe_load", return_value=yaml_safe_load_side_effect)
@pytest.fixture(name="experiment")
def fixture_experiment():
    """Return Experiment object."""
    return Experiment(platform_name=DEFAULT_PLATFORM_NAME, experiment_name=DEFAULT_EXPERIMENT_NAME)


@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
@patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
def connect_instruments(mock_rs: MagicMock, mock_pulsar: MagicMock, execution: Execution):
    """Return connected platform"""
    # add dynamically created attributes
    mock_rs_instance = mock_rs.return_value
    mock_rs_instance.mock_add_spec(["power", "frequency"])
    mock_pulsar_instance = mock_pulsar.return_value
    mock_pulsar_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
        ]
    )
    mock_pulsar_instance.sequencer0.mock_add_spec(["sync_en", "gain_awg_path0", "gain_awg_path1", "sequence"])
    execution.connect()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return execution


class TestExecution:
    """Unit tests checking the Execution attributes and methods"""

    def test_setup_method(self, experiment: Experiment):
        """Test setup method."""
        connect_instruments(execution=experiment.execution)  # pylint: disable=no-value-for-parameter
        experiment.execution.setup(settings=experiment.settings)
        experiment.execution.close()
        platform = experiment.platform
        # assert that the class attributes of different instruments are equal to the platform settings
        i_0, _ = platform.get_element(category=Category.QUBIT_INSTRUMENT, id_=0)
        i_1, _ = platform.get_element(category=Category.QUBIT_INSTRUMENT, id_=1)
        assert i_0.hardware_average == i_1.hardware_average == experiment.settings.hardware_average
        assert i_0.software_average == i_1.software_average == experiment.settings.software_average
        assert i_0.delay_between_pulses == i_1.delay_between_pulses == experiment.settings.delay_between_pulses
        assert i_0.repetition_duration == i_1.repetition_duration == experiment.settings.repetition_duration

    def test_connect_method_raises_error_when_already_connected(self, experiment: Experiment):
        """Test connect method raises error when already connected."""
        connect_instruments(execution=experiment.execution)  # pylint: disable=no-value-for-parameter
        with pytest.raises(ValueError):
            experiment.execution.connect()
        experiment.execution.close()
