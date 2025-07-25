import queue
import re
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import qibo
from qibo import gates
from qibo.backends import NumpyBackend
from qibo.gates import CZ, M, X
from qibo.models import Circuit
import networkx as nx

from qililab.digital import CircuitTranspiler
from qililab.digital.native_gates import Drag, Wait
from qililab.pulse import PulseSchedule
from qililab.settings.digital import DigitalCompilationSettings
from qililab.digital import DigitalTranspilationConfig

qibo.set_backend("numpy")  # set backend to numpy (this is the faster option for < 15 qubits)

# transpilable gates
default_gates = [
    gates.I(0),
    gates.X(0),
    gates.Y(0),
    gates.Z(0),
    gates.H(0),
    gates.RX(0, 0),
    gates.RY(0, 0),
    gates.RZ(0, 0),
    gates.U1(0, 0),
    gates.U2(0, 0, 0),
    gates.U3(0, 0, 0, 0),
    gates.S(0),
    gates.SDG(0),
    gates.T(0),
    gates.TDG(0),
    gates.CNOT(0, 1),
    gates.CZ(0, 1),
    gates.SWAP(0, 1),
    gates.iSWAP(0, 1),
    gates.CRX(0, 1, 0),
    gates.CRY(0, 1, 0),
    gates.CRZ(0, 1, 0),
    gates.CU1(0, 1, 0),
    gates.CU2(0, 1, 0, 0),
    gates.CU3(0, 1, 0, 0, 0),
    gates.FSWAP(0, 1),
    gates.RXX(0, 1, 0),
    gates.RYY(0, 1, 0),
    gates.RZZ(0, 1, 0),
    gates.TOFFOLI(0, 1, 2),
]


def random_circuit(
    nqubits: int,
    ngates: int,
    rng: np.random.Generator,
    circuit_gates: list[qibo.gates.Gate] | None = None,
    exhaustive=False,
) -> Circuit:
    """Generates random qibo circuit with ngates

    Args:
        nqubits (int): number of qubits in the circuit
        ngates (int): number of gates in the circuit
        circuit_gates (dict[gates:int]): dictionary with gates and amount of qubits where those should be applied
        exhaustive (bool) : use all gates at least once (requires ngates>=len(gates))

    Returns:
        c (qibo.Circuit) : resulting circuit
    """

    # get list available gates
    if circuit_gates is None:
        circuit_gates = default_gates

    # init circuit
    c = Circuit(nqubits)

    # get list of gates to use
    if not exhaustive:
        list_gates = rng.choice(circuit_gates, ngates)
    # if exhaustive = True then add all the gates available
    else:
        if ngates < len(circuit_gates):
            raise ValueError("If exhaustive is set to True then ngates must be bigger than len(circuit_gates)!")
        list_gates = []
        for _ in range(ngates // len(circuit_gates)):
            list_gates.extend(circuit_gates)
        list_gates.extend(rng.choice(circuit_gates, ngates % len(circuit_gates), replace=False))
        rng.shuffle(list_gates)

    # add gates iteratively
    for gate in list_gates:
        # apply gate to random qubits
        new_qubits = rng.choice(list(range(nqubits)), len(gate.qubits), replace=False)
        gate = gate.on_qubits(dict(enumerate(new_qubits)))
        if (len(gate.parameters) != 0) and gate.name != "id":
            new_params = tuple(1 for _ in range(len(gate.parameters)))
            gate.parameters = new_params
        c.add(gate)

    return c


def apply_circuit(circuit: Circuit) -> np.ndarray:
    """Apply native gates from a transpiled circuit
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
        if gate.name == "rz":
            state = backend.apply_gate(gate, state, nqubits)
        if gate.name == "drag":
            theta = gate.parameters[0]
            phi = gate.parameters[1]
            qubit = gate.qubits[0]
            # apply Drag gate as RZ and RX gates
            state = backend.apply_gate(gates.RZ(qubit, -phi), state, nqubits)
            state = backend.apply_gate(gates.RX(qubit, theta), state, nqubits)
            state = backend.apply_gate(gates.RZ(qubit, phi), state, nqubits)

        if gate.name == "cz":
            state = backend.apply_gate(gate, state, nqubits)

    return state


def compare_circuits(circuit_q: Circuit, circuit_t: Circuit, nqubits: int) -> float:
    """Runs same circuit using transpiled gates and qibo gates,
    and calculates the scalar product of the 2 resulting states

    Args:
        circuit_q (Circuit): qibo circuit (not transpiled)
        circuit_t (Circuit): transpiled qibo circuit
        nqubits (int): number of qubits in the circuit

    Returns:
        float: absolute scalar product of the 2 resulting states from circuit execution
    """

    # get final state
    state_q = circuit_q().state()
    state_t = apply_circuit(circuit_t)

    # if state_t = k*state_q, where k is a global phase
    # then |state_q * state_t| = |state_q * state_q| * |k| = 1
    return np.abs(np.dot(np.conjugate(state_t), state_q))  # type: ignore[no-any-return]


def compare_exp_z(circuit_q: Circuit, circuit_t: Circuit, nqubits: int) -> list[np.ndarray]:
    r"""Runs same circuit using transpiled gates and qibo gates, applies Z operator to all qubits
    and then calculates the modulo of each coefficient of the state vector. This last operation
    removes the phase difference in Z so that if the state vectors have the same Z observables
    then the state vector coefficients will be the same.
    That is, for the state vector psi, psi' for the transpiled and qibo circuits
    .. math:: \Psi_k == \Psi'_k \forall k
    Where each psi_k is the coefficient of each basis of the 2^n dimensional state vector
    representation in Z

    Args:
        circuit_q (Circuit): qibo circuit (not transpiled)
        circuit_t (Circuit): transpiled qibo circuit
        nqubits (int): number of qubits in the circuit

    Returns:
        list[np.ndarray]: a list with 2 arrays, one corresponding to the state vector for the
            transpiled circuit and another one for the qibo circuit
    """

    # get final states and save them for modulo calculation
    state_q = circuit_q().state()
    state_q_0 = state_q.copy()
    state_t = apply_circuit(circuit_t)
    state_t_0 = state_t.copy()

    # apply measurement in Z
    backend = NumpyBackend()
    for q in range(circuit_q.nqubits):
        state_q = backend.apply_gate(gates.Z(q), state_q, circuit_q.nqubits)
        state_t = backend.apply_gate(gates.Z(q), state_t, circuit_q.nqubits)

    return [
        np.array([i * k for i, k in zip(np.conjugate(state_t_0), state_t)]),
        np.array([i * k for i, k in zip(np.conjugate(state_q_0), state_q)]),
    ]

@pytest.fixture(name="digital_settings")
def fixture_digital_compilation_settings() -> DigitalCompilationSettings:
    """Fixture that returns an instance of a ``Runcard.GatesSettings`` class."""
    digital_settings_dict = {
        "minimum_clock_time": 5,
        "delay_before_readout": 0,
        "topology": [(0, 2), (1, 2), (2, 3), (2, 4)],
        "gates": {
            "M(0)": [
                {
                    "bus": "readout_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "Drag(0)": [
                {
                    "bus": "drive_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 198,  # try some non-multiple of clock time (4)
                        "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
                    },
                }
            ],
            # random X schedule
            "X(0)": [
                {
                    "bus": "drive_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
                    },
                },
                {
                    "bus": "flux_q0",
                    "wait_time": 30,
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
                    },
                },
                {
                    "bus": "drive_q0",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "rectangular"},
                    },
                },
                {
                    "bus": "drive_q4",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "gaussian", "num_sigmas": 4},
                    },
                },
            ],
            "M(1)": [
                {
                    "bus": "readout_q1",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "M(2)": [
                {
                    "bus": "readout_q2",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                    },
                }
            ],
            "M(3)": [
                {
                    "bus": "readout_q3",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0.5,
                        "duration": 100,
                        "shape": {"name": "gaussian", "num_sigmas": 2},
                    },
                }
            ],
            "M(4)": [
                {
                    "bus": "readout_q4",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0.5,
                        "duration": 100,
                        "shape": {"name": "gaussian", "num_sigmas": 2},
                    },
                }
            ],
            "CZ(2,3)": [
                {
                    "bus": "flux_q2",
                    "wait_time": 10,
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 90,
                        "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                    },
                },
                # park pulse
                {
                    "bus": "flux_q0",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "rectangular"},
                    },
                },
            ],
            # test couplers
            "CZ(4, 0)": [
                {
                    "bus": "flux_c2",
                    "wait_time": 10,
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 90,
                        "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
                    },
                },
                {
                    "bus": "flux_q0",
                    "pulse": {
                        "amplitude": 0.7,
                        "phase": 0,
                        "duration": 100,
                        "shape": {"name": "rectangular"},
                    },
                },
            ],
            "CZ(0,1)": [
                {
                    "bus": "flux_q1",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                        "options": {"q0_phase_correction": 1, "q1_phase_correction": 2},
                    },
                }
            ],
            "CZ(0,2)": [
                {
                    "bus": "flux_q2",
                    "pulse": {
                        "amplitude": 0.8,
                        "phase": 0,
                        "duration": 200,
                        "shape": {"name": "rectangular"},
                        "options": {"q1_phase_correction": 2, "q2_phase_correction": 0},
                    },
                }
            ],
        },
        "buses": {
            "readout_q0": {
                "line": "readout",
                "qubits": [0]
            },
            "readout_q1": {
                "line": "readout",
                "qubits": [1]
            },
            "readout_q2": {
                "line": "readout",
                "qubits": [2]
            },
            "readout_q3": {
                "line": "readout",
                "qubits": [3]
            },
            "readout_q4": {
                "line": "readout",
                "qubits": [4]
            },
            "drive_q0": {
                "line": "drive",
                "qubits": [0]
            },
            "drive_q1": {
                "line": "drive",
                "qubits": [1]
            },
            "drive_q2": {
                "line": "drive",
                "qubits": [2]
            },
            "drive_q3": {
                "line": "drive",
                "qubits": [3]
            },
            "drive_q4": {
                "line": "drive",
                "qubits": [4]
            },
            "flux_q0": {
                "line": "flux",
                "qubits": [0]
            },
            "flux_q1": {
                "line": "flux",
                "qubits": [1]
            },
            "flux_q2": {
                "line": "flux",
                "qubits": [2]
            },
            "flux_q3": {
                "line": "flux",
                "qubits": [3]
            },
            "flux_q4": {
                "line": "flux",
                "qubits": [4]
            },
            "flux_c2": {
                "line": "flux",
                "qubits": [2]
            }
        }
    }
    return DigitalCompilationSettings(**digital_settings_dict)  # type: ignore[arg-type]


def get_bus_schedule(pulse_bus_schedule: dict, port: str) -> list[dict]:
    """Helper function for bus schedule data"""

    return [
        {**asdict(schedule)["pulse"], "start_time": schedule.start_time, "qubit": schedule.qubit}
        for schedule in pulse_bus_schedule[port]
    ]


class TestCircuitTranspiler:
    """Tests for the circuit transpiler class"""

    def test_circuit_to_native(self):
        """Tests the circuit to native gates function without/with optimization
        Does not test phase corrections.
        Test that the transpiled circuit outputs same result if
        circuits are the same, and different results if circuits are
        not the same. State vectors should be the same up to a global
        phase difference.
        With optimization, virtual Zs are applied so there will be a phase difference
        between each single qubit. To check that the transpiled and untranspiled circuits
        are equal, we then check the expected value for each element of the state vector
        """
        # FIXME: do these equality tests for the unitary matrix resulting from the circuit rather
        # than from the state vectors for a more full-proof test
        transpiler = CircuitTranspiler(settings=MagicMock())

        # Test with optimizer=False
        rng = np.random.default_rng(seed=42)  # init random number generator

        # circuits are the same
        for _ in range(500):
            nqubits = np.random.randint(4, 10)
            c1 = random_circuit(
                nqubits=nqubits,
                ngates=len(default_gates),
                rng=rng,
                circuit_gates=None,
                exhaustive=True,
            )

            c2_native_gates = transpiler.gates_to_native(c1.queue)

            # check that both c1, c2 are qibo.Circuit
            assert isinstance(c1, Circuit)
            assert isinstance(c2_native_gates, list)
            assert isinstance(c2_native_gates[0], gates.Gate)

            # Build circuit for comparison:
            c2 = Circuit(nqubits)
            [c2.add(gate) for gate in c2_native_gates]

            # check that states are equivalent up to a global phase
            assert np.allclose(1, compare_circuits(c1, c2, nqubits))

        # test with optimizer=True
        rng = np.random.default_rng(seed=42)  # init random number generator

        # circuits are the same
        for _ in range(500):
            nqubits = np.random.randint(4, 10)
            c1 = random_circuit(
                nqubits=nqubits,
                ngates=len(default_gates),
                rng=rng,
                circuit_gates=None,
                exhaustive=True,
            )
            c2_native_gates = transpiler.gates_to_native(c1.queue)
            # check that both c1, c2 are qibo.Circuit
            assert isinstance(c1, Circuit)
            assert isinstance(c2_native_gates, list)
            assert isinstance(c2_native_gates[0], gates.Gate)

            # Build circuit for comparison:
            c2 = Circuit(nqubits)
            [c2.add(gate) for gate in c2_native_gates]

            # check that states have the same absolute coefficients
            z1_exp, z2_exp = compare_exp_z(c1, c2, nqubits)
            assert np.allclose(z1_exp, z2_exp)

    def test_add_phases_from_RZs_and_CZs_to_drags(self, digital_settings):
        """Test that add_phases_from_RZs_and_CZs_to_drags behaves as expected"""
        transpiler = CircuitTranspiler(settings=digital_settings)

        # gate list to optimize
        test_gates = [
            Drag(0, 1, 1),
            gates.CZ(0, 1),
            gates.RZ(1, 1),
            gates.M(0),
            gates.RZ(0, 2),
            Drag(0, 3, 3),
            gates.CZ(0, 2),
            gates.CZ(1, 0),
            Drag(1, 2, 3),
            gates.RZ(1, 0),
        ]
        # resulting gate list from optimization
        result_gates = [
            Drag(0, 1, 1),
            gates.CZ(0, 1),
            gates.M(0),
            Drag(0, 3, 0),
            gates.CZ(0, 2),
            gates.CZ(1, 0),
            Drag(1, 2, -2),
        ]

        # create circuit to test function with
        circuit = Circuit(3)
        circuit.add(test_gates)

        # check that lists are the same
        optimized_gates = transpiler.add_phases_from_RZs_and_CZs_to_drags(circuit.queue, circuit.nqubits)
        for gate_r, gate_opt in zip(result_gates, optimized_gates):
            assert gate_r.name == gate_opt.name
            assert gate_r.parameters == gate_opt.parameters
            assert gate_r.qubits == gate_opt.qubits

    def test_circuit_to_pulses(self, digital_settings):
        """Test translate method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        # test circuit
        circuit = Circuit(5)
        circuit.add(X(0))
        circuit.add(Drag(0, 1, 0.5))
        circuit.add(CZ(3, 2))
        circuit.add(M(0))
        circuit.add(CZ(2, 3))
        circuit.add(CZ(4, 0))
        circuit.add(M(*range(4)))
        circuit.add(Wait(0, t=10))
        circuit.add(Drag(0, 2, 0.5))

        pulse_schedule = transpiler.gates_to_pulses(circuit.queue)

        # test general properties of the pulse schedule
        assert isinstance(pulse_schedule, PulseSchedule)

        # there are 6 different buses + 3 empty for unused flux lines
        assert len(pulse_schedule) == 12
        assert all(len(schedule_element.timeline) == 0 for schedule_element in pulse_schedule.elements[-3:])

        # we can ignore empty elements from here on
        pulse_schedule.elements = [element for element in pulse_schedule.elements if element.timeline]

        # extract pulse events per bus and separate measurement pulses
        pulse_bus_schedule = {
            pulse_bus_schedule.bus_alias: pulse_bus_schedule.timeline for pulse_bus_schedule in pulse_schedule
        }

        # TODO: I have tested it manually, should add assertions here.


    def test_normalize_angle(self, digital_settings):
        """Test that the angle is normalized properly for drag pulses"""
        c = Circuit(1)
        c.add(Drag(0, 2 * np.pi + 0.1, 0))
        transpiler = CircuitTranspiler(settings=digital_settings)
        pulse_schedule = transpiler.gates_to_pulses(c.queue)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.amplitude, 0.1 * 0.8 / np.pi)
        c = Circuit(1)
        c.add(Drag(0, np.pi + 0.1, 0))
        transpiler = CircuitTranspiler(settings=digital_settings)
        pulse_schedule = transpiler.gates_to_pulses(c.queue)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.amplitude, abs(-0.7745352091052967))

    def test_negative_amplitudes_add_extra_phase(self, digital_settings):
        """Test that transpiling negative amplitudes results in an added PI phase."""
        c = Circuit(1)
        c.add(Drag(0, -np.pi / 2, 0))
        transpiler = CircuitTranspiler(settings=digital_settings)
        pulse_schedule = transpiler.gates_to_pulses(c.queue)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.amplitude, (np.pi / 2) * 0.8 / np.pi)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.phase, 0 + np.pi)

    def test_drag_schedule_error(self, digital_settings):
        """Test error is raised if len(drag schedule) > 1"""
        # append schedule of M(0) to Drag(0) so that Drag(0)'s gate schedule has 2 elements
        digital_settings.gates["Drag(0)"].append(digital_settings.gates["M(0)"][0])
        gate_schedule = digital_settings.gates["Drag(0)"]
        error_string = re.escape(
            f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
        )
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 1))
        transpiler = CircuitTranspiler(settings=digital_settings)
        with pytest.raises(ValueError, match=error_string):
            transpiler.gates_to_pulses(circuit.queue)


    @pytest.mark.parametrize("optimize", [True, False])
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.add_phases_from_RZs_and_CZs_to_drags")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.optimize_gates")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.optimize_transpiled_gates")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.route_circuit")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.gates_to_native")
    @patch("qililab.digital.circuit_transpiler.CircuitTranspiler.gates_to_pulses")
    def test_transpile_circuit(self, mock_to_pulses, mock_to_native, mock_route, mock_opt_trans, mock_opt_circuit, mock_add_phases, optimize, digital_settings):
        """Test transpile_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing=True
        placer = MagicMock()
        router = MagicMock()
        routing_iterations = 7
        transpilation_config = DigitalTranspilationConfig(routing=routing, optimize=optimize, router=router, placer=placer, routing_iterations=routing_iterations)

        # Mock circuit for return values
        mock_circuit = Circuit(5)
        mock_circuit.add(Drag(0, 2*np.pi, np.pi))
        mock_circuit_gates = mock_circuit.queue

        # Mock layout for return values
        mock_layout = [0, 1, 2, 3, 4]

        # Mock schedule for return values
        mock_schedule = PulseSchedule()

        # Mock the return values
        mock_route.return_value = mock_circuit.queue, mock_circuit.nqubits, mock_layout
        mock_opt_circuit.return_value = mock_circuit_gates
        mock_to_native.return_value = mock_circuit_gates
        mock_add_phases.return_value = mock_circuit_gates
        mock_opt_trans.return_value = mock_circuit_gates
        mock_to_pulses.return_value = mock_schedule

        circuit = random_circuit(5, 10, np.random.default_rng())

        schedule, layout = transpiler.transpile_circuit(circuit, transpilation_config)

        # Mandatory asserts in order:
        mock_route.assert_called_once_with(circuit, placer, router, routing_iterations)
        mock_to_native.assert_called_once_with(mock_circuit.queue)
        mock_add_phases.assert_called_once_with(mock_circuit_gates, mock_circuit.nqubits)
        mock_to_pulses.assert_called_once_with(mock_circuit_gates)
        assert (schedule, layout) == (mock_schedule, mock_layout)

        # Asserts if optimize=True:
        if optimize:
            mock_opt_circuit.assert_called_once_with(mock_circuit_gates)
            mock_opt_trans.assert_called_once_with(mock_circuit_gates)
        else:
            mock_opt_circuit.assert_not_called()
            mock_opt_trans.assert_not_called()

            # Test if routing skipped:
            transpilation_config.routing = False
            mock_route.reset_mock()
            _, _ = transpiler.transpile_circuit(circuit, transpilation_config)
            mock_route.assert_not_called()

            # Test if no config is provided:
            mock_route.reset_mock()
            _, _ = transpiler.transpile_circuit(circuit)
            mock_route.assert_not_called()
            mock_opt_circuit.assert_not_called()
            mock_opt_trans.assert_not_called()


    @patch("qililab.digital.circuit_router.CircuitRouter.route")
    def test_route_trivial_circuit(self, mock_route, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 7

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(X(0))
        mock_layout = [0, 1, 2, 3, 4]
        mock_route.return_value = (mock_circuit, mock_layout)

        # Execute the function
        circuit_gates, nqubits, layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)

        # Asserts:
        mock_route.assert_called_once_with(mock_circuit, routing_iterations)
        assert (circuit_gates, nqubits, layout) == (mock_circuit.queue, mock_circuit.nqubits, mock_layout)

    def test_route_circuit_only_needs_remapping_integration(self, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 10

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(gates.CNOT(1, 0))
        mock_circuit.add(gates.CNOT(0, 1))
        mock_circuit.add(gates.CNOT(3, 0))


        # Execute the function
        circuit_gates, nqubits, final_layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)
        output_gates = [(gate.name, gate.qubits) for gate in circuit_gates]

        # Asserts:
        expected_layout = [2, 1, 0, 3, 4]
        expected_gates = [('cx', (1, 2)), ('cx', (2, 1)), ('cx', (3, 2))]

        assert (output_gates, nqubits, final_layout) == (expected_gates, mock_circuit.nqubits, expected_layout)

    def test_route_circuit_swap_needed_integration(self, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 10

        # Mock the return values
        mock_circuit = Circuit(4)
        mock_circuit.add(gates.CNOT(1, 0))
        mock_circuit.add(gates.CNOT(3, 2))


        # Execute the function
        circuit_gates, nqubits, final_layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)
        output_gates = [(gate.name, gate.qubits) for gate in circuit_gates]

        # Asserts:
        expected_gates_and_layout = [
            ([('cx', (2, 0)), ('swap', (2, 3)), ('cx', (2, 1))], [0, 3, 1, 2, 4]),
            ([('cx', (2, 0)), ('swap', (3, 2)), ('cx', (2, 1))], [0, 3, 1, 2, 4]),
            ([('cx', (2, 0)), ('swap', (2, 1)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (2, 0)), ('swap', (1, 2)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (1, 2)), ('swap', (2, 0)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (1, 2)), ('swap', (0, 2)), ('cx', (3, 2))], [0, 1, 2, 3, 4]),
            ([('cx', (1, 2)), ('swap', (2, 3)), ('cx', (2, 0))], [2, 1, 3, 0, 4]),
            ([('cx', (1, 2)), ('swap', (3, 2)), ('cx', (2, 0))], [2, 1, 3, 0, 4]),
            ([('cx', (3, 2)), ('swap', (2, 0)), ('cx', (1, 2))], [2, 1, 0, 3, 4]),
            ([('cx', (3, 2)), ('swap', (0, 2)), ('cx', (1, 2))], [2, 1, 0, 3, 4]),
            ([('cx', (3, 2)), ('swap', (2, 1)), ('cx', (2, 0))], [0, 2, 1, 3, 4]),
            ([('cx', (3, 2)), ('swap', (1, 2)), ('cx', (2, 0))], [0, 2, 1, 3, 4]),

        ]

        assert nqubits == 5 # The routing changes the size to fit that of the topology
        # Test one of the possible routing has been achieved:
        assert (output_gates, final_layout) in expected_gates_and_layout

    def test_route_circuit_complex_integration(self, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 10

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(gates.CNOT(0, 1))
        mock_circuit.add(gates.CNOT(1, 2))
        mock_circuit.add(gates.CNOT(3, 0))
        mock_circuit.add(gates.CNOT(1, 4))
        mock_circuit.add(gates.CNOT(3, 4))
        mock_circuit.add(gates.CNOT(1, 0))


        # Execute the function
        circuit_gates, _, final_layout = transpiler.route_circuit(mock_circuit, iterations=routing_iterations)
        output_gates = [[gate.name, gate.qubits] for gate in circuit_gates]

        # Undo routing with SWAPS
        for idx, gate in enumerate(output_gates):
            if gate[0] == 'swap':
                output_gates[idx] = None
                mapping_to_do = {gate[1][0]: gate[1][1], gate[1][1]:gate[1][0]}
                for idx_2, gate_2 in enumerate(output_gates[idx+1:]):
                    qubit_1, qubit_2 = gate_2[1]
                    output_gates[idx_2+idx+1][1] = (mapping_to_do.get(qubit_1, qubit_1), mapping_to_do.get(qubit_2, qubit_2))
                # Change layout:
                final_layout[gate[1][0]], final_layout[gate[1][1]] = final_layout[gate[1][1]], final_layout[gate[1][0]]

        # Undo initial mapping
        for idx, gate in enumerate(output_gates):
            if gate is not None:
                output_gates[idx] = gate[0], tuple(final_layout[q] for q in gate[1])

        output_gates = [gate for gate in output_gates if gate is not None]

        # Test you retrieve original circuit:
        assert sorted(output_gates) == sorted([(gate.name, gate.qubits) for gate in mock_circuit.queue])

    @patch("qililab.digital.circuit_transpiler.nx.Graph")
    @patch("qililab.digital.circuit_transpiler.CircuitRouter")
    def test_that_route_circuit_instantiates_Router(self, mock_router, mock_graph, digital_settings):
        """Test route_circuit method"""
        transpiler = CircuitTranspiler(settings=digital_settings)
        routing_iterations = 7

        # Mock the return values
        mock_circuit = Circuit(5)
        mock_circuit.add(X(0))

        graph_mocking = nx.Graph(transpiler.settings.topology)
        mock_graph.return_value = graph_mocking

        # Execute the function
        with pytest.raises(ValueError, match=re.escape("not enough values to unpack (expected 2, got 0)")):
            transpiler.route_circuit(mock_circuit, iterations=routing_iterations)

        # Asserts:
        mock_router.assert_called_once_with(graph_mocking, None, None)

    def test_DigitalTranspilerConfig(self):
        """Test that the dataclass default values are correct, and that properies give the correct order
        """
        tc = DigitalTranspilationConfig()
        assert tc._attributes_ordered == (False, None, None, 10, False)

    def test__check_that_no_SWAP_gate_is_after_measurement_no_violation(self):
        """Test _check_that_no_SWAP_gate_is_after_measurement passes when no gate is after measurement."""
        transpiler = CircuitTranspiler(settings=MagicMock())
        circuit = Circuit(2)
        circuit.add(gates.SWAP(0, 1))
        circuit.add(gates.M(0))
        circuit.add(gates.M(1))
        # No gate after measurement for either qubit
        transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before")  # Should not raise

        circuit = Circuit(2)
        circuit.add(gates.SWAP(0, 1))
        circuit.add(gates.M(0,1)) # Same for both measures defined together
        # No gate after measurement for either qubit
        transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before")  # Should not raise

        circuit = Circuit(2)
        circuit.add(gates.CNOT(0,1))
        circuit.add(gates.M(0))
        circuit.add(gates.CNOT(0,1))  # Gate after measurement on qubit 0
        circuit.add(gates.M(1))
        transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before") # Should not raise


    def test__check_that_no_SWAP_gate_is_after_measurement_violation_single_qubit(self):
        """Test _check_that_no_SWAP_gate_is_after_measurement raises when a gate is after measurement on one qubit."""
        transpiler = CircuitTranspiler(settings=MagicMock())
        circuit = Circuit(2)
        circuit.add(gates.X(0))
        circuit.add(gates.M(0))
        circuit.add(gates.SWAP(0, 1))  # Gate after measurement on qubit 0
        with pytest.raises(ValueError, match="For automatic routing to work, no SWAP gate can be after a Measurement gate on each qubit. This validation is performed during the transpilation of an `execute`. Check the gates at qubit: 0."):
            transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before")

        circuit = Circuit(2)
        circuit.add(gates.CNOT(0,1))
        circuit.add(gates.M(0))
        circuit.add(gates.SWAP(0,1))  # Gate after measurement on qubit 0
        circuit.add(gates.M(1))
        with pytest.raises(ValueError, match="For automatic routing to work, no SWAP gate can be after a Measurement gate on each qubit. This validation is performed during the transpilation of an `execute`. Check the gates at qubit: 0."):
            transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before")

    def test__check_that_no_SWAP_gate_is_after_measurement_violation_multiple_qubits(self):
        """Test _check_that_no_SWAP_gate_is_after_measurement raises when a gate is after measurement on multiple qubits."""
        transpiler = CircuitTranspiler(settings=MagicMock())
        circuit = Circuit(3)
        circuit.add(gates.X(0))
        circuit.add(gates.M(0))
        circuit.add(gates.SWAP(0, 1))  # Violation on qubit 0
        circuit.add(gates.M(1))
        circuit.add(gates.X(1))
        with pytest.raises(ValueError) as excinfo:
            transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before")
        assert "no gate can be after a Measurement gate on each qubit" in str(excinfo.value)

    def test__check_that_no_SWAP_gate_is_after_measurement_measurement_last(self):
        """Test _check_that_no_SWAP_gate_is_after_measurement passes when measurement is last gate for all qubits."""
        transpiler = CircuitTranspiler(settings=MagicMock())
        circuit = Circuit(2)
        circuit.add(gates.SWAP(0, 1))
        circuit.add(gates.M(0))
        circuit.add(gates.X(1))
        circuit.add(gates.M(1))
        transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before")  # Should not raise

    def test__check_that_no_SWAP_gate_is_after_measurement_no_measurement(self):
        """Test _check_that_no_SWAP_gate_is_after_measurement passes when there are no measurement gates."""
        transpiler = CircuitTranspiler(settings=MagicMock())
        circuit = Circuit(2)
        circuit.add(gates.SWAP(0, 1))
        circuit.add(gates.X(1))
        transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "before")  # Should not raise

    def test_check_error_raise_if_SWAP_added_during_routing(self, digital_settings):
        """Test that an error is raised if a SWAP gate is added during routing."""
        transpiler = CircuitTranspiler(settings=digital_settings)
        circuit = Circuit(5)
        circuit.add(gates.SWAP(0, 1))
        circuit.add(gates.CNOT(1, 2))
        circuit.add(gates.CNOT(3, 0))
        circuit.add(gates.CNOT(1, 4))
        circuit.add(gates.CNOT(3, 4))
        circuit.add(gates.CNOT(1, 0))
        circuit.add(M(0,1,2,3,4))
        circuit.add(gates.SWAP(0, 1))

        with pytest.raises(ValueError, match="The routing algorithm has added a SWAP gate after a Measurement on qubit: 0, which isn't allowed in the automatic routing. Change routing algorithm, or route it manually with `CircuitRouter` before executing the circuit."):
            transpiler._check_that_no_SWAP_gate_is_after_measurement(circuit, "after")
