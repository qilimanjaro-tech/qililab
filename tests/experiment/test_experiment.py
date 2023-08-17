"""Tests for the Experiment class."""
import copy
import time
from queue import Queue
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure
from qibo.models.circuit import Circuit
from qpysequence import Sequence

import qililab as ql
from qililab.constants import RUNCARD
from qililab.execution import ExecutionManager
from qililab.experiment.experiment import Experiment
from qililab.platform import Platform
from qililab.pulse import PulseSchedule
from qililab.typings import InstrumentName, Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import FluxQubitSimulator, Galadriel, experiment_params, simulated_experiment_circuit
from tests.test_utils import build_platform, mock_instruments


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

    return build_platform(FluxQubitSimulator.runcard)


@pytest.fixture(name="nested_experiment", params=experiment_params)
def fixture_nested_experiment(request: pytest.FixtureRequest):
    """Return a nested Experiment object."""
    runcard, circuits = request.param  # type: ignore
    platform = build_platform(runcard)
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
    platform = build_platform(runcard)
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
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
def fixture_experiment_all_platforms(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    platform = build_platform(runcard)
    return Experiment(
        platform=platform,
        circuits=circuits if isinstance(circuits, list) else [circuits],
    )


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
    experiment_all_platforms.platform.connect()
    mock_mini_circuits.assert_called()
    mock_keithley.assert_called()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return experiment_all_platforms


@pytest.fixture(name="experiment_reset", params=experiment_params)
def fixture_experiment_reset(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    runcard = copy.deepcopy(runcard)
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            mock_load.return_value[RUNCARD.INSTRUMENT_CONTROLLERS][0] |= {"reset": False}
            platform = ql.build_platform(name="galadriel")
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


@pytest.fixture(name="simulated_experiment")
def fixture_simulated_experiment(simulated_platform: Platform):
    """Return Experiment object."""
    return Experiment(platform=simulated_platform, circuits=[simulated_experiment_circuit])


class TestMethods:
    """Test the methods of the Experiment class."""

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

    def test_draw_method_with_one_bus(self, experiment: Experiment):
        """Test draw method with only one measurement gate."""
        experiment.build_execution()
        experiment.draw()

    def test_str_method(self, experiment: Experiment):
        """Test __str__ method."""
        expected = f"BaseExperiment {experiment.options.name}:\n{str(experiment.platform)}\n{str(experiment.options)}\n{str(experiment.circuits)}\n{str(experiment.pulse_schedules)}\n"
        test_str = str(experiment)
        assert expected == test_str

    def test_process_loops_raises_without_idx(self, experiment: Experiment):
        """Test that the _process_loops method raises an exception when called without 'idx' parameter"""
        with pytest.raises(ValueError, match="Parameter 'idx' must be specified"):
            loops = [Loop(alias="foo", parameter=Parameter.POWER, values=np.linspace(0, 10, 10))]
            queue: Queue = Queue()
            experiment._process_loops(loops=loops, queue=queue, depth=0)

    def test_execute_recursive_loops_raises_without_idx(self, experiment: Experiment):
        """Test that the _execute_recursive_loops method raises an exception when called without 'idx' parameter"""
        with pytest.raises(ValueError, match="Parameter 'idx' must be specified"):
            loops = [Loop(alias="foo", parameter=Parameter.POWER, values=np.linspace(0, 10, 10))]
            queue: Queue = Queue()
            experiment._execute_recursive_loops(loops=loops, queue=queue)

    def test_run_raises_without_execution_manager(self, experiment: Experiment):
        """Test the run method raises an exception if the execution manager was not previously built"""
        with pytest.raises(ValueError, match="Please build the execution_manager before running an experiment."):
            experiment.run()

    def test_set_parameter_method_with_gate_value(self, experiment: Experiment):
        """Test the ``set_parameter`` method with a parameter of a gate."""
        experiment.set_parameter(alias="X(0)", parameter=Parameter.DURATION, value=123)
        assert experiment.platform.gates_settings.get_gate(name="X", qubits=0)[0].pulse.duration == 123

    def test_set_parameter_method_with_gate_parameter_in_circuit(self, experiment: Experiment):
        """Test the ``set_parameter`` method with a parameter of a gate in circuit."""
        experiment.set_parameter(alias="0", parameter=Parameter.GATE_PARAMETER, value=123)
        assert experiment.circuits[0].get_parameters()[0][0] == 123

    def test_from_dict_method_loop(self, nested_experiment: Experiment):
        """Test from_dict method with a Experiment that contains a nested loop."""
        dictionary = nested_experiment.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)


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


@patch("qililab.experiment.base_experiment.open")
@patch("qililab.experiment.base_experiment.yaml.safe_dump")
@patch("qililab.system_control.simulated_system_control.SimulatedSystemControl.run")
@patch("qililab.experiment.base_experiment.os.makedirs")
class TestSimulatedExecution:
    """Unit tests checking the execution of a simulated platform"""

    def test_execute_without_saving_experiment(
        self,
        mock_open: MagicMock,
        mock_dump: MagicMock,
        mock_ssc_run: MagicMock,
        mock_makedirs: MagicMock,
        simulated_experiment: Experiment,
    ):  # pylint: disable=W0613
        """Test execute method with simulated qubit"""

        # Method under test
        results = simulated_experiment.execute(save_experiment=False)

        time.sleep(0.3)

        # Assert simulator called
        mock_ssc_run.assert_called()

        # Test result
        with pytest.raises(ValueError):  # Result should be SimulatedResult
            results.acquisitions()

    def test_execute_with_saving_experiment(
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
