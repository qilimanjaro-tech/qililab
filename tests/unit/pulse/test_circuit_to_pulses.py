"""This file contains unit tests for the ``CircuitToPulses`` class."""
import copy

import numpy as np
import pytest
from qibo.gates import M, X, Y
from qibo.models import Circuit

from qililab.constants import NODE, PLATFORM, RUNCARD
from qililab.platform import Platform
from qililab.pulse import PulseSchedule, PulseShape
from qililab.pulse.circuit_to_pulses import CircuitToPulses
from qililab.pulse.hardware_gates import HardwareGate, HardwareGateFactory
from qililab.transpiler import Drag
from qililab.typings import Parameter
from qililab.typings.enums import Line
from tests.data import Galadriel
from tests.utils import platform_db


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=copy.deepcopy(Galadriel.runcard))


class TestInitialization:
    """Unit tests for the initialization of a ``CircuitToPulses`` class."""

    def test_gate_settings_are_set_during_instantiation(self, platform: Platform):
        """Test that during initialization of the ``CircuitToPulses`` class we set the settings of all the hardware
        gates."""
        _ = CircuitToPulses(platform=platform)

        for gate in HardwareGateFactory.pulsed_gates.values():
            if gate.name not in platform.settings.gate_names:
                # Some gates derive from others (such as RY from Y), thus they have no settings
                assert not hasattr(gate, "settings")
            else:
                for qubit in range(platform.chip.num_qubits):
                    settings = platform.settings.get_gate(name=gate.name, qubits=qubit)
                    assert isinstance(gate.settings[qubit], HardwareGate.HardwareGateSettings)
                    assert gate.settings[qubit].amplitude == settings.amplitude
                    assert gate.settings[qubit].duration == settings.duration
                    assert gate.settings[qubit].phase == settings.phase
                    assert isinstance(gate.settings[qubit].shape, dict)
                    assert gate.settings[qubit].shape == settings.shape

    def test_gate_settings_are_updated_during_instantiation(self, platform: Platform):
        """Test that gate settings are updated if the ``CircuitToPulses`` class is re-instantiated with
        different settings."""
        X = HardwareGateFactory.get(name="X")

        _ = CircuitToPulses(platform=platform)

        assert X.settings[0].amplitude == 1.0

        platform.settings.set_parameter(alias="X(0)", parameter=Parameter.AMPLITUDE, value=123)

        _ = CircuitToPulses(platform=platform)

        assert X.settings[0].amplitude == 123


class TestTranslation:
    """Unit tests for the ``translate`` method of the ``CircuitToPulses`` class."""

    def test_translate(self, platform: Platform):
        """Test the ``translate`` method of the ``CircuitToPulses`` class."""
        translator = CircuitToPulses(platform=platform)

        circuit = Circuit(1)
        circuit.add(X(0))
        circuit.add(Y(0))
        circuit.add(Drag(0, 1, 0.5))  # 1 defines amplitude, 0.5 defines phase
        circuit.add(M(0))

        pulsed_gates = [
            platform.settings.get_gate(name="X", qubits=0),
            platform.settings.get_gate(name="Y", qubits=0),
            platform.settings.get_gate(name="Drag", qubits=0),
            platform.settings.get_gate(name="M", qubits=0),
        ]

        pulse_schedules = translator.translate(circuits=[circuit])

        assert isinstance(pulse_schedules, list)
        assert len(pulse_schedules) == 1
        assert isinstance(pulse_schedules[0], PulseSchedule)

        pulse_schedule = pulse_schedules[0]

        assert len(pulse_schedule) == 3  # it contains pulses for 3 buses (control, flux and readout)

        control_pulse_bus_schedule = pulse_schedule.elements[0]
        control_port = next(item for item in Galadriel.chip[NODE.NODES] if item[NODE.LINE] == Line.DRIVE.value)[
            RUNCARD.ID
        ]
        assert control_pulse_bus_schedule.port == control_port  # it targets the qubit, which is connected to drive line
        assert len(control_pulse_bus_schedule.timeline) == 3  # it contains 3 gates

        flux_pulse_bus_schedule = pulse_schedule.elements[1]
        flux_port = next(item for item in Galadriel.chip[NODE.NODES] if item[NODE.LINE] == Line.FLUX.value)[RUNCARD.ID]
        assert flux_pulse_bus_schedule.port == flux_port  # it targets the flux line, which is connected to flux line
        assert len(flux_pulse_bus_schedule.timeline) == 0

        readout_pulse_bus_schedule = pulse_schedule.elements[2]
        readout_port = next(
            item for item in Galadriel.chip[NODE.NODES] if item[NODE.LINE] == Line.FEEDLINE_INPUT.value
        )[RUNCARD.ID]
        assert (
            readout_pulse_bus_schedule.port == readout_port
        )  # it targets the resonator, which is connected to feedline input
        assert len(readout_pulse_bus_schedule.timeline) == 1

        all_pulse_events = control_pulse_bus_schedule.timeline + readout_pulse_bus_schedule.timeline

        for pulse_event, gate_settings in zip(all_pulse_events, pulsed_gates):
            pulse = pulse_event.pulse
            assert pulse.duration == gate_settings.duration
            if gate_settings.name == "Drag":
                # drag amplitude is defined by the first parameter, in this case 1
                drag_amplitude = (1 / np.pi) * gate_settings.amplitude
                assert pulse.amplitude == pytest.approx(drag_amplitude)
                # drag phase is defined by the second parameter, in this case 0.5
                assert pulse.phase == 0.5
            else:
                assert pulse.amplitude == gate_settings.amplitude
                assert pulse.phase == gate_settings.phase

            if gate_settings.name == "M":
                frequency = platform.chip.get_node_from_alias(alias="resonator").frequency
            else:
                frequency = platform.chip.get_node_from_alias(alias="qubit").frequency

            assert pulse.frequency == frequency
            assert isinstance(pulse.pulse_shape, PulseShape)
            for name, value in gate_settings.shape.items():
                assert getattr(pulse.pulse_shape, name) == value

    def test_gate_duration_errors_raised_in_translate(self, platform: Platform):
        """Test whether errors are raised correctly if gate values are not what is expected"""
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 0.5))  # 1 defines amplitude, 0.5 defines phase
        # test error raised when duration has decimal part
        platform.settings.get_gate(name="Drag", qubits=0).duration = 2.3
        error_string = "The settings of the gate drag have a non-integer duration \(2.3ns\). The gate duration must be an integer or a float with 0 decimal part"
        translator = CircuitToPulses(platform=platform)
        with pytest.raises(ValueError, match=error_string):
            translator.translate(circuits=[circuit])

    def test_translate_pulses_with_duration_not_multiple_of_minimum_clock_time(self, platform: Platform):
        """Test that when the duration of a pulse is not a multiple of the minimum clock time, the next pulse
        start time is delayed by ``pulse_time mod min_clock_time``."""
        translator = CircuitToPulses(platform=platform)

        circuit = Circuit(1)
        circuit.add(X(0))
        circuit.add(Y(0))
        circuit.add(Drag(0, 1, 0.5))
        circuit.add(M(0))

        pulse_schedule = translator.translate(circuits=[circuit])[0]

        min_clock_t = Galadriel.platform[PLATFORM.MINIMUM_CLOCK_TIME]
        x_dur = next(item for item in Galadriel.platform["gates"][0] if item[RUNCARD.NAME] == "X")["duration"]
        y_dur = next(item for item in Galadriel.platform["gates"][0] if item[RUNCARD.NAME] == "Y")["duration"]
        drag_dur = next(item for item in Galadriel.platform["gates"][0] if item[RUNCARD.NAME] == "Drag")["duration"]

        x_dur_mod = x_dur
        if x_dur % min_clock_t != 0:
            x_dur_mod += min_clock_t - (x_dur % min_clock_t)

        xy_dur_mod = x_dur_mod + y_dur
        if (x_dur_mod + y_dur) % min_clock_t != 0:
            xy_dur_mod += min_clock_t - ((x_dur_mod + y_dur) % min_clock_t)

        xydrag_dur_mod = xy_dur_mod + drag_dur
        if (xy_dur_mod + drag_dur) % min_clock_t != 0:
            xydrag_dur_mod += min_clock_t - ((xy_dur_mod + drag_dur) % min_clock_t)

        expected_start_times = [0, x_dur_mod, xy_dur_mod, xydrag_dur_mod]

        pulse_events = pulse_schedule.elements[0].timeline + pulse_schedule.elements[1].timeline

        for pulse_event, expected_start_time in zip(pulse_events, expected_start_times):
            assert pulse_event.start_time == expected_start_time
