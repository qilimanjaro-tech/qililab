import numpy as np
import pytest

from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings
from qililab.settings.digital.gate_event import GateEvent
from qililab.typings import Parameter
from qililab.waveforms.gaussian import Gaussian


def build_settings() -> DigitalCompilationSettings:
    gaussian = Gaussian(amplitude=1.0, duration=20, num_sigmas=5.0)
    events = [GateEvent(bus="drive_q0", waveform=gaussian, phase=0.123, wait_time=4)]
    gates = {"Rmw(0)": events, "CZ(0,1)": events}
    return DigitalCompilationSettings(topology=[(0, 1)], gates=gates)


def test_to_dict_returns_model_dump():
    settings = build_settings()
    dumped = settings.to_dict()
    assert dumped["topology"] == [(0, 1)]
    assert "Rmw(0)" in dumped["gates"]
    assert dumped["relaxation_duration"] == 200_000


@pytest.mark.parametrize(
    "qubits,expected_key",
    [
        (0, "Rmw(0)"),
        ((0,), "Rmw(0)"),
        ((0, 1), "CZ(0,1)"),
        ((1, 0), "CZ(0,1)"),
    ],
)
def test_get_gate_handles_various_qubit_inputs(qubits, expected_key):
    settings = build_settings()
    gate_events = settings.get_gate("Rmw" if expected_key.startswith("Rmw") else "CZ", qubits)
    assert isinstance(gate_events, list)
    assert gate_events[0].bus in {"drive_q0"}


def test_get_gate_raises_key_error():
    settings = build_settings()
    with pytest.raises(KeyError, match="Gate Rmw for qubits"):
        settings.get_gate("Rmw", 5)


def test_gate_names_property():
    settings = build_settings()
    assert sorted(settings.gate_names) == ["CZ(0,1)", "Rmw(0)"]


def test_set_parameter_updates_gate_event(monkeypatch):
    settings = build_settings()
    events = settings.gates["Rmw(0)"]

    original_phase = events[0].phase
    settings.set_parameter("Rmw(0)", Parameter.PHASE, 0.99)
    assert events[0].phase == 0.99
    assert events[0].phase != original_phase

    events.append(GateEvent(bus="drive_q0", waveform=events[0].waveform, phase=0.0))
    settings.set_parameter("Rmw(0)_1", Parameter.PHASE, -0.5)
    assert events[1].phase == -0.5


def test_set_parameter_invalid_alias_raises():
    settings = build_settings()
    with pytest.raises(ValueError, match="incorrect format"):
        settings.set_parameter("invalid_alias", Parameter.PHASE, 0.0)


def test_get_parameter_returns_current_value():
    settings = build_settings()
    value = settings.get_parameter("Rmw(0)", Parameter.PHASE)
    assert np.isclose(value, 0.123)

    new_event = GateEvent(bus="drive_q0", waveform=settings.gates["Rmw(0)"][0].waveform, phase=0.0)
    settings.gates["Rmw(0)"].append(new_event)
    settings.set_parameter("Rmw(0)_1", Parameter.PHASE, 0.7)
    assert np.isclose(settings.get_parameter("Rmw(0)_1", Parameter.PHASE), 0.7)


def test_get_parameter_invalid_alias_raises():
    settings = build_settings()
    with pytest.raises(ValueError, match="Could not find gate invalid"):
        settings.get_parameter("invalid", Parameter.PHASE)
