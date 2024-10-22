"""Tests for the Platform class."""

import copy
import io
import re
from pathlib import Path
from queue import Queue
from types import MethodType
from unittest.mock import MagicMock, create_autospec, patch

import numpy as np
import pytest
from qibo import gates
from qibo.models import Circuit
from qpysequence import Sequence, Waveforms
from ruamel.yaml import YAML

from qililab import Arbitrary, save_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.exceptions import ExceptionGroup
from qililab.instrument_controllers import InstrumentControllers
from qililab.instruments import SGS100A
from qililab.instruments.instruments import Instruments
from qililab.instruments.qblox import QbloxModule
from qililab.instruments.quantum_machines import QuantumMachinesCluster
from qililab.platform import Bus, Buses, Platform
from qililab.pulse import Drag, Pulse, PulseEvent, PulseSchedule, Rectangular
from qililab.qprogram import Calibration, Domain, Experiment, QProgram
from qililab.result.qblox_results import QbloxResult
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.settings import Runcard, DigitalCompilationSettings, AnalogCompilationSettings
from qililab.settings.digital.gate_event_settings import GateEventSettings
from qililab.settings.analog.flux_control_topology import FluxControlTopology
from qililab.typings.enums import InstrumentName, Parameter
from qililab.waveforms import Chained, IQPair, Ramp, Square
from tests.data import Galadriel, SauronQuantumMachines
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="platform_quantum_machines")
def fixture_platform_quantum_machines():
    return build_platform(runcard=SauronQuantumMachines.runcard)


@pytest.fixture(name="runcard")
def fixture_runcard():
    return Runcard(**copy.deepcopy(Galadriel.runcard))


@pytest.fixture(name="qblox_results")
def fixture_qblox_results():
    return [
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [0],
                "avg_cnt": [1],
            },
            "qubit": 0,
            "measurement": 0,
        },
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [1],
                "avg_cnt": [1],
            },
            "qubit": 0,
            "measurement": 1,
        },
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [2],
                "avg_cnt": [1],
            },
            "qubit": 1,
            "measurement": 0,
        },
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [3],
                "avg_cnt": [1],
            },
            "qubit": 1,
            "measurement": 1,
        },
    ]


@pytest.fixture(name="flux_to_bus_topology")
def get_flux_to_bus_topology():
    flux_control_topology_dict = [
        {"flux": "phix_q0", "bus": "flux_line_phix_q0"},
        {"flux": "phiz_q0", "bus": "flux_line_phiz_q0"},
        {"flux": "phix_q1", "bus": "flux_line_phix_q1"},
        {"flux": "phiz_q1", "bus": "flux_line_phiz_q1"},
        {"flux": "phix_c0_1", "bus": "flux_line_phix_c0_1"},
        {"flux": "phiz_c0_1", "bus": "flux_line_phiz_c0_1"},
    ]
    return [FluxControlTopology(**flux_control) for flux_control in flux_control_topology_dict]


@pytest.fixture(name="calibration")
def get_calibration():
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)

    measurement_qp = QProgram()
    measurement_qp.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)

    calibration = Calibration()
    calibration.add_block(name="measurement", block=measurement_qp.body)

    return calibration


@pytest.fixture(name="calibration_with_preparation_block")
def get_calibration_with_preparation_block():
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)

    preparation_wf = Chained(
        waveforms=[Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100), Square(amplitude=1.0, duration=200)]
    )
    preparation_qp = QProgram()
    preparation_qp.play(bus="flux_line_phix_q0", waveform=preparation_wf)
    preparation_qp.play(bus="flux_line_phiz_q0", waveform=preparation_wf)

    measurement_qp = QProgram()
    measurement_qp.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)

    calibration = Calibration()
    calibration.add_block(name="preparation", block=preparation_qp.body)
    calibration.add_block(name="measurement", block=measurement_qp.body)

    return calibration


@pytest.fixture(name="anneal_qprogram")
def get_anneal_qprogram(runcard, flux_to_bus_topology):
    platform = Platform(runcard=runcard)
    platform.analog_compilation_settings = flux_to_bus_topology
    anneal_waveforms = {
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phix_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 1.0])
        ),
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phiz_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 2.0])
        ),
    }
    num_averages = 2
    num_shots = 1
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)

    qp_anneal = QProgram()
    shots_variable = qp_anneal.variable("num_shots", Domain.Scalar, int)
    with qp_anneal.for_loop(variable=shots_variable, start=0, stop=num_shots, step=1):
        with qp_anneal.average(num_averages):
            for bus, waveform in anneal_waveforms.items():
                qp_anneal.play(bus=bus, waveform=waveform)
            qp_anneal.sync()
            with qp_anneal.block():
                qp_anneal.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)
    return qp_anneal


@pytest.fixture(name="anneal_qprogram_with_preparation")
def get_anneal_qprogram_with_preparation(runcard, flux_to_bus_topology):
    platform = Platform(runcard=runcard)
    platform.analog_compilation_settings = flux_to_bus_topology
    anneal_waveforms = {
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phix_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 1.0])
        ),
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phiz_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 2.0])
        ),
    }
    num_averages = 2
    num_shots = 1
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)
    preparation_wf = Chained(
        waveforms=[Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100), Square(amplitude=1.0, duration=200)]
    )

    qp_anneal = QProgram()
    shots_variable = qp_anneal.variable("num_shots", Domain.Scalar, int)
    with qp_anneal.for_loop(variable=shots_variable, start=0, stop=num_shots, step=1):
        with qp_anneal.average(num_averages):
            with qp_anneal.block():
                qp_anneal.play(bus="flux_line_phix_q0", waveform=preparation_wf)
                qp_anneal.play(bus="flux_line_phiz_q0", waveform=preparation_wf)
            qp_anneal.sync()
            for bus, waveform in anneal_waveforms.items():
                qp_anneal.play(bus=bus, waveform=waveform)
            qp_anneal.sync()
            with qp_anneal.block():
                qp_anneal.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)
    return qp_anneal


class TestPlatformInitialization:
    """Unit tests for the Platform class initialization"""

    def test_init_method(self, runcard):
        """Test initialization of the class"""
        platform = Platform(runcard=runcard)

        assert platform.name == runcard.name
        assert isinstance(platform.name, str)
        assert isinstance(platform.digital_compilation_settings, DigitalCompilationSettings)
        assert isinstance(platform.analog_compilation_settings, AnalogCompilationSettings)
        assert isinstance(platform.instruments, Instruments)
        assert isinstance(platform.instrument_controllers, InstrumentControllers)
        assert isinstance(platform.buses, Buses)
        assert platform._connected_to_instruments is False


class TestPlatform:
    """Unit tests checking the Platform class."""

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_initial_setup_no_instrument_connection(self, platform: Platform):
        """Test platform raises and error if no instrument connection."""
        platform._connected_to_instruments = False
        with pytest.raises(
            AttributeError, match="Can not do initial_setup without being connected to the instruments."
        ):
            platform.initial_setup()

    def test_set_parameter_no_instrument_connection_QBLOX(self, platform: Platform):
        """Test platform raises and error if no instrument connection."""
        platform._connected_to_instruments = False
        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, value=0.14, channel_id=0)
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, channel_id=0) == 0.14

    @pytest.mark.parametrize(
        "bus, parameter, value",
        [
            ("drive_q0_rf", Parameter.LO_FREQUENCY, 5e9),
            ("drive_q0_rf", Parameter.IF, 14e6),
            ("drive_q0_rf", Parameter.GAIN, 0.001),
            ("readout_q0_rf", Parameter.LO_FREQUENCY, 8e9),
            ("readout_q0_rf", Parameter.IF, 16e6),
            ("readout_q0_rf", Parameter.GAIN, 0.002),
            ("drive_q0", Parameter.IF, 13e6),
        ],
    )
    def test_set_parameter_no_instrument_connection_QM(self, bus: str, parameter: Parameter, value: float | str | bool):
        """Test platform raises and error if no instrument connection."""
        # Overwrite platform to use Quantum Machines:
        platform = build_platform(runcard=SauronQuantumMachines.runcard)
        platform._connected_to_instruments = False

        platform.set_parameter(alias=bus, parameter=parameter, value=value)
        assert platform.get_parameter(alias=bus, parameter=parameter) == value

    def test_connect_logger(self, platform: Platform):
        platform._connected_to_instruments = True
        platform.instrument_controllers = MagicMock()
        with patch("qililab.platform.platform.logger", autospec=True) as mock_logger:
            platform.connect()
        mock_logger.info.assert_called_once_with("Already connected to the instruments")

    def test_disconnect_logger(self, platform: Platform):
        platform._connected_to_instruments = False
        platform.instrument_controllers = MagicMock()
        with patch("qililab.platform.platform.logger", autospec=True) as mock_logger:
            platform.disconnect()
        mock_logger.info.assert_called_once_with("Already disconnected from the instruments")

    def test_get_element_method_unknown_returns_none(self, platform: Platform):
        """Test get_element method with unknown element."""
        element = platform.get_element(alias="ABC")
        assert element is None

    def test_get_element_with_gate(self, platform: Platform):
        """Test the get_element method with a gate alias."""
        p_gates = platform.digital_compilation_settings.gates.keys()
        all(isinstance(event, GateEventSettings) for gate in p_gates for event in platform.get_element(alias=gate))

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_gates_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.digital_compilation_settings, DigitalCompilationSettings)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        element = platform.get_element(alias="rs_0")
        assert isinstance(element, SGS100A)

    def test_bus_1_awg_instance(self, platform: Platform):
        """Test bus 1 qubit readout instance."""
        element = platform.get_element(alias=f"{InstrumentName.QBLOX_QRM.value}_0")
        assert isinstance(element, QbloxModule)

    @patch("qililab.data_management.open")
    @patch("qililab.data_management.YAML.dump")
    def test_platform_manager_dump_method(self, mock_dump: MagicMock, mock_open: MagicMock, platform: Platform):
        """Test PlatformManager dump method."""
        save_platform(path="runcard.yml", platform=platform)
        mock_open.assert_called_once_with(file=Path("runcard.yml"), mode="w", encoding="utf-8")
        mock_dump.assert_called_once()

    # def test_get_bus_by_qubit_index(self, platform: Platform):
    #     """Test get_bus_by_qubit_index method."""
    #     _, control_bus, readout_bus = platform._get_bus_by_qubit_index(0)
    #     assert isinstance(control_bus, Bus)
    #     assert isinstance(readout_bus, Bus)
    #     assert not isinstance(control_bus.system_control, ReadoutSystemControl)
    #     assert isinstance(readout_bus.system_control, ReadoutSystemControl)

    # def test_get_bus_by_qubit_index_raises_error(self, platform: Platform):
    #     """Test that the get_bus_by_qubit_index method raises an error when there is no bus connected to the port
    #     of the given qubit."""
    #     platform.buses[0].settings.port = 100
    #     with pytest.raises(
    #         ValueError,
    #         match="There can only be one bus connected to a port. There are 0 buses connected to port drive_q0",
    #     ):
    #         platform._get_bus_by_qubit_index(0)
    #     platform.buses[0].settings.port = 0  # Setting it back to normal to not disrupt future tests

    @pytest.mark.parametrize("alias", ["drive_line_q0_bus", "drive_line_q1_bus", "feedline_input_output_bus", "foobar"])
    def test_get_bus_by_alias(self, platform: Platform, alias):
        """Test get_bus_by_alias method"""
        bus = platform._get_bus_by_alias(alias)
        if alias == "foobar":
            assert bus is None
        else:
            assert bus in platform.buses

    def test_print_platform(self, platform: Platform):
        """Test print platform."""
        assert str(platform) == str(YAML().dump(platform.to_dict(), io.BytesIO()))

    # I'm leaving this test here, because there is no test_instruments.py, but should be moved there when created
    def test_print_instruments(self, platform: Platform):
        """Test print instruments."""
        assert str(platform.instruments) == str(YAML().dump(platform.instruments._short_dict(), io.BytesIO()))

    def test_serialization(self, platform: Platform):
        """Test that a serialization of the Platform is possible"""
        runcard_dict = platform.to_dict()
        assert isinstance(runcard_dict, dict)

        new_platform = Platform(runcard=Runcard(**runcard_dict))
        assert isinstance(new_platform, Platform)
        assert str(new_platform) == str(platform)
        assert str(new_platform.name) == str(platform.name)
        assert str(new_platform.buses) == str(platform.buses)
        assert str(new_platform.instruments) == str(platform.instruments)
        assert str(new_platform.instrument_controllers) == str(platform.instrument_controllers)

        new_runcard_dict = new_platform.to_dict()
        assert isinstance(new_runcard_dict, dict)
        assert new_runcard_dict == runcard_dict

        newest_platform = Platform(runcard=Runcard(**new_runcard_dict))
        assert isinstance(newest_platform, Platform)
        assert str(newest_platform) == str(new_platform)
        assert str(newest_platform.name) == str(new_platform.name)
        assert str(newest_platform.buses) == str(new_platform.buses)
        assert str(newest_platform.instruments) == str(new_platform.instruments)
        assert str(newest_platform.instrument_controllers) == str(new_platform.instrument_controllers)


class TestMethods:
    """Unit tests for the methods of the Platform class."""

    def test_session_success(self):
        """Test the session method when everything works successfully."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Run the session successfully
        with platform.session():
            pass  # Simulate a successful experiment execution

        # Ensure methods were called in the correct order
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure cleanup is called in reverse order
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    def test_session_with_exception(self):
        """Test the session method when an exception occurs during execution."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Simulate an exception during the experiment
        with pytest.raises(AttributeError, match="Test Error"):
            with platform.session():
                raise AttributeError("Test Error")

        # Ensure methods were called in the correct order before the exception
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure cleanup is still called in reverse order even after the exception
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    def test_session_with_exception_in_setup(self):
        """Test the session method when an error occurs before turning on instruments."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Raise an exception after connect() and initial_setup() but before turn_on_instruments()
        platform.turn_on_instruments.side_effect = Exception("Instrument failure")

        # Simulate an error after connect() and initial_setup() but before turn_on_instruments()
        with pytest.raises(Exception, match="Instrument failure"):
            with platform.session():
                pass  # The exception will occur inside the context

        # Ensure methods were called until the point of failure
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure turn_off_instruments is not called, but disconnect is called
        platform.turn_off_instruments.assert_not_called()
        platform.disconnect.assert_called_once()

    def test_session_with_exception_in_cleanup(self):
        """Test the session method when an exception occurs during cleanup."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Simulate turn_off_instruments failing
        platform.turn_off_instruments.side_effect = Exception("Turn off instruments error")

        # Simulate no exception during the experiment, but failure during cleanup
        with pytest.raises(Exception, match="Turn off instruments error"):
            with platform.session():
                pass  # No exception during the experiment

        # Ensure methods were called in the correct order
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure the exception is raised in cleanup
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    def test_session_with_multiple_exceptions_in_cleanup(self):
        """Test the session method when multiple exceptions occur during cleanup."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Simulate turn_off_instruments and disconnect failing
        platform.turn_off_instruments.side_effect = Exception("Turn off instruments error")
        platform.disconnect.side_effect = Exception("Disconnect error")

        with pytest.raises(ExceptionGroup) as exc_info:
            with platform.session():
                pass

        # Ensure ExceptionGroup has captured all exceptions
        assert len(exc_info.value.exceptions) == 2
        assert str(exc_info.value.exceptions[0]) == "Turn off instruments error"
        assert str(exc_info.value.exceptions[1]) == "Disconnect error"

        # Ensure methods were called in the correct order
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    def test_compile_circuit(self, platform: Platform):
        """Test the compilation of a qibo Circuit."""
        circuit = Circuit(3)
        circuit.add(gates.X(0))
        circuit.add(gates.X(1))
        circuit.add(gates.Y(0))
        circuit.add(gates.Y(1))
        circuit.add(gates.M(0, 1, 2))

        self._compile_and_assert(platform, circuit, 6)

    def test_compile_pulse_schedule(self, platform: Platform):
        """Test the compilation of a qibo Circuit."""
        pulse_schedule = PulseSchedule()
        drag_pulse = Pulse(
            amplitude=1, phase=0.5, duration=200, frequency=1e9, pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
        )
        readout_pulse = Pulse(amplitude=1, phase=0.5, duration=1500, frequency=1e9, pulse_shape=Rectangular())
        pulse_schedule.add_event(PulseEvent(pulse=drag_pulse, start_time=0), bus_alias="drive_line_q0_bus", delay=0)
        pulse_schedule.add_event(
            PulseEvent(pulse=readout_pulse, start_time=200, qubit=0), bus_alias="feedline_input_output_bus", delay=0
        )

        self._compile_and_assert(platform, pulse_schedule, 2)

    def _compile_and_assert(self, platform: Platform, program: Circuit | PulseSchedule, len_sequences: int):
        sequences = platform.compile(program=program, num_avg=1000, repetition_duration=200_000, num_bins=1)
        assert isinstance(sequences, dict)
        assert len(sequences) == len_sequences
        for alias, sequences_list in sequences.items():
            assert alias in {bus.alias for bus in platform.buses}
            assert isinstance(sequences_list, list)
            assert all(isinstance(sequence, Sequence) for sequence in sequences_list)
            assert sequences_list[0]._program.duration == 200_000 * 1000 + 4 + 4 + 4

    @pytest.mark.parametrize(
        "qprogram_fixture, calibration_fixture",
        [
            ("anneal_qprogram", "calibration"),
            ("anneal_qprogram_with_preparation", "calibration_with_preparation_block"),
        ],
    )
    def test_execute_anneal_program(
        self,
        platform: Platform,
        qprogram_fixture: str,
        flux_to_bus_topology: list[FluxControlTopology],
        calibration_fixture: str,
        request,
    ):
        anneal_qprogram = request.getfixturevalue(qprogram_fixture)
        calibration = request.getfixturevalue(calibration_fixture)

        mock_execute_qprogram = MagicMock()
        mock_execute_qprogram.return_value = QProgramResults()
        platform.execute_qprogram = mock_execute_qprogram  # type: ignore[method-assign]
        platform.analog_compilation_settings.flux_control_topology = flux_to_bus_topology
        transpiler = MagicMock()
        transpiler.return_value = (1, 2)

        results = platform.execute_annealing_program(
            annealing_program_dict=[{"qubit_0": {"sigma_x": 0.1, "sigma_z": 0.2}}],
            transpiler=transpiler,
            calibration=calibration,
            num_averages=2,
            num_shots=1,
        )
        qprogram = mock_execute_qprogram.call_args[1]["qprogram"].with_calibration(calibration)
        assert str(anneal_qprogram) == str(qprogram)
        assert isinstance(results, QProgramResults)

    def test_execute_anneal_program_no_measurement_raises_error(self, platform: Platform, calibration):
        mock_execute_qprogram = MagicMock()
        platform.execute_qprogram = mock_execute_qprogram  # type: ignore[method-assign]
        transpiler = MagicMock()
        transpiler.return_value = (1, 2)
        error_string = "The calibrated measurement is not present in the calibration file."
        with pytest.raises(ValueError, match=error_string):
            platform.execute_annealing_program(
                annealing_program_dict=[{"qubit_0": {"sigma_x": 0.1, "sigma_z": 0.2}}],
                transpiler=transpiler,
                calibration=calibration,
                num_averages=2,
                num_shots=1,
                measurement_block="whatever",
            )

    def test_execute_experiment(self):
        """Test the execute_experiment method of the Platform class."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the execute_experiment method to the real one
        platform.execute_experiment = MethodType(Platform.execute_experiment, platform)

        # Create an autospec of the Experiment class
        mock_experiment = create_autospec(Experiment)

        expected_results_path = "mock/results/path/data.h5"

        # Mock the ExperimentExecutor to ensure it's used correctly
        with patch("qililab.platform.platform.ExperimentExecutor") as MockExecutor:
            mock_executor_instance = MockExecutor.return_value  # Mock instance of ExperimentExecutor
            mock_executor_instance.execute.return_value = expected_results_path

            # Call the method under test
            results_path = platform.execute_experiment(experiment=mock_experiment)

            # Check that ExperimentExecutor was instantiated with the correct arguments
            MockExecutor.assert_called_once_with(platform=platform, experiment=mock_experiment)

            # Ensure the execute method was called on the ExperimentExecutor instance
            mock_executor_instance.execute.assert_called_once()

            # Ensure that execute_experiment returns the correct value
            assert results_path == expected_results_path

    def test_execute_qprogram_with_qblox(self, platform: Platform):
        """Test that the execute method compiles the qprogram, calls the buses to run and return the results."""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)
        qprogram.play(bus="drive_line_q1_bus", waveform=drive_wf)
        qprogram.sync()
        qprogram.play(bus="feedline_input_output_bus", waveform=readout_wf)
        qprogram.play(bus="feedline_input_output_bus_1", waveform=readout_wf)
        qprogram.qblox.acquire(bus="feedline_input_output_bus", weights=weights_wf)
        qprogram.qblox.acquire(bus="feedline_input_output_bus_1", weights=weights_wf)

        with (
            patch("builtins.open") as patched_open,
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run") as run,
            patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results,
            patch.object(QbloxModule, "sync_sequencer") as sync_sequencer,
            patch.object(QbloxModule, "desync_sequencer") as desync_sequencer,
        ):
            acquire_qprogram_results.return_value = [123]
            first_execution_results = platform.execute_qprogram(qprogram=qprogram)

            acquire_qprogram_results.return_value = [456]
            second_execution_results = platform.execute_qprogram(qprogram=qprogram)

            _ = platform.execute_qprogram(qprogram=qprogram, debug=True)

        # assert upload executed only once (2 because there are 2 buses)
        assert upload.call_count == 4

        # assert run executed all three times (6 because there are 2 buses)
        assert run.call_count == 12
        assert acquire_qprogram_results.call_count == 6  # only readout buses
        assert sync_sequencer.call_count == 12  # called as many times as run
        assert desync_sequencer.call_count == 12
        assert first_execution_results.results["feedline_input_output_bus"] == [123]
        assert first_execution_results.results["feedline_input_output_bus_1"] == [123]
        assert second_execution_results.results["feedline_input_output_bus"] == [456]
        assert second_execution_results.results["feedline_input_output_bus_1"] == [456]

        # assure only one debug was called
        assert patched_open.call_count == 1

    def test_execute_qprogram_with_qblox_distortions(self, platform: Platform):
        drive_wf = Square(amplitude=1.0, duration=4)
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        test_waveforms_q0 = Waveforms()
        test_waveforms_q0.add(array=[0.5, 1.0, 0.5, 0.0], index=0)
        test_waveforms_q0.add(array=[0.0, 0.0, 0.0, 0.0], index=1)

        with (
            patch("builtins.open"),
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run"),
            patch.object(Bus, "acquire_qprogram_results"),
            patch.object(QbloxModule, "sync_sequencer"),
            patch.object(QbloxModule, "desync_sequencer"),
        ):
            _ = platform.execute_qprogram(qprogram=qprogram)
            assert test_waveforms_q0.to_dict() == upload.call_args_list[0].kwargs["qpysequence"]._waveforms.to_dict()

    def test_execute_qprogram_with_quantum_machines(self, platform_quantum_machines: Platform):
        """Test that the execute_qprogram method executes the qprogram for Quantum Machines correctly"""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qprogram = QProgram()
        qprogram.play(bus="drive_q0_rf", waveform=drive_wf)
        qprogram.sync()
        qprogram.play(bus="readout_q0_rf", waveform=readout_wf)
        qprogram.measure(bus="readout_q0_rf", waveform=readout_wf, weights=weights_wf)

        with (
            patch("builtins.open") as patched_open,
            patch("qililab.platform.platform.generate_qua_script", return_value=None) as generate_qua,
            patch.object(QuantumMachinesCluster, "config") as config,
            patch.object(QuantumMachinesCluster, "append_configuration") as append_configuration,
            patch.object(QuantumMachinesCluster, "compile") as compile_program,
            patch.object(QuantumMachinesCluster, "run_compiled_program") as run_compiled_program,
            patch.object(QuantumMachinesCluster, "get_acquisitions") as get_acquisitions,
        ):
            cluster = platform_quantum_machines.get_element("qmm")
            config.return_value = cluster.settings.to_qua_config()

            get_acquisitions.return_value = {"I_0": np.array([1, 2, 3]), "Q_0": np.array([4, 5, 6])}
            first_execution_results = platform_quantum_machines.execute_qprogram(qprogram=qprogram)

            get_acquisitions.return_value = {"I_0": np.array([3, 2, 1]), "Q_0": np.array([6, 5, 4])}
            second_execution_results = platform_quantum_machines.execute_qprogram(qprogram=qprogram)

            _ = platform_quantum_machines.execute_qprogram(qprogram=qprogram, debug=True)

        assert compile_program.call_count == 3
        assert append_configuration.call_count == 3
        assert run_compiled_program.call_count == 3
        assert get_acquisitions.call_count == 3

        assert "readout_q0_rf" in first_execution_results.results
        assert len(first_execution_results.results["readout_q0_rf"]) == 1
        assert isinstance(first_execution_results.results["readout_q0_rf"][0], QuantumMachinesMeasurementResult)
        np.testing.assert_array_equal(first_execution_results.results["readout_q0_rf"][0].I, np.array([1, 2, 3]))
        np.testing.assert_array_equal(first_execution_results.results["readout_q0_rf"][0].Q, np.array([4, 5, 6]))

        assert "readout_q0_rf" in second_execution_results.results
        assert len(second_execution_results.results["readout_q0_rf"]) == 1
        assert isinstance(second_execution_results.results["readout_q0_rf"][0], QuantumMachinesMeasurementResult)
        np.testing.assert_array_equal(second_execution_results.results["readout_q0_rf"][0].I, np.array([3, 2, 1]))
        np.testing.assert_array_equal(second_execution_results.results["readout_q0_rf"][0].Q, np.array([6, 5, 4]))

        # assure only one debug was called
        assert patched_open.call_count == 1
        assert generate_qua.call_count == 1

    def test_execute(self, platform: Platform, qblox_results: list[dict]):
        """Test that the execute method calls the buses to run and return the results."""
        # Define pulse schedule
        pulse_schedule = PulseSchedule()
        drag_pulse = Pulse(
            amplitude=1, phase=0.5, duration=200, frequency=1e9, pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
        )
        readout_pulse = Pulse(amplitude=1, phase=0.5, duration=1500, frequency=1e9, pulse_shape=Rectangular())
        pulse_schedule.add_event(PulseEvent(pulse=drag_pulse, start_time=0), bus_alias="drive_line_q0_bus", delay=0)
        pulse_schedule.add_event(
            PulseEvent(pulse=readout_pulse, start_time=200, qubit=0), bus_alias="feedline_input_output_bus", delay=0
        )
        qblox_result = QbloxResult(qblox_raw_results=qblox_results, integration_lengths=[1, 1, 1, 1])
        with patch.object(Bus, "upload") as upload:
            with patch.object(Bus, "run") as run:
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers") as desync:
                        acquire_result.return_value = qblox_result
                        result = platform.execute(
                            program=pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1
                        )

        assert upload.call_count == len(pulse_schedule.elements)
        assert run.call_count == len(pulse_schedule.elements)
        acquire_result.assert_called_once_with()
        assert result == qblox_result
        desync.assert_called()

    def test_execute_with_queue(self, platform: Platform, qblox_results: list[dict]):
        """Test that the execute method adds the obtained results to the given queue."""
        queue: Queue = Queue()
        pulse_schedule = PulseSchedule()
        pulse_schedule.add_event(
            PulseEvent(
                pulse=Pulse(amplitude=1, phase=0.5, duration=1500, frequency=1e9, pulse_shape=Rectangular()),
                start_time=200,
                qubit=0,
            ),
            bus_alias="feedline_input_output_bus",
            delay=0,
        )
        qblox_result = QbloxResult(qblox_raw_results=qblox_results, integration_lengths=[1, 1, 1, 1])
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers") as desync:
                        acquire_result.return_value = qblox_result
                        _ = platform.execute(
                            program=pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1, queue=queue
                        )

        assert len(queue.queue) == 1
        assert queue.get() == qblox_result
        desync.assert_called()

    def test_execute_returns_ordered_measurements(self, platform: Platform, qblox_results: list[dict]):
        """Test that executing with some circuit returns acquisitions with multiple measurements in same order
        as they appear in circuit"""

        # Define circuit
        c = Circuit(2)
        c.add([gates.M(1), gates.M(0), gates.M(0, 1)])  # without ordering, these are retrieved for each sequencer, so
        # the order from qblox qrm will be M(0),M(0),M(1),M(1)

        platform.compile = MagicMock()  # type: ignore # don't care about compilation
        platform.compile.return_value = {"feedline_input_output_bus": None}
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers"):
                        acquire_result.return_value = QbloxResult(
                            qblox_raw_results=qblox_results, integration_lengths=[1, 1, 1, 1]
                        )
                        result = platform.execute(program=c, num_avg=1000, repetition_duration=2000, num_bins=1)

        # check that the order of #measurement # qubit is the same as in the circuit
        assert [(result["measurement"], result["qubit"]) for result in result.qblox_raw_results] == [  # type: ignore
            (0, 1),
            (0, 0),
            (1, 0),
            (1, 1),
        ]

    def test_execute_no_readout_raises_error(self, platform: Platform, qblox_results: list[dict]):
        """Test that executing with some circuit returns acquisitions with multiple measurements in same order
        as they appear in circuit"""

        # Define circuit
        c = Circuit(2)
        c.add([gates.M(1), gates.M(0), gates.M(0, 1)])  # without ordering, these are retrieved for each sequencer, so
        # the order from qblox qrm will be M(0),M(0),M(1),M(1)

        # compile will return nothing and thus
        # readout_buses = [
        #     bus for bus in self.buses if isinstance(bus.system_control, ReadoutSystemControl) and bus.alias in programs
        # ]
        # in platform will be empty
        platform.compile = MagicMock()  # type: ignore # don't care about compilation
        platform.compile.return_value = {"drive_line_q0_bus": None}
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers"):
                        acquire_result.return_value = QbloxResult(
                            qblox_raw_results=qblox_results, integration_lengths=[1, 1, 1, 1]
                        )
                        error_string = "There are no readout buses in the platform."
                        with pytest.raises(ValueError, match=error_string):
                            _ = platform.execute(program=c, num_avg=1000, repetition_duration=20_000, num_bins=1)

    def test_order_results_circuit_M_neq_acquisitions(self, platform: Platform, qblox_results: list[dict]):
        """Test that executing with some circuit returns acquisitions with multiple measurements in same order
        as they appear in circuit"""

        # Define circuit
        c = Circuit(2)
        c.add([gates.M(1), gates.M(0, 1)])  # without ordering, these are retrieved for each sequencer, so
        # the order from qblox qrm will be M(0),M(1),M(1)
        n_m = len([qubit for gate in c.queue for qubit in gate.qubits if isinstance(gate, gates.M)])

        platform.compile = MagicMock()  # type: ignore[method-assign] # don't care about compilation
        platform.compile.return_value = {"feedline_input_output_bus": None}
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers"):
                        acquire_result.return_value = QbloxResult(
                            qblox_raw_results=qblox_results, integration_lengths=[1, 1, 1, 1]
                        )
                        error_string = f"Number of measurements in the circuit {n_m} does not match number of acquisitions {len(qblox_results)}"
                        with pytest.raises(ValueError, match=error_string):
                            _ = platform.execute(program=c, num_avg=1000, repetition_duration=2000, num_bins=1)

    def test_execute_raises_error_if_program_type_wrong(self, platform: Platform):
        """Test that `Platform.execute` raises an error if the program sent is not a Circuit or a PulseSchedule."""
        c = Circuit(1)
        c.add(gates.M(0))
        program = [c, c]
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Program to execute can only be either a single circuit or a pulse schedule. Got program of type {type(program)} instead"
            ),
        ):
            platform.execute(program=program, num_avg=1000, repetition_duration=2000, num_bins=1)

    def test_execute_stack_2qrm(self, platform: Platform):
        """Test that the execute stacks results when more than one qrm is called."""
        # build mock qblox results
        qblox_raw_results = QbloxResult(
            integration_lengths=[20],
            qblox_raw_results=[
                {
                    "scope": {
                        "path0": {"data": [1, 1, 1, 1, 1, 1, 1, 1], "out-of-range": False, "avg_cnt": 1000},
                        "path1": {"data": [0, 0, 0, 0, 0, 0, 0, 0], "out-of-range": False, "avg_cnt": 1000},
                    },
                    "bins": {
                        "integration": {"path0": [1, 1, 1, 1], "path1": [0, 0, 0, 0]},
                        "threshold": [0.5, 0.5, 0.5, 0.5],
                        "avg_cnt": [1000, 1000, 1000, 1000],
                    },
                    "qubit": 0,
                    "measurement": 0,
                }
            ],
        )
        pulse_schedule = PulseSchedule()
        # mock compile method
        platform.compile = MagicMock()  # type: ignore[method-assign]
        platform.compile.return_value = {"feedline_input_output_bus": None, "feedline_input_output_bus_2": None}
        # mock execution
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers"):
                        acquire_result.return_value = qblox_raw_results
                        result = platform.execute(
                            program=pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1
                        )
        assert len(result.qblox_raw_results) == 2  # type: ignore[attr-defined]
        assert qblox_raw_results.qblox_raw_results[0] == result.qblox_raw_results[0]  # type: ignore[attr-defined]
        assert qblox_raw_results.qblox_raw_results[0] == result.qblox_raw_results[1]  # type: ignore[attr-defined]

    @pytest.mark.parametrize("parameter", [Parameter.AMPLITUDE, Parameter.DURATION, Parameter.PHASE])
    @pytest.mark.parametrize("gate", ["I(0)", "X(0)", "Y(0)"])
    def test_get_parameter_of_gates(self, parameter, gate, platform: Platform):
        """Test the ``get_parameter`` method with gates."""
        gate_settings = platform.digital_compilation_settings.gates[gate][0]
        assert platform.get_parameter(parameter=parameter, alias=gate) == getattr(gate_settings.pulse, parameter.value)

    @pytest.mark.parametrize("parameter", [Parameter.DRAG_COEFFICIENT, Parameter.NUM_SIGMAS])
    @pytest.mark.parametrize("gate", ["X(0)", "Y(0)"])
    def test_get_parameter_of_pulse_shapes(self, parameter, gate, platform: Platform):
        """Test the ``get_parameter`` method with gates."""
        gate_settings = platform.digital_compilation_settings.gates[gate][0]
        assert platform.get_parameter(parameter=parameter, alias=gate) == gate_settings.pulse.shape[parameter.value]

    def test_get_parameter_of_gates_raises_error(self, platform: Platform):
        """Test that the ``get_parameter`` method with gates raises an error when a gate is not found."""
        with pytest.raises(KeyError, match="Gate Drag for qubits 3 not found in settings"):
            platform.get_parameter(parameter=Parameter.AMPLITUDE, alias="Drag(3)")

    @pytest.mark.parametrize("parameter", [Parameter.DELAY_BEFORE_READOUT])
    def test_get_parameter_of_platform(self, parameter, platform: Platform):
        """Test the ``get_parameter`` method with platform parameters."""
        value = platform.get_parameter(parameter=parameter, alias="platform")
        assert value == 0

    def test_get_parameter_with_delay(self, platform: Platform):
        """Test the ``get_parameter`` method with the delay of a bus."""
        value = platform.get_parameter(parameter=Parameter.DELAY, alias="drive_line_q0_bus")
        assert value == 0

    @pytest.mark.parametrize(
        "parameter",
        [Parameter.IF, Parameter.GAIN, Parameter.LO_FREQUENCY, Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT2],
    )
    def test_get_parameter_of_bus(self, parameter, platform: Platform):
        """Test the ``get_parameter`` method with the parameters of a bus."""
        CHANNEL_ID = 0
        bus = platform._get_bus_by_alias(alias="drive_line_q0_bus")
        assert bus is not None
        assert bus.get_parameter(parameter=parameter, channel_id=CHANNEL_ID) == platform.get_parameter(
            parameter=parameter, alias="drive_line_q0_bus", channel_id=CHANNEL_ID
        )

    def test_no_bus_to_flux_raises_error(self, platform: Platform):
        """Test that if flux to bus topology is not specified an error is raised"""
        platform.analog_compilation_settings = None
        error_string = "Flux to bus topology not given in the runcard"
        with pytest.raises(ValueError, match=error_string):
            platform.execute_annealing_program(
                annealing_program_dict=[{}],
                calibration=MagicMock(),
                transpiler=MagicMock(),
                num_averages=2,
                num_shots=1,
            )

    def test_get_element_flux(self, platform: Platform):
        """Get the bus from a flux using get_element"""
        for flux in ["phiz_q0", "phix_c0_1"]:
            bus = platform.get_element(flux)
            assert bus.alias == next(flux_bus.bus for flux_bus in platform.analog_compilation_settings.flux_control_topology if flux_bus.flux == flux)
