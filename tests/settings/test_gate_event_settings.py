import pytest

from qililab import Parameter
from qililab.settings.digital.gate_event import GateEvent
from qililab.waveforms import IQDrag


@pytest.fixture(name="gate_event")
def fixture_gate_event() -> GateEvent:
    """Returns a gate event"""
    return GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 30,
        "phase": 0,
        "waveform": {
            "type": "IQDrag",
            "amplitude": 1.0,
            "duration": 50,
            "num_sigmas": 4,
            "drag_coefficient": 0,
        },
    })


class TestGateEventSettings:
    def test_init(self, gate_event: GateEvent):
        """ "Test init method"""
        assert gate_event.bus == "drive_q0_bus"
        assert gate_event.wait_time == 30
        assert isinstance(gate_event.waveform, IQDrag)
        assert gate_event.waveform.amplitude == 1.0
        assert gate_event.waveform.duration == 50
        assert gate_event.waveform.num_sigmas == 4
        assert gate_event.waveform.drag_coefficient == 0

    def test_set_parameter(self, gate_event: GateEvent):
        """Test the set parameter method"""
        gate_event.set_parameter(parameter=Parameter.WAIT_TIME, value=10)
        assert gate_event.wait_time == 10
        gate_event.set_parameter(parameter=Parameter.AMPLITUDE, value=10)
        assert gate_event.waveform.amplitude == 10
        gate_event.set_parameter(parameter=Parameter.DRAG_COEFFICIENT, value=10)
        assert gate_event.waveform.drag_coefficient == 10
