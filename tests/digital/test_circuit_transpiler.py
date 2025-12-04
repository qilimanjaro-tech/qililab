import pytest

from qilisdk.digital import Circuit

from qililab.digital.circuit_transpiler import CircuitTranspiler
from qililab.digital.circuit_transpiler_passes import (
    AddPhasesToRmwFromRZAndCZPass,
    CancelIdentityPairsPass,
    CanonicalBasisToNativeSetPass,
    CircuitToCanonicalBasisPass,
    CircuitTranspilerPass,
    CustomLayoutPass,
    FuseSingleQubitGatesPass,
    SabreLayoutPass,
    SabreSwapPass,
)
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings


class DummyPass(CircuitTranspilerPass):
    def __init__(self, tag: str, log: list[tuple[str, int]]) -> None:
        self.tag = tag
        self.log = log

    def run(self, circuit: Circuit) -> Circuit:
        self.log.append((self.tag, id(circuit)))
        return circuit


@pytest.fixture
def basic_settings() -> DigitalCompilationSettings:
    return DigitalCompilationSettings(topology=[(0, 1), (1, 2)], gates={})


def test_circuit_transpiler_builds_default_pipeline(basic_settings: DigitalCompilationSettings) -> None:
    transpiler = CircuitTranspiler(basic_settings)

    pipeline_types = [type(p) for p in transpiler._pipeline]
    expected_prefix = [
        CancelIdentityPairsPass,
        CircuitToCanonicalBasisPass,
        FuseSingleQubitGatesPass,
        SabreLayoutPass,
        SabreSwapPass,
        CircuitToCanonicalBasisPass,
        FuseSingleQubitGatesPass,
        CanonicalBasisToNativeSetPass,
        AddPhasesToRmwFromRZAndCZPass,
    ]
    assert pipeline_types == expected_prefix

    for transpiler_pass in transpiler._pipeline:
        assert transpiler_pass.context is transpiler.context

    topology_nodes = sorted(transpiler._topology.node_indices())
    assert topology_nodes == [0, 1, 2]
    assert transpiler._topology.has_edge(0, 1)
    assert transpiler._topology.has_edge(1, 2)


def test_circuit_transpiler_uses_custom_mapping_layout(basic_settings: DigitalCompilationSettings) -> None:
    transpiler = CircuitTranspiler(basic_settings, qubit_mapping={0: 2, 1: 0})

    pipeline_types = [type(p) for p in transpiler._pipeline]
    assert CustomLayoutPass in pipeline_types
    assert SabreLayoutPass not in pipeline_types
    assert SabreSwapPass not in pipeline_types

    custom_layout = next(p for p in transpiler._pipeline if isinstance(p, CustomLayoutPass))
    assert custom_layout.context is transpiler.context


def test_circuit_transpiler_respects_custom_pipeline(basic_settings: DigitalCompilationSettings) -> None:
    log: list[tuple[str, int]] = []
    pipeline = [DummyPass("a", log), DummyPass("b", log)]

    transpiler = CircuitTranspiler(basic_settings, pipeline=pipeline)

    for transpiler_pass in pipeline:
        assert transpiler_pass.context is transpiler.context

    circuit = Circuit(1)
    result = transpiler.run(circuit)

    assert [entry[0] for entry in log] == ["a", "b"]
    first_pass_circuit_id = log[0][1]
    second_pass_circuit_id = log[1][1]
    assert first_pass_circuit_id != id(circuit)
    assert second_pass_circuit_id != first_pass_circuit_id
    assert result is not circuit


def test_circuit_transpiler_context_property(basic_settings: DigitalCompilationSettings) -> None:
    transpiler = CircuitTranspiler(basic_settings)
    assert transpiler.context is transpiler._context
