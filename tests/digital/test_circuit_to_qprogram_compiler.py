import numpy as np
import pytest


from qilisdk.digital import Circuit, CZ, M
from qililab.digital.circuit_to_qprogram_compiler import (
    CircuitToQProgramCompiler,
    extract_qubit_index,
)
from qililab.digital.native_gates import Rmw
from qililab.settings.digital import DigitalCompilationSettings
from qililab.settings.digital.gate_event import GateEvent
from qililab.waveforms import Arbitrary, IQDrag, IQPair, Square


@pytest.mark.parametrize(
    "label, expected",
    [("drive_q0_bus", 0), ("flux_q12_channel", 12), ("readout_q3", 3)],
)
def test_extract_qubit_index_valid(label, expected):
    assert extract_qubit_index(label) == expected


def test_extract_qubit_index_invalid():
    with pytest.raises(ValueError):
        extract_qubit_index("drive_bus")


@pytest.mark.parametrize(
    "value, wrapped",
    [
        (0.0, 0.0),
        (np.pi, -np.pi),
        (-np.pi, -np.pi),
        (3 * np.pi, -np.pi),
        (-4 * np.pi, 0.0),
        (7.3, CircuitToQProgramCompiler.wrap_to_pi(7.3)),
    ],
)
def test_wrap_to_pi(value, wrapped):
    assert np.isclose(CircuitToQProgramCompiler.wrap_to_pi(value), wrapped)


def test_rmw_from_calibrated_pi_drag_rotates_and_scales():
    drag = IQDrag(amplitude=0.4, duration=16, num_sigmas=2.0, drag_coefficient=-0.3)
    theta = -np.pi / 2
    phase = np.pi / 4

    result = CircuitToQProgramCompiler._rmw_from_calibrated_pi_drag(drag, theta=theta, phase=phase)

    I0 = drag.get_I().envelope()
    Q0 = drag.get_Q().envelope()
    theta_mod = CircuitToQProgramCompiler.wrap_to_pi(theta)
    adjusted_phase = phase
    if theta_mod < 0:
        theta_mod = -theta_mod
        adjusted_phase += np.pi
    expected_phase = CircuitToQProgramCompiler.wrap_to_pi(adjusted_phase)
    c, s = np.cos(expected_phase), np.sin(expected_phase)
    scale = theta_mod / np.pi
    expected_I = scale * (I0 * c - Q0 * s)
    expected_Q = scale * (I0 * s + Q0 * c)

    assert isinstance(result.I, Arbitrary)
    assert isinstance(result.Q, Arbitrary)
    np.testing.assert_allclose(result.I.envelope(), expected_I)
    np.testing.assert_allclose(result.Q.envelope(), expected_Q)


@pytest.fixture
def compiler_settings() -> DigitalCompilationSettings:
    readout_waveform = Square(amplitude=0.5, duration=20)
    readout_weights = IQPair(Square(0.2, 20), Square(-0.2, 20))
    second_weights = IQPair(Square(0.1, 10), Square(0.1, 10))
    readout_pair = IQPair(Square(0.3, 10), Square(0.0, 10))

    return DigitalCompilationSettings.model_validate(
        {
            "topology": [(0, 1)],
            "relaxation_duration": 42,
            "gates": {
                "Rmw(0)": [
                    GateEvent(
                        bus="drive_q0_bus",
                        waveform=IQDrag(amplitude=0.5, duration=24, num_sigmas=3.0, drag_coefficient=0.1),
                    )
                ],
                "CZ(0,1)": [
                    GateEvent(bus="flux_q0_bus", waveform=Square(amplitude=0.2, duration=12)),
                    GateEvent(bus="flux_q1_bus", waveform=Square(amplitude=0.3, duration=12)),
                ],
                "M(0)": [
                    GateEvent(bus="readout_q0_bus", waveform=readout_waveform, weights=readout_weights),
                    GateEvent(bus="readout_q2_bus", waveform=readout_pair, weights=second_weights),
                ],
            },
        }
    )


def flatten_operations(block):
    from qililab.qprogram.blocks import Block

    ops = []
    for element in block.elements:
        if isinstance(element, Block):
            ops.extend(flatten_operations(element))
        else:
            ops.append(element)
    return ops


def test_compile_generates_qprogram(compiler_settings):
    compiler = CircuitToQProgramCompiler(compiler_settings)
    circuit = Circuit(2)
    circuit.add(Rmw(0, theta=np.pi / 2, phase=np.pi / 3))
    circuit.add(CZ(0, 1))
    circuit.add(M(0))

    qprogram = compiler.compile(circuit, nshots=3)

    assert len(qprogram.body.elements) == 10
    loop = qprogram.body.elements[-1]
    operations = flatten_operations(loop)

    from qililab.qprogram.operations import Measure, Play, Sync, Wait

    sync_ops = [op for op in operations if isinstance(op, Sync)]
    play_ops = [op for op in operations if isinstance(op, Play)]
    measure_ops = [op for op in operations if isinstance(op, Measure)]
    wait_ops = [op for op in operations if isinstance(op, Wait)]

    assert len(sync_ops) == 4
    assert any("drive_q0_bus" in sync.buses for sync in sync_ops)
    assert any(set(sync.buses) >= {"drive_q0_bus", "flux_q0_bus", "readout_q0_bus"} for sync in sync_ops)
    assert any("flux_q1_bus" in sync.buses for sync in sync_ops)

    assert len(play_ops) == 3
    assert all(play.bus in {"drive_q0_bus", "flux_q0_bus", "flux_q1_bus"} for play in play_ops)
    assert any(isinstance(play.waveform, IQDrag) for play in play_ops)

    assert len(measure_ops) == 2
    assert isinstance(measure_ops[0].waveform, IQPair)
    assert isinstance(measure_ops[0].weights, IQPair)
    assert isinstance(measure_ops[1].waveform, IQPair)
    assert isinstance(measure_ops[1].weights, IQPair)

    assert len(wait_ops) == 2
    assert all(wait.duration == compiler_settings.relaxation_duration for wait in wait_ops)
    assert {wait.bus for wait in wait_ops} == {"readout_q0_bus", "readout_q2_bus"}


def test_measurement_without_weights_raises():
    settings = DigitalCompilationSettings.model_validate(
        {
            "topology": [],
            "gates": {
                "M(0)": [GateEvent(bus="readout_q0_bus", waveform=Square(amplitude=0.1, duration=10), weights=None)],
            },
        }
    )
    compiler = CircuitToQProgramCompiler(settings)
    circuit = Circuit(1)
    circuit.add(M(0))

    with pytest.raises(ValueError, match="weights defined"):
        compiler.compile(circuit, nshots=1)
