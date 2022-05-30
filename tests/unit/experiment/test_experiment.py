"""Tests for the Experiment class."""
from unittest.mock import MagicMock, patch

import pytest
from qiboconnection.api import API

from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.result import Results
from qililab.utils import Loop

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

    def test_repetition_duration_property(self, experiment: Experiment):
        """Test repetition_duration property."""
        assert experiment.repetition_duration == experiment.settings.repetition_duration

    def test_circuit_to_pulse_property(self, experiment: Experiment):
        """Test circuit_to_pulse property."""
        assert experiment.translation == experiment.settings.translation

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

    def test_str_method(self, experiment_all_platforms: Experiment):
        """Test __str__ method with all platforms."""
        str(experiment_all_platforms)
        str(experiment_all_platforms.settings)

    def test_set_parameter_method(self, experiment: Experiment):
        """Test set_parameter method with all platforms."""
        experiment.set_parameter(category="awg", id_=0, parameter="frequency", value=1e9)

    @patch("qililab.instruments.system_control.simulated_system_control.qutip", autospec=True)
    def test_execute_method_without_loop(self, mock_qutip: MagicMock, simulated_experiment: Experiment):
        """Test execute method with simulated qubit."""
        simulated_experiment.execute()  # type: ignore
        mock_qutip.Options.assert_called()
        mock_qutip.ket2dm.assert_called()
        mock_qutip.mesolve.assert_called()

    @patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
    @patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
    def test_execute_method_with_nested_loop(self, mock_rs: MagicMock, mock_pulsar: MagicMock, experiment: Experiment):
        """Test execute method with nested loops."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        loop1 = Loop(category="awg", id_=0, parameter="frequency", start=0, stop=1, num=2)
        loop2 = Loop(category="awg", id_=0, parameter="gain", start=0, stop=1, num=2)
        loop3 = Loop(category="signal_generator", id_=0, parameter="frequency", start=0, stop=1, num=2)
        results = experiment.execute(loops=[loop1, loop2, loop3])  # type: ignore
        assert isinstance(results, Results)
        assert len(results.results) == 8
        assert results.loops == [loop1, loop2, loop3]

    @patch("qililab.instruments.system_control.simulated_system_control.qutip", autospec=True)
    def test_execute_method_with_simulated_qubit(self, mock_qutip: MagicMock, simulated_experiment: Experiment):
        """Test execute method with simulated qubit."""
        connection = MagicMock(name="API", spec=API, autospec=True)
        connection.create_liveplot.return_value = 0
        loop = Loop(category="system_control", id_=0, parameter="frequency", start=0, stop=1, num=2)
        results = simulated_experiment.execute(loops=loop, connection=connection)  # type: ignore
        with pytest.raises(ValueError):
            results.acquisitions()
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
        loop = Loop(category="system_control", id_=0, parameter="frequency", start=3544000000, stop=3744000000, num=2)
        results = experiment.execute(loops=loop)
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, list)
        assert isinstance(acquisitions, list)
