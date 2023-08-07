import re
from dataclasses import asdict

import numpy as np
import pytest

from qililab.chip import Chip
from qililab.config import logger
from qililab.platform import Bus, Buses, Platform
from qililab.pulse import PulseBusSchedule, PulseEvent, PulseSchedule
from qililab.pulse.circuit_to_pulses import CircuitToPulses
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_shape import SNZ
from qililab.pulse.pulse_shape import Drag as Drag_pulse
from qililab.settings.gate_settings import GateEventSettings
from qililab.typings.enums import Parameter


@pytest.fixture(name="schedule")
def fixture_schedule() -> list[dict]:
    """Returns a list of dictionary schedules"""

    return [
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
    ]


class TestGateEventSettings:
    def test_init(self, schedule):
        gate_event = GateEventSettings(**schedule[1])
        assert gate_event.bus == "flux_line_q0_bus"
        assert gate_event.wait_time == 30
        # test pulse
        pulse = gate_event.pulse
        assert isinstance(pulse, GateEventSettings.GatePulseSettings)
        assert pulse.amplitude == 0.8
        assert pulse.phase == 0
        assert pulse.frequency == 3.0e6
        assert pulse.duration == 200
        assert pulse.shape == {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2}
