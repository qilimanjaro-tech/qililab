"""Tests for the Experiment class."""
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from matplotlib.figure import Figure
from qibo.gates import M
from qibo.models.circuit import Circuit

from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.pulse import PulseSchedule
from qililab.result.results import Results
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.utils.live_plot import LivePlot

from .aux_methods import mock_instruments


@pytest.fixture(name="connected_experiment")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
@patch("qililab.instrument_controllers.mini_circuits.mini_circuits_controller.MiniCircuitsDriver", autospec=True)
def fixture_connected_experiment(
    mock_mini_circuits: MagicMock,
    mock_keithley: MagicMock,
    mock_rs: MagicMock,
    mock_pulsar: MagicMock,
    experiment: Experiment,
):
    """Fixture that returns a connected and built experiment."""
    mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
    experiment.connect()
    mock_mini_circuits.assert_called()
    mock_keithley.assert_called()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return experiment


@pytest.fixture(name="built_experiment")
def fixture_built_experiment(connected_experiment: Experiment):
    """Fixture that returns a connected and built experiment."""
    with patch("qililab.experiment.prepare_results.open") as mock_open:
        with patch("qililab.experiment.prepare_results.os.makedirs") as mock_makedirs:
            # Build execution
            connected_experiment.build_execution()
            # Assert that the mocks are called when building the execution (such that NO files are created)
            mock_open.assert_called()
            mock_makedirs.assert_called()
    return connected_experiment


class TestAttributes:
    """Unit tests checking the Experiment attributes and methods"""

    def test_platform_attributes(self, experiment: Experiment):
        """Test platform attributes after initialization."""
        assert isinstance(experiment.platform, Platform)
        assert isinstance(experiment.circuits, list)
        if len(experiment.circuits) > 0:
            for circuit in experiment.circuits:
                assert isinstance(circuit, Circuit)
        assert isinstance(experiment.pulse_schedules, list)
        if len(experiment.pulse_schedules) > 0:
            for pulse_schedule in experiment.pulse_schedules:
                assert isinstance(pulse_schedule, PulseSchedule)
        assert isinstance(experiment.options, ExperimentOptions)
        assert not hasattr(experiment, "execution")
        assert not hasattr(experiment, "results")
        assert not hasattr(experiment, "results_path")
        assert not hasattr(experiment, "_plot")
        assert not hasattr(experiment, "_remote_id")


class TestProperties:
    """Test the properties of the Experiment class."""

    def test_software_average_property(self, experiment: Experiment):
        """Test software_average property."""
        assert experiment.software_average == experiment.options.settings.software_average

    def test_hardware_average_property(self, experiment: Experiment):
        """Test hardware_average property."""
        assert experiment.hardware_average == experiment.options.settings.hardware_average

    def test_repetition_duration_property(self, experiment: Experiment):
        """Test repetition_duration property."""
        assert experiment.repetition_duration == experiment.options.settings.repetition_duration


class TestMethods:
    """Test the methods of the Experiment class."""

    def test_connect(self, experiment: Experiment):
        """Test the ``connect`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.connect") as mock_connect:
            experiment.connect()
            mock_connect.assert_called_once()

    def test_initial_setup(self, experiment: Experiment):
        """Test the ``initial_setup`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.initial_setup") as mock_initial_setup:
            experiment.initial_setup()
            mock_initial_setup.assert_called_once()

    def test_build_execution(self, experiment: Experiment):
        """Test the ``build_execution`` method of the Experiment class."""
        # Check that the ``pulse_schedules`` attribute is empty
        assert len(experiment.pulse_schedules) == 0
        # Check that attributes don't exist
        assert not hasattr(experiment, "execution")
        assert not hasattr(experiment, "results")
        assert not hasattr(experiment, "results_path")
        assert not hasattr(experiment, "_plot")
        assert not hasattr(experiment, "_remote_id")
        with patch("qililab.experiment.prepare_results.open") as mock_open:
            with patch("qililab.experiment.prepare_results.os.makedirs") as mock_makedirs:
                # Build execution
                experiment.build_execution()
                # Assert that the mocks are called when building the execution (such that NO files are created)
                mock_open.assert_called()
                mock_makedirs.assert_called()
        # Check that the ``pulse_schedules`` attribute is NOT empty
        assert len(experiment.pulse_schedules) == len(experiment.circuits)
        # Check that new attributes are created
        assert isinstance(experiment.execution, Execution)
        assert isinstance(experiment.results, Results)
        assert isinstance(experiment.results_path, Path)
        assert isinstance(experiment._plot, LivePlot)
        assert not hasattr(experiment, "_remote_id")

    def test_run(self, built_experiment: Experiment):
        """Test the ``run`` method of the Experiment class."""
        assert len(built_experiment.results.results) == 0
        built_experiment.run()
        assert len(built_experiment.results.results) > 0

    def test_run_raises_error(self, experiment: Experiment):
        """Test that the ``run`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution before running an experiment"):
            experiment.run()

    def test_turn_on_instruments(self, built_experiment: Experiment):
        """Test the ``turn_on_instruments`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.turn_on_instruments") as mock_turn_on:
            built_experiment.turn_on_instruments()
            mock_turn_on.assert_called_once()

    def test_turn_on_instruments_raises_error(self, experiment: Experiment):
        """Test that the ``turn_on_instruments`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution before turning on the instruments"):
            experiment.turn_on_instruments()

    def test_turn_off_instruments(self, built_experiment: Experiment):
        """Test the ``turn_off_instruments`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.turn_off_instruments") as mock_turn_off:
            built_experiment.turn_off_instruments()
            mock_turn_off.assert_called_once()

    def test_turn_off_instruments_raises_error(self, experiment: Experiment):
        """Test that the ``turn_off_instruments`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution before turning off the instruments"):
            experiment.turn_off_instruments()

    def test_disconnect(self, experiment: Experiment):
        """Test the ``disconnect`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.disconnect") as mock_disconnect:
            experiment.disconnect()
            mock_disconnect.assert_called_once()

    def test_to_dict_method(self, experiment: Experiment):
        """Test to_dict method."""
        dictionary = experiment.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, experiment: Experiment):
        # sourcery skip: class-extract-method
        """Test from_dict method."""
        dictionary = experiment.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_from_dict_method_loop(self, nested_experiment: Experiment):
        """Test from_dict method with an experiment with a nested loop."""
        dictionary = nested_experiment.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_draw_method(self, built_experiment: Experiment):
        """Test draw method."""
        figure = built_experiment.draw()
        assert isinstance(figure, Figure)

    def test_draw_raises_error(self, experiment: Experiment):
        """Test that the ``draw`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution before drawing the experiment"):
            experiment.draw()

    def test_loop_num_loops_property(self, experiment: Experiment):
        """Test loop's num_loops property."""
        if experiment.options.loops is not None:
            print(experiment.options.loops[0].num_loops)

    @patch("qililab.experiment.prepare_results.open")
    @patch("qililab.experiment.prepare_results.os.makedirs")
    def test_draw_method_with_one_bus(self, mock_open: MagicMock, mock_makedirs: MagicMock, platform: Platform):
        """Test draw method with only one measurement gate."""
        circuit = Circuit(1)
        circuit.add(M(0))
        experiment = Experiment(circuits=[circuit], platform=platform)
        experiment.build_execution()
        # Assert that the mocks are called when building the execution (such that NO files are created)
        mock_open.assert_called()
        mock_makedirs.assert_called()
        experiment.draw()

    def test_str_method(self, experiment: Experiment):
        """Test __str__ method."""
        str(experiment)


class TestSetParameter:
    """Unit tests for the ``set_parameter`` method."""

    def test_set_parameter_method_without_a_connected_device(self, experiment: Experiment):
        """Test set_parameter method raising an error when device is not connected."""
        with pytest.raises(ValueError):
            experiment.set_parameter(
                alias=InstrumentName.QBLOX_QCM.value, parameter=Parameter.IF, value=1e9, channel_id=0
            )

    @patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
    @patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    def test_set_parameter_method_with_a_connected_device(
        self,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        experiment: Experiment,  # pylint: disable=unused-argument
    ):
        """Test set_parameter method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        experiment.platform.connect()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        experiment.set_parameter(alias=InstrumentName.QBLOX_QCM.value, parameter=Parameter.IF, value=1e9, channel_id=0)

    def test_set_parameter_method_with_platform_settings(self, experiment: Experiment):
        """Test set_parameter method with platform settings."""
        experiment.set_parameter(alias="M", parameter=Parameter.AMPLITUDE, value=0.3)
        assert experiment.platform.settings.get_gate(name="M").amplitude == 0.3

    def test_set_parameter_method_with_instrument_controller_reset(self, experiment: Experiment):
        """Test set_parameter method with instrument controller reset."""
        experiment.set_parameter(alias="pulsar_controller_qcm_0", parameter=Parameter.RESET, value=False)
        assert (
            experiment.platform.instrument_controllers.get_instrument_controller(
                alias="pulsar_controller_qcm_0"
            ).settings.reset
            is False
        )


class TestReset:
    """Unit tests for the reset option."""

    @patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
    @patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    @patch("qililab.instrument_controllers.instrument_controller.InstrumentController.reset")
    def test_set_reset_true_with_connected_device(
        self,
        mock_reset: MagicMock,
        mock_urllib: MagicMock,  # pylint: disable=unused-argument
        mock_keithley: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        experiment: Experiment,  # pylint: disable=unused-argument
    ):
        """Test set reset to false method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        experiment.platform.connect()
        experiment.platform.disconnect()
        mock_reset.assert_called()
        assert mock_reset.call_count == 12

    @patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
    @patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    @patch("qililab.instrument_controllers.instrument_controller.InstrumentController.reset")
    def test_set_reset_false_with_connected_device(
        self,
        mock_reset: MagicMock,
        mock_urllib: MagicMock,  # pylint: disable=unused-argument
        mock_keithley: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        experiment_reset: Experiment,  # pylint: disable=unused-argument
    ):
        """Test set reset to false method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        experiment_reset.platform.connect()
        experiment_reset.platform.disconnect()
        assert mock_reset.call_count == 10


@patch("qililab.experiment.prepare_results.open")
@patch("qililab.experiment.prepare_results.os.makedirs")
@patch("qililab.system_controls.system_control_types.simulated_system_control.SimulatedSystemControl.run")
@patch("qililab.execution.execution_manager.yaml.safe_dump")
@patch("qililab.execution.execution_manager.open")
class TestSimulatedExecution:
    """Unit tests checking the execution of a simulated platform"""

    def test_execute(
        self,
        mock_open_0: MagicMock,
        mock_dump: MagicMock,
        mock_ssc_run: MagicMock,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        simulated_experiment: Experiment,
    ):
        """Test execute method with simulated qubit"""

        # Method under test
        results = simulated_experiment.execute()

        time.sleep(0.3)

        # Assert simulator called
        mock_ssc_run.assert_called()

        # Assert called functions
        mock_makedirs.assert_called()
        mock_open.assert_called()
        mock_open_0.assert_called()
        mock_dump.assert_called()

        # Test result
        with pytest.raises(ValueError):  # Result should be SimulatedResult
            results.acquisitions()
