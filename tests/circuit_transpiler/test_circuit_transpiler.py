import re
from dataclasses import asdict
from unittest.mock import MagicMock

import numpy as np
import pytest
import qibo
from qibo import gates
from qibo.backends import NumpyBackend
from qibo.gates import CZ, M, X
from qibo.models import Circuit

from qililab.chip import Chip
from qililab.circuit_transpiler import CircuitTranspiler
from qililab.circuit_transpiler.native_gates import Drag, Wait
from qililab.platform import Bus, Buses, Platform
from qililab.pulse import Pulse, PulseEvent, PulseSchedule
from qililab.pulse.pulse_shape import SNZ, Gaussian, Rectangular
from qililab.pulse.pulse_shape import Drag as Drag_pulse
from qililab.settings import Runcard
from qililab.settings.gate_event_settings import GateEventSettings
from tests.data import Galadriel
from tests.test_utils import build_platform

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
    gates_list: list[qibo.gates.Gate] | None = None,
    exhaustive=False,
) -> Circuit:
    """Generates random qibo circuit with ngates

    Args:
        nqubits (int): number of qubits in the circuit
        ngates (int): number of gates in the circuit
        gates_list (dict[gates:int]): dictionary with gates and amount of qubits where those should be applied
        exhaustive (bool) : use all gates at least once (requires ngates>=len(gates))

    Returns:
        c (qibo.Circuit) : resulting circuit
    """

    # get list available gates
    if gates_list is None:
        gates_list = default_gates

    # init circuit
    c = Circuit(nqubits)

    # get list of gates to use
    if not exhaustive:
        list_gates = rng.choice(gates_list, ngates)
    # if exhaustive = True then add all the gates available
    else:
        if ngates < len(gates_list):
            raise ValueError("If exhaustive is set to True then ngates must be bigger than len(gates_list)!")
        list_gates = []
        for _ in range(ngates // len(gates_list)):
            list_gates.extend(gates_list)
        list_gates.extend(rng.choice(gates_list, ngates % len(gates_list), replace=False))
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


platform_gates = {
    "M(0)": [
        {
            "bus": "feedline_bus",
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
            "bus": "drive_q0_bus",
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
            "bus": "drive_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 200,
                "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
            },
        },
        {
            "bus": "flux_q0_bus",
            "wait_time": 30,
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 200,
                "shape": {"name": "drag", "drag_coefficient": 0.8, "num_sigmas": 2},
            },
        },
        {
            "bus": "drive_q0_bus",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 100,
                "shape": {"name": "rectangular"},
            },
        },
        {
            "bus": "drive_q4_bus",
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
            "bus": "feedline_bus",
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
            "bus": "feedline_bus",
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
            "bus": "feedline_bus",
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
            "bus": "feedline_bus",
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
            "bus": "flux_q2_bus",
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
            "bus": "flux_q0_bus",
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
            "bus": "flux_c2_bus",
            "wait_time": 10,
            "pulse": {
                "amplitude": 0.7,
                "phase": 0,
                "duration": 90,
                "shape": {"name": "snz", "b": 0.5, "t_phi": 1},
            },
        },
        {
            "bus": "flux_q0_bus",
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
            "bus": "flux_line_q1",
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
            "bus": "flux_line_q2",
            "pulse": {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 200,
                "shape": {"name": "rectangular"},
                "options": {"q1_phase_correction": 2, "q2_phase_correction": 0},
            },
        }
    ],
}


@pytest.fixture(name="chip")
def fixture_chip():
    r"""Fixture that returns an instance of a ``Chip`` class.


    Chip schema (qubit_id, GHz, id)

   3,4,5  4,4,7
     \   /
     2,5,4
     /   \
   0,6,3 1,3,6
    """
    settings = {
        "nodes": [
            {
                "name": "port",
                "alias": "feedline_input",
                "line": "feedline_input",
                "nodes": ["resonator_q0", "resonator_q1", "resonator_q2", "resonator_q3", "resonator_q4"],
            },
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 6e9,
                "nodes": ["q2", "drive_q0", "flux_q0", "resonator_q0"],
            },
            {
                "name": "qubit",
                "alias": "q2",
                "qubit_index": 2,
                "frequency": 5e9,
                "nodes": ["q0", "q1", "q3", "q4", "drive_q2", "flux_q2", "resonator_q2"],
            },
            {
                "name": "qubit",
                "alias": "q1",
                "qubit_index": 1,
                "frequency": 4e9,
                "nodes": ["q2", "drive_q1", "flux_q1", "resonator_q1"],
            },
            {
                "name": "qubit",
                "alias": "q3",
                "qubit_index": 3,
                "frequency": 3e9,
                "nodes": ["q2", "drive_q3", "flux_q3", "resonator_q3"],
            },
            {
                "name": "qubit",
                "alias": "q4",
                "qubit_index": 4,
                "frequency": 4e9,
                "nodes": ["q2", "drive_q4", "flux_q4", "resonator_q4"],
            },
            {"name": "port", "line": "drive", "alias": "drive_q0", "nodes": ["q0"]},
            {"name": "port", "line": "drive", "alias": "drive_q1", "nodes": ["q1"]},
            {"name": "port", "line": "drive", "alias": "drive_q2", "nodes": ["q2"]},
            {"name": "port", "line": "drive", "alias": "drive_q3", "nodes": ["q3"]},
            {"name": "port", "line": "drive", "alias": "drive_q4", "nodes": ["q4"]},
            {"name": "port", "line": "flux", "alias": "flux_q0", "nodes": ["q0"]},
            {"name": "port", "line": "flux", "alias": "flux_q1", "nodes": ["q1"]},
            {"name": "port", "line": "flux", "alias": "flux_q2", "nodes": ["q2"]},
            {"name": "port", "line": "flux", "alias": "flux_q3", "nodes": ["q3"]},
            {"name": "port", "line": "flux", "alias": "flux_q4", "nodes": ["q4"]},
            {"name": "resonator", "alias": "resonator_q0", "frequency": 8072600000, "nodes": ["feedline_input", "q0"]},
            {"name": "resonator", "alias": "resonator_q1", "frequency": 8072600000, "nodes": ["feedline_input", "q1"]},
            {"name": "resonator", "alias": "resonator_q2", "frequency": 8072600000, "nodes": ["feedline_input", "q2"]},
            {"name": "resonator", "alias": "resonator_q3", "frequency": 8072600000, "nodes": ["feedline_input", "q3"]},
            {"name": "resonator", "alias": "resonator_q4", "frequency": 8072600000, "nodes": ["feedline_input", "q4"]},
            {"name": "port", "alias": "flux_c2", "line": "flux", "nodes": ["coupler"]},
            {"name": "coupler", "alias": "coupler", "frequency": 6e9, "nodes": ["flux_c2"]},
        ],
    }
    return Chip(**settings)


@pytest.fixture(name="platform")
def fixture_platform(chip: Chip) -> Platform:
    """Fixture that returns an instance of a ``Runcard.GatesSettings`` class."""
    gates_settings = {
        "minimum_clock_time": 5,
        "delay_between_pulses": 0,
        "delay_before_readout": 0,
        "reset_method": "passive",
        "passive_reset_duration": 100,
        "timings_calculation_method": "as_soon_as_possible",
        "operations": [],
        "gates": {},
    }
    bus_settings = [
        {
            "alias": "feedline_bus",
            "system_control": {
                "name": "readout_system_control",
                "instruments": ["QRM_0", "rs_1"],
            },
            "port": "feedline_input",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q0_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "drive_q0",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q0_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "flux_q0",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q1_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "drive_q1",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q1_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "flux_q1",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q2_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "drive_q2",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q2_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "flux_q2",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_c2_bus",  # c2 coupler
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "flux_c2",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q3_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "drive_q3",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q3_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "flux_q3",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "drive_q4_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "drive_q4",
            "distortions": [],
            "delay": 0,
        },
        {
            "alias": "flux_q4_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["QCM"],
            },
            "port": "flux_q4",
            "distortions": [],
            "delay": 0,
        },
    ]

    gates_settings = Runcard.GatesSettings(**gates_settings)  # type: ignore
    platform = build_platform(runcard=Galadriel.runcard)
    platform.gates_settings = gates_settings  # type: ignore
    platform.chip = chip
    buses = Buses(
        elements=[Bus(settings=bus, platform_instruments=platform.instruments, chip=chip) for bus in bus_settings]
    )
    platform.buses = buses
    platform.gates_settings.gates = {  # type: ignore
        gate: [GateEventSettings(**event) for event in schedule]  # type: ignore
        for gate, schedule in platform_gates.items()  # type: ignore
    }
    return platform


def get_pulse0(time: int, qubit: int) -> PulseEvent:
    """Helper function for pulse test data"""
    return PulseEvent(
        pulse=Pulse(
            amplitude=0.8,
            phase=0,
            duration=200,
            frequency=0,
            pulse_shape=Rectangular(),
        ),
        start_time=time,
        pulse_distortions=[],
        qubit=qubit,
    )


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
        transpiler = CircuitTranspiler(platform=MagicMock())

        # Test with optimizer=False
        rng = np.random.default_rng(seed=42)  # init random number generator

        # circuits are the same
        for _ in range(500):
            nqubits = np.random.randint(4, 10)
            c1 = random_circuit(
                nqubits=nqubits,
                ngates=len(default_gates),
                rng=rng,
                gates_list=None,
                exhaustive=True,
            )

            c2 = transpiler.circuit_to_native(c1, optimize=False)

            # check that both c1, c2 are qibo.Circuit
            assert isinstance(c1, Circuit)
            assert isinstance(c2, Circuit)

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
                gates_list=None,
                exhaustive=True,
            )
            c2 = transpiler.circuit_to_native(c1)
            # check that both c1, c2 are qibo.Circuit
            assert isinstance(c1, Circuit)
            assert isinstance(c2, Circuit)
            # check that states have the same absolute coefficients
            z1_exp, z2_exp = compare_exp_z(c1, c2, nqubits)
            assert np.allclose(z1_exp, z2_exp)

    def test_optimize_transpilation(self, platform):
        """Test that optimize_transpilation behaves as expected"""
        transpiler = CircuitTranspiler(platform=platform)

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

        # check that lists are the same
        optimized_gates = transpiler.optimize_transpilation(3, test_gates)
        for gate_r, gate_opt in zip(result_gates, optimized_gates):
            assert gate_r.name == gate_opt.name
            assert gate_r.parameters == gate_opt.parameters
            assert gate_r.qubits == gate_opt.qubits

    def test_translate_for_no_awg(self, platform):
        """Test translate method adding/removing AWG instruments to test empty schedules.

        This test ensures that the correct number of pulse schedules are added when we have a flux bus
        which contains and AWG instrument, as opposed to no empty schedules for flux buses that don't contain
        AWG instruments. This test is designed to test this bug is not reintroduced as a regression:
        https://github.com/qilimanjaro-tech/qililab/issues/626
        """
        transpiler = CircuitTranspiler(platform=platform)
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

        pulse_schedules = transpiler.circuit_to_pulses(circuits=[circuit])
        pulse_schedule = pulse_schedules[0]
        # there should be 9 pulse_schedules in this configuration
        assert len(pulse_schedule) == 9

        buses_elements = [bus for bus in platform.buses.elements if bus.settings.alias != "flux_q4_bus"]
        buses = Buses(elements=buses_elements)
        platform.buses = buses
        pulse_schedules = transpiler.circuit_to_pulses(circuits=[circuit])

        pulse_schedule = pulse_schedules[0]
        # there should be a pulse_schedule removed
        assert len(pulse_schedule) == 8

        flux_bus_no_awg_settings = {
            "alias": "flux_q4_bus",
            "system_control": {
                "name": "system_control",
                "instruments": ["rs_1"],
            },
            "port": "flux_q4",
            "distortions": [],
            "delay": 0,
        }

        platform.buses.add(
            Bus(settings=flux_bus_no_awg_settings, platform_instruments=platform.instruments, chip=platform.chip)
        )
        pulse_schedules = transpiler.circuit_to_pulses(circuits=[circuit])
        pulse_schedule = pulse_schedules[0]
        # there should not be any extra pulse schedule added
        assert len(pulse_schedule) == 8

    def test_circuit_to_pulses(self, platform):
        """Test translate method"""
        transpiler = CircuitTranspiler(platform=platform)
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

        pulse_schedules = transpiler.circuit_to_pulses(circuits=[circuit])

        # test general properties of the pulse schedule
        assert isinstance(pulse_schedules, list)
        assert len(pulse_schedules) == 1
        assert isinstance(pulse_schedules[0], PulseSchedule)

        pulse_schedule = pulse_schedules[0]
        # there are 6 different buses + 3 empty for unused flux lines
        assert len(pulse_schedule) == 9
        assert all(len(schedule_element.timeline) == 0 for schedule_element in pulse_schedule.elements[-3:])

        # we can ignore empty elements from here on
        pulse_schedule.elements = pulse_schedule.elements[:-3]

        # extract pulse events per bus and separate measurement pulses
        pulse_bus_schedule = {
            pulse_bus_schedule.port: pulse_bus_schedule.timeline for pulse_bus_schedule in pulse_schedule
        }
        m_schedule = pulse_bus_schedule["feedline_input"]

        # check measurement gates
        assert len(m_schedule) == 5

        m_pulse1 = PulseEvent(
            pulse=Pulse(
                amplitude=0.7,
                phase=0.5,
                duration=100,
                frequency=0,
                pulse_shape=Gaussian(num_sigmas=2),
            ),
            start_time=930,
            pulse_distortions=[],
            qubit=3,
        )

        assert all(
            pulse == get_pulse0(time, qubit)
            for pulse, time, qubit in zip(m_schedule[:-1], [530, 930, 930, 930], [0, 0, 1, 2])
        )
        assert m_schedule[-1] == m_pulse1

        # assert wait gate delayed drive pulse at port 8 for 10ns (time should be 930+200+10=1140)
        assert pulse_bus_schedule["drive_q0"][-1].start_time == 1140

        # test actions for control gates

        # data
        drive_q0 = [
            {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 200,
                "frequency": 0,
                "start_time": 0,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
            {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 100,
                "frequency": 0,
                "start_time": 0,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
            {
                "amplitude": 0.8 / np.pi,
                "phase": 0.5,
                "duration": 198,
                "frequency": 0,
                "start_time": 230,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
            {
                "amplitude": 2 * 0.8 / np.pi,
                "phase": 0.5,
                "duration": 198,
                "frequency": 0,
                "start_time": 1140,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
        ]

        drive_q4 = [
            {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 100,
                "frequency": 0,
                "start_time": 0,
                "qubit": 4,
                "pulse_shape": asdict(Gaussian(num_sigmas=4)),
            }
        ]

        flux_q0 = [
            {
                "amplitude": 0.8,
                "phase": 0,
                "duration": 200,
                "frequency": 0,
                "start_time": 30,
                "qubit": 0,
                "pulse_shape": asdict(Drag_pulse(drag_coefficient=0.8, num_sigmas=2)),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "duration": 100,
                "frequency": 0,
                "start_time": 430,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "duration": 100,
                "frequency": 0,
                "start_time": 730,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "duration": 100,
                "frequency": 0,
                "start_time": 830,
                "qubit": 0,
                "pulse_shape": asdict(Rectangular()),
            },
        ]

        flux_q2 = [
            {
                "amplitude": 0.7,
                "phase": 0,
                "duration": 90,
                "frequency": 0,
                "start_time": 440,
                "qubit": 2,
                "pulse_shape": asdict(SNZ(b=0.5, t_phi=1)),
            },
            {
                "amplitude": 0.7,
                "phase": 0,
                "duration": 90,
                "frequency": 0,
                "start_time": 740,
                "qubit": 2,
                "pulse_shape": asdict(SNZ(b=0.5, t_phi=1)),
            },
        ]

        flux_c2 = [
            {
                "amplitude": 0.7,
                "phase": 0,
                "duration": 90,
                "frequency": 0,
                "start_time": 840,
                "qubit": None,
                "pulse_shape": asdict(SNZ(b=0.5, t_phi=1)),
            }
        ]

        # drive q0
        transpiled_drive_q0 = get_bus_schedule(pulse_bus_schedule, "drive_q0")
        assert len(transpiled_drive_q0) == len(drive_q0)
        assert all(i == k for i, k in zip(transpiled_drive_q0, drive_q0))

        # flux q0
        transpiled_flux_q0 = get_bus_schedule(pulse_bus_schedule, "flux_q0")
        assert len(transpiled_flux_q0) == len(flux_q0)
        assert all(i == k for i, k in zip(transpiled_flux_q0, flux_q0))

        # drive q4
        transpiled_drive_q4 = get_bus_schedule(pulse_bus_schedule, "drive_q4")
        assert len(transpiled_drive_q4) == len(drive_q4)
        assert all(i == k for i, k in zip(transpiled_drive_q4, drive_q4))

        # flux q2
        transpiled_flux_q2 = get_bus_schedule(pulse_bus_schedule, "flux_q2")
        assert len(transpiled_flux_q2) == len(flux_q2)
        assert all(i == k for i, k in zip(transpiled_flux_q2, flux_q2))

        # flux c2
        transpiled_flux_c2 = get_bus_schedule(pulse_bus_schedule, "flux_c2")
        assert len(transpiled_flux_c2) == len(flux_c2)
        assert all(i == k for i, k in zip(transpiled_flux_c2, flux_c2))

    def test_normalize_angle(self, platform):
        """Test that the angle is normalized properly for drag pulses"""
        c = Circuit(1)
        c.add(Drag(0, 2 * np.pi + 0.1, 0))
        transpiler = CircuitTranspiler(platform=platform)
        pulse_schedules = transpiler.circuit_to_pulses(circuits=[c])
        assert np.allclose(pulse_schedules[0].elements[0].timeline[0].pulse.amplitude, 0.1 * 0.8 / np.pi)
        c = Circuit(1)
        c.add(Drag(0, np.pi + 0.1, 0))
        transpiler = CircuitTranspiler(platform=platform)
        pulse_schedules = transpiler.circuit_to_pulses(circuits=[c])
        assert np.allclose(pulse_schedules[0].elements[0].timeline[0].pulse.amplitude, abs(-0.7745352091052967))

    def test_negative_amplitudes_add_extra_phase(self, platform):
        """Test that transpiling negative amplitudes results in an added PI phase."""
        c = Circuit(1)
        c.add(Drag(0, -np.pi / 2, 0))
        transpiler = CircuitTranspiler(platform=platform)
        pulse_schedule = transpiler.circuit_to_pulses(circuits=[c])[0]
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.amplitude, (np.pi / 2) * 0.8 / np.pi)
        assert np.allclose(pulse_schedule.elements[0].timeline[0].pulse.phase, 0 + np.pi)

    def test_drag_schedule_error(self, platform: Platform):
        """Test error is raised if len(drag schedule) > 1"""
        # append schedule of M(0) to Drag(0) so that Drag(0)'s gate schedule has 2 elements
        platform.gates_settings.gates["Drag(0)"].append(platform.gates_settings.gates["M(0)"][0])
        gate_schedule = platform.gates_settings.gates["Drag(0)"]
        error_string = re.escape(
            f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
        )
        circuit = Circuit(1)
        circuit.add(Drag(0, 1, 1))
        transpiler = CircuitTranspiler(platform=platform)
        with pytest.raises(ValueError, match=error_string):
            transpiler.circuit_to_pulses(circuits=[circuit])
