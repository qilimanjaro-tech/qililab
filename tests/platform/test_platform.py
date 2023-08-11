"""Tests for the Platform class."""
from queue import Queue
from unittest.mock import MagicMock, patch

import pytest
from qibo import gates
from qibo.models import Circuit
from qpysequence import Sequence

from qililab import logger, save_platform
from qililab.chip import Qubit
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.instruments import AWG, AWGAnalogDigitalConverter, SignalGenerator
from qililab.platform import Bus, Buses, Platform, Schema
from qililab.pulse import Drag, Pulse, PulseEvent, PulseSchedule, Rectangular
from qililab.settings import RuncardSchema
from qililab.settings.gate_settings import GateEventSettings
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import InstrumentName
from tests.data import Galadriel
from tests.test_utils import platform_db, platform_yaml


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=Galadriel.runcard)


@pytest.mark.parametrize("platform", [platform_db(runcard=Galadriel.runcard), platform_yaml(runcard=Galadriel.runcard)])
class TestPlatform:
    """Unit tests checking the Platform attributes and methods."""

    def test_id_property(self, platform: Platform):
        """Test id property."""
        assert platform.id_ == platform.settings.id_

    def test_name_property(self, platform: Platform):
        """Test name property."""
        assert platform.name == platform.settings.name

    def test_category_property(self, platform: Platform):
        """Test category property."""
        assert platform.category == platform.settings.category

    def test_num_qubits_property(self, platform: Platform):
        """Test num_qubits property."""
        assert platform.num_qubits == platform.chip.num_qubits

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_get_element_method_unknown_returns_none(self, platform: Platform):
        """Test get_element method with unknown element."""
        element = platform.get_element(alias="ABC")
        assert element is None

    def test_get_element_with_gate(self, platform: Platform):
        """Test the get_element method with a gate alias."""
        gates = platform.settings.gates.keys()
        all(isinstance(event, GateEventSettings) for gate in gates for event in platform.get_element(alias=gate))

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.settings, RuncardSchema.PlatformSettings)

    def test_schema_instance(self, platform: Platform):
        """Test schema instance."""
        assert isinstance(platform.schema, Schema)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        element = platform.get_element(alias="rs_0")
        assert isinstance(element, SignalGenerator)

    def test_qubit_0_instance(self, platform: Platform):
        """Test qubit 1 instance."""
        element = platform.get_element(alias="qubit")
        assert isinstance(element, Qubit)

    def test_bus_0_awg_instance(self, platform: Platform):
        """Test bus 0 qubit control instance."""
        element = platform.get_element(alias=InstrumentName.QBLOX_QCM.value)
        assert isinstance(element, AWG)

    def test_bus_1_awg_instance(self, platform: Platform):
        """Test bus 1 qubit readout instance."""
        element = platform.get_element(alias=InstrumentName.QBLOX_QRM.value)
        assert isinstance(element, AWGAnalogDigitalConverter)

    @patch("qililab.platform.platform_manager.yaml.dump")
    def test_platform_manager_dump_method(self, mock_dump: MagicMock, platform: Platform):
        """Test PlatformManager dump method."""
        save_platform(platform=platform)
        with pytest.raises(NotImplementedError):
            save_platform(platform=platform, database=True)
        mock_dump.assert_called()

    def test_get_bus_by_qubit_index(self, platform: Platform):
        """Test get_bus_by_qubit_index method."""
        _, control_bus, readout_bus = platform.get_bus_by_qubit_index(0)
        assert isinstance(control_bus, Bus)
        assert isinstance(readout_bus, Bus)
        assert not isinstance(control_bus.system_control, ReadoutSystemControl)
        assert isinstance(readout_bus.system_control, ReadoutSystemControl)

    def test_get_bus_by_qubit_index_raises_error(self, platform: Platform):
        """Test that the get_bus_by_qubit_index method raises an error when there is no bus connected to the port
        of the given qubit."""
        platform.buses[0].settings.port = 100
        with pytest.raises(
            ValueError, match="There can only be one bus connected to a port. There are 0 buses connected to port 0"
        ):
            platform.get_bus_by_qubit_index(0)

    @pytest.mark.parametrize("alias", ["drive_line_bus", "feedline_input_output_bus", "foobar"])
    def test_get_bus_by_alias(self, platform: Platform, alias):
        """Test get_bus_by_alias method"""
        bus = platform.get_bus_by_alias(alias)
        if alias == "foobar":
            assert bus is None
        if bus is not None:
            assert bus in platform.buses


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
        pulse_schedule.add_event(PulseEvent(pulse=drag_pulse, start_time=0), port=0, port_delay=0)
        pulse_schedule.add_event(PulseEvent(pulse=readout_pulse, start_time=200, qubit=0), port=1, port_delay=0)

        self._compile_and_assert(platform, pulse_schedule, 2)

    def _compile_and_assert(self, platform: Platform, program: Circuit | PulseSchedule, len_sequences: int):
        sequences = platform.compile(program=program, num_avg=1000, repetition_duration=2000, num_bins=1)
        assert isinstance(sequences, dict)
        assert len(sequences) == len_sequences
        for alias, sequences in sequences.items():
            assert alias in {bus.alias for bus in platform.buses}
            assert isinstance(sequences, list)
            assert len(sequences) == 1
            assert isinstance(sequences[0], Sequence)
            assert sequences[0]._program.duration == 2000 * 1000 + 4

    def test_execute(self, platform: Platform):
        """Test that the execute method calls the buses to run and return the results."""
        with patch.object(Bus, "upload") as upload:
            with patch.object(Bus, "run") as run:
                with patch.object(Bus, "acquire_result") as acquire_result:
                    acquire_result.return_value = 123
                    result = platform.execute(
                        program=PulseSchedule(), num_avg=1000, repetition_duration=2000, num_bins=1
                    )

        assert upload.call_count == len(platform.buses)
        assert run.call_count == len(platform.buses)
        acquire_result.assert_called_once_with()
        assert result == 123

    def test_execute_with_queue(self, platform: Platform):
        """Test that the execute method adds the obtained results to the given queue."""
        queue: Queue = Queue()
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result") as acquire_result:
                    acquire_result.return_value = 123
                    _ = platform.execute(
                        program=PulseSchedule(), num_avg=1000, repetition_duration=2000, num_bins=1, queue=queue
                    )

        assert len(queue.queue) == 1
        assert queue.get() == 123

    def test_execute_raises_error_if_no_readout_buses_present(self, platform: Platform):
        """Test that `Platform.execute` raises an error when the platform contains more than one readout bus."""
        platform.buses.elements = []
        with pytest.raises(ValueError, match="There are no readout buses in the platform."):
            platform.execute(program=PulseSchedule(), num_avg=1000, repetition_duration=2000, num_bins=1)

    def test_execute_raises_error_if_more_than_one_readout_bus_present(self, platform: Platform):
        """Test that `Platform.execute` raises an error when the platform contains more than one readout bus."""
        platform.buses.add(
            Bus(settings=Galadriel.buses[1], platform_instruments=platform.instruments, chip=platform.chip)
        )
        with patch.object(Bus, "upload"):
            with patch.object(Bus, "run"):
                with patch.object(Bus, "acquire_result"):
                    with patch("qililab.platform.platform.logger") as mock_logger:
                        _ = platform.execute(
                            program=PulseSchedule(), num_avg=1000, repetition_duration=2000, num_bins=1
                        )

        mock_logger.error.assert_called_once_with("Only One Readout Bus allowed. Reading only from the first one.")
