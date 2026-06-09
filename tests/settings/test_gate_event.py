import numpy as np
import pytest

from qililab import Parameter
from qililab.settings.digital import gate_event as gate_event_module
from qililab.settings.digital.gate_event import (
    GateEvent,
    _from_external,
    _mapping_to_wf,
    _split_tag_and_payload,
    _to_external,
    _wf_to_mapping,
)
from qililab.waveforms import IQDrag, IQPair, Square
from qililab.waveforms.waveform import Waveform


@pytest.fixture
def iqdrag_payload() -> dict:
    return {
        "type": "IQDrag",
        "amplitude": 1.0,
        "duration": 50,
        "num_sigmas": 4,
        "drag_coefficient": 0.1,
    }


@pytest.fixture
def gate_event_dict_waveform(iqdrag_payload: dict) -> GateEvent:
    return GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 30,
        "phase": 0.0,
        "waveform": iqdrag_payload,
    })


@pytest.fixture
def gate_event_str_waveform(iqdrag_payload: dict) -> GateEvent:
    payload = "!IQDrag {amplitude: 1.0, duration: 50, num_sigmas: 4, drag_coefficient: 0.1}"
    return GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 30,
        "phase": 0.0,
        "waveform": payload,
    })


@pytest.fixture
def gate_event_object_waveform() -> GateEvent:
    return GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 30,
        "phase": 0.0,
        "waveform": Square(amplitude=1.0, duration=50),
    })


def test_gate_event_initialization_variants(
    gate_event_dict_waveform: GateEvent,
    gate_event_str_waveform: GateEvent,
    gate_event_object_waveform: GateEvent,
):
    for gate_event in (gate_event_dict_waveform, gate_event_str_waveform):
        assert gate_event.bus == "drive_q0_bus"
        assert gate_event.wait_time == 30
        assert isinstance(gate_event.waveform, IQDrag)
        assert gate_event.waveform.amplitude == 1.0
        assert gate_event.waveform.duration == 50
        assert gate_event.waveform.num_sigmas == 4
        assert gate_event.waveform.drag_coefficient == 0.1

    assert gate_event_object_waveform.bus == "drive_q0_bus"
    assert gate_event_object_waveform.wait_time == 30
    assert isinstance(gate_event_object_waveform.waveform, Square)
    assert gate_event_object_waveform.waveform.amplitude == 1.0
    assert gate_event_object_waveform.waveform.duration == 50


def test_gate_event_parameter_accessors(gate_event_dict_waveform: GateEvent):
    gate_event_dict_waveform.set_parameter(Parameter.WAIT_TIME, 10)
    assert gate_event_dict_waveform.get_parameter(Parameter.WAIT_TIME) == 10

    gate_event_dict_waveform.set_parameter(Parameter.AMPLITUDE, 2.5)
    assert gate_event_dict_waveform.get_parameter(Parameter.AMPLITUDE) == pytest.approx(2.5)


def test_gate_event_model_dump_serializes_waveforms(gate_event_dict_waveform: GateEvent):
    dumped = gate_event_dict_waveform.model_dump()
    assert dumped["waveform"]["type"] == "IQDrag"
    assert dumped["waveform"]["amplitude"] == pytest.approx(1.0)


def test_gate_event_weights_handling(iqdrag_payload: dict):
    weight_obj = IQDrag(amplitude=0.2, duration=20, num_sigmas=2, drag_coefficient=0.05)

    gate_event_obj_weights = GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 5,
        "waveform": {
            "type": "Square",
            "amplitude": 0.3,
            "duration": 20,
        },
        "weights": weight_obj,
    })

    assert gate_event_obj_weights.weights is weight_obj
    dumped_obj = gate_event_obj_weights.model_dump()
    assert dumped_obj["weights"]["type"] == "IQDrag"

    gate_event_dict_weights = GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "wait_time": 5,
        "waveform": {
            "type": "Square",
            "amplitude": 0.3,
            "duration": 20,
        },
        "weights": iqdrag_payload,
    })

    assert isinstance(gate_event_dict_weights.weights, IQDrag)
    dumped_dict = gate_event_dict_weights.model_dump()
    assert dumped_dict["weights"]["type"] == "IQDrag"


def test_gate_event_weights_accept_string(iqdrag_payload: dict):
    payload = "!IQDrag {amplitude: 1.0, duration: 50, num_sigmas: 4, drag_coefficient: 0.1}"
    gate_event = GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "waveform": {
            "type": "Square",
            "amplitude": 0.3,
            "duration": 20,
        },
        "weights": payload,
    })

    assert isinstance(gate_event.weights, IQDrag)


def test_gate_event_weights_none_serializes_to_none():
    gate_event = GateEvent.model_validate({
        "bus": "drive_q0_bus",
        "waveform": {
            "type": "Square",
            "amplitude": 0.3,
            "duration": 20,
        },
    })

    assert gate_event.model_dump()["weights"] is None


def test_gate_event_rejects_invalid_waveform():
    with pytest.raises(TypeError):
        GateEvent.model_validate({
            "bus": "drive_q0_bus",
            "waveform": 123,
        })


def test_gate_event_rejects_invalid_weights():
    with pytest.raises(TypeError):
        GateEvent.model_validate({
            "bus": "drive_q0_bus",
            "waveform": {
                "type": "Square",
                "amplitude": 0.3,
                "duration": 20,
            },
            "weights": 3.14,
        })


def test_split_tag_and_payload_variants():
    assert _split_tag_and_payload("plain text") == ("", "plain text")
    assert _split_tag_and_payload("!Square") == ("!Square", "")

    tag, payload = _split_tag_and_payload("!IQDrag {amplitude: 1.0}\n")
    assert tag == "!IQDrag"
    assert payload == "{amplitude: 1.0}"


def test_to_external_handles_nested_waveforms():
    square = Square(amplitude=0.5, duration=10)
    iq_pair = IQPair(I=square, Q=Square(amplitude=0.5, duration=10))
    data = {
        "pair": iq_pair,
        "list": [square, (square, "text")],
    }

    external = _to_external(data)

    assert external["pair"]["type"] == "IQPair"
    assert external["pair"]["I"]["type"] == "Square"
    assert external["list"][0]["type"] == "Square"
    assert external["list"][1][0]["type"] == "Square"
    assert external["list"][1][1] == "text"


def test_from_external_recreates_waveforms():
    iqdrag = _from_external({
        "type": "IQDrag",
        "amplitude": 1.0,
        "duration": 50,
        "num_sigmas": 4,
        "drag_coefficient": 0.1,
    })
    assert isinstance(iqdrag, IQDrag)

    pair = _from_external({
        "type": "IQPair",
        "I": {"type": "Square", "amplitude": 0.5, "duration": 10},
        "Q": {"type": "Square", "amplitude": 0.5, "duration": 10},
    })
    assert isinstance(pair, IQPair)
    assert isinstance(pair.get_I(), Square)
    assert isinstance(pair.get_Q(), Square)


def test_from_external_handles_collections():
    payload = [
        {"type": "Square", "amplitude": 0.2, "duration": 5},
        ("keep", {"type": "Square", "amplitude": 0.2, "duration": 5}),
    ]

    result = _from_external(payload)
    assert isinstance(result[0], Square)
    assert result[1][0] == "keep"
    assert isinstance(result[1][1], Square)


def test_from_external_requires_type_discriminator():
    with pytest.raises(TypeError):
        _from_external({"type": None})


class DummyWaveform(Waveform):
    def envelope(self, resolution: int = 1):
        return np.ones(2)


def test_wf_to_mapping_normalizes_kind(monkeypatch):
    dummy = DummyWaveform()

    def fake_to_external(obj):
        assert obj is dummy
        return {"kind": "Custom", "extra": 1}

    monkeypatch.setattr(gate_event_module, "_to_external", fake_to_external)
    mapped = _wf_to_mapping(dummy)
    assert mapped["type"] == "Custom"
    assert mapped["extra"] == 1


def test_wf_to_mapping_rejects_non_mapping(monkeypatch):
    dummy = DummyWaveform()
    monkeypatch.setattr(gate_event_module, "_to_external", lambda obj: "not a mapping")

    with pytest.raises(TypeError):
        _wf_to_mapping(dummy)


def test_mapping_to_wf_roundtrip():
    square = _mapping_to_wf({"type": "Square", "amplitude": 0.5, "duration": 10})
    assert isinstance(square, Square)

    iqdrag = _mapping_to_wf({
        "type": "IQDrag",
        "amplitude": 1.0,
        "duration": 50,
        "num_sigmas": 4,
        "drag_coefficient": 0.1,
    })
    assert isinstance(iqdrag, IQDrag)


def test_mapping_to_wf_rejects_invalid_mapping():
    with pytest.raises(TypeError):
        _mapping_to_wf({"amplitude": 1.0})
