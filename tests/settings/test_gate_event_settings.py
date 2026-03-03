import pytest

from qililab import Parameter
from qililab.settings.digital.gate_event_settings import GateEventSettings


@pytest.fixture(name="schedule")
def fixture_schedule() -> list[dict]:
    """Returns a list of dictionary schedules"""

    return [
        {
            "bus": "drive_line_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
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
                "duration": 200,
                "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
                "options": {"test_option": 1},
            },
        },
        {
            "bus": "drive_line_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 100,
                "shape": {"name": "rectangular"},
            },
        },
    ]


class TestGateEventSettings:
    def test_init(self, schedule):
        """ "Test init method"""
        gate_event = GateEventSettings(**schedule[1])
        assert gate_event.bus == "flux_line_q0_bus"
        assert gate_event.wait_time == 30
        # test pulse
        pulse = gate_event.pulse
        assert isinstance(pulse, GateEventSettings.GatePulseSettings)
        assert pulse.amplitude == 0.8
        assert pulse.phase == 0
        assert pulse.duration == 200
        assert pulse.shape == {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2}
        assert pulse.options["test_option"] == 1

    def test_set_parameter(self, schedule):
        """Test the set parameter method"""
        gate_event = GateEventSettings(**schedule[1])
        gate_event.set_parameter(parameter=Parameter.WAIT_TIME, value=10)
        assert gate_event.wait_time == 10
        gate_event.set_parameter(parameter=Parameter.AMPLITUDE, value=10)
        assert gate_event.pulse.amplitude == 10
        gate_event.set_parameter(parameter=Parameter.DRAG_COEFFICIENT, value=10)
        assert gate_event.pulse.shape["drag_coefficient"] == 10
