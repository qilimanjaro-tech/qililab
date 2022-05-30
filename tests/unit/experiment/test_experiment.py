"""Tests for the Experiment class."""
import copy
from unittest.mock import MagicMock, patch

from qiboconnection.api import API

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.result import Result

from ...conftest import mock_instruments


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

    def test_loop_duration_property(self, experiment: Experiment):
        """Test loop_duration property."""
        assert experiment.loop_duration == experiment.settings.loop_duration

    def test_circuit_to_pulse_property(self, experiment: Experiment):
        """Test circuit_to_pulse property."""
        assert experiment.circuit_to_pulse == experiment.settings.circuit_to_pulse

    def test_to_dict_method(self, experiment_all_platforms: Experiment):
        """Test to_dict method with all platforms."""
        dictionary = experiment_all_platforms.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, experiment_all_platforms: Experiment):
        """Test from_dict method with all platforms."""
        dictionary = experiment_all_platforms.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_draw_method(self, experiment_all_platforms: Experiment):
        """Test draw method with all platforms."""
        experiment_all_platforms.draw()

    def test_add_parameter_to_loop_method(self, experiment: Experiment):
        """Test add_parameter_to_loop method."""
        experiment.add_parameter_to_loop(category="awg", id_=0, parameter="frequency", start=0, stop=1, num=100)

    @patch("qililab.instruments.system_control.simulated_system_control.qutip", autospec=True)
    def test_execute_method_with_simulated_qubit(self, mock_qutip: MagicMock, simulated_experiment: Experiment):
        """Test execute method with simulated qubit."""
        connection = MagicMock(name="API", spec=API, autospec=True)
        connection.create_liveplot.return_value = 0
        simulated_experiment.add_parameter_to_loop(
            category="system_control", id_=0, parameter="frequency", start=0, stop=1, num=2
        )
        simulated_experiment.execute(connection=connection)  # type: ignore
        connection.create_liveplot.assert_called_once()
        connection.send_plot_points.assert_called()
        mock_qutip.Options.assert_called()
        mock_qutip.ket2dm.assert_called()
        mock_qutip.mesolve.assert_called()

    @patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
    @patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
    def test_execute_method_with_instruments(self, mock_rs: MagicMock, mock_pulsar: MagicMock, experiment: Experiment):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        experiment.add_parameter_to_loop(
            category="system_control", id_=0, parameter="frequency", start=3544000000, stop=3744000000, num=2
        )
        results = experiment.execute()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, list)
        assert isinstance(results[0][0], Result)
