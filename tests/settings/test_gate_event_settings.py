import pytest

from qililab import Parameter
from qililab.settings.digital.gate_event import GateEvent
from qililab.waveforms import IQDrag, Square


@pytest.fixture(name="gate_event_dict_waveform")
def fixture_gate_event_dict_waveform() -> GateEvent:
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


@pytest.fixture(name="gate_event_str_waveform")
def fixture_gate_event_str_waveform() -> GateEvent:
    """Returns a gate event"""
    return GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 30,
        "phase": 0,
        "waveform": "!IQDrag {amplitude: 1.0, duration: 50, num_sigmas: 4, drag_coefficient: 0}",
    })


@pytest.fixture(name="gate_event_object_waveform")
def fixture_gate_event_object_waveform() -> GateEvent:
    """Returns a gate event"""
    return GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 30,
        "phase": 0,
        "waveform": Square(1.0, 50),
    })


class TestGateEventSettings:
    def test_init(self, gate_event_dict_waveform: GateEvent, gate_event_str_waveform: GateEvent, gate_event_object_waveform: GateEvent):
        """ "Test init method"""
        for gate_event in [gate_event_dict_waveform, gate_event_str_waveform]:
            assert gate_event.bus == "drive_q0_bus"
            assert gate_event.wait_time == 30
            assert isinstance(gate_event.waveform, IQDrag)
            assert gate_event.waveform.amplitude == 1.0
            assert gate_event.waveform.duration == 50
            assert gate_event.waveform.num_sigmas == 4
            assert gate_event.waveform.drag_coefficient == 0
        
        assert gate_event_object_waveform.bus == "drive_q0_bus"
        assert gate_event_object_waveform.wait_time == 30
        assert isinstance(gate_event_object_waveform.waveform, Square)
        assert gate_event.waveform.amplitude == 1.0
        assert gate_event.waveform.duration == 50
        

    def test_set_parameter(self, gate_event_dict_waveform: GateEvent, gate_event_str_waveform: GateEvent, gate_event_object_waveform: GateEvent):
        """Test the set parameter method"""
        for gate_event in [gate_event_dict_waveform, gate_event_str_waveform, gate_event_object_waveform]:
            gate_event.set_parameter(parameter=Parameter.WAIT_TIME, value=10)
            assert gate_event.wait_time == 10
            gate_event.set_parameter(parameter=Parameter.AMPLITUDE, value=10)
            assert gate_event.waveform.amplitude == 10

    def test_wrong_waveform_raises_error(self):
        with pytest.raises(TypeError):
            _ = GateEvent.model_validate({
                "bus": "drive_q0_bus",
                "wait_time": 30,
                "phase": 0,
                "waveform": {
                    "type": "QProgram",
                },
            })

