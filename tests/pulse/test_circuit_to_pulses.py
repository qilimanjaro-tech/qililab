"""This file contains unit tests for the ``CircuitToPulses`` class."""
import re
from dataclasses import asdict

import numpy as np
import pytest
from qibo.gates import CZ, M, X
from qibo.models import Circuit

from qililab.chip import Chip
from qililab.platform import Bus, Buses, Platform
from qililab.pulse import PulseEvent, PulseSchedule
from qililab.pulse.circuit_to_pulses import CircuitToPulses
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_shape import SNZ
from qililab.pulse.pulse_shape import Drag as Drag_pulse
from qililab.pulse.pulse_shape import Gaussian, Rectangular
from qililab.settings import Runcard
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.transpiler import Drag
from qililab.utils import Wait
from tests.data import Galadriel
from tests.test_utils import platform_db

platform_gates = {
    "M(0)": [
        {
            "bus": "feedline_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "shape": {"name": "rectangular"},
            },
        }
    ],
    "Drag(0)": [
        {
            "bus": "drive_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 198,  # try some non-multiple of clock time (4)
                "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
            },
        }
    ],
    # random X schedule
    "X(0)": [
        {
            "bus": "drive_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
            },
        },
        {
            "bus": "flux_q0_bus",
            "wait_time": 30,
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
            },
        },
        {
            "bus": "drive_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "shape": {"name": "rectangular"},
            },
        },
        {
            "bus": "drive_q4_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "shape": {"name": "gaussian", "num_sigmas": 4},
            },
        },
    ],
    "M(1)": [
        {
            "bus": "feedline_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "shape": {"name": "rectangular"},
            },
        }
    ],
    "M(2)": [
        {
            "bus": "feedline_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "shape": {"name": "rectangular"},
            },
        }
    ],
    "M(3)": [
        {
            "bus": "feedline_bus",
            "pulse": {
                "amplitude": 0.7,
                "phase": 0.5,
                "frequency": 2.0e6,
                "duration": 100,
                "shape": {"name": "gaussian", "num_sigmas": 2},
            },
        }
    ],
    "M(4)": [
        {
            "bus": "feedline_bus",
            "pulse": {
                "amplitude": 0.7,
                "phase": 0.5,
                "frequency": 2.0e6,
                "duration": 100,
                "shape": {"name": "gaussian", "num_sigmas": 2},
            },
        }
    ],
    "CZ(2,3)": [
        {
            "bus": "flux_q2_bus",
            "wait_time": 10,
            "pulse": {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 90,
                "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
            },
        },
        # park pulse
        {
            "bus": "flux_q0_bus",
            "pulse": {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "shape": {"name": "rectangular"},
            },
        },
    ],
    # test couplers
    "CZ(4, 0)": [
        {
            "bus": "flux_c2_bus",
            "wait_time": 10,
            "pulse": {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 90,
                "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
            },
        },
        {
            "bus": "flux_q0_bus",
            "pulse": {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "shape": {"name": "rectangular"},
            },
        },
    ],
}


@pytest.fixture(name="chip")
def fixture_chip():
    r"""Fixture that returns an instance of a ``Chip`` class.


    Chip schema (qubit_id, GHz, id)

   3,4,5  4,4,7
     \   /
     2,5,4
     /   \
   0,6,3 1,3,6
    """
    settings = {
        "nodes": [
            {
                "name": "port",
                "alias": "feedline_input",
                "line": "feedline_input",
                "nodes": ["resonator_q0", "resonator_q1", "resonator_q2", "resonator_q3", "resonator_q4"],
            },
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 6e9,
                "nodes": ["q2", "drive_q0", "flux_q0", "resonator_q0"],
            },
            {
                "name": "qubit",
                "alias": "q2",
                "qubit_index": 2,
                "frequency": 5e9,
                "nodes": ["q0", "q1", "q3", "q4", "drive_q2", "flux_q2", "resonator_q2"],
            },
            {
                "name": "qubit",
                "alias": "q1",
                "qubit_index": 1,
                "frequency": 4e9,
                "nodes": ["q2", "drive_q1", "flux_q1", "resonator_q1"],
            },
            {
                "name": "qubit",
                "alias": "q3",
                "qubit_index": 3,
                "frequency": 3e9,
                "nodes": ["q2", "drive_q3", "flux_q3", "resonator_q3"],
            },
            {
                "name": "qubit",
                "alias": "q4",
                "qubit_index": 4,
                "frequency": 4e9,
                "nodes": ["q2", "drive_q4", "flux_q4", "resonator_q4"],
            },
            {"name": "port", "line": "drive", "alias": "drive_q0", "nodes": ["q0"]},
            {"name": "port", "line": "drive", "alias": "drive_q1", "nodes": ["q1"]},
            {"name": "port", "line": "drive", "alias": "drive_q2", "nodes": ["q2"]},
            {"name": "port", "line": "drive", "alias": "drive_q3", "nodes": ["q3"]},
            {"name": "port", "line": "drive", "alias": "drive_q4", "nodes": ["q4"]},
            {"name": "port", "line": "flux", "alias": "flux_q0", "nodes": ["q0"]},
            {"name": "port", "line": "flux", "alias": "flux_q1", "nodes": ["q1"]},
            {"name": "port", "line": "flux", "alias": "flux_q2", "nodes": ["q2"]},
            {"name": "port", "line": "flux", "alias": "flux_q3", "nodes": ["q3"]},
            {"name": "port", "line": "flux", "alias": "flux_q4", "nodes": ["q4"]},
            {"name": "resonator", "alias": "resonator_q0", "frequency": 8072600000, "nodes": ["feedline_input", "q0"]},
            {"name": "resonator", "alias": "resonator_q1", "frequency": 8072600000, "nodes": ["feedline_input", "q1"]},
            {"name": "resonator", "alias": "resonator_q2", "frequency": 8072600000, "nodes": ["feedline_input", "q2"]},
            {"name": "resonator", "alias": "resonator_q3", "frequency": 8072600000, "nodes": ["feedline_input", "q3"]},
            {"name": "resonator", "alias": "resonator_q4", "frequency": 8072600000, "nodes": ["feedline_input", "q4"]},
            {"name": "port", "alias": "flux_c2", "line": "flux", "nodes": ["coupler"]},
            {"name": "coupler", "alias": "coupler", "frequency": 6e9, "nodes": ["flux_c2"]},
        ],
    }
    return Chip(**settings)


@pytest.fixture(name="platform")
def fixture_platform(chip: Chip) -> Platform:
    """Fixture that returns an instance of a ``Runcard.GatesSettings`` class."""
    name = "dummy"

    device_id = 9

    gates_settings = {
        "minimum_clock_time": 5,
        "delay_between_pulses": 0,
        "delay_before_readout": 0,
        "reset_method": "passive",
        "passive_reset_duration": 100,
        "timings_calculation_method": "as_soon_as_possible",
        "operations": [],
        "gates": {},
    }
    bus_settings = [
        {
            "alias": "feedline_bus",
            "system_control": {
                "name": "readout_system_control",
                "instruments": ["QRM1", "rs_1"],
            },
            "port": "feedline_input",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q0_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM-RF1"],
            },
            "port": "drive_q0",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q0_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM1"],
            },
            "port": "flux_q0",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q1_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM-RF1"],
            },
            "port": "drive_q1",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q1_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM1"],
            },
            "port": "flux_q1",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q2_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM-RF2"],
            },
            "port": "drive_q2",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q2_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM2"],
            },
            "port": "flux_q2",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_c2_bus",  # c2 coupler
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM1"],
            },
            "port": "flux_c2",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q3_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM-RF3"],
            },
            "port": "drive_q3",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q3_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM1"],
            },
            "port": "flux_q3",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q4_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM-RF3"],
            },
            "port": "drive_q4",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q4_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM1"],
            },
            "port": "flux_q4",
            "distortions": [],
            "delay": 0,
        },
    ]

    gates_settings = Runcard.GatesSettings(**gates_settings)  # type: ignore  # pylint: disable=unexpected-keyword-arg
    platform = platform_db(runcard=Galadriel.runcard)
    platform.name = name
    platform.device_id = device_id
    platform.gates_settings = gates_settings  # type: ignore
    platform.chip = chip
    buses = Buses(
        elements=[Bus(settings=bus, platform_instruments=platform.instruments, chip=chip) for bus in bus_settings]
    )
    platform.buses = buses
    platform.gates_settings.gates = {  # type: ignore
        gate: [GateEventSettings(**event) for event in schedule] for gate, schedule in platform_gates.items()  # type: ignore
    }
    return platform


class TestCircuitToPulses:  # pylint: disable=R0903 # disable too few public methods warning
    """Test class for circuit_to_pulses"""

    def test_init(self, platform):
        """Test init method."""
        circuit_to_pulses = CircuitToPulses(platform)
        assert list(platform_gates.keys()) == circuit_to_pulses.platform.gates_settings.gate_names


class TestTranslation:
    """Unit tests for the ``translate`` method of the ``CircuitToPulses`` class."""

    def get_pulse0(self, time: int, qubit: int) -> PulseEvent:
        """Helper function for pulse test data"""
        return PulseEvent(
            pulse=Pulse(
                amplitude=0.8,
                phase=0,
                duration=200,
                frequency=3.0e6,
                pulse_shape=Rectangular(),
            ),
            start_time=time,
            pulse_distortions=[],
            qubit=qubit,
        )

    def get_bus_schedule(self, pulse_bus_schedule: dict, port: str) -> list[dict]:
        """Helper function for bus schedule data"""

        return [
            {**asdict(schedule)["pulse"], "start_time": schedule.start_time, "qubit": schedule.qubit}
            for schedule in pulse_bus_schedule[port]
        ]

    def test_translate(self, platform):  # pylint: disable=R0914 # disable pyling too many variables
        """Test translate method"""
        translator = CircuitToPulses(platform=platform)
        # test circuit
        circuit = Circuit(5)
        circuit.add(X(0))
        circuit.add(Drag(0, 1, 0.5))
        circuit.add(CZ(3, 2))
        circuit.add(M(0))
        circuit.add(CZ(2, 3))
        circuit.add(CZ(4, 0))
        circuit.add(M(*range(4)))
        circuit.add(Wait(0, t=10))
        circuit.add(Drag(0, 2, 0.5))

        pulse_schedules = translator.translate(circuits=[circuit])

        # test general properties of the pulse schedule
        assert isinstance(pulse_schedules, list)
        assert len(pulse_schedules) == 1
        assert isinstance(pulse_schedules[0], PulseSchedule)

        pulse_schedule = pulse_schedules[0]
        # there are 6 different buses + 3 empty for unused flux lines
        assert len(pulse_schedule) == 9
        assert all(len(schedule_element.timeline) == 0 for schedule_element in pulse_schedule.elements[-3:])

        # we can ignore empty elements from here on
        pulse_schedule.elements = pulse_schedule.elements[:-3]

        # extract pulse events per bus and separate measurement pulses
        pulse_bus_schedule = {
            pulse_bus_schedule.port: pulse_bus_schedule.timeline for pulse_bus_schedule in pulse_schedule
        }
        m_schedule = pulse_bus_schedule["feedline_input"]

        # check measurement gates
        assert len(m_schedule) == 5

        m_pulse1 = PulseEvent(
            pulse=Pulse(
                amplitude=0.7,
                phase=0.5,
                duration=100,
                frequency=2.0e6,
                pulse_shape=Gaussian(num_sigmas=2),
            ),
            start_time=930,
            pulse_distortions=[],
            qubit=3,
        )

        assert all(
            pulse == self.get_pulse0(time, qubit)
            for pulse, time, qubit in zip(m_schedule[:-1], [530, 930, 930, 930], [0, 0, 1, 2])
        )
        assert m_schedule[-1] == m_pulse1

        # assert wait gate delayed drive pulse at port 8 for 10ns (time should be 930+200+10=1140)
        assert pulse_bus_schedule["drive_q0"][-1].start_time == 1140

        # test actions for control gates

        # data
        drive_q0 = [
            {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "start_time": 0,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
            {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "start_time": 0,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
            {
                "amplitude": 0.8 / np.pi,
                "phase": 0.5,
                "frequency": 3.0e6,
                "duration": 198,
                "start_time": 230,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
            {
                "amplitude": 2 * 0.8 / np.pi,
                "phase": 0.5,
                "frequency": 3.0e6,
                "duration": 198,
                "start_time": 1140,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
        ]

        drive_q4 = [
            {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "start_time": 0,
                "qubit": 4,
                "pulse_shape": asdict(Gaussian(num_sigmas=4)),
            }
        ]

        flux_q0 = [
            {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "start_time": 30,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "start_time": 430,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "start_time": 730,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "start_time": 830,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
        ]

        flux_q2 = [
            {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 90,
                "start_time": 440,
                "qubit": 2,
                "pulse_shape": asdict(SNZ(b=0.5, t_phi=1)),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 90,
                "start_time": 740,
                "qubit": 2,
                "pulse_shape": asdict(SNZ(b=0.5, t_phi=1)),
            },
        ]

        flux_c2 = [
            {
                "amplitude": 0.7,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 90,
                "start_time": 840,
                "qubit": None,
                "pulse_shape": asdict(SNZ(b=0.5, t_phi=1)),
            }
        ]

        # drive q0
        port_8 = self.get_bus_schedule(pulse_bus_schedule, "drive_q0")
        assert len(port_8) == len(drive_q0)
        assert all(i == k for i, k in zip(port_8, drive_q0))

        # flux q0
        port_13 = self.get_bus_schedule(pulse_bus_schedule, "flux_q0")
        assert len(port_13) == len(flux_q0)
        assert all(i == k for i, k in zip(port_13, flux_q0))

        # drive q4
        port_12 = self.get_bus_schedule(pulse_bus_schedule, "drive_q4")
        assert len(port_12) == len(drive_q4)
        assert all(i == k for i, k in zip(port_12, drive_q4))

        # flux q2
        port_15 = self.get_bus_schedule(pulse_bus_schedule, "flux_q2")
        assert len(port_15) == len(flux_q2)
        assert all(i == k for i, k in zip(port_15, flux_q2))

        # flux c2
        port_43 = self.get_bus_schedule(pulse_bus_schedule, "flux_c2")
        assert len(port_43) == len(flux_c2)
        assert all(i == k for i, k in zip(port_43, flux_c2))

    def test_normalize_angle(self, platform):
        """Test that the angle is normalized properly for drag pulses"""
        c = Circuit(1)
        c.add(Drag(0, 2 * np.pi + 0.1, 0))
        translator = CircuitToPulses(platform=platform)
        pulse_schedules = translator.translate(circuits=[c])
        assert np.allclose(pulse_schedules[0].elements[0].timeline[0].pulse.amplitude, 0.1 * 0.8 / np.pi)
        c = Circuit(1)
        c.add(Drag(0, np.pi + 0.1, 0))
        translator = CircuitToPulses(platform=platform)
        pulse_schedules = translator.translate(circuits=[c])
        assert np.allclose(pulse_schedules[0].elements[0].timeline[0].pulse.amplitude, -0.7745352091052967)

    def test_drag_schedule_error(self, platform: Platform):
        """Test error is raised if len(drag schedule) > 1"""
        # append schedule of M(0) to Drag(0) so that Drag(0)'s gate schedule has 2 elements
        platform.gates_settings.gates["Drag(0)"].append(platform.gates_settings.gates["M(0)"][0])
        gate_schedule = platform.gates_settings.gates["Drag(0)"]
        error_string = re.escape(
            f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
        )
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 1))
        translator = CircuitToPulses(platform=platform)
        with pytest.raises(ValueError, match=error_string):
            translator.translate(circuits=[circuit])
