import math
import builtins

import pytest
from qilisdk.digital import Circuit, CZ
from rustworkx import PyGraph

from qililab.digital.circuit_transpiler_passes.sabre_swap_pass import SabreSwapPass


def _empty_graph(num_nodes: int) -> PyGraph:
    graph = PyGraph()
    graph.add_nodes_from(range(num_nodes))
    return graph


def _chain_graph(num_nodes: int) -> PyGraph:
    graph = _empty_graph(num_nodes)
    for i in range(num_nodes - 1):
        graph.add_edge(i, i + 1, None)
    return graph


def _two_qubit_circuit() -> Circuit:
    circuit = Circuit(2)
    circuit.add(CZ(0, 1))
    return circuit


def test_run_raises_after_all_attempts(monkeypatch):
    swap_pass = SabreSwapPass(_chain_graph(2), max_attempts=5)
    circuit = Circuit(1)  # trivial circuit; loop won't run

    original_max = builtins.max

    def fake_max(*args, **kwargs):
        if len(args) == 2 and args[0] == 1 and isinstance(args[1], int):
            return 0
        return original_max(*args, **kwargs)

    monkeypatch.setattr("builtins.max", fake_max)

    with pytest.raises(RuntimeError, match="SABRE routing failed after 0 attempts"):
        swap_pass.run(circuit)


def test_run_no_candidate_swaps_available(monkeypatch):
    graph = _empty_graph(2)  # no edges
    swap_pass = SabreSwapPass(graph, max_attempts=1)
    circuit = _two_qubit_circuit()

    def fake_init_layout(self, n_logical, phys_nodes, active_qubits, layout_hint):
        return [0, 0]  # force both logical qubits onto the same physical node

    monkeypatch.setattr(SabreSwapPass, "_init_layout", fake_init_layout)

    with pytest.raises(RuntimeError, match="No candidate swaps available; coupling graph likely degenerate"):
        swap_pass.run(circuit)


def test_run_no_swap_candidate_selected(monkeypatch):
    swap_pass = SabreSwapPass(_chain_graph(3), max_attempts=1, initial_layout=[0, 2])
    circuit = _two_qubit_circuit()

    # Keep layout stable so distances never improve.
    monkeypatch.setattr(SabreSwapPass, "_swap_mapping", lambda *args, **kwargs: None)
    monkeypatch.setattr(SabreSwapPass, "_cost_set", lambda *args, **kwargs: math.inf)

    with pytest.raises(RuntimeError, match="SABRE heuristic could not select a swap candidate"):
        swap_pass.run(circuit)


def test_extended_set_zero_budget():
    swap_pass = SabreSwapPass(_chain_graph(2))
    per_qubit = [[0], [0]]
    pos = [0, 0]
    assert swap_pass._extended_set(per_qubit, pos, 0) == set()
