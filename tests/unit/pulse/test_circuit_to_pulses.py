"""This file contains unit tests for the ``CircuitToPulses`` class."""
import logging
import re

import numpy as np
import pytest
from qibo import gates
from qibo.models import Circuit

from qililab.chip import Chip
from qililab.config import logger
from qililab.platform import Bus, Buses, Platform
from qililab.pulse import PulseEvent, PulseSchedule
from qililab.pulse.circuit_to_pulses import CircuitToPulses
from qililab.pulse.hardware_gates import CZ
from qililab.pulse.hardware_gates import Drag as DragGate
from qililab.pulse.hardware_gates import HardwareGate, HardwareGateFactory, I, M
from qililab.pulse.hardware_gates import Park as ParkGate
from qililab.settings import Runcard
from qililab.transpiler import Drag, Park
from qililab.typings import Parameter
from qililab.utils import Wait
from tests.data import Galadriel
from tests.utils import platform_db


@pytest.fixture(name="platform")
def fixture_platform(chip: Chip) -> Platform:
    """Fixture that returns an instance of a ``RuncardSchema.PlatformSettings`` class."""
    settings = {
        "id_": 0,
        "category": "platform",
        "name": "dummy",
        "device_id": 9,
        "minimum_clock_time": 5,
        "delay_between_pulses": 0,
        "delay_before_readout": 0,
        "reset_method": "passive",
        "passive_reset_duration": 100,
        "timings_calculation_method": "as_soon_as_possible",
        "operations": [],
        "gates": {
            0: [
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
                {
                    "name": "Drag",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": 0, "duration": 93, "shape": {"name": "rectangular"}},
            ],
            1: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "Drag",
                    "amplitude": 0.5,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": 0, "duration": 93, "shape": {"name": "rectangular"}},
            ],
            2: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "Drag",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": 0, "duration": 93, "shape": {"name": "rectangular"}},
            ],
            3: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "Drag",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": 0, "duration": 93, "shape": {"name": "rectangular"}},
            ],
            4: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "Drag",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": 0, "duration": 83, "shape": {"name": "rectangular"}},
            ],
            (2, 0): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
            (1, 2): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
            (3, 2): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
            (2, 3): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
            (4, 2): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 83,
                    "shape": {"name": "rectangular"},
                },
            ],
        },
    }
    bus_settings = [
        {
            "id_": 0,
            "category": "bus",
            "alias": "feedline_bus",
            "system_control": {
                "id_": 0,
                "name": "readout_system_control",
                "category": "system_control",
                "instruments": ["QRM1", "rs_1"],
            },
            "port": 0,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 20,
            "category": "bus",
            "alias": "drive_line_q0_bus",
            "system_control": {
                "id_": 20,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM-RF1"],
            },
            "port": 8,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 30,
            "category": "bus",
            "alias": "flux_line_q0_bus",
            "system_control": {
                "id_": 30,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM1"],
            },
            "port": 13,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 21,
            "category": "bus",
            "alias": "drive_line_q1_bus",
            "system_control": {
                "id_": 21,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM-RF1"],
            },
            "port": 9,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 31,
            "category": "bus",
            "alias": "flux_line_q1_bus",
            "system_control": {
                "id_": 31,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM1"],
            },
            "port": 14,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 22,
            "category": "bus",
            "alias": "drive_line_q2_bus",
            "system_control": {
                "id_": 22,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM-RF2"],
            },
            "port": 10,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 32,
            "category": "bus",
            "alias": "flux_line_q2_bus",
            "system_control": {
                "id_": 32,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM2"],
            },
            "port": 15,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 23,
            "category": "bus",
            "alias": "drive_line_q3_bus",
            "system_control": {
                "id_": 23,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM-RF3"],
            },
            "port": 11,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 33,
            "category": "bus",
            "alias": "flux_line_q3_bus",
            "system_control": {
                "id_": 33,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM1"],
            },
            "port": 16,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 24,
            "category": "bus",
            "alias": "drive_line_q4_bus",
            "system_control": {
                "id_": 24,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM-RF3"],
            },
            "port": 12,
            "distortions": [],
            "delay": 0,
        },
        {
            "id_": 34,
            "category": "bus",
            "alias": "flux_line_q4_bus",
            "system_control": {
                "id_": 34,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM1"],
            },
            "port": 17,
            "distortions": [],
            "delay": 0,
        },
    ]
    settings = Runcard.TranspilationSettings(**settings)  # type: ignore  # pylint: disable=unexpected-keyword-arg
    platform = platform_db(runcard=Galadriel.runcard)
    platform.transpilation_settings = settings  # type: ignore
    platform.chip = chip
    buses = Buses(
        elements=[Bus(settings=bus, platform_instruments=platform.instruments, chip=chip) for bus in bus_settings]
    )
    platform.buses = buses
    return platform


@pytest.fixture(name="chip")
def fixture_chip():
    """Fixture that returns an instance of a ``Chip`` class.


    Chip schema (qubit_id, GHz, id)

   3,4,5  4,4,7
     \   /
     2,5,4
     /   \
   0,6,3 1,3,6
    """
    settings = {
        "id_": 0,
        "category": "chip",
        "nodes": [
            {"name": "port", "line": "feedline_input", "id_": 0, "nodes": [3]},
            {
                "name": "qubit",
                "alias": "qubit",
                "id_": 3,
                "qubit_index": 0,
                "frequency": 6e9,
                "nodes": [4, 13, 8, 18],
            },
            {
                "name": "qubit",
                "alias": "qubit",
                "id_": 4,
                "qubit_index": 2,
                "frequency": 5e9,
                "nodes": [3, 5, 6, 7, 15, 10, 20],
            },
            {
                "name": "qubit",
                "alias": "qubit",
                "id_": 5,
                "qubit_index": 3,
                "frequency": 4e9,
                "nodes": [4, 16, 11, 21],
            },
            {
                "name": "qubit",
                "alias": "qubit",
                "id_": 6,
                "qubit_index": 1,
                "frequency": 3e9,
                "nodes": [4, 14, 9, 19],
            },
            {
                "name": "qubit",
                "alias": "qubit",
                "id_": 7,
                "qubit_index": 4,
                "frequency": 4e9,
                "nodes": [4, 17, 12, 22],
            },
            {
                "name": "port",
                "line": "drive",
                "id_": 8,
                "alias": "drive_line_q0",
                "nodes": [3],
            },
            {
                "name": "port",
                "line": "drive",
                "id_": 9,
                "alias": "drive_line_q1",
                "nodes": [6],
            },
            {
                "name": "port",
                "line": "drive",
                "id_": 10,
                "alias": "drive_line_q2",
                "nodes": [4],
            },
            {
                "name": "port",
                "line": "drive",
                "id_": 11,
                "alias": "drive_line_q3",
                "nodes": [5],
            },
            {
                "name": "port",
                "line": "drive",
                "id_": 12,
                "alias": "drive_line_q4",
                "nodes": [7],
            },
            {
                "name": "port",
                "line": "flux",
                "id_": 13,
                "alias": "flux_line_q0",
                "nodes": [3],
            },
            {
                "name": "port",
                "line": "flux",
                "id_": 14,
                "alias": "flux_line_q1",
                "nodes": [6],
            },
            {
                "name": "port",
                "line": "flux",
                "id_": 15,
                "alias": "flux_line_q2",
                "nodes": [4],
            },
            {
                "name": "port",
                "line": "flux",
                "id_": 16,
                "alias": "flux_line_q3",
                "nodes": [5],
            },
            {
                "name": "port",
                "line": "flux",
                "id_": 17,
                "alias": "flux_line_q4",
                "nodes": [7],
            },
            {"name": "resonator", "alias": "resonator", "id_": 18, "frequency": 8072600000, "nodes": [3, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 19, "frequency": 8072600000, "nodes": [4, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 20, "frequency": 8072600000, "nodes": [5, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 21, "frequency": 8072600000, "nodes": [6, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 22, "frequency": 8072600000, "nodes": [7, 0]},
        ],
    }
    return Chip(**settings)


class TestInitialization:
    """Unit tests for the initialization of a ``CircuitToPulses`` class."""

    def test_gate_settings_are_set_during_instantiation(self, platform: Platform):
        """Test that during initialization of the ``CircuitToPulses`` class we set the settings of all the hardware
        gates."""
        _ = CircuitToPulses(platform=platform)

        for gate in {I, M, ParkGate, DragGate, CZ}:
            if gate.name not in platform.transpilation_settings.gate_names:
                # Some gates derive from others (such as RY from Y), thus they have no settings
                assert not hasattr(gate, "settings")
                continue
            # test CZ separately
            if gate.name == "CZ":
                for qubits in ((2, 0), (1, 2)):
                    # TODO remove duplicate code
                    settings = platform.transpilation_settings.get_gate(name=gate.name, qubits=qubits)
                    assert isinstance(gate.settings[qubits], HardwareGate.HardwareGateSettings)
                    assert gate.settings[qubits].amplitude == settings.amplitude
                    assert gate.settings[qubits].duration == settings.duration
                    assert gate.settings[qubits].phase == settings.phase
                    assert isinstance(gate.settings[qubits].shape, dict)
                    assert gate.settings[qubits].shape == settings.shape
            else:
                for qubit in range(platform.chip.num_qubits):
                    settings = platform.transpilation_settings.get_gate(name=gate.name, qubits=qubit)
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

        assert X.settings[0].amplitude == 0.8

        platform.transpilation_settings.set_parameter(alias="X(0)", parameter=Parameter.AMPLITUDE, value=123)

        _ = CircuitToPulses(platform=platform)

        assert X.settings[0].amplitude == 123


class TestTranslation:
    """Unit tests for the ``translate`` method of the ``CircuitToPulses`` class."""

    def test_translate(self, platform: Platform):
        """Test the ``translate`` method of the ``CircuitToPulses`` class."""
        translator = CircuitToPulses(platform=platform)

        circuit = Circuit(5)
        circuit.add(gates.X(0))
        circuit.add(gates.Y(0))
        circuit.add(Drag(0, 1, 0.5))  # 1 defines amplitude, 0.5 defines phase
        circuit.add(Park(0))
        circuit.add(gates.CZ(3, 2))  # CZ(control, target)
        circuit.add(gates.M(0))

        pulse_schedules = translator.translate(circuits=[circuit])

        assert isinstance(pulse_schedules, list)
        assert len(pulse_schedules) == 1
        assert isinstance(pulse_schedules[0], PulseSchedule)

        # test parking gates
        assert len(translator._get_parking_gates(gates.CZ(3, 2), platform.chip)) == 2

        pulse_schedule = pulse_schedules[0]

        assert len(pulse_schedule) == 7  # it contains pulses for 7 buses (control, flux and readout)

    def test_gate_duration_errors_raised_in_translate(self, platform: Platform):
        """Test whether errors are raised correctly if gate values are not what is expected"""
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 0.5))  # 1 defines amplitude, 0.5 defines phase
        # test error raised when duration has decimal part
        platform.transpilation_settings.get_gate(name="Drag", qubits=0).duration = 2.3
        error_string = "The settings of the gate drag have a non-integer duration \(2.3ns\). The gate duration must be an integer or a float with 0 decimal part"
        translator = CircuitToPulses(platform=platform)
        with pytest.raises(ValueError, match=error_string):
            translator.translate(circuits=[circuit])

    def test_cz_errors_raised_in_translate(self, platform: Platform):
        circuit = Circuit(4)
        cz = gates.CZ(2, 3)
        circuit.add(cz)
        translator = CircuitToPulses(platform=platform)
        error_string = f"Attempting to perform {cz.name} on qubits {re.escape(str(cz.qubits))} by targeting qubit {cz.target_qubits[0]} which has lower frequency than {cz.control_qubits[0]}"
        with pytest.raises(ValueError, match=error_string):
            translator.translate(circuits=[circuit])

    def test_bus_error_is_raised(self, platform: Platform, chip: Chip):
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 1))
        # create platform without buses for qubit 0
        buses = Buses(elements=[platform.buses[3], platform.buses[4]])
        platform.buses = buses
        translator = CircuitToPulses(platform=platform)
        error_string = "bus cannot be None to get the distortions"
        with pytest.raises(TypeError, match=error_string):
            translator.translate(circuits=[circuit])

    def test_no_park_raises_warning(self, caplog, platform: Platform, chip: Chip):
        cz = gates.CZ(1, 2)
        park_qubit = 3
        circuit = Circuit(3)
        circuit.add(cz)

        # delete parking gate for q3
        del platform.transpilation_settings.gates[park_qubit][3]
        translator = CircuitToPulses(platform=platform)
        caplog.set_level(logging.WARNING)
        translator.translate(circuits=[circuit])
        warning_string = f"Found parking candidate qubit {park_qubit} for {cz.name} at qubits {cz.qubits} but did not find settings for parking gate at qubit {park_qubit}"
        assert warning_string in caplog.text

    def test_error_on_pad_time_negative(self, caplog, platform: Platform, chip: Chip):
        cz = gates.CZ(1, 2)
        circuit = Circuit(3)
        circuit.add(cz)

        # decrease park time for gate for q3, q4
        pad_time = (10 - 83) / 2
        platform.transpilation_settings.gates[3][3].duration = 10
        platform.transpilation_settings.gates[4][3].duration = 10
        translator = CircuitToPulses(platform=platform)
        error_string = re.escape(
            f"Negative value pad_time {pad_time} for park gate at 3 and CZ {cz.qubits}. Pad time is calculated as (ParkGate.duration - CZ pulse duration) / 2"
        )
        with pytest.raises(ValueError, match=error_string):
            translator.translate(circuits=[circuit])

    def test_translate_pulses_with_duration_not_multiple_of_minimum_clock_time(self, platform: Platform):
        """Test that when the duration of a pulse is not a multiple of the minimum clock time, the next pulse
        start time is delayed by ``pulse_time mod min_clock_time``."""
        translator = CircuitToPulses(platform=platform)

        circuit = Circuit(5)
        circuit.add(gates.X(0))
        circuit.add(gates.Y(0))
        circuit.add(Park(0))
        circuit.add(Drag(0, 1, 0.5))
        circuit.add(Wait(1, 17))  # wait on q1 which will be parked by CZ(3,2)
        circuit.add(gates.CZ(3, 2))
        circuit.add(gates.M(0))

        pulse_schedule = translator.translate(circuits=[circuit])[0]

        # minimum_clock_time is 5ns so every start time will be multiple of 5
        # the order respects drive-flux-resonator (line 337)
        # duration for CZ is 30*2+2+1
        bus0_start_times = [220]
        bus8_start_times = [0, 45, 180]
        bus13_start_times = [85]
        bus14_start_times = [20]
        bus15_start_times = [25]  # padding (5) + wait (20)
        bus17_start_times = [20]

        expected_start_times = (
            bus0_start_times
            + bus8_start_times
            + bus13_start_times
            + bus14_start_times
            + bus15_start_times
            + bus17_start_times
        )

        sorted_bus_schedules = sorted(pulse_schedule.elements, key=lambda element: element.port)
        pulse_events: list[PulseEvent] = sum((element.timeline for element in sorted_bus_schedules), [])

        for pulse_event, expected_start_time in zip(pulse_events, expected_start_times):
            assert pulse_event.start_time == expected_start_time


@pytest.mark.parametrize(
    "circuit_gates, expected",
    [
        (
            [Drag(0, 1, 1), Wait(0, 40), gates.M(*range(5))],
            {
                "gates": [Drag(0, 1, 1), Wait(0, 40), gates.M(0), gates.M(1), gates.M(2), gates.M(3), gates.M(4)],
                "pulse_times": [0, 0, 80, 0, 0, 0],
                "pulse_name": ["drag", "rectangular", "rectangular", "rectangular", "rectangular", "rectangular"],
                "nodes": [8, 0, 0, 0, 0, 0],
            },
        ),
        (
            [gates.CZ(3, 2), gates.M(*range(5)), Drag(3, np.pi, np.pi / 2)],
            {
                "pulse_events": [
                    gates.CZ(2, 3),
                    Park(1),
                    Park(4),
                    gates.M(0),
                    gates.M(1),
                    gates.M(2),
                    gates.M(3),
                    gates.M(4),
                    Drag(3, np.pi, np.pi / 2),
                ],
                "pulse_times": [5, 0, 0, 0, 95, 95, 95, 85, 195],
                "pulse_name": [
                    "snz",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "drag",
                ],
                "nodes": [15, 14, 17, 0, 0, 0, 0, 0, 11],
            },
        ),
        (
            [Drag(4, np.pi, 3 * np.pi / 2), gates.CZ(0, 2), gates.M(2)],
            {
                "pulse_events": [Drag(4, np.pi, 3 * np.pi / 2), gates.CZ(0, 2), gates.M(2)],
                "pulse_times": [0, 0, 85],
                "pulse_name": ["drag", "snz", "rectangular"],
                "nodes": [12, 13, 0],
            },
        ),
        (
            [Drag(2, 1, 1), Drag(4, 2, 1), gates.CZ(0, 2), gates.M(1)],
            {
                "pulse_events": [Drag(2, 1, 1), Drag(4, 2, 1), gates.CZ(0, 2), gates.M(1)],
                "pulse_times": [0, 0, 40, 0],
                "pulse_name": ["drag", "drag", "snz", "rectangular"],
                "nodes": [10, 12, 13, 0],
            },
        ),
        (
            [
                Drag(1, 1, 1),
                Drag(2, 1, 1),
                Wait(2, 10),
                gates.CZ(2, 3),
                Wait(2, 10),
                Drag(0, 1, 0),
                Drag(3, 2, 2),
                gates.M(0),
                Wait(1, 4),
                gates.M(2),
                gates.CZ(4, 2),
                gates.CZ(2, 3),
                gates.M(4),
            ],
            {
                "pulse_events": [
                    Drag(1, 1, 1),
                    Drag(2, 1, 1),
                    Wait(2, 10),
                    gates.CZ(2, 3),
                    Wait(2, 10),
                    Park(1),
                    Park(4),
                    Drag(0, 1, 0),
                    Drag(3, 2, 2),
                    gates.M(0),
                    Wait(1, 4),
                    gates.M(2),
                    gates.CZ(4, 2),
                    Park(1),
                    Park(3),
                    gates.CZ(2, 3),
                    Park(1),
                    Park(4),
                    gates.M(4),
                ],
                "pulse_times": [0, 0, 55, 50, 50, 0, 145, 40, 155, 260, 255, 255, 355, 350, 350, 435],
                "pulse_name": [
                    "drag",
                    "drag",
                    "snz",
                    "rectangular",
                    "rectangular",
                    "drag",
                    "drag",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                    "snz",
                    "rectangular",
                    "rectangular",
                    "rectangular",
                ],
                "nodes": [9, 10, 15, 14, 17, 8, 11, 0, 0, 15, 14, 16, 15, 14, 17, 0],
            },
        ),
    ],
)
class TestIntegration:
    def test_native_circuit_to_pulse(
        self, circuit_gates: list[gates.Gate], platform: Platform, expected: dict[str, list]
    ):
        platform.transpilation_settings.gates.pop((2, 3))
        c = Circuit(5)
        c.add(circuit_gates)
        translator = CircuitToPulses(platform=platform)
        pulse_schedules = translator.translate(circuits=[c])

        # TODO if resonator is missing then M gate is not added but no error is raised
        pulse_schedule = pulse_schedules[0]

        events: list[tuple] = []
        for pulse_bus_schedule in pulse_schedule.elements:
            events.extend(
                (pulse_bus_schedule.port, pulse_event.pulse.pulse_shape.name.value, pulse_event.start_time)
                for pulse_event in pulse_bus_schedule.timeline
            )
        assert len(events) == len(expected["nodes"])
        pulse_values = list(zip(expected["nodes"], expected["pulse_name"], expected["pulse_times"]))
        assert sorted(pulse_values) == sorted(events)
