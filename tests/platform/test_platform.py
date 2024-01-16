"""Tests for the Platform class."""
import copy
import io
import re
from pathlib import Path
from queue import Queue
from unittest.mock import MagicMock, patch

import pytest
from qibo import gates
from qibo.models import Circuit
from qpysequence import Sequence
from ruamel.yaml import YAML

from qililab import save_platform
from qililab.chip import Chip, Qubit
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.instrument_controllers import InstrumentControllers
from qililab.instruments import AWG, AWGAnalogDigitalConverter, SignalGenerator
from qililab.instruments.instruments import Instruments
from qililab.instruments.qblox import QbloxModule
from qililab.platform import Bus, Buses, Platform
from qililab.pulse import Drag, Pulse, PulseEvent, PulseSchedule, Rectangular
from qililab.qprogram import QProgram
from qililab.settings import Runcard
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import InstrumentName, Parameter
from qililab.waveforms import IQPair, Square
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="runcard")
def fixture_runcard():
    return Runcard(**copy.deepcopy(Galadriel.runcard))


class TestPlatformInitialization:
    """Unit tests for the Platform class initialization"""

    def test_init_method(self, runcard):
        """Test initialization of the class"""
        platform = Platform(runcard=runcard)

        assert platform.name == runcard.name
        assert isinstance(platform.name, str)
        assert platform.device_id == runcard.device_id
        assert isinstance(platform.device_id, int)
        assert platform.gates_settings == runcard.gates_settings
        assert isinstance(platform.gates_settings, Runcard.GatesSettings)
        assert isinstance(platform.instruments, Instruments)
        assert isinstance(platform.instrument_controllers, InstrumentControllers)
        assert isinstance(platform.chip, Chip)
        assert isinstance(platform.buses, Buses)
        assert platform.connection is None
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

    def test_set_parameter_no_instrument_connection(self, platform: Platform):
        """Test platform raises and error if no instrument connection."""
        platform._connected_to_instruments = False
        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, value=0.14, channel_id=0)
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, channel_id=0) == 0.14

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

    def test_get_qrm_ch_id_from_qubit(self, platform: Platform):
        """Test that get_ch_id_from_qubits gets the channel id it should get from the runcard"""
        channel_id = platform.get_qrm_ch_id_from_qubit(alias="feedline_input_output_bus", qubit_index=0)
        assert channel_id == 0

    def test_get_qrm_ch_id_from_qubit_error_no_bus(self, platform: Platform):
        """Test that the method raises an error if the alias is not in the buses returned."""
        alias = "dummy"
        qubit_id = 0
        error_string = f"Could not find bus with alias {alias} for qubit {qubit_id}"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            platform.get_qrm_ch_id_from_qubit(alias=alias, qubit_index=qubit_id)

    def test_get_element_method_unknown_returns_none(self, platform: Platform):
        """Test get_element method with unknown element."""
        element = platform.get_element(alias="ABC")
        assert element is None

    def test_get_element_with_gate(self, platform: Platform):
        """Test the get_element method with a gate alias."""
        p_gates = platform.gates_settings.gates.keys()
        all(isinstance(event, GateEventSettings) for gate in p_gates for event in platform.get_element(alias=gate))

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_gates_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.gates_settings, Runcard.GatesSettings)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        element = platform.get_element(alias="rs_0")
        assert isinstance(element, SignalGenerator)

    def test_qubit_0_instance(self, platform: Platform):
        """Test qubit 0 instance."""
        element = platform.get_element(alias="q0")
        assert isinstance(element, Qubit)

    def test_bus_0_awg_instance(self, platform: Platform):
        """Test bus 0 qubit control instance."""
        element = platform.get_element(alias=InstrumentName.QBLOX_QCM.value)
        assert isinstance(element, AWG)

    def test_bus_1_awg_instance(self, platform: Platform):
        """Test bus 1 qubit readout instance."""
        element = platform.get_element(alias=InstrumentName.QBLOX_QRM.value)
        assert isinstance(element, AWGAnalogDigitalConverter)

    @patch("qililab.data_management.open")
    @patch("qililab.data_management.YAML.dump")
    def test_platform_manager_dump_method(self, mock_dump: MagicMock, mock_open: MagicMock, platform: Platform):
        """Test PlatformManager dump method."""
        save_platform(path="runcard.yml", platform=platform)
        mock_open.assert_called_once_with(file=Path("runcard.yml"), mode="w", encoding="utf-8")
        mock_dump.assert_called_once()

    def test_get_bus_by_qubit_index(self, platform: Platform):
        """Test get_bus_by_qubit_index method."""
        _, control_bus, readout_bus = platform._get_bus_by_qubit_index(0)
        assert isinstance(control_bus, Bus)
        assert isinstance(readout_bus, Bus)
        assert not isinstance(control_bus.system_control, ReadoutSystemControl)
        assert isinstance(readout_bus.system_control, ReadoutSystemControl)

    def test_get_bus_by_qubit_index_raises_error(self, platform: Platform):
        """Test that the get_bus_by_qubit_index method raises an error when there is no bus connected to the port
        of the given qubit."""
        platform.buses[0].settings.port = 100
        with pytest.raises(
            ValueError,
            match="There can only be one bus connected to a port. There are 0 buses connected to port drive_q0",
        ):
            platform._get_bus_by_qubit_index(0)
        platform.buses[0].settings.port = 0  # Setting it back to normal to not disrupt future tests

    @pytest.mark.parametrize("alias", ["drive_line_bus", "feedline_input_output_bus", "foobar"])
    def test_get_bus_by_alias(self, platform: Platform, alias):
        """Test get_bus_by_alias method"""
        bus = platform._get_bus_by_alias(alias)
        if alias == "foobar":
            assert bus is None
        if bus is not None:
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
        assert str(new_platform.device_id) == str(platform.device_id)
        assert str(new_platform.buses) == str(platform.buses)
        assert str(new_platform.chip) == str(platform.chip)
        assert str(new_platform.instruments) == str(platform.instruments)
        assert str(new_platform.instrument_controllers) == str(platform.instrument_controllers)

        new_runcard_dict = new_platform.to_dict()
        assert isinstance(new_runcard_dict, dict)
        assert new_runcard_dict == runcard_dict

        newest_platform = Platform(runcard=Runcard(**new_runcard_dict))
        assert isinstance(newest_platform, Platform)
        assert str(newest_platform) == str(new_platform)
        assert str(newest_platform.name) == str(new_platform.name)
        assert str(newest_platform.device_id) == str(new_platform.device_id)
        assert str(newest_platform.buses) == str(new_platform.buses)
        assert str(newest_platform.chip) == str(new_platform.chip)
        assert str(newest_platform.instruments) == str(new_platform.instruments)
        assert str(newest_platform.instrument_controllers) == str(new_platform.instrument_controllers)


class TestMethods:
    """Unit tests for the methods of the Platform class."""

    def test_compile_circuit(self, platform: Platform):
        """Test the compilation of a qibo Circuit."""
        circuit = Circuit(1)
        circuit.add(gates.X(0))
        circuit.add(gates.Y(0))
        circuit.add(gates.M(0))

        self._compile_and_assert(platform, circuit, 3)

    def test_compile_pulse_schedule(self, platform: Platform):
        """Test the compilation of a qibo Circuit."""
        pulse_schedule = PulseSchedule()
        drag_pulse = Pulse(
            amplitude=1, phase=0.5, duration=200, frequency=1e9, pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
        )
        readout_pulse = Pulse(amplitude=1, phase=0.5, duration=1500, frequency=1e9, pulse_shape=Rectangular())
        pulse_schedule.add_event(PulseEvent(pulse=drag_pulse, start_time=0), port="drive_q0", port_delay=0)
        pulse_schedule.add_event(
            PulseEvent(pulse=readout_pulse, start_time=200, qubit=0), port="feedline_input", port_delay=0
        )

        self._compile_and_assert(platform, pulse_schedule, 2)

    def _compile_and_assert(self, platform: Platform, program: Circuit | PulseSchedule, len_sequences: int):
        sequences = platform.compile(program=program, num_avg=1000, repetition_duration=200_000, num_bins=1)
        assert isinstance(sequences, dict)
        assert len(sequences) == len_sequences
        for alias, sequence in sequences.items():
            assert alias in {bus.alias for bus in platform.buses}
            assert isinstance(sequence, list)
            assert len(sequence) == 1
            assert isinstance(sequence[0], Sequence)
            assert sequence[0]._program.duration == 200_000 * 1000 + 4

    def test_execute_qprogram(self, platform: Platform):
        """Test that the execute method compiles the qprogram, calls the buses to run and return the results."""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)
        qprogram.sync()
        qprogram.play(bus="feedline_input_output_bus", waveform=readout_wf)
        qprogram.acquire(bus="feedline_input_output_bus", weights=weights_wf)

        with patch.object(Bus, "upload_qpysequence") as upload:
            with patch.object(Bus, "run") as run:
                with patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results:
                    with patch.object(QbloxModule, "desync_sequencers") as desync:
                        acquire_qprogram_results.return_value = 123
                        results = platform.execute_qprogram(qprogram=qprogram)

        assert upload.call_count == 2
        assert run.call_count == 2
        acquire_qprogram_results.assert_called_once()
        assert results == {"feedline_input_output_bus": 123}
        desync.assert_called()

    def test_execute(self, platform: Platform):
        """Test that the execute method calls the buses to run and return the results."""
        # Define pulse schedule
        pulse_schedule = PulseSchedule()
        drag_pulse = Pulse(
            amplitude=1, phase=0.5, duration=200, frequency=1e9, pulse_shape=Drag(num_sigmas=4, drag_coefficient=0.5)
        )
        readout_pulse = Pulse(amplitude=1, phase=0.5, duration=1500, frequency=1e9, pulse_shape=Rectangular())
        pulse_schedule.add_event(PulseEvent(pulse=drag_pulse, start_time=0), port="drive_q0", port_delay=0)
        pulse_schedule.add_event(
            PulseEvent(pulse=readout_pulse, start_time=200, qubit=0), port="feedline_input", port_delay=0
        )
        with patch.object(Bus, "upload") as upload:
            with patch.object(Bus, "run") as run:
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers") as desync:
                        acquire_result.return_value = 123
                        result = platform.execute(
                            program=pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1
                        )

        assert upload.call_count == len(pulse_schedule.elements)
        assert run.call_count == len(pulse_schedule.elements)
        acquire_result.assert_called_once_with()
        assert result == 123
        desync.assert_called()

    def test_execute_with_queue(self, platform: Platform):
        """Test that the execute method adds the obtained results to the given queue."""
        queue: Queue = Queue()
        pulse_schedule = PulseSchedule()
        pulse_schedule.add_event(
            PulseEvent(
                pulse=Pulse(amplitude=1, phase=0.5, duration=1500, frequency=1e9, pulse_shape=Rectangular()),
                start_time=200,
                qubit=0,
            ),
            port="feedline_input",
            port_delay=0,
        )
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result") as acquire_result:
                    with patch.object(QbloxModule, "desync_sequencers") as desync:
                        acquire_result.return_value = 123
                        _ = platform.execute(
                            program=pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1, queue=queue
                        )

        assert len(queue.queue) == 1
        assert queue.get() == 123
        desync.assert_called()

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

    @pytest.mark.parametrize("parameter", [Parameter.AMPLITUDE, Parameter.DURATION, Parameter.PHASE])
    @pytest.mark.parametrize("gate", ["I(0)", "X(0)", "Y(0)"])
    def test_get_parameter_of_gates(self, parameter, gate, platform: Platform):
        """Test the ``get_parameter`` method with gates."""
        gate_settings = platform.gates_settings.gates[gate][0]
        assert platform.get_parameter(parameter=parameter, alias=gate) == getattr(gate_settings.pulse, parameter.value)

    @pytest.mark.parametrize("parameter", [Parameter.DRAG_COEFFICIENT, Parameter.NUM_SIGMAS])
    @pytest.mark.parametrize("gate", ["X(0)", "Y(0)"])
    def test_get_parameter_of_pulse_shapes(self, parameter, gate, platform: Platform):
        """Test the ``get_parameter`` method with gates."""
        gate_settings = platform.gates_settings.gates[gate][0]
        assert platform.get_parameter(parameter=parameter, alias=gate) == gate_settings.pulse.shape[parameter.value]

    def test_get_parameter_of_gates_raises_error(self, platform: Platform):
        """Test that the ``get_parameter`` method with gates raises an error when a gate is not found."""
        with pytest.raises(KeyError, match="Gate Drag for qubits 3 not found in settings"):
            platform.get_parameter(parameter=Parameter.AMPLITUDE, alias="Drag(3)")

    @pytest.mark.parametrize("parameter", [Parameter.DELAY_BETWEEN_PULSES, Parameter.DELAY_BEFORE_READOUT])
    def test_get_parameter_of_platform(self, parameter, platform: Platform):
        """Test the ``get_parameter`` method with platform parameters."""
        value = getattr(platform.gates_settings, parameter.value)
        assert value == platform.get_parameter(parameter=parameter, alias="platform")

    def test_get_parameter_with_delay(self, platform: Platform):
        """Test the ``get_parameter`` method with the delay of a bus."""
        bus = platform._get_bus_by_alias(alias="drive_line_q0_bus")
        assert bus is not None
        assert bus.delay == platform.get_parameter(parameter=Parameter.DELAY, alias="drive_line_q0_bus")

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

    def test_get_parameter_of_qblox_module_without_channel_id(self, platform: Platform):
        """Test that getting a parameter of a ``QbloxModule`` with multiple sequencers without specifying a channel
        id still works."""
        bus = platform._get_bus_by_alias(alias="drive_line_q0_bus")
        awg = bus.system_control.instruments[0]
        assert isinstance(awg, QbloxModule)
        sequencer = awg.get_sequencers_from_chip_port_id(bus.port)[0]
        assert (sequencer.gain_i, sequencer.gain_q) == platform.get_parameter(
            parameter=Parameter.GAIN, alias="drive_line_q0_bus"
        )

    def test_get_parameter_of_qblox_module_without_channel_id_and_1_sequencer(self, platform: Platform):
        """Test that we can get a parameter of a ``QbloxModule`` with one sequencers without specifying a channel
        id."""
        bus = platform._get_bus_by_alias(alias="drive_line_q0_bus")
        assert isinstance(bus, Bus)
        qblox_module = bus.system_control.instruments[0]
        assert isinstance(qblox_module, QbloxModule)
        qblox_module.settings.num_sequencers = 1
        assert platform.get_parameter(parameter=Parameter.GAIN, alias="drive_line_q0_bus") == bus.get_parameter(
            parameter=Parameter.GAIN
        )
