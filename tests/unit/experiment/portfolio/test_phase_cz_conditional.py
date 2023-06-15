"""Unit tests for the three ``cz conditional`` experiments."""

from unittest.mock import MagicMock, patch

import matplotlib.pyplot
import numpy as np
import pytest
from qibo.backends import NumpyBackend
from qibo.gates import CZ, RX, RZ
from qibo.models import Circuit

from qililab import build_platform
from qililab.experiment import CzConditional
from tests.data import Galadriel


@pytest.fixture(name="cz_exp")
def fixture_cz_exp():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    return CzConditional(
        control_qubit=1,
        target_qubit=0,
        platform=platform,
        phase_loop_values=np.linspace(0, np.pi, 2),
        duration_loop_values=np.linspace(0, 40, 2),
        amplitude_loop_values=None,
        b_cz_loop_values=None,
        park_qubit_id=None,
        experiment_gate="Park",
    )


matplotlib.pyplot = MagicMock()


def apply_circuit(circuit: Circuit, target_qubit, control_qubit) -> np.ndarray:
    """Based on same method for gate transpiler tests, but adding
    support for Park/Park/Wait -> CZ
    Transpile park gates to CZ if they are applied either in control or target qubits
    Apply native gates from a transpiled circuit
    Drag pulses are translated to supported qibo.gates RX, RZ.
    Gates are applied onto initial state |00...0>
    Backend is set to numpy for faster execution since circuits are small

    Args:
        circuit (Circuit): transpiled qibo circuit to be executed

    Returns:
        state (np.ndarray): resulting state
    """

    backend = NumpyBackend()

    nqubits = circuit.nqubits
    # start initial state |00...0>
    state = np.zeros(2**nqubits)
    state[0] = 1
    for gate in circuit.queue:
        if gate.name == "park" and gate.qubits[0] in (control_qubit, target_qubit):
            cz = CZ(control_qubit, target_qubit)
            state = backend.apply_gate(cz, state, nqubits)

        if gate.name == "rz":
            state = backend.apply_gate(gate, state, nqubits)
        if gate.name == "drag":
            theta = gate.parameters[0]
            phi = gate.parameters[1]
            qubit = gate.qubits[0]
            # apply Drag gate as RZ and RX gates
            state = backend.apply_gate(RZ(qubit, -phi), state, nqubits)
            state = backend.apply_gate(RX(qubit, theta), state, nqubits)
            state = backend.apply_gate(RZ(qubit, phi), state, nqubits)

        if gate.name == "cz":
            state = backend.apply_gate(gate, state, nqubits)

    return state


class TestCzConditional:
    def test_init(self, cz_exp):
        assert cz_exp.control_qubit == 1
        assert cz_exp.target_qubit == 0
        assert np.allclose(cz_exp.phase_loop_values, np.linspace(0, np.pi, 2))
        assert np.allclose(cz_exp.duration_loop_values, np.linspace(0, 40, 2))
        assert cz_exp.park_qubit_id is None

        assert cz_exp.flux_active_qubit == 1
        assert cz_exp.flux_passive_qubit == 0
        # from tests.data.Galadriel
        assert cz_exp.drag_time == 50
        assert cz_exp.nqubits == 2

    def test_get_off_on_c(self, cz_exp):
        # in both cases (park, cz) target and control are the same
        ctrl = cz_exp.control_qubit
        tgt = cz_exp.target_qubit
        # circuits should be 1 on 0th qubit and differ in phase
        c_off_result = np.array([-1, 0, 0, 0])
        c_on_result = np.array([0, 0, -1j, 0])
        # test for park gates
        c_off, c_on = cz_exp.get_off_on_c(ctrl, tgt)
        assert np.allclose(apply_circuit(c_off, tgt, ctrl), c_off_result)
        assert np.allclose(apply_circuit(c_on, tgt, ctrl), c_on_result)
        assert [(gate.name, gate.qubits, gate.parameters) for gate in c_on.queue] == [
            ("drag", (1,), (0, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("park", (1,), ()),
            ("wait", (0,), (50,)),
            ("drag", (1,), (0, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("measure", (1,), ()),
            ("measure", (0,), ()),
        ]
        assert [(gate.name, gate.qubits, gate.parameters) for gate in c_off.queue] == [
            ("drag", (1,), (3.141592653589793, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("park", (1,), ()),
            ("wait", (0,), (50,)),
            ("drag", (1,), (3.141592653589793, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("measure", (1,), ()),
            ("measure", (0,), ()),
        ]

        # test for cz gates
        cz_exp.experiment_gate = "CZ"
        c_off, c_on = cz_exp.get_off_on_c(ctrl, tgt)
        assert np.allclose(apply_circuit(c_off, tgt, ctrl), c_off_result)
        assert np.allclose(apply_circuit(c_on, tgt, ctrl), c_on_result)
        assert [(gate.name, gate.qubits, gate.parameters) for gate in c_on.queue] == [
            ("drag", (1,), (0, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("cz", (1, 0), ()),
            ("drag", (1,), (0, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("measure", (1,), ()),
            ("measure", (0,), ()),
        ]
        assert [(gate.name, gate.qubits, gate.parameters) for gate in c_off.queue] == [
            ("drag", (1,), (3.141592653589793, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("cz", (1, 0), ()),
            ("drag", (1,), (3.141592653589793, 0)),
            ("drag", (0,), (1.5707963267948966, 0)),
            ("measure", (1,), ()),
            ("measure", (0,), ()),
        ]

    @patch("qililab.experiment.portfolio.ExperimentAnalysis.post_process_results")
    def test_post_process_results(self, mock_postprocess, cz_exp):
        cz_exp.amplitude_loop_values = np.linspace(1, 2, 2)
        # this_shape should be:
        #  len(loop) (duration or b_cz) = 2
        #  len(amplitude_loop) = 2
        #  num_circuits = 2
        #  len(phase_loop) = 2
        #  num_qubits = 2
        results = np.ones(2**5)
        cz_exp.post_processed_results = results
        post_processed_results = cz_exp.post_process_results()
        assert cz_exp.this_shape == (2, 2, 2, 2, 2)
        assert np.allclose(post_processed_results, results.reshape((2, 2, 2, 2, 2)))
        assert np.allclose(cz_exp.these_loops["values"], [np.linspace(1, 2, 2), np.linspace(0, 40, 2)])
        assert cz_exp.these_loops["labels"] == ["Duration", "Amplitude"]

        # b_cz instead of duration
        cz_exp.duration_loop_values = None
        cz_exp.b_cz_loop_values = np.linspace(1, 2, 3)
        results = np.ones(3 * 2**4)
        cz_exp.post_processed_results = results
        post_processed_results = cz_exp.post_process_results(snz_cal=True)
        assert cz_exp.this_shape == (3, 2, 2, 2, 2)
        assert np.allclose(post_processed_results, results.reshape((3, 2, 2, 2, 2)))
        assert np.allclose(cz_exp.these_loops["values"][0], np.linspace(1, 2, 2))
        assert np.allclose(cz_exp.these_loops["values"][1], np.linspace(1, 2, 3))
        assert cz_exp.these_loops["labels"] == ["B_cz", "Amplitude"]

        # try the same with no duration / b_cz loop
        cz_exp.duration_loop_values = None
        results = np.ones(2**4)
        cz_exp.post_processed_results = results
        post_processed_results = cz_exp.post_process_results()
        assert cz_exp.this_shape == (2, 2, 2, 2)
        assert np.allclose(post_processed_results, results.reshape((2, 2, 2, 2)))
        assert np.allclose(cz_exp.these_loops["values"], [np.linspace(1, 2, 2)])
        assert cz_exp.these_loops["labels"] == ["Amplitude"]

        # no amplitude loop with duration loop
        cz_exp.duration_loop_values = np.linspace(0, 40, 2)
        cz_exp.amplitude_loop_values = None
        results = np.ones(2**4)
        cz_exp.post_processed_results = results
        post_processed_results = cz_exp.post_process_results()
        assert cz_exp.this_shape == (2, 2, 2, 2)
        assert np.allclose(post_processed_results, results.reshape((2, 2, 2, 2)))
        assert np.allclose(cz_exp.these_loops["values"], [np.linspace(0, 40, 2)])
        assert cz_exp.these_loops["labels"] == ["Duration"]

        # no amplitude or duration / b_cz loop
        cz_exp.duration_loop_values = None
        cz_exp.amplitude_loop_values = None
        results = np.ones(2**3)
        cz_exp.post_processed_results = results
        post_processed_results = cz_exp.post_process_results()
        assert cz_exp.this_shape == (2, 2, 2)
        results = results.reshape((2, 2, 2))
        assert np.allclose(post_processed_results, results)

    def test_fit_cosines(self, cz_exp):
        # TODO: test plot methods
        cosines = np.array([[np.cos(np.linspace(0, 2 * np.pi, 40))], [np.sin(np.linspace(0, 2 * np.pi, 40))]])
        cz_exp.phase_loop_values = [np.linspace(0, 2 * np.pi, 40)]
        phase_diff, fit = cz_exp.fit_cosines(cosines, "mock_label")
        assert np.allclose(phase_diff, -1 * np.pi / 2)
        assert np.allclose(fit, -1 * np.pi / 2)

    @patch("qililab.experiment.portfolio.ExperimentAnalysis.post_process_results")
    @patch("qililab.experiment.portfolio.CzConditional.fit_cosines", return_value=[0, 1])
    def test_fit_all_curves(self, mock_postproces, mock_fit, cz_exp):
        cz_exp.amplitude_loop_values = np.linspace(1, 2, 2)
        cz_exp.duration_loop_values = None
        results = np.ones(2**4)
        cz_exp.post_processed_results = results
        cz_exp.post_process_results()
        cz_exp.fit_all_curves()
        return
