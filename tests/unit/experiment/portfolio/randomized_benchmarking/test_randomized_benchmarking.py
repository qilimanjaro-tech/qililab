from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
from qibo.gates import RX, RY, I

from qililab import Experiment, build_platform
from qililab.experiment.portfolio.randomized_benchmarking.randomized_benchmarking import (
    CliffordGate,
    RandomizedBenchmarking,
    RandomizedBenchmarkingWithLoops,
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
            platform = build_platform(name="mock")
            mock_load.assert_called()
            mock_open.assert_called()
    lengths = list(np.arange(0, 5, 1, dtype=int))
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


@pytest.fixture(name="rbloops")
def fixture_rb_loops():
    """Return RandomizedBenchmarkingWithLoops object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="mock")
            mock_load.assert_called()
            mock_open.assert_called()
    rbloop = RandomizedBenchmarkingWithLoops(
        length_list=[2],
        num_qubits=2,
        qubit_idx=0,
        simulation=False,
        num_seeds=1,
        platform=platform,
        amplitude_values=np.linspace(0, 0.8, 2),
        frequency_values=np.linspace(3 * 10**9, 4 * 10**9, 2),
        drag_coeff_values=np.linspace(0, 1, 2),
    )
    rbloop._execute_qibo_circuit = MockResult()

    return rbloop


@pytest.fixture(name="circuits_I_X_1")
def fixture_circuits_I_X1():
    circuit_X = [
        ("ry", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("measure", ()),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("measure", ()),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (3.141592653589793,)),
        ("id", (2,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
    ]
    circuit_I = [
        ("ry", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("ry", (1.5707963267948966,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("measure", ()),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("measure", ()),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (3.141592653589793,)),
        ("rx", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("ry", (1.5707963267948966,)),
        ("rx", (1.5707963267948966,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("rx", (1.5707963267948966,)),
        ("rx", (3.141592653589793,)),
        ("ry", (3.141592653589793,)),
        ("measure", ()),
    ]

    return (circuit_I, circuit_X)


# mocks for acquisitions = result.results[0].acquisitions()
class MockResult(Mock):
    def __getitem__(self, key):
        return MockAquisition()


class MockAquisition:
    def acquisitions(self):
        data = {"i": 10 / np.sqrt(2) * np.ones(4), "q": 10 / np.sqrt(2) * np.ones(4)}
        return pd.DataFrame(data)


class TestRandomizedBenchmarking:
    def test_init(self, rb):
        assert rb.length_list == list(np.arange(0, 5, 1, dtype=int))
        assert rb.num_seeds == 10
        assert rb.seed == 70
        assert not rb._circuits
        assert rb.simulation is False
        assert rb.loops == []
        assert rb.num_qubits == 5
        assert rb.qubit_idx == 2
        assert rb.signal is None

        assert rb.initial_fit_params_I is None
        assert rb.initial_fit_params_X is None

    def test_properties(self, rb, circuits_I_X_1):
        rb._seed = 80
        assert rb.seed == 80
        rb.seed = 80  # set seed with setter method
        gen = np.random.default_rng(seed=80)
        assert np.allclose(rb.rng.random(10), gen.random(10))

        circuits = rb.circuits[1]
        circuits_I, circuits_X = circuits_I_X_1
        assert [(gate.name, gate.parameters) for circuit in circuits["X"] for gate in circuit.queue] == circuits_X
        assert [(gate.name, gate.parameters) for circuit in circuits["I"] for gate in circuit.queue] == circuits_I
        # check that the final state for I circuits is the 0th state
        assert np.allclose(sum(np.abs(circuit().state()) for circuit in circuits["I"])[0], len(circuits["I"]))
        # check that the final state for X circuits is the RX(pi) state of the 2nd qubit
        assert np.allclose(sum(abs(circuit().state()) for circuit in circuits["X"])[4], len(circuits["X"]))

    def test_run(self, rb):
        options = ExperimentOptions(loops=[])

        signal = rb.run(options)
        assert isinstance(signal, dict)
        assert isinstance(signal["I"], dict)
        assert isinstance(signal["X"], dict)
        # check that length loop is stored as it should
        assert sum(key == lenght for key, lenght in zip(signal["I"].keys(), [0, 10])) == 1
        assert sum(key == lenght for key, lenght in zip(signal["X"].keys(), [0, 10])) == 1
        # check that values are passed properly
        assert all(np.allclose(20.0 * np.ones(4), value) for value in signal["I"].values())
        assert all(np.allclose(20.0 * np.ones(4), value) for value in signal["X"].values())

    @patch(
        "qililab.experiment.portfolio.randomized_benchmarking.randomized_benchmarking.RandomizedBenchmarking.Id",
        new=-44 - 2 * np.exp(-np.arange(0, 5, 1) / 45),
    )
    @patch(
        "qililab.experiment.portfolio.randomized_benchmarking.randomized_benchmarking.RandomizedBenchmarking.X",
        new=-44 + 2 * np.exp(-np.arange(0, 5, 1) / 45),
    )
    def test_plot_fit(self, rb):
        lengths = np.arange(0, 5, 1)
        i_vals = -44 - 2 * np.exp(-lengths / 45)
        x_vals = -44 + 2 * np.exp(-lengths / 45)
        rb.Id = i_vals
        rb.X = x_vals

        fig, fit_res_I, fit_res_X, gate_fid = rb.plot_fit()

        line_I_expected = (lengths, i_vals)
        line_X_expected = (lengths, x_vals)
        fit_I_expected = (lengths, np.array([-45.99901404, -45.93858115, -45.89961807, -45.87449729, -45.8583011]))
        fit_X_expected = (lengths, np.array([-42.0009839, -42.06141903, -42.10038275, -42.12550343, -42.14169924]))

        line_I, line_X, fit_I, fit_X = fig.gca().get_lines()
        assert all((np.allclose(lin_i, exp_i) for lin_i, exp_i in zip(line_I.get_data(), line_I_expected)))
        assert all((np.allclose(lin_x, exp_x) for lin_x, exp_x in zip(line_X.get_data(), line_X_expected)))
        assert all((np.allclose(fit_i, exp_i) for fit_i, exp_i in zip(fit_I.get_data(), fit_I_expected)))
        assert all((np.allclose(fit_x, exp_x) for fit_x, exp_x in zip(fit_X.get_data(), fit_X_expected)))

        assert fig.axes[0].get_xlabel() == "# Cliffords"
        assert fig.axes[0].get_ylabel() == "Signal (a.u.)"
        assert fig.axes[0].get_title() == "Gate Fidelity = 0.8956"

        assert np.allclose(
            fit_res_I.best_fit, np.array([-45.99901404, -45.93858115, -45.89961807, -45.87449729, -45.8583011])
        )
        assert np.allclose(
            fit_res_X.best_fit, np.array([-42.0009839, -42.06141903, -42.10038275, -42.12550343, -42.14169924])
        )
        assert np.allclose(gate_fid, 0.8956452)


class TestRandomizedBenchmarkingWithLoops:
    def test_init(self, rbloops):
        drag_values = np.linspace(0, 1, 2)
        amp_values = np.linspace(0, 0.8, 2)
        freq_values = np.linspace(3 * 10**9, 4 * 10**9, 2)

        assert rbloops.num_qubits == 2
        assert rbloops.qubit_idx == 0
        assert rbloops.simulation is False
        assert rbloops.num_seeds == 1
        assert np.allclose(rbloops.amplitude_values, amp_values)
        assert np.allclose(rbloops.frequency_values, freq_values)
        assert np.allclose(rbloops.drag_coeff_values, drag_values)
        assert rbloops.seed == 70

        loop_drag, loop_freq, loop_amp = rbloops.loops[0].loops

        assert np.allclose(loop_drag.values, drag_values)
        assert np.allclose(loop_amp.values, amp_values)
        assert np.allclose(loop_freq.values, freq_values)

        assert loop_drag.parameter.value == "drag_coefficient"
        assert loop_drag.alias == "Drag(0)"

        assert loop_amp.parameter.value == "amplitude"
        assert loop_amp.alias == "Drag(0)"

        assert loop_freq.parameter.value == "intermediate_frequency"
        assert loop_freq.alias == "drive_line_q0_bus"

        assert rbloops.results_shape == (2, 2, 2)

    @patch(
        "qililab.experiment.portfolio.randomized_benchmarking.randomized_benchmarking.RandomizedBenchmarking.Id",
        new=np.full((2, 2, 2, 2), 7),
    )
    def test_plot(self, rbloops):
        pass
