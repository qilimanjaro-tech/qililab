import pytest
from rustworkx import PyGraph

from qilisdk.digital import Circuit, CZ, M, RX

from qililab.digital.circuit_transpiler_passes.custom_layout_pass import CustomLayoutPass
from qililab.digital.circuit_transpiler_passes.transpilation_context import TranspilationContext


def _make_topology(n_nodes: int) -> PyGraph:
    graph = PyGraph()
    graph.add_nodes_from(range(n_nodes))
    return graph


def test_custom_layout_retargets_gates_and_updates_context():
    topology = _make_topology(3)
    topology.add_edge(0, 1, None)
    topology.add_edge(1, 2, None)

    circuit = Circuit(2)
    circuit.add(RX(0, theta=0.5))
    circuit.add(CZ(0, 1))
    circuit.add(M(1))

    user_mapping = {0: 2, 1: 0}
    layout_pass = CustomLayoutPass(topology, user_mapping)

    context = TranspilationContext()
    layout_pass.attach_context(context)

    output = layout_pass.run(circuit)

    assert output.nqubits == 3
    assert [gate.qubits for gate in output.gates] == [(2,), (2, 0), (0,)]
    assert [gate.qubits for gate in circuit.gates] == [(0,), (0, 1), (1,)]
    assert layout_pass.last_layout == [2, 0]
    assert context.initial_layout == [2, 0]
    assert "CustomLayoutPass" in context.circuits
    assert context.circuits["CustomLayoutPass"] is output


def test_custom_layout_mapping_requires_all_logical_qubits():
    topology = _make_topology(2)
    circuit = Circuit(2)

    layout_pass = CustomLayoutPass(topology, {0: 0})

    with pytest.raises(ValueError, match=r"missing logical qubits \[1\]"):
        layout_pass.run(circuit)


def test_custom_layout_mapping_must_be_injective():
    topology = _make_topology(2)
    circuit = Circuit(2)

    layout_pass = CustomLayoutPass(topology, {0: 0, 1: 0})

    with pytest.raises(ValueError, match=r"duplicated physical qubits: \[0\]"):
        layout_pass.run(circuit)


def test_custom_layout_rejects_out_of_range_physical_indices():
    topology = _make_topology(3)
    circuit = Circuit(2)

    layout_pass = CustomLayoutPass(topology, {0: 0, 1: 3})

    with pytest.raises(ValueError, match=r"Mapping refers to physical qubits not present in the coupling graph: \[3\]"):
        layout_pass.run(circuit)
