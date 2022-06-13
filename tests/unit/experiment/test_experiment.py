"""Tests for the Experiment class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.core.circuit import Circuit
from qibo.gates import M
from qiboconnection.api import API

from qililab import build_platform
from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.result import Results
from qililab.typings import Category, Parameter

from ...conftest import mock_instruments
from ...utils import yaml_safe_load_side_effect


class TestExperiment:
    """Unit tests checking the Experiment attributes and methods"""

    def test_platform_attribute_instance(self, experiment: Experiment):
        """Test platform attribute instance."""
        assert isinstance(experiment.platform, Platform)

    def test_execution_attribute_instance(self, experiment: Experiment):
        """Test execution attribute instance."""
        assert isinstance(experiment.execution, Execution)

    def test_parameters_property(self, experiment: Experiment):
        """Test parameters property."""
        assert isinstance(experiment.parameters, str)

    def test_software_average_property(self, experiment: Experiment):
        """Test software_average property."""
        assert experiment.software_average == experiment.settings.software_average

    def test_hardware_average_property(self, experiment: Experiment):
        """Test hardware_average property."""
        assert experiment.hardware_average == experiment.settings.hardware_average

    def test_repetition_duration_property(self, experiment: Experiment):
        """Test repetition_duration property."""
        assert experiment.repetition_duration == experiment.settings.repetition_duration

    def test_to_dict_method(self, experiment_all_platforms: Experiment):
        """Test to_dict method."""
        dictionary = experiment_all_platforms.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, experiment_all_platforms: Experiment):
        """Test from_dict method."""
        dictionary = experiment_all_platforms.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_from_dict_method_loop(self, nested_experiment: Experiment):
        """Test from_dict method with an experiment with a nested loop."""
        dictionary = nested_experiment.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_draw_method(self, experiment_all_platforms: Experiment):
        """Test draw metho."""
        experiment_all_platforms.draw()

    def test_loop_num_loops_property(self, experiment_all_platforms: Experiment):
        """Test loop's num_loops property."""
        if experiment_all_platforms.loop is not None:
            print(experiment_all_platforms.loop.num_loops)

    @patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
    def test_draw_method_with_one_bus(self, mock_load: MagicMock):
        """Test draw method with only one measurement gate."""
        platform = build_platform(name="platform_0")
        mock_load.assert_called()
        circuit = Circuit(1)
        circuit.add(M(0))
        experiment = Experiment(sequences=circuit, platform=platform)
        experiment.draw()

    def test_str_method(self, experiment_all_platforms: Experiment):
        """Test __str__ method."""
        str(experiment_all_platforms)
        str(experiment_all_platforms.settings)

    def test_set_parameter_method(self, experiment: Experiment):
        """Test set_parameter method."""
        experiment.set_parameter(category="awg", id_=0, parameter=Parameter.FREQUENCY, value=1e9)

    def test_set_parameter_method_with_experiment_settings(self, experiment: Experiment):
        """Test set_parameter method with experiment settings."""
        experiment.set_parameter(category=Category.EXPERIMENT, id_=0, parameter="repetition_duration", value=3e6)

    def test_set_parameter_method_with_platform_settings(self, experiment: Experiment):
        """Test set_parameter method with platform settings."""
        experiment.set_parameter(category=Category.PLATFORM, id_=0, parameter=Parameter.READOUT_AMPLITUDE, value=0.3)
        assert experiment.platform.settings.translation_settings.readout_amplitude == 0.3

    @patch("qililab.instruments.system_control.simulated_system_control.qutip", autospec=True)
    @patch("qililab.execution.buses_execution.yaml.safe_dump")
    @patch("qililab.execution.buses_execution.open")
    @patch("qililab.experiment.experiment.open")
    @patch("qililab.experiment.experiment.os.makedirs")
    def test_execute_method_without_loop(
        self,
        mock_dump: MagicMock,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        mock_open_1: MagicMock,
        mock_qutip: MagicMock,
        simulated_experiment: Experiment,
    ):
        """Test execute method with simulated qubit."""
        mock_qutip.mesolve.return_value.expect = [[1.0], [0.0]]
        results = simulated_experiment.execute()  # type: ignore
        mock_qutip.Options.assert_called()
        mock_qutip.ket2dm.assert_called()
        mock_qutip.mesolve.assert_called()
        mock_dump.assert_called()
        mock_open.assert_called()
        mock_open_1.assert_called()
        mock_makedirs.assert_called()
        with pytest.raises(ValueError):
            print(results.ranges)

    @patch("qililab.instruments.mini_circuits.step_attenuator.urllib", autospec=True)
    @patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
    @patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.execution.buses_execution.yaml.safe_dump")
    @patch("qililab.execution.buses_execution.open")
    @patch("qililab.experiment.experiment.open")
    @patch("qililab.experiment.experiment.os.makedirs")
    @patch("qililab.instruments.qblox.qblox_pulsar.json.dump")
    @patch("qililab.instruments.qblox.qblox_pulsar.open")
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
        nested_experiment: Experiment,
    ):
        """Test execute method with nested loops."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        nested_experiment.settings.software_average = 5
        results = nested_experiment.execute()  # type: ignore
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert isinstance(results, Results)
        assert np.shape(results.acquisitions(mean=True))[1:4] == (2, 2, 2)
        assert np.shape(results.probabilities(mean=True))[1:4] == (2, 2, 2)
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
                    nested_experiment.loop.range,  # type: ignore
                    nested_experiment.loop.loop.range,  # type: ignore
                    nested_experiment.loop.loop.loop.range,  # type: ignore
                ]
            )
        ).all()

    @patch("qililab.instruments.system_control.simulated_system_control.qutip", autospec=True)
    @patch("qililab.execution.buses_execution.yaml.safe_dump")
    @patch("qililab.execution.buses_execution.open")
    @patch("qililab.experiment.experiment.open")
    @patch("qililab.experiment.experiment.os.makedirs")
    def test_execute_method_with_simulated_qubit(
        self,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        mock_open_1: MagicMock,
        mock_dump: MagicMock,
        mock_qutip: MagicMock,
        simulated_experiment: Experiment,
    ):
        """Test execute method with simulated qubit."""
        mock_qutip.mesolve.return_value.expect = [[1.0], [0.0]]
        connection = MagicMock(name="API", spec=API, autospec=True)
        connection.create_liveplot.return_value = 0
        results = simulated_experiment.execute(connection=connection)  # type: ignore
        with pytest.raises(ValueError):
            results.acquisitions()
        connection.create_liveplot.assert_called_once()
        connection.send_plot_points.assert_called()
        mock_qutip.Options.assert_called()
        mock_qutip.ket2dm.assert_called()
        mock_qutip.mesolve.assert_called()
        mock_open.assert_called()
        mock_open_1.assert_called()
        mock_dump.assert_called()
        mock_makedirs.assert_called()

    @patch("qililab.instruments.mini_circuits.step_attenuator.urllib", autospec=True)
    @patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
    @patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.execution.buses_execution.yaml.safe_dump")
    @patch("qililab.execution.buses_execution.open")
    @patch("qililab.experiment.experiment.open")
    @patch("qililab.experiment.experiment.os.makedirs")
    @patch("qililab.instruments.qblox.qblox_pulsar.json.dump")
    @patch("qililab.instruments.qblox.qblox_pulsar.open")
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
        experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
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

    @patch("qililab.instruments.mini_circuits.step_attenuator.urllib", autospec=True)
    @patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
    @patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.execution.buses_execution.yaml.safe_dump")
    @patch("qililab.execution.buses_execution.open")
    @patch("qililab.experiment.experiment.open")
    @patch("qililab.experiment.experiment.os.makedirs")
    @patch("qililab.instruments.qblox.qblox_pulsar.json.dump")
    @patch("qililab.instruments.qblox.qblox_pulsar.open")
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
        nested_experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        experiment = Experiment.from_dict(nested_experiment.to_dict())
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
