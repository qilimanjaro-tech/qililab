from itertools import product

import numpy as np
from qibo import gates
from qibo.models import Circuit

import qililab as ql

basic_rotations = [
    gates.I(0),
    gates.RX(0, np.pi),
    gates.RX(0, np.pi / 2),
    gates.RX(0, -np.pi / 2),
    gates.RY(0, np.pi / 2),
    gates.RY(0, np.pi / 2),
]

# import itertools


combs = list(product(basic_rotations, basic_rotations, basic_rotations, basic_rotations))

for comb in combs:
    c = Circuit(2)
    # assign gates
    c.add(comb[0].on_qubits({comb[0].target_qubits[0]: 0}))
    c.add(comb[1].on_qubits({comb[1].target_qubits[0]: 1}))
    c.add(gates.CZ(0, 1))  # WARNING this 2q gate should be valid in the qpu
    c.add(comb[0].on_qubits({comb[0].target_qubits[0]: 0}))
    c.add(comb[1].on_qubits({comb[1].target_qubits[0]: 1}))

    # execute circuit
    ql.execute_qibo_circuit(c, "galadriel", get_experiment_only=False)
