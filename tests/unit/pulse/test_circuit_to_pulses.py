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
from qililab.settings import RuncardSchema
from qililab.settings.gate_settings import GateEventSettings
from qililab.transpiler import Drag
from qililab.utils import Wait
from tests.data import Galadriel
from tests.utils import platform_db

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
            "bus": "drive_line_q0_bus",
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
            "bus": "drive_line_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 200,
                "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
            },
        },
        {
            "bus": "flux_line_q0_bus",
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
            "bus": "drive_line_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "frequency": 3.0e6,
                "duration": 100,
                "shape": {"name": "rectangular"},
            },
        },
        {
            "bus": "drive_line_q4_bus",
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
            "bus": "flux_line_q2_bus",
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
            "bus": "flux_line_q0_bus",
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
            "bus": "flux_line_c2_bus",
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
            "bus": "flux_line_q0_bus",
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
        "id_": 0,
        "category": "chip",
        "nodes": [
            {"name": "port", "line": "feedline_input", "id_": 0, "nodes": [18, 19, 20, 21, 22]},
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
            {"name": "port", "line": "flux", "id_": 43, "alias": "flux_line_c2", "nodes": [44]},
            {
                "name": "coupler",
                "alias": "coupler",
                "id_": 44,
                "frequency": 6e9,
                "nodes": [43],
            },
            {"name": "resonator", "alias": "resonator", "id_": 18, "frequency": 8072600000, "nodes": [3, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 19, "frequency": 8072600000, "nodes": [4, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 20, "frequency": 8072600000, "nodes": [5, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 21, "frequency": 8072600000, "nodes": [6, 0]},
            {"name": "resonator", "alias": "resonator", "id_": 22, "frequency": 8072600000, "nodes": [7, 0]},
        ],
    }
    return Chip(**settings)


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
        "gates": {},
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
            "id_": 42,
            "category": "bus",
            "alias": "flux_line_c2_bus",  # c2 coupler
            "system_control": {
                "id_": 42,
                "name": "system_control",
                "category": "system_control",
                "instruments": ["QCM1"],
            },
            "port": 43,
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

    platform.settings.gates = {  # type: ignore
        gate: [GateEventSettings(**event) for event in schedule] for gate, schedule in platform_gates.items()  # type: ignore
    }
    return platform


class TestCircuitToPulses:  # pylint: disable=R0903 # disable too few public methods warning
    """Test class for circuit_to_pulses"""

    def test_init(self, platform):
        """Test init method."""
        circuit_to_pulses = CircuitToPulses(platform)
        assert list(platform_gates.keys()) == circuit_to_pulses.platform.settings.gate_names


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

    def get_bus_schedule(self, pulse_bus_schedule: dict, port: int) -> list[dict]:
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
        m_schedule = pulse_bus_schedule[0]  # port 0 is the readout

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
        assert pulse_bus_schedule[8][-1].start_time == 1140

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

        # port 8 (drive q0)
        port_8 = self.get_bus_schedule(pulse_bus_schedule, 8)
        assert all(i == k for i, k in zip(port_8, drive_q0))
        # port 13 (flux q0)
        port_13 = self.get_bus_schedule(pulse_bus_schedule, 13)
        assert all(i == k for i, k in zip(port_13, flux_q0))
        # port 12 (drive 14)
        port_12 = self.get_bus_schedule(pulse_bus_schedule, 12)
        assert all(i == k for i, k in zip(port_12, drive_q4))

        # port 15 (flux q2)
        port_15 = self.get_bus_schedule(pulse_bus_schedule, 15)
        assert all(i == k for i, k in zip(port_15, flux_q2))

        # port 43 (flux c2)
        port_43 = self.get_bus_schedule(pulse_bus_schedule, 43)
        assert all(i == k for i, k in zip(port_43, flux_c2))

    def test_normalize_angle(self, platform):
        """Test that the angle is normalized properly for drag pulses"""
        c = Circuit(1)
        c.add(Drag(0, 2 * np.pi + 0.1, 0))
        translator = CircuitToPulses(platform=platform)
        pulse_schedules = translator.translate(circuits=[c])
        assert np.allclose(pulse_schedules[0].elements[0].timeline[0].pulse.amplitude, 0.1 * 0.8 / np.pi)

    def test_drag_schedule_error(self, platform: Platform):
        """Test error is raised if len(drag schedule) > 1"""
        # append schedule of M(0) to Drag(0) so that Drag(0)'s gate schedule has 2 elements
        platform.settings.gates["Drag(0)"].append(platform.settings.gates["M(0)"][0])
        gate_schedule = platform.settings.gates["Drag(0)"]
        error_string = re.escape(
            f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
        )
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 1))
        translator = CircuitToPulses(platform=platform)
        with pytest.raises(ValueError, match=error_string):
            translator.translate(circuits=[circuit])
