"""Integration test for the circuit native gate to circuit pulse (PulseSchedule) implementation"""
import numpy as np
import pytest
from qibo import gates
from qibo.models import Circuit

from qililab.chip import Chip
from qililab.pulse import CircuitToPulses
from qililab.settings import RuncardSchema
from qililab.transpiler import Drag, Park


@pytest.fixture(name="platform_settings")
def fixture_platform_settings() -> RuncardSchema.PlatformSettings:
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
                    "phase": None,
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
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": None, "duration": 93, "shape": {"name": "rectangular"}},
            ],
            2: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "Drag",
                    "amplitude": 1,
                    "phase": None,
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
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": None, "duration": 93, "shape": {"name": "rectangular"}},
            ],
            4: [
                {"name": "I", "amplitude": 0, "phase": 0, "duration": 0, "shape": {"name": "rectangular"}},
                {"name": "M", "amplitude": 1, "phase": 0, "duration": 100, "shape": {"name": "rectangular"}},
                {
                    "name": "Drag",
                    "amplitude": 1,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "drag", "num_sigmas": 4, "drag_coefficient": 1},
                },
                {"name": "Park", "amplitude": 1.0, "phase": None, "duration": 83, "shape": {"name": "rectangular"}},
            ],
            (2, 0): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
            (1, 2): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
            (3, 2): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
            (4, 2): [
                {
                    "name": "CZ",
                    "amplitude": 1,
                    "phase": None,
                    "duration": 40,
                    "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                },
            ],
        },
    }
    return RuncardSchema.PlatformSettings(**settings)  # type: ignore  # pylint: disable=unexpected-keyword-arg


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
            {"name": "port", "line": "drive", "id_": 1, "nodes": [2]},
            {"name": "port", "line": "drive", "id_": 2, "nodes": [2]},
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


# TODO test cases
# CZ at the beginning
# CZ new for both qubits
# CZ new for one qubit
# CZ without parking


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
        self,
        circuit_gates: list[gates.Gate],
        platform_settings: RuncardSchema.PlatformSettings,
        chip: Chip,
        expected: dict[str, list],
    ):
        c = Circuit(5)
        c.add(circuit_gates)
        translator = CircuitToPulses(settings=platform_settings)
        pulse_schedules = translator.translate(circuits=[c], chip=chip)

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
