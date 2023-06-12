from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
from qibo.gates import RX, RY, I

from qililab import Experiment, build_platform
from qililab.experiment.portfolio.randomized_benchmarking.randomized_benchmarking import (
    CliffordGate,
    RandomizedBenchmarking,
)
from qililab.typings import ExperimentOptions
from tests.data import Galadriel


@pytest.fixture(name="primitive_gates")
def primitive_gates():
    # primitives are a subset of cliffords
    return {0: {"name": "I"}, 1: {"name": "X_pi/2"}, 2: {"name": "Y_pi/2"}, 3: {"name": "X_pi"}, 4: {"name": "Y_pi"}}


@pytest.fixture(name="clifford_gates")
def get_clifford_gates():
    return [0, 21, 123, 3, 214, 124, 4, 2134, 12, 34, 213, 1234, 23, 13, 1214, 24, 1, 121, 234, 14, 12134, 2, 134, 1213]


@pytest.fixture(name="clifford_gate")
def get_clifford_gate():
    # WARNING: the index of the clifford gate is the clifford num - 1 (i.e. starts at 0, not 1)
    return CliffordGate(7, 5, 6)


class TestCliffordGate:
    def test_init_logging_error(self):
        return

    def test_init(self, clifford_gate, primitive_gates, clifford_gates):
        assert clifford_gate.idx == 7
        assert clifford_gate.num_qubits == 6
        assert clifford_gate.clifford_gates == clifford_gates
        assert clifford_gate._gate == 2134

        prim_gates = [gate["name"] for gate in clifford_gate.prim_gates.values()]
        assert prim_gates == ["I", "X_pi/2", "Y_pi/2", "X_pi", "Y_pi"]

    def test_properties(self, clifford_gate):
        assert clifford_gate.inverse.idx == 11
        assert clifford_gate.gate_decomp == ["Y_pi/2", "X_pi/2", "X_pi", "Y_pi"]
        assert np.allclose(clifford_gate.matrix, np.array([[0.5 + 0.5j, 0.5 - 0.5j], [-0.5 - 0.5j, 0.5 - 0.5j]]))
        assert [(gate.name, gate.parameters) for gate in clifford_gate.circuit.queue] == [
            ("ry", (1.5707963267948966,)),
            ("rx", (1.5707963267948966,)),
            ("rx", (3.141592653589793,)),
            ("ry", (3.141592653589793,)),
        ]


@pytest.fixture(name="rb")
def fixture_rb():
    """Return RandomizedBenchmarking object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    lengths = list(np.arange(0, 31, 10, dtype=int))
    num_qubits = 5
    qubit_idx = 2
    simulation = False
    num_seeds = 10
    rb = RandomizedBenchmarking(
        lengths,
        num_qubits=num_qubits,
        qubit_idx=qubit_idx,
        simulation=simulation,
        num_seeds=num_seeds,
        platform=platform,
    )
    rb._execute_qibo_circuit = MockResult()
    return rb


# mocks for acquisitions = result.results[0].acquisitions()
class MockResult(Mock):
    def __getitem__(self, key):
        return MockAquisition()


class MockAquisition:
    def acquisitions(self):
        data = {"i": np.exp(-1 * np.linspace(0, 10, 4)), "q": np.exp(-1.2 * np.linspace(0, 10, 4))}
        return pd.DataFrame(data)


class TestRandomizedBenchmarking:
    def test_init(self, rb):
        assert rb.length_list == list(np.arange(0, 11, 10, dtype=int))
        assert rb.num_seeds == 10
        assert rb.seed == 70
        assert rb._circuits is None
        assert rb.simulation is False
        assert rb.loops == []
        assert rb.num_qubits == 5
        assert rb.qubit_idx == 2
        assert rb.signal is None

        assert rb.initial_fit_params_I is None
        assert rb.initial_fit_params_X is None

    def test_properties(self, rb):
        rb._seed = 80
        assert rb.seed == 80
        rb.seed = 80  # set seed with setter method
        gen = np.random.default_rng(seed=80)
        assert np.allclose(rb.rng.random(10), gen.random(10))

        # no way around this other than to copy - test the output since
        # the circuits are random
        circuits = rb.circuits[0]
        circuits_I = [
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
            ("id", (2,)),
            ("measure", ()),
        ]
        circuits_X = [
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
            ("rx", (3.141592653589793,)),
            ("measure", ()),
        ]
        assert [(gate.name, gate.parameters) for circuit in circuits["X"] for gate in circuit.queue] == circuits_X
        assert [(gate.name, gate.parameters) for circuit in circuits["I"] for gate in circuit.queue] == circuits_I
        # check that the final state for I circuits is the 0th state
        assert np.allclose(sum(circuit().state() for circuit in circuits["I"])[0], len(circuits["I"]))

        # check that the final state for X circuits is the RX(pi) state of the 2nd qubit
        assert np.allclose(sum(circuit().state() for circuit in circuits["X"])[4], -1j * len(circuits["X"]))

    def test_run(self, rb):
        options = ExperimentOptions(loops=[])

        signal = rb.run(options)
        assert isinstance(signal, dict)
        assert isinstance(signal["I"], dict)
        assert isinstance(signal["X"], dict)
        # check that length loop is stored as it should
        assert sum(key == lenght for key, lenght in zip(signal["I"].keys(), [0, 10])) == 2
        assert sum(key == lenght for key, lenght in zip(signal["X"].keys(), [0, 10])) == 2
        # check that values are passed properly
        assert all(np.allclose(20.0 * np.ones(4), value) for value in signal["I"].values())
        assert all(np.allclose(20.0 * np.ones(4), value) for value in signal["X"].values())

    def test_fit(self, rb):
        """Test fit method."""
        options = ExperimentOptions(loops=[])

        initial_params_I = {"p": 0.9, "A": 1, "B": -44.5}

        rb.initial_fit_params_I = initial_params_I
        # rb.initial_fit_params_X = initial_params_X
        rb.run(options)
        rb.fit()
