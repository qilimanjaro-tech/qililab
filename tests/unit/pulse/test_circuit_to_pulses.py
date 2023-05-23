"""This file contains unit tests for the ``CircuitToPulses`` class."""
import re

import numpy as np
import pytest
from qibo import gates
from qibo.models import Circuit

from qililab.chip import Chip
from qililab.constants import NODE, RUNCARD
from qililab.platform import Bus, Buses, Platform
from qililab.pulse import PulseSchedule, PulseShape
from qililab.pulse.circuit_to_pulses import CircuitToPulses
from qililab.pulse.hardware_gates import HardwareGate, HardwareGateFactory
from qililab.settings import RuncardSchema
from qililab.transpiler import Drag, Park
from qililab.typings import Parameter
from qililab.typings.enums import Line
from tests.data import Galadriel
from tests.utils import platform_db

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
        "distortions": ["BiasTeeCorrection(tau_bias_tee=1.0)", "LFilter(a = [0.1, 1.1], b = [1.1, 1.3])"],
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
    },
]


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
            (4, 2): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": 0,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
        },
    }

    settings = RuncardSchema.PlatformSettings(**settings)  # type: ignore  # pylint: disable=unexpected-keyword-arg
    platform = platform_db(runcard=Galadriel.runcard)
    platform.settings = settings  # type: ignore
    platform.schema.chip = chip
    buses = Buses(
        elements=[
            Bus(settings=bus, platform_instruments=platform.schema.instruments, chip=chip) for bus in bus_settings
        ]
    )
    platform.schema.buses = buses
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

        for gate in HardwareGateFactory.pulsed_gates.values():
            if gate.name not in platform.settings.gate_names:
                # Some gates derive from others (such as RY from Y), thus they have no settings
                assert not hasattr(gate, "settings")
                continue
            # test CZ separately
            if gate.name == "CZ":
                for qubits in ((2, 0), (1, 2)):
                    # TODO remove duplicate code
                    settings = platform.settings.get_gate(name=gate.name, qubits=qubits)
                    assert isinstance(gate.settings[qubits], HardwareGate.HardwareGateSettings)
                    assert gate.settings[qubits].amplitude == settings.amplitude
                    assert gate.settings[qubits].duration == settings.duration
                    assert gate.settings[qubits].phase == settings.phase
                    assert isinstance(gate.settings[qubits].shape, dict)
                    assert gate.settings[qubits].shape == settings.shape
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

        circuit = Circuit(2)
        circuit.add(gates.X(0))
        circuit.add(gates.Y(0))
        circuit.add(Drag(0, 1, 0.5))  # 1 defines amplitude, 0.5 defines phase
        circuit.add(Park(0))
        circuit.add(gates.CZ(0, 1))  # CZ(control, target)
        circuit.add(gates.M(0))

        pulsed_gates = [
            platform.settings.get_gate(name="X", qubits=0),
            platform.settings.get_gate(name="Y", qubits=0),
            platform.settings.get_gate(name="Drag", qubits=0),
            platform.settings.get_gate(name="Park", qubits=0),
            platform.settings.get_gate(name="Park", qubits=(2)),
            platform.settings.get_gate(name="CZ", qubits=(0, 1)),
            platform.settings.get_gate(name="M", qubits=0),
        ]

        pulse_schedules = translator.translate(circuits=[circuit])

        assert isinstance(pulse_schedules, list)
        assert len(pulse_schedules) == 1
        assert isinstance(pulse_schedules[0], PulseSchedule)

        # test parking gates
        assert len(translator._get_parking_gates(gates.CZ(0, 1), platform.chip)) == 1

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
        assert len(flux_pulse_bus_schedule.timeline) == 3  # it contains 2 gates (CZ, Park, Park for the CZ)

        readout_pulse_bus_schedule = pulse_schedule.elements[2]
        readout_port = next(
            item for item in Galadriel.chip[NODE.NODES] if item[NODE.LINE] == Line.FEEDLINE_INPUT.value
        )[RUNCARD.ID]
        assert readout_pulse_bus_schedule.port == readout_port  # it targets resonator, which is connected to feedline
        assert len(readout_pulse_bus_schedule.timeline) == 1

        all_pulse_events = (
            control_pulse_bus_schedule.timeline + flux_pulse_bus_schedule.timeline + readout_pulse_bus_schedule.timeline
        )

        for pulse_event, gate_settings in zip(all_pulse_events, pulsed_gates):
            pulse = pulse_event.pulse
            # check duration
            if gate_settings.name == "CZ":
                assert pulse.duration == 2 * gate_settings.duration + 2 + gate_settings.shape["t_phi"]
            else:
                assert pulse.duration == gate_settings.duration

            if gate_settings.name == "Drag":
                # drag amplitude is defined by the first parameter, in this case 1
                drag_amplitude = (1 / np.pi) * gate_settings.amplitude
                assert pulse.amplitude == pytest.approx(drag_amplitude)
                # drag phase is defined by the second parameter, in this case 0.5
                assert pulse.phase == 0.5
            else:
                if gate_settings.name == "CZ" or gate_settings.name == "Park":
                    assert pulse.phase == 0
                else:
                    assert pulse.phase == gate_settings.phase
                assert pulse.amplitude == gate_settings.amplitude

            if gate_settings.name == "M":
                frequency = platform.chip.get_node_from_alias(alias="resonator").frequency
            elif gate_settings.name == "CZ":
                frequency = platform.chip.get_node_from_qubit_idx(idx=0, readout=False).frequency
            else:
                frequency = platform.chip.get_node_from_alias(alias="qubit").frequency

            if gate_settings.name == "CZ" or gate_settings.name == "Park":
                assert pulse.frequency == 0
            else:
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

    def test_cz_errors_raised_in_translate(self, platform: Platform):
        circuit = Circuit(2)
        cz = gates.CZ(1, 0)
        circuit.add(cz)
        translator = CircuitToPulses(platform=platform)
        error_string = f"Attempting to perform {cz.name} on qubits {re.escape(str(cz.qubits))} by targeting qubit {cz.target_qubits[0]} which has lower frequency than {cz.control_qubits[0]}"
        with pytest.raises(ValueError, match=error_string):
            translator.translate(circuits=[circuit])

    def test_translate_pulses_with_duration_not_multiple_of_minimum_clock_time(self, platform: Platform):
        """Test that when the duration of a pulse is not a multiple of the minimum clock time, the next pulse
        start time is delayed by ``pulse_time mod min_clock_time``."""
        translator = CircuitToPulses(platform=platform)

        circuit = Circuit(2)
        circuit.add(gates.X(0))
        circuit.add(gates.Y(0))
        circuit.add(Park(0))
        circuit.add(Drag(0, 1, 0.5))
        circuit.add(gates.CZ(0, 1))
        circuit.add(gates.M(0))

        pulse_schedule = translator.translate(circuits=[circuit])[0]

        # minimum_clock_time is 4ns so every start time will be multiple of 4
        # the order respects drive-flux-resonator (line 337)
        # duration for CZ is 30*2+2+1
        expected_start_times = [0, 48, 160, 88, 200, 204, 272]  # TODO why not 264

        pulse_events = (
            pulse_schedule.elements[0].timeline
            + pulse_schedule.elements[1].timeline
            + pulse_schedule.elements[2].timeline
        )

        for pulse_event, expected_start_time in zip(pulse_events, expected_start_times):
            assert pulse_event.start_time == expected_start_time


@pytest.mark.parametrize(
    "circuit_gates, expected",
    [
        (
            [Drag(0, 1, 1), gates.M(*range(5))],
            {
                "gates": [Drag(0, 1, 1), gates.M(0), gates.M(1), gates.M(2), gates.M(3), gates.M(4)],
                "pulse_times": [0, 0, 40, 0, 0, 0],
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
                gates.CZ(2, 3),
                Drag(0, 1, 0),
                Drag(3, 2, 2),
                gates.M(0),
                gates.M(2),
                gates.CZ(4, 2),
                gates.CZ(2, 3),
                gates.M(4),
            ],
            {
                "pulse_events": [
                    Drag(1, 1, 1),
                    Drag(2, 1, 1),
                    gates.CZ(2, 3),
                    Park(1),
                    Park(4),
                    Drag(0, 1, 0),
                    Drag(3, 2, 2),
                    gates.M(0),
                    gates.M(2),
                    gates.CZ(4, 2),
                    Park(1),
                    Park(3),
                    gates.CZ(2, 3),
                    Park(1),
                    Park(4),
                    gates.M(4),
                ],
                "pulse_times": [0, 0, 45, 40, 40, 0, 135, 40, 135, 240, 235, 235, 335, 330, 330, 415],
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
                    "snz",
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
