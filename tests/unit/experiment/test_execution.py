"""Tests for the Experiment class."""
from unittest.mock import MagicMock, patch

import numpy as np

from qililab.experiment import Experiment
from qililab.result import Results

from ...conftest import mock_instruments


@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
@patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.execution.buses_execution.yaml.safe_dump")
@patch("qililab.execution.buses_execution.open")
@patch("qililab.experiment.experiment.open")
@patch("qililab.utils.results_data_management.os.makedirs")
@patch("qililab.instruments.qblox.qblox_module.json.dump")
@patch("qililab.instruments.qblox.qblox_module.open")
class TestExecution:
    """Unit tests checking the the execution of a platform with instruments."""

    def test_execute_method_with_nested_loop(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        nested_experiment: Experiment,
    ):
        """Test execute method with nested loops."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        nested_experiment.settings.software_average = 5
        results = nested_experiment.execute()  # type: ignore
        nested_experiment.to_dict()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert isinstance(results, Results)
        assert np.shape(results.acquisitions(mean=True))[2:5] == (2, 2, 2)
        assert np.shape(results.probabilities(mean=True))[2:5] == (2, 2, 2)
        mock_dump_0.assert_called()
        mock_dump_1.assert_called()
        mock_open_0.assert_called()
        mock_open_1.assert_called()
        mock_open_2.assert_called()
        mock_makedirs.assert_called()
        assert (
            results.ranges
            == np.array(
                [
                    nested_experiment.loops[0].range,  # type: ignore
                    nested_experiment.loops[0].loop.range,  # type: ignore
                    nested_experiment.loops[0].loop.loop.range,  # type: ignore
                ]
            )
        ).all()

    def test_execute_method_with_instruments(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        results = experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, np.ndarray)
        assert isinstance(acquisitions, np.ndarray)
        mock_dump_0.assert_called()
        mock_dump_1.assert_called()
        mock_open_0.assert_called()
        mock_open_1.assert_called()
        mock_open_2.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_from_dict_experiment(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        nested_experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        nested_experiment_dict = nested_experiment.to_dict()
        experiment = Experiment.from_dict(nested_experiment_dict)
        results = experiment.execute()
        results_2 = nested_experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert results == results_2
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, np.ndarray)
        assert isinstance(acquisitions, np.ndarray)
        mock_dump_0.assert_called()
        mock_dump_1.assert_called()
        mock_open_0.assert_called()
        mock_open_1.assert_called()
        mock_open_2.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_keyboard_interrupt(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        mock_pulsar.return_value.get_acquisitions.side_effect = KeyboardInterrupt()
        results = experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        mock_open_0.assert_called()
        mock_dump_0.assert_called()
        mock_open_1.assert_called()
        mock_dump_1.assert_not_called()
        mock_open_2.assert_not_called()
        mock_makedirs.assert_called()
