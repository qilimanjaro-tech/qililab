import math
import random
from types import SimpleNamespace
from typing import Iterable

import numpy as np
import pytest
from rustworkx import PyGraph

from qilisdk.digital import Circuit
from qilisdk.digital.gates import CZ, RX, RY, RZ, SWAP, U3, Controlled, Gate, M
from qilisdk.digital.exceptions import GateHasNoMatrixError

from qililab.digital.circuit_transpiler import CircuitTranspiler
from qililab.digital.circuit_transpiler_passes import TranspilationContext
from qililab.digital.circuit_transpiler_passes.add_phases_to_drags_from_rz_and_cz import (
    AddPhasesToRmwFromRZAndCZPass,
)
from qililab.digital.circuit_transpiler_passes.cancel_identity_pairs_pass import (
    CancelIdentityPairsPass,
    _first_nonzero_phase,
)
from qililab.digital.circuit_transpiler_passes.circuit_transpiler_pass import CircuitTranspilerPass
from qililab.digital.circuit_transpiler_passes.custom_layout_pass import CustomLayoutPass
from qililab.digital.circuit_transpiler_passes.fuse_single_qubit_gates_pass import FuseSingleQubitGatesPass
from qililab.digital.circuit_transpiler_passes.numeric_helpers import _mat_RZ, _wrap_angle, _zyz_from_unitary
from qililab.digital.circuit_transpiler_passes.sabre_layout_pass import SabreLayoutPass
from qililab.digital.circuit_transpiler_passes.sabre_swap_pass import SabreSwapPass
from qililab.digital.utils import qprogram_results_to_samples
from qililab.result.qprogram import QProgramResults
from qililab.settings.digital import DigitalCompilationSettings


def _empty_digital_settings(topology: Iterable[tuple[int, int]]):
    return DigitalCompilationSettings.model_validate({"topology": list(topology), "gates": {}})


def test_build_topology_graph_handles_empty_and_sparse():
    empty_settings = _empty_digital_settings([])
    transpiler_empty = CircuitTranspiler(empty_settings)
    assert list(transpiler_empty._topology.node_indices()) == []

    sparse_settings = _empty_digital_settings([(0, 2)])
    transpiler_sparse = CircuitTranspiler(sparse_settings)
    assert list(transpiler_sparse._topology.node_indices()) == [0, 2]


def test_extract_gate_corrections_skips_non_dict_entries():
    settings = _empty_digital_settings([])
    transpiler_pass = AddPhasesToRmwFromRZAndCZPass(settings)

    class DummyEvent:
        def __init__(self, options):
            self.options = options

    gate_settings = [
        DummyEvent(options=["not", "a", "dict"]),
        DummyEvent(options={}),
        DummyEvent(options={"q0_phase_correction": 0.3, "q1_phase_correction": -0.1}),
    ]

    corr = transpiler_pass._extract_gate_corrections(gate_settings, 0, 1)
    assert corr == {"q0_phase_correction": 0.3, "q1_phase_correction": -0.1}


def test_first_nonzero_phase_returns_zero_for_empty_matrix():
    assert _first_nonzero_phase(np.zeros((2, 2), dtype=complex)) == 0.0


class _LazyGate(Gate):
    """Gate whose first matrix access succeeds and subsequent accesses fail."""

    def __init__(self, qubit: int) -> None:
        super().__init__()
        self._qubits = (qubit,)
        self._calls = 0

    @property
    def name(self) -> str:
        return "Lazy"

    @property
    def qubits(self) -> tuple[int, ...]:
        return self._qubits

    @property
    def target_qubits(self) -> tuple[int, ...]:
        return self._qubits

    @property
    def control_qubits(self) -> tuple[int, ...]:
        return ()

    @property
    def nqubits(self) -> int:
        return 1

    @property
    def matrix(self) -> np.ndarray:
        self._calls += 1
        if self._calls == 1:
            return np.eye(2)
        raise GateHasNoMatrixError("no matrix available on second access")


def test_cancel_identity_controlled_fallback_to_matrix_keys():
    pass_instance = CancelIdentityPairsPass()
    controlled = Controlled(1, basic_gate=_LazyGate(0))

    f_key, inv_key = pass_instance._forward_inverse_keys(controlled)
    assert f_key[0] == "U" and inv_key[0] == "U"
    assert controlled.basic_gate._calls == 2


def test_circuit_transpiler_pass_appends_unique_keys():
    class DummyPass(CircuitTranspilerPass):
        def run(self, circuit: Circuit) -> Circuit:
            self.append_circuit_to_context(circuit)
            return circuit

    ctx = TranspilationContext()
    p = DummyPass()
    p.attach_context(ctx)
    circ = Circuit(1)
    circ.add(RZ(0, phi=0.1))

    p.append_circuit_to_context(circ)
    p.append_circuit_to_context(circ)
    assert list(ctx.circuits) == ["DummyPass", "DummyPass_2"]


def _make_line_graph(num_nodes: int) -> PyGraph:
    graph = PyGraph()
    graph.add_nodes_from(range(num_nodes))
    for a in range(num_nodes - 1):
        graph.add_edge(a, a + 1, None)
    return graph


def test_custom_layout_runtime_when_swaps_do_not_update(monkeypatch):
    topology = _make_line_graph(3)
    mapping = {0: 0, 1: 2}
    circuit = Circuit(2)
    circuit.add(CZ(0, 1))

    custom = CustomLayoutPass(topology, mapping)

    monkeypatch.setattr(custom, "_apply_swap_to_layout", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="still non-adjacent"):
        custom.run(circuit)


@pytest.mark.parametrize(
    "gate,new_qubits,expected_cls",
    [
        (RY(0, theta=0.5), (2,), RY),
        (RZ(0, phi=0.1), (3,), RZ),
        (U3(0, theta=0.2, phi=0.3, gamma=-0.1), (1,), U3),
        (CZ(0, 1), (1, 2), CZ),
        (SWAP(0, 1), (2, 3), SWAP),
        (M(0), (4,), M),
    ],
)
def test_custom_layout_retarget_gate(gate, new_qubits, expected_cls):
    topology = _make_line_graph(2)
    custom = CustomLayoutPass(topology, {0: 0})
    retargeted = custom._retarget_gate(gate, new_qubits)
    assert isinstance(retargeted, expected_cls)
    assert retargeted.qubits == new_qubits


def test_custom_layout_shortest_path_start_equals_goal():
    topology = _make_line_graph(2)
    custom = CustomLayoutPass(topology, {0: 0})
    assert custom._shortest_path(1, 1) == [1]


@pytest.mark.parametrize(
    "gates,expected_name",
    [
        ([RZ(0, phi=0.25)], "RZ"),
        ([RY(0, theta=0.7)], "RY"),
        ([RY(0, theta=-0.3)], "RY"),
        ([RX(0, theta=0.4)], "RX"),
        ([RX(0, theta=-0.6)], "RX"),
        ([U3(0, theta=0.2, phi=0.1, gamma=0.05)], "U3"),
    ],
)
def test_fuse_single_qubit_flush_variants(gates, expected_name):
    circuit = Circuit(1)
    for g in gates:
        circuit.add(g)

    fused = FuseSingleQubitGatesPass().run(circuit)
    assert len(fused.gates) == 1
    out_gate = fused.gates[0]
    assert out_gate.name == expected_name


def test_fuse_single_qubit_flush_no_pending_on_measurement():
    circuit = Circuit(1)
    circuit.add(M(0))
    fused = FuseSingleQubitGatesPass().run(circuit)
    assert len(fused.gates) == 1
    assert isinstance(fused.gates[0], M)


def test_zyz_from_unitary_validations():
    with pytest.raises(ValueError, match="Expected 2x2"):
        _zyz_from_unitary(np.eye(3))

    with pytest.raises(ValueError, match="singular"):
        _zyz_from_unitary(np.array([[0.0, 0.0], [0.0, 0.0]], dtype=complex))


def test_qprogram_results_to_samples_skip_with_all_missing_raises():
    qresults = QProgramResults()
    qresults.results = {}
    with pytest.raises(ValueError, match="No measurement data found"):
        qprogram_results_to_samples(qresults, {0: 0}, on_missing="skip")


def test_qprogram_results_to_samples_skip_after_filtering(monkeypatch):
    class UniqueKey(int):
        __hash__ = int.__hash__

        def __eq__(self, other):
            return False

    class CloneList(list):
        def __init__(self, data: list[int]) -> None:
            super().__init__(data)
            self._iter_count = 0

        def __iter__(self):
            self._iter_count += 1
            if self._iter_count == 1:
                return super().__iter__()
            return (UniqueKey(item) for item in super().__iter__())

    def sorted_clone(iterable):
        return CloneList(list(iterable))

    monkeypatch.setattr("builtins.sorted", sorted_clone)

    qresults = QProgramResults()
    qresults.results = {"readout_q0_bus": [SimpleNamespace(threshold=[0, 1, 0, 1])]}

    with pytest.raises(ValueError, match="All requested qubits were missing"):
        qprogram_results_to_samples(qresults, {0: 0}, on_missing="skip")


def _make_triangle_graph() -> PyGraph:
    graph = PyGraph()
    graph.add_nodes_from(range(3))
    graph.add_edges_from([(0, 1, None), (1, 2, None), (0, 2, None)])
    return graph


def test_sabre_layout_extended_set_zero_budget():
    topology = _make_triangle_graph()
    layout_pass = SabreLayoutPass(topology, num_trials=1, seed=1)

    extended = layout_pass._extended_set(
        twoq_qubits=[(0, 1), (1, 2)],
        per_qubit=[[0, 1], [0, 1], [1]],
        pos=[0, 0, 0],
        max_size=0,
    )
    assert extended == set()


def test_sabre_layout_extended_set_respects_budget_and_breaks():
    topology = _make_triangle_graph()
    layout_pass = SabreLayoutPass(topology, num_trials=1, seed=1)

    extended = layout_pass._extended_set(
        twoq_qubits=[(0, 1), (1, 2), (0, 2)],
        per_qubit=[[0, 2], [0, 1], [1]],
        pos=[0, 0, 0],
        max_size=1,
    )
    assert extended == {2}


def test_sabre_layout_cost_front_handles_disconnected_and_decay():
    topology = _make_triangle_graph()
    layout_pass = SabreLayoutPass(topology, num_trials=1, seed=1)

    dist = [
        [0, 1_000_000_000, 2],
        [1_000_000_000, 0, 1],
        [2, 1, 0],
    ]
    decay = [0.1, 0.2, 0.3]
    cost = layout_pass._cost_front({0, 1}, [0, 1, 2], [(0, 1), (1, 2)], dist, decay, {0: 0, 1: 1, 2: 2})
    assert cost > 0

    cost_no_decay = layout_pass._cost_front({0}, [0, 1, 2], [(0, 1)], dist, None, {0: 0, 1: 1, 2: 2})
    assert cost_no_decay == 1e6


def test_sabre_layout_random_initial_layout_validates_physical_capacity():
    topology = _make_triangle_graph()
    layout_pass = SabreLayoutPass(topology, num_trials=1, seed=1)

    rng = random.Random(0)
    with pytest.raises(ValueError, match="need ≥ 4"):
        layout_pass._random_initial_layout(rng, 4, [0, 1, 2])


def test_sabre_swap_front_and_extended_sets_skip_scheduled():
    per_qubit = [[0, 1], [0]]
    pos = [0, 0]
    scheduled = [True, False]
    front = SabreSwapPass._front_set(per_qubit, pos, scheduled)
    assert front == {1}

    extended = SabreSwapPass._extended_set(per_qubit, pos, max_size=1)
    assert extended == {1}


def test_sabre_swap_cost_set_with_disconnected_and_decay():
    layout = [0, 1]
    twoq_pairs = [(0, 1)]
    dist = [[0, 1_000_000_000], [1_000_000_000, 0]]
    decay = [0.5, 0.25]
    phys_index = {0: 0, 1: 1}
    cost = SabreSwapPass._cost_set({0}, layout, twoq_pairs, dist, decay, phys_index)
    assert cost == pytest.approx(1e6 * (1 + 0.5 + 0.25))

    cost_no_decay = SabreSwapPass._cost_set({0}, layout, twoq_pairs, dist, None, phys_index)
    assert cost_no_decay == pytest.approx(1e6)


def _make_swap_pass(topology: PyGraph) -> SabreSwapPass:
    return SabreSwapPass(topology, max_attempts=1)


def test_sabre_swap_init_layout_exact_hint():
    topology = _make_line_graph(4)
    swap_pass = _make_swap_pass(topology)
    layout = swap_pass._init_layout(
        n_logical=2,
        phys_nodes=[0, 1, 2, 3],
        active_qubits={0, 1},
        layout_hint=[3, 1],
    )
    assert layout == [3, 1]


def test_sabre_swap_init_layout_active_only_hint():
    topology = _make_line_graph(4)
    swap_pass = _make_swap_pass(topology)
    layout = swap_pass._init_layout(
        n_logical=3,
        phys_nodes=[5, 6, 7, 8],
        active_qubits={1, 2},
        layout_hint=[7, 5],
    )
    assert layout[1] == 7 and layout[2] == 5
    assert len(layout) == 3


def test_sabre_swap_init_layout_prefix_hint_pads():
    topology = _make_line_graph(3)
    swap_pass = _make_swap_pass(topology)
    layout = swap_pass._init_layout(
        n_logical=3,
        phys_nodes=[1, 2, 3],
        active_qubits={0, 1, 2},
        layout_hint=[2],
    )
    assert set(layout) == {1, 2, 3}


def test_sabre_swap_init_layout_errors_for_missing_physicals():
    topology = _make_line_graph(3)
    swap_pass = _make_swap_pass(topology)
    with pytest.raises(ValueError, match="not present"):
        swap_pass._init_layout(
            n_logical=2,
            phys_nodes=[0, 1, 2],
            active_qubits={0, 1},
            layout_hint=[10, 11],
        )


def test_sabre_swap_init_layout_errors_for_duplicate_active_targets():
    topology = _make_line_graph(3)
    swap_pass = _make_swap_pass(topology)
    with pytest.raises(ValueError, match="unique physical qubits"):
        swap_pass._init_layout(
            n_logical=2,
            phys_nodes=[0, 1, 2],
            active_qubits={0, 1},
            layout_hint=[0, 0],
        )


def test_sabre_swap_init_layout_identity_with_empty_topology():
    topology = PyGraph()
    swap_pass = _make_swap_pass(topology)
    layout = swap_pass._init_layout(
        n_logical=0,
        phys_nodes=[],
        active_qubits=set(),
        layout_hint=None,
    )
    assert layout == []


def test_sabre_swap_init_layout_requires_enough_physical_nodes():
    topology = _make_line_graph(1)
    swap_pass = _make_swap_pass(topology)
    with pytest.raises(ValueError, match="needs 2"):
        swap_pass._init_layout(
            n_logical=2,
            phys_nodes=[0],
            active_qubits={0, 1},
            layout_hint=None,
        )


def test_sabre_swap_retarget_gate_supports_u3_and_swap():
    topology = _make_line_graph(2)
    swap_pass = _make_swap_pass(topology)

    new_u3 = swap_pass._retarget_gate(U3(0, theta=0.2, phi=0.1, gamma=-0.4), (1,))
    assert isinstance(new_u3, U3)
    assert new_u3.qubits == (1,)

    new_swap = swap_pass._retarget_gate(SWAP(0, 1), (0, 1))
    assert isinstance(new_swap, SWAP)
    assert new_swap.qubits == (0, 1)


def test_sabre_swap_run_uses_context_provided_initial_layout():
    topology = _make_line_graph(3)
    swap_pass = SabreSwapPass(topology, max_attempts=1)
    ctx = TranspilationContext()
    ctx.initial_layout = [0, 1]
    swap_pass.attach_context(ctx)

    circuit = Circuit(2)
    circuit.add(CZ(0, 1))

    out = swap_pass.run(circuit)
    assert list(g.name for g in out.gates) == ["CZ"]
    assert ctx.final_layout == {0: 0, 1: 1}
    assert ctx.metrics["swap_count"] == 0
