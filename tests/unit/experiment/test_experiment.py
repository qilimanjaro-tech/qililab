"""Tests for the Experiment class."""
import itertools
import os
import time
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure
from qibo.models.circuit import Circuit
from qpysequence import Sequence

from qililab import build_platform
from qililab.constants import DATA, RUNCARD, SCHEMA
from qililab.execution.execution_manager import ExecutionManager
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.pulse import PulseSchedule
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import FluxQubitSimulator, Galadriel, experiment_params, simulated_experiment_circuit
from tests.utils import mock_instruments, platform_db


@pytest.fixture(name="simulated_platform")
@patch("qililab.system_control.simulated_system_control.Evolution", autospec=True)
def fixture_simulated_platform(mock_evolution: MagicMock) -> Platform:
    """Return Platform object."""

    # Mocked Evolution needs: system.qubit.frequency, psi0, states, times
    mock_system = MagicMock()
    mock_system.qubit.frequency = 0
    mock_evolution.return_value.system = mock_system
    mock_evolution.return_value.states = []
    mock_evolution.return_value.times = []
    mock_evolution.return_value.psi0 = None

    with patch(
        "qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=FluxQubitSimulator.runcard
    ) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform


@pytest.fixture(name="nested_experiment", params=experiment_params)
def fixture_nested_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop2 = Loop(
        alias="platform",
        parameter=Parameter.DELAY_BEFORE_READOUT,
        values=np.arange(start=40, stop=100, step=40),
    )
    loop = Loop(
        alias=InstrumentName.QBLOX_QRM.value,
        parameter=Parameter.GAIN,
        values=np.linspace(start=0, stop=1, num=2),
        channel_id=0,
        loop=loop2,
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )


@pytest.fixture(name="experiment", params=experiment_params)
def fixture_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="X(0)",
        parameter=Parameter.DURATION,
        values=np.arange(start=4, stop=1000, step=40),
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=Galadriel.runcard)


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
    experiment_all_platforms: Experiment,
):
    """Fixture that mocks all the instruments, connects to the mocked instruments and returns the `Experiment`
    instance."""
    mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
    experiment_all_platforms.connect()
    mock_mini_circuits.assert_called()
    mock_keithley.assert_called()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return experiment_all_platforms


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
        assert not hasattr(experiment, "execution_manager")
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


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
def fixture_experiment_all_platforms(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    experiment = Experiment(platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits])
    mock_load.assert_called()
    return experiment


class TestMethods:
    """Test the methods of the Experiment class."""

    def test_connect(self, experiment_all_platforms: Experiment):
        """Test the ``connect`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.connect") as mock_connect:
            experiment_all_platforms.connect()
            mock_connect.assert_called_once()

    def test_initial_setup(self, experiment_all_platforms: Experiment):
        """Test the ``initial_setup`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.initial_setup") as mock_initial_setup:
            experiment_all_platforms.initial_setup()
            mock_initial_setup.assert_called_once()

    def test_build_execution(self, experiment: Experiment):
        """Test the ``build_execution`` method of the Experiment class."""
        # Check that the ``pulse_schedules`` attribute is empty
        assert len(experiment.pulse_schedules) == 0
        # Check that attributes don't exist
        assert not hasattr(experiment, "execution_manager")
        assert not hasattr(experiment, "results")
        assert not hasattr(experiment, "results_path")
        assert not hasattr(experiment, "_plot")
        assert not hasattr(experiment, "_remote_id")
        experiment.build_execution()
        # Check that the ``pulse_schedules`` attribute is NOT empty
        assert len(experiment.pulse_schedules) == len(experiment.circuits)
        # Check that new attributes are created
        assert isinstance(experiment.execution_manager, ExecutionManager)
        assert not hasattr(experiment, "results")
        assert not hasattr(experiment, "results_path")
        assert not hasattr(experiment, "_plot")
        assert not hasattr(experiment, "_remote_id")

    def test_compile(self, experiment: Experiment):
        """Test the compile method of the ``Execution`` class."""
        experiment.build_execution()
        pulse_schedules = experiment.compile()
        assert isinstance(pulse_schedules, list)
        assert len(pulse_schedules) == len(experiment.circuits)
        pulse_schedule = pulse_schedules[0]
        buses = experiment.execution_manager.buses
        assert len(pulse_schedule) == len(buses)
        for alias, bus_schedule in pulse_schedule.items():
            assert alias in {bus.alias for bus in buses}
            assert isinstance(bus_schedule, list)
            assert len(bus_schedule) == 1
            assert isinstance(bus_schedule[0], Sequence)
            assert (
                bus_schedule[0]._program.duration == experiment.hardware_average * experiment.repetition_duration + 4
            )  # additional 4ns for the initial wait_sync

    def test_compile_raises_error(self, experiment: Experiment):
        """Test that the ``compile`` method of the ``Experiment`` class raises an error when ``build_execution`` is
        not called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before compilation"):
            experiment.compile()

    def test_run_without_data_path_raises_error(self, experiment: Experiment):
        """Test that the ``build_execution`` method of the ``Experiment`` class raises an error when no DATA
        path is specified."""
        old_data = os.environ.get(DATA)
        del os.environ[DATA]
        with pytest.raises(ValueError, match="Environment variable DATA is not set"):
            experiment.build_execution()
            experiment.run()
        if old_data is not None:
            os.environ[DATA] = old_data

    def test_run(self, connected_experiment: Experiment):
        """Test the ``run`` method of the Experiment class."""
        connected_experiment.build_execution()
        connected_experiment.platform.connection = MagicMock()  # mock connection
        assert not hasattr(connected_experiment, "_plot")
        assert not hasattr(connected_experiment, "results")
        with patch("qililab.execution.open") as mock_open:
            with patch("qililab.experiment.experiment.open") as mock_open:
                with patch("qililab.experiment.experiment.os.makedirs") as mock_makedirs:
                    with patch("qililab.experiment.experiment.LivePlot") as mock_plot:
                        # Build execution
                        connected_experiment.run()
                        # Assert that the mocks are called when building the execution (such that NO files are created)
                        mock_open.assert_called()
                        mock_makedirs.assert_called()
                        mock_open.assert_called()
                        mock_plot.assert_called_once_with(
                            connection=connected_experiment.platform.connection,
                            loops=connected_experiment.options.loops or [],
                            num_schedules=len(connected_experiment.pulse_schedules),
                            title=connected_experiment.options.name,
                        )
                        mock_plot.assert_called_once()
        assert len(connected_experiment.results.results) > 0

    def test_run_raises_error(self, experiment: Experiment):
        """Test that the ``run`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before running an experiment"):
            experiment.run()

    def test_turn_on_instruments(self, connected_experiment: Experiment):
        """Test the ``turn_on_instruments`` method of the Experiment class."""
        connected_experiment.build_execution()
        with patch("qililab.platform.platform.Platform.turn_on_instruments") as mock_turn_on:
            connected_experiment.turn_on_instruments()
            mock_turn_on.assert_called_once()

    def test_turn_on_instruments_raises_error(self, experiment: Experiment):
        """Test that the ``turn_on_instruments`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before turning on the instruments"):
            experiment.turn_on_instruments()

    def test_turn_off_instruments(self, connected_experiment: Experiment):
        """Test the ``turn_off_instruments`` method of the Experiment class."""
        connected_experiment.build_execution()
        with patch("qililab.platform.platform.Platform.turn_off_instruments") as mock_turn_off:
            connected_experiment.turn_off_instruments()
            mock_turn_off.assert_called_once()

    def test_turn_off_instruments_raises_error(self, experiment: Experiment):
        """Test that the ``turn_off_instruments`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before turning off the instruments"):
            experiment.turn_off_instruments()

    def test_disconnect(self, experiment: Experiment):
        """Test the ``disconnect`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.disconnect") as mock_disconnect:
            experiment.disconnect()
            mock_disconnect.assert_called_once()

    def test_to_dict_method(self, experiment_all_platforms: Experiment):
        """Test to_dict method."""
        dictionary = experiment_all_platforms.to_dict()
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

    def test_draw_method(self, connected_experiment: Experiment):
        """Test draw method."""
        connected_experiment.build_execution()

        figures = [
            connected_experiment.draw(),
            connected_experiment.draw(
                modulation=False,
                linestyle="--",
                resolution=1.3,
            ),
            connected_experiment.draw(
                real=False,
                imag=False,
                absolute=True,
                modulation=False,
                linestyle=".",
                resolution=0.11,
            ),
        ]

        for figure in figures:
            assert figure is not None
            assert isinstance(figure, Figure)

        plt.close()

    def test_draw_raises_error(self, experiment: Experiment):
        """Test that the ``draw`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before drawing the experiment"):
            experiment.draw()

    def test_loop_num_loops_property(self, experiment_all_platforms: Experiment):
        """Test loop's num_loops property."""
        if experiment_all_platforms.options.loops is not None:
            print(experiment_all_platforms.options.loops[0].num_loops)

    def test_draw_method_with_one_bus(self, experiment: Experiment):
        """Test draw method with only one measurement gate."""
        experiment.build_execution()
        experiment.draw()

    def test_str_method(self, experiment_all_platforms: Experiment):
        """Test __str__ method."""
        str(experiment_all_platforms)


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
        experiment.set_parameter(alias="M(0)", parameter=Parameter.AMPLITUDE, value=0.3)
        assert experiment.platform.settings.get_gate(name="M", qubits=0).amplitude == 0.3

    def test_set_parameter_method_with_instrument_controller_reset(self, experiment: Experiment):
        """Test set_parameter method with instrument controller reset."""
        experiment.set_parameter(alias="pulsar_controller_qcm_0", parameter=Parameter.RESET, value=False)
        assert (
            experiment.platform.instrument_controllers.get_instrument_controller(
                alias="pulsar_controller_qcm_0"
            ).settings.reset
            is False
        )

    def test_set_parameter_method_with_gate_value(self, experiment: Experiment):
        """Test the ``set_parameter`` method with a parameter of a gate."""
        experiment.set_parameter(alias="X(0)", parameter=Parameter.DURATION, value=123)
        assert experiment.platform.settings.get_gate(name="X", qubits=0).duration == 123


@pytest.fixture(name="experiment_reset", params=experiment_params)
def fixture_experiment_reset(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            mock_load.return_value[RUNCARD.SCHEMA][SCHEMA.INSTRUMENT_CONTROLLERS][0] |= {"reset": False}
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="rs_0",
        parameter=Parameter.LO_FREQUENCY,
        values=np.linspace(start=3544000000, stop=3744000000, num=2),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )
    mock_load.assert_called()
    return experiment


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


@pytest.fixture(name="simulated_experiment")
def fixture_simulated_experiment(simulated_platform: Platform):
    """Return Experiment object."""
    return Experiment(platform=simulated_platform, circuits=[simulated_experiment_circuit])


@patch("qililab.experiment.experiment.open")
@patch("qililab.experiment.experiment.yaml.safe_dump")
@patch("qililab.system_control.simulated_system_control.SimulatedSystemControl.run")
@patch("qililab.experiment.experiment.os.makedirs")
class TestSimulatedExecution:
    """Unit tests checking the execution of a simulated platform"""

    def test_execute(
        self,
        mock_open: MagicMock,
        mock_dump: MagicMock,
        mock_ssc_run: MagicMock,
        mock_makedirs: MagicMock,
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
        mock_dump.assert_called()

        # Test result
        with pytest.raises(ValueError):  # Result should be SimulatedResult
            results.acquisitions()