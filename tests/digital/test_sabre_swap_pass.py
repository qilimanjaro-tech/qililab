import pytest
from rustworkx import PyGraph

from qilisdk.digital import Circuit, CZ, M, RX, RY, RZ

from qililab.digital.circuit_transpiler_passes.sabre_swap_pass import SabreSwapPass
from qililab.digital.circuit_transpiler_passes.transpilation_context import TranspilationContext


def make_line_topology(n: int) -> PyGraph:
    graph = PyGraph()
    graph.add_nodes_from(range(n))
    for i in range(n - 1):
        graph.add_edge(i, i + 1, None)
    return graph


def test_sabre_swap_requires_pygraph():
    with pytest.raises(TypeError, match="requires a rustworkx.PyGraph"):
        SabreSwapPass("not-a-graph")  # type: ignore[arg-type]


def test_sabre_swap_rejects_empty_coupling_graph():
    topology = PyGraph()
    swap_pass = SabreSwapPass(topology)
    circuit = Circuit(1)
    circuit.add(RX(0, theta=0.3))

    with pytest.raises(ValueError, match="Coupling graph has no nodes"):
        swap_pass.run(circuit)


def test_sabre_swap_initial_layout_length_must_match_logical_qubits():
    topology = make_line_topology(2)
    swap_pass = SabreSwapPass(topology, initial_layout=[0])
    circuit = Circuit(2)

    with pytest.raises(ValueError, match="initial_layout length 1 != circuit.nqubits 2"):
        swap_pass.run(circuit)


def test_sabre_swap_routes_adjacent_gate_without_swaps_and_updates_context():
    topology = make_line_topology(2)
    swap_pass = SabreSwapPass(topology, seed=4)
    context = TranspilationContext()
    swap_pass.attach_context(context)

    circuit = Circuit(2)
    circuit.add(RY(0, theta=0.2))
    circuit.add(CZ(0, 1))
    circuit.add(M(1))

    out = swap_pass.run(circuit)

    assert [type(g).__name__ for g in out.gates] == ["RY", "CZ", "M"]
    assert [gate.qubits for gate in out.gates] == [(0,), (0, 1), (1,)]
    assert swap_pass.last_swap_count == 0
    assert swap_pass.last_final_layout == [0, 1]
    assert context.final_layout == [0, 1]
    assert context.metrics["swap_count"] == 0
    assert any(name.startswith("SabreSwapPass") for name in context.circuits)


def test_sabre_swap_inserts_swaps_for_non_adjacent_gate():
    topology = make_line_topology(3)
    swap_pass = SabreSwapPass(topology, seed=0)

    circuit = Circuit(3)
    circuit.add(RZ(0, phi=0.1))
    circuit.add(CZ(0, 2))

    out = swap_pass.run(circuit)

    names = [type(g).__name__ for g in out.gates]
    qubits = [gate.qubits for gate in out.gates]
    assert names == ["RZ", "SWAP", "CZ"]
    assert qubits[0] == (0,)
    assert qubits[1] in {(0, 1), (1, 0)}
    assert qubits[2] in {(1, 2), (2, 1)}
    assert swap_pass.last_swap_count == 1
    assert set(swap_pass.last_final_layout or []) == {0, 1, 2}


def test_sabre_swap_respects_custom_initial_layout():
    topology = PyGraph()
    topology.add_nodes_from(range(3))
    topology.add_edge(0, 1, None)
    topology.add_edge(1, 2, None)
    topology.add_edge(0, 2, None)

    swap_pass = SabreSwapPass(topology, initial_layout=[2, 0], seed=2)

    circuit = Circuit(2)
    circuit.add(RX(0, theta=0.5))
    circuit.add(CZ(0, 1))

    out = swap_pass.run(circuit)

    assert [gate.qubits for gate in out.gates][0] == (2,)
    assert swap_pass.last_final_layout[:2] == [2, 0]


def test_sabre_swap_rejects_multi_qubit_gate():
    topology = make_line_topology(3)
    swap_pass = SabreSwapPass(topology)

    class FakeGate:
        def __init__(self, qubits):
            self.qubits = qubits
            self.nqubits = len(qubits)

    circuit = Circuit(3)
    circuit._gates = [FakeGate((0, 1, 2))]

    with pytest.raises(NotImplementedError, match="FakeGate"):
        swap_pass.run(circuit)


def test_sabre_swap_raises_when_swap_budget_exceeded():
    topology = make_line_topology(3)
    swap_pass = SabreSwapPass(topology, seed=1, max_swaps_factor=0.0)

    circuit = Circuit(3)
    circuit.add(CZ(0, 2))

    with pytest.raises(RuntimeError, match="Exceeded swap budget"):
        swap_pass.run(circuit)


def test_sabre_swap_handles_sparse_physical_indices_with_default_layout():
    topology = PyGraph()
    topology.add_nodes_from(range(5))
    for node in (3, 1):
        topology.remove_node(node)
    topology.add_edge(0, 2, None)
    topology.add_edge(2, 4, None)
    assert sorted(topology.node_indices()) == [0, 2, 4]

    swap_pass = SabreSwapPass(topology, seed=3)

    circuit = Circuit(2)
    circuit.add(CZ(0, 1))

    out = swap_pass.run(circuit)

    assert out.nqubits >= 5
    assert all(q in {0, 2, 4} for gate in out.gates for q in gate.qubits)
    assert swap_pass.last_final_layout is not None
    assert set(swap_pass.last_final_layout).issubset({0, 2, 4})


def test_sabre_swap_handles_sparse_physical_indices_with_custom_layout():
    topology = PyGraph()
    topology.add_nodes_from(range(5))
    for node in (3, 1):
        topology.remove_node(node)
    topology.add_edge(0, 2, None)
    topology.add_edge(2, 4, None)
    assert sorted(topology.node_indices()) == [0, 2, 4]

    swap_pass = SabreSwapPass(topology, initial_layout=[0, 4], seed=5)

    circuit = Circuit(2)
    circuit.add(CZ(0, 1))

    out = swap_pass.run(circuit)

    assert out.nqubits >= 5
    assert any(type(g).__name__ == "SWAP" for g in out.gates)
    assert all(q in {0, 2, 4} for gate in out.gates for q in gate.qubits)
    assert swap_pass.last_final_layout is not None
    assert set(swap_pass.last_final_layout).issubset({0, 2, 4})
    assert swap_pass.last_swap_count and swap_pass.last_swap_count > 0


def test_sabre_swap_accepts_padding_qubits_after_layout():
    topology = PyGraph()
    topology.add_nodes_from(range(5))
    topology.remove_node(3)
    topology.add_edge(0, 1, None)
    topology.add_edge(1, 2, None)
    topology.add_edge(2, 4, None)
    assert sorted(topology.node_indices()) == [0, 1, 2, 4]

    swap_pass = SabreSwapPass(topology, seed=7)

    circuit = Circuit(5)
    circuit.add(CZ(0, 4))

    out = swap_pass.run(circuit)

    assert out.nqubits >= 5
    assert swap_pass.last_final_layout is not None
    assert len(swap_pass.last_final_layout) == circuit.nqubits
    assert set(q for gate in out.gates for q in gate.qubits).issubset({0, 1, 2, 4})
    assert 3 not in swap_pass.last_final_layout
