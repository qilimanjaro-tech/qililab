import pytest
from rustworkx import PyGraph

from qilisdk.digital import Circuit, CZ, M, RX, RY, RZ, SWAP, U3

from qililab.digital.circuit_transpiler_passes.sabre_layout_pass import SabreLayoutPass
from qililab.digital.circuit_transpiler_passes.transpilation_context import TranspilationContext


def make_graph(edges, nodes=None):
    graph = PyGraph()
    if nodes is None:
        if edges:
            max_node = max(max(u, v) for u, v in edges)
            nodes = range(max_node + 1)
        else:
            nodes = []
    graph.add_nodes_from(nodes)
    for u, v in edges:
        graph.add_edge(u, v, None)
    return graph


def test_sabre_layout_requires_pygraph():
    with pytest.raises(TypeError, match="requires a rustworkx.PyGraph"):
        SabreLayoutPass("not-a-graph")  # type: ignore[arg-type]


def test_sabre_layout_rejects_empty_topology():
    topology = PyGraph()
    layout_pass = SabreLayoutPass(topology)
    circuit = Circuit(1)
    with pytest.raises(ValueError, match="Coupling graph has no nodes"):
        layout_pass.run(circuit)


def test_sabre_layout_raises_when_circuit_needs_more_qubits():
    topology = make_graph([(0, 1)], nodes=range(2))
    layout_pass = SabreLayoutPass(topology)
    circuit = Circuit(3)
    with pytest.raises(ValueError, match="circuit needs 3 qubits"):
        layout_pass.run(circuit)


def test_sabre_layout_identity_when_no_two_qubit_gates():
    topology = make_graph([(0, 1), (1, 2)])
    layout_pass = SabreLayoutPass(topology, seed=123)
    context = TranspilationContext()
    layout_pass.attach_context(context)

    circuit = Circuit(2)
    circuit.add(RX(0, theta=0.1))
    circuit.add(RY(1, theta=0.2))

    out = layout_pass.run(circuit)

    assert out.nqubits == 3
    assert [gate.qubits for gate in out.gates] == [(0,), (1,)]
    assert layout_pass.last_layout == [0, 1]
    assert layout_pass.last_score == 0.0
    assert context.initial_layout == [0, 1]
    assert context.circuits == {}

    # Original circuit untouched
    assert [gate.qubits for gate in circuit.gates] == [(0,), (1,)]


def test_sabre_layout_retarges_all_gate_types_and_updates_diagnostics():
    topology = make_graph([(0, 1), (1, 2), (2, 3)])
    layout_pass = SabreLayoutPass(topology, num_trials=1, seed=7, lookahead_size=2)
    context = TranspilationContext()
    layout_pass.attach_context(context)

    circuit = Circuit(3)
    circuit.add(RX(0, theta=0.1))
    circuit.add(RY(1, theta=0.2))
    circuit.add(RZ(2, phi=0.3))
    circuit.add(U3(0, theta=0.4, phi=0.5, gamma=0.6))
    circuit.add(CZ(1, 2))
    circuit.add(SWAP(0, 1))
    circuit.add(M(0))

    out = layout_pass.run(circuit)

    assert out.nqubits == 4
    assert len(out.gates) == len(circuit.gates)
    assert all(type(o) is type(i) for o, i in zip(out.gates, circuit.gates))
    assert layout_pass.last_layout is not None
    assert len(layout_pass.last_layout) == circuit.nqubits
    assert sorted(layout_pass.last_layout) == sorted(set(layout_pass.last_layout))
    assert layout_pass.last_score is not None
    assert context.initial_layout == layout_pass.last_layout
    assert any(key.startswith("SabreLayoutPass") for key in context.circuits)
