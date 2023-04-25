"""This file contains unit tests for the ``CircuitToPulses`` class."""
import pytest
from qibo.gates import M, X, Y
from qibo.models import Circuit

from qililab.chip import Chip
from qililab.pulse import CircuitToPulses, PulseSchedule, PulseShape
from qililab.pulse.hardware_gates import HardwareGate, HardwareGateFactory
from qililab.settings import RuncardSchema
from qililab.typings import Parameter


@pytest.fixture(name="platform_settings")
def fixture_platform_settings() -> RuncardSchema.PlatformSettings:
    """Fixture that returns an instance of a ``RuncardSchema.PlatformSettings`` class."""
    settings = {
        "id_": 0,
        "category": "platform",
        "name": "dummy",
        "device_id": 9,
        "minimum_clock_time": 4,
        "delay_between_pulses": 0,
        "delay_before_readout": 0,
        "master_amplitude_gate": 1,
        "master_duration_gate": 40,
        "reset_method": "passive",
        "passive_reset_duration": 100,
        "timings_calculation_method": "as_soon_as_possible",
        "operations": [],
        "gates": [
            {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
            {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
            {
                "name": "X",
                "amplitude": 0.8,
                "phase": 0,
                "duration": 45,
                "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 0},
            },
            {
                "name": "Y",
                "amplitude": 0.3,
                "phase": 90,
                "duration": 40,
                "shape": {"name": "gaussian", "num_sigmas": 4},
            },
        ],
    }
    return RuncardSchema.PlatformSettings(**settings)  # type: ignore  # pylint: disable=unexpected-keyword-arg


class TestInitialization:
    """Unit tests for the initialization of a ``CircuitToPulses`` class."""

    def test_gate_settings_are_set_during_instantiation(self, platform_settings: RuncardSchema.PlatformSettings):
        """Test that during initialization of the ``CircuitToPulses`` class we set the settings of all the hardware
        gates."""
        _ = CircuitToPulses(settings=platform_settings)

        for gate in HardwareGateFactory.pulsed_gates.values():
            if gate.name not in platform_settings.gate_names:
                # Some gates derive from others (such as RY from Y), thus they have no settings
                assert gate.settings is None
            else:
                settings = platform_settings.get_gate(name=gate.name)
                assert isinstance(gate.settings, HardwareGate.HardwareGateSettings)
                assert gate.settings.amplitude == settings.amplitude
                assert gate.settings.duration == settings.duration
                assert gate.settings.phase == settings.phase
                assert isinstance(gate.settings.shape, dict)
                assert gate.settings.shape == settings.shape

    def test_gate_settings_are_updated_during_instantiation(self, platform_settings: RuncardSchema.PlatformSettings):
        """Test that gate settings are updated if the ``CircuitToPulses`` class is re-instantiated with
        different settings."""
        X = HardwareGateFactory.get(name="X")

        _ = CircuitToPulses(settings=platform_settings)

        assert X.settings.amplitude == 0.8

        platform_settings.set_parameter(alias="X", parameter=Parameter.AMPLITUDE, value=123)

        _ = CircuitToPulses(settings=platform_settings)

        assert X.settings.amplitude == 123


@pytest.fixture(name="chip")
def fixture_chip():
    """Fixture that returns an instance of a ``Chip`` class."""
    settings = {
        "id_": 0,
        "category": "chip",
        "nodes": [
            {"name": "port", "id_": 0, "nodes": [3]},
            {"name": "port", "id_": 1, "nodes": [2]},
            {"name": "resonator", "alias": "resonator", "id_": 2, "frequency": 8072600000, "nodes": [1, 3]},
            {
                "name": "qubit",
                "alias": "qubit",
                "id_": 3,
                "qubit_index": 0,
                "frequency": 6532800000,
                "nodes": [0, 2],
            },
        ],
    }
    return Chip(**settings)


class TestTranslation:
    """Unit tests for the ``translate`` method of the ``CircuitToPulses`` class."""

    def test_translate(self, platform_settings: RuncardSchema.PlatformSettings, chip: Chip):
        """Test the ``translate`` method of the ``CircuitToPulses`` class."""
        translator = CircuitToPulses(settings=platform_settings)

        circuit = Circuit(1)
        circuit.add(X(0))
        circuit.add(Y(0))
        circuit.add(M(0))

        pulsed_gates = [
            platform_settings.get_gate(name="X"),
            platform_settings.get_gate(name="Y"),
            platform_settings.get_gate(name="M"),
        ]

        pulse_schedules = translator.translate(circuits=[circuit], chip=chip)

        assert isinstance(pulse_schedules, list)
        assert len(pulse_schedules) == 1
        assert isinstance(pulse_schedules[0], PulseSchedule)

        pulse_schedule = pulse_schedules[0]

        assert len(pulse_schedule) == 2  # it contains pulses for 2 buses

        control_pulse_bus_schedule = pulse_schedule.elements[0]

        assert control_pulse_bus_schedule.port == 0  # it targets the qubit, which is connected to port 0
        assert len(control_pulse_bus_schedule.timeline) == 2  # it contains 2 gates

        readout_pulse_bus_schedule = pulse_schedule.elements[1]

        assert readout_pulse_bus_schedule.port == 1
        assert len(readout_pulse_bus_schedule.timeline) == 1

        all_pulse_events = control_pulse_bus_schedule.timeline + readout_pulse_bus_schedule.timeline

        for pulse_event, gate_settings in zip(all_pulse_events, pulsed_gates):
            pulse = pulse_event.pulse
            assert pulse.amplitude == gate_settings.amplitude
            assert pulse.duration == gate_settings.duration
            assert pulse.phase == gate_settings.phase

            if gate_settings.name == "M":
                frequency = chip.get_node_from_alias(alias="resonator").frequency
            else:
                frequency = chip.get_node_from_alias(alias="qubit").frequency

            assert pulse.frequency == frequency
            assert isinstance(pulse.pulse_shape, PulseShape)
            for name, value in gate_settings.shape.items():
                assert getattr(pulse.pulse_shape, name) == value

    def test_translate_pulses_with_duration_not_multiple_of_minimum_clock_time(
        self, platform_settings: RuncardSchema.PlatformSettings, chip: Chip
    ):
        """Test that when the duration of a pulse is not a multiple of the minimum clock time, the next pulse
        start time is delayed by ``pulse_time mod min_clock_time``."""
        translator = CircuitToPulses(settings=platform_settings)

        circuit = Circuit(1)
        circuit.add(X(0))
        circuit.add(Y(0))
        circuit.add(M(0))

        pulse_schedule = translator.translate(circuits=[circuit], chip=chip)[0]

        expected_start_times = [0, 48, 88]  # X has a duration of 45ns, but Y doesn't start until 48ns!

        pulse_events = pulse_schedule.elements[0].timeline + pulse_schedule.elements[1].timeline

        for pulse_event, expected_start_time in zip(pulse_events, expected_start_times):
            assert pulse_event.start_time == expected_start_time
