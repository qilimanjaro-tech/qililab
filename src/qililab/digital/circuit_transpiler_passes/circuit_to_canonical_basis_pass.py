# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import math
from typing import List

from qilisdk.digital import Circuit
from qilisdk.digital.exceptions import GateHasNoMatrixError
from qilisdk.digital.gates import (
    CNOT,
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    Adjoint,
    BasicGate,
    Controlled,
    Exponential,
    Gate,
    H,
    I,
    M,
    S,
    T,
    X,
    Y,
    Z,
)

from .circuit_transpiler_pass import CircuitTranspilerPass
from .numeric_helpers import (
    _mat_U3,
    _unitary_sqrt_2x2,
    _zyz_from_unitary,
)

# ======================= Class =======================


class CircuitToCanonicalBasisPass(CircuitTranspilerPass):
    """
    Map an arbitrary circuit to the circuit basis {U3, RX, RY, RZ, CZ} (+ M).

    - Eliminates CNOT / SWAP to CZ + 1Q.
    - Controlled with any #controls (target 1-qubit) → ancilla-free recursive synthesis.
    - Adjoint(g) → canonicalize(g) then reverse+invert.
    - Exponential(1q) → ZYZ → U3.

    NOTE: This pass does *not* perform any 1-qubit fusion/merging.
    """
# All directly supported gates

    def __init__(self):
        self.canonical = {
            M: self._M_canonical,
            I: self._I_canonical,
            X: self._X_canonical,
            Y: self._Y_canonical,
            Z: self._Z_canonical,
            H: self._H_canonical,
            S: self._S_canonical,
            T: self._T_canonical,
            RX: self._RX_canonical,
            RY: self._RY_canonical,
            RZ: self._RZ_canonical,
            U1: self._U1_canonical,
            U2: self._U2_canonical,
            U3: self._U3_canonical,
            CZ: self._CZ_canonical,
            CNOT: self._CNOT_canonical,
            SWAP: self._SWAP_canonical,
            Exponential: self._Exponential_canonical,
            Adjoint: self._Adjoint_handeling,
            Controlled: self._Controled_handeling,
            }
        self.controlled_canonical = {
            RX: self._CRX_canonical,
            RY: self._CRY_canonical,
            RZ: self._CRZ_canonical,
            U3: self._CU3_canonical,
        }

    def run(self, circuit: Circuit) -> Circuit:
        seq = self._rewrite_list(circuit.gates)

        out = Circuit(circuit.nqubits)
        for g in seq:
            out.add(g)

        self.append_circuit_to_context(out)
        return out

    def _rewrite_list(self, gates: List[Gate], adjointed: bool = False):
        out: List[Gate] = []
        for g in gates:
            out += self._rewrite_gate(g, adjointed=adjointed)
        return out

    def _rewrite_gate(self, gate: Gate, adjointed: bool = False) -> List[Gate]:
        # this lists would very much be a class variable or something like that, not somethinf in this function
        g_class = gate.__class__
        if g_class in self.canonical:
            return self.canonical[g_class](gate, adjointed)
        if isinstance(gate, BasicGate):
            try:
                return self._BasicGate_canonical(gate, adjointed)
            except GateHasNoMatrixError:
                raise NotImplementedError(f"{g_class}, isn't supported in the current build")
        raise NotImplementedError(f"{g_class}, isn't supported in the current build")

    def _Controled_handeling(self, g: Controlled | Gate, adjointed: bool = False, controls: List[int] = []):
        if isinstance(g, Controlled):
            controls = g.control_qubits
            basic_gate = g.basic_gate

        elif isinstance(g, Gate):
            basic_gate = g

        if isinstance(basic_gate, SWAP):
            raise NotImplementedError("Controled SWAP isn't implemented in the current build")
        if len(controls) == 1:
                return self._single_controlled(basic_gate, controls[0], adjointed)
        if len(controls) == 0:
            return [basic_gate]

        c_last = controls[-1]
        rest = controls[:-1]

        V = self._sqrt_1q_gate_as_basis(basic_gate)
        Vd = self._rewrite_gate(V, adjointed=True)[0]

        t = g.target_qubits[0]
        seq: List[Gate] = []
        seq += self._Controled_handeling(V, controls=rest, adjointed=adjointed)
        seq += self._CNOT_canonical(CNOT(c_last, t), adjointed=adjointed)
        seq += self._Controled_handeling(Vd, controls=rest, adjointed=adjointed)
        seq += self._CNOT_canonical(CNOT(c_last, t), adjointed=adjointed)
        seq += self._Controled_handeling(V, controls=rest, adjointed=adjointed)
        return seq

    def _single_controlled(self, target_gate: Gate, control_qubit: int, adjointed: bool = False) -> List[Gate]:
        g_class = target_gate.__class__
        if g_class in self.controlled_canonical:
            return self.controlled_canonical[g_class](target_gate, control_qubit, adjointed)
        return self._single_controlled(self._rewrite_gate(target_gate)[0], control_qubit)

    def _sqrt_1q_gate_as_basis(self, g: Gate) -> Gate:
        """Return V such that V^2 = g, as a basis gate (U3/RX/RY/RZ)."""
        q = g.qubits[0]
        # Fast paths
        if isinstance(g, RZ):
            return RZ(q, phi=g.phi / 2.0)
        if isinstance(g, RX):
            return RX(q, theta=g.theta / 2.0)
        if isinstance(g, RY):
            return RY(q, theta=g.theta / 2.0)
        if isinstance(g, Z):
            return RZ(q, phi=math.pi / 2.0)
        if isinstance(g, X):
            return RX(q, theta=math.pi / 2.0)
        if isinstance(g, Y):
            return RY(q, theta=math.pi / 2.0)
        if isinstance(g, U1):
            return RZ(q, phi=g.phi / 2.0)

        # General 1q unitary
        if isinstance(g, U2):
            U = _mat_U3(math.pi / 2.0, g.phi, g.gamma)
        elif isinstance(g, U3):
            U = _mat_U3(g.theta, g.phi, g.gamma)
        else:
            return self._sqrt_1q_gate_as_basis(self._rewrite_gate(g)[0])

        Vs = _unitary_sqrt_2x2(U)
        th, ph, lam = _zyz_from_unitary(Vs)
        return U3(q, theta=th, phi=ph, gamma=lam)

    def _Adjoint_handeling(self, g: Adjoint, adjointed: bool = False):
        ad_gates = self._rewrite_gate(g.basic_gate, adjointed=not adjointed)
        return ad_gates if adjointed else ad_gates[::-1]

    def _BasicGate_canonical(self, g: BasicGate, adjointed: bool = False):
        th, phi, gm = _zyz_from_unitary(g.matrix)
        return [U3(g.qubits[0], theta=-th, phi=-gm, gamma=-phi)]if adjointed\
            else [U3(g.qubits[0], theta=th, phi=phi, gamma=gm)]

    def _I_canonical(self, g: I, adjointed: bool = False):
        return []

    def _M_canonical(self, g: M, adjointed: bool = False):
        return [g]

    def _X_canonical(self, g: X, adjointed: bool = False):
        return [RX(g.qubits[0], theta=math.pi)] if not adjointed else [RX(g.qubits[0], theta=-math.pi)]

    def _Y_canonical(self, g: Y, adjointed: bool = False):
        return [RY(g.qubits[0], theta=math.pi)] if not adjointed else [RY(g.qubits[0], theta=-math.pi)]

    def _Z_canonical(self, g: Z, adjointed: bool = False):
        return [RZ(g.qubits[0], phi=math.pi)] if not adjointed else [RZ(g.qubits[0], phi=-math.pi)]

    def _H_canonical(self, g: H, adjointed: bool = False):
        return [U3(g.qubits[0], theta=math.pi / 2, phi=0.0, gamma=math.pi)]

    def _S_canonical(self, g: S, adjointed: bool = False):
        return [RZ(g.qubits[0], phi=-math.pi / 2)] if adjointed else [RZ(g.qubits[0], phi=math.pi / 2)]

    def _T_canonical(self, g: T, adjointed: bool = False):
        return [RZ(g.qubits[0], phi=-math.pi / 4)] if adjointed else [RZ(g.qubits[0], phi=math.pi / 4)]

    def _RX_canonical(self, g: RX, adjointed: bool = False):
        return [RX(g.qubits[0], theta=-g.theta)] if adjointed else [g]

    def _RY_canonical(self, g: RY, adjointed: bool = False):
        return [RY(g.qubits[0], theta=-g.theta)] if adjointed else [g]

    def _RZ_canonical(self, g: RZ, adjointed: bool = False):
        return [RZ(g.qubits[0], phi=-g.phi)] if adjointed else [g]

    def _U1_canonical(self, g: U1, adjointed: bool = False):
        return [RZ(g.qubits[0], phi=-g.phi)] if adjointed else [RZ(g.qubits[0], phi=g.phi)]

    def _U2_canonical(self, g: U2, adjointed: bool = False):
        return [U3(g.qubits[0], theta=-math.pi / 2.0, phi=-g.gamma, gamma=-g.phi)] if adjointed\
            else [U3(g.qubits[0], theta=math.pi / 2.0, phi=g.phi, gamma=g.gamma)]

    def _U3_canonical(self, g: U3, adjointed: bool = False):
        return [U3(g.qubits[0], theta=-g.theta, phi=-g.gamma, gamma=-g.phi)] if adjointed else [g]

    def _CZ_canonical(self, g: CZ, adjointed: bool = False):
        return [g]

    def _CNOT_canonical(self, g: CNOT, adjointed: bool = False):
        t = g.target_qubits[0]
        sequence = [U3(t, theta=math.pi / 2, phi=0.0, gamma=math.pi),
                    CZ(g.control_qubits[0], t),
                    U3(t, theta=math.pi / 2, phi=0.0, gamma=math.pi)]
        return sequence

    def _SWAP_canonical(self, g: SWAP, adjointed: bool = False):
        a, b = g.target_qubits
        Ha = self._H_canonical(H(a), adjointed=adjointed)[0]
        Hb = self._H_canonical(H(b), adjointed=adjointed)[0]
        sequence = [Hb, CZ(a, b), Hb, Ha, CZ(b, a), Ha, Hb, CZ(a, b), Hb]
        return sequence

    def _Exponential_canonical(self, g: Exponential, adjointed: bool = False):
        base = g.basic_gate
        if base.nqubits != 1:
            raise NotImplementedError("Exponential of multi-qubit gates not supported.")
        U = g.matrix
        th, ph, lam = _zyz_from_unitary(U)
        return [U3(base.qubits[0], theta=th, phi=ph, gamma=lam)] if not adjointed\
            else [U3(base.qubits[0], theta=-th, phi=-lam, gamma=-ph)]

    def _CRX_canonical(self, g: RX, control_qubit: int, adjointed: bool = False):
        theta = g.theta / 2
        target_qubit = g.qubits[0]
        sequence = [RX(target_qubit, theta=theta),
                    CZ(control_qubit, target_qubit),
                    RX(target_qubit, theta=-theta),
                    CZ(control_qubit, target_qubit),]
        return sequence if not adjointed else self._rewrite_list(sequence, adjointed=adjointed)

    def _CRY_canonical(self, g: RY, control_qubit: int, adjointed: bool = False):
        theta = g.theta / 2
        target_qubit = g.qubits[0]
        sequence = [RY(target_qubit, theta=theta),
                    CZ(control_qubit, target_qubit),
                    RY(target_qubit, theta=-theta),
                    CZ(control_qubit, target_qubit),]
        return sequence if not adjointed else self._rewrite_list(sequence, adjointed=adjointed)

    def _CRZ_canonical(self, g: RZ, control_qubit: int, adjointed: bool = False):
        phi = g.phi / 2
        target_qubit = g.qubits[0]
        sequence = [
                    RZ(target_qubit, phi=phi),
                    U3(target_qubit, theta=math.pi / 2, phi=0.0, gamma=math.pi),  # n H
                    CZ(control_qubit, target_qubit),
                    RX(target_qubit, theta=-phi),
                    CZ(control_qubit, target_qubit),
                    U3(target_qubit, theta=math.pi / 2, phi=0.0, gamma=math.pi),  # An H
                    ]
        return sequence if not adjointed else self._rewrite_list(sequence, adjointed=adjointed)

    def _CU3_canonical(self, g: U3, control_qubit: int, adjointed: bool = False):
        theta = g.theta
        phi = g.phi
        lam = g.gamma
        target_qubit = g.qubits[0]
        sequence = [
                    RZ(target_qubit, phi=(lam - phi) / 2),
                    U3(target_qubit, theta=math.pi / 2, phi=0.0, gamma=math.pi),  # An H
                    CZ(control_qubit, target_qubit),
                    U3(target_qubit, theta=math.pi / 2, phi=0.0, gamma=math.pi),  # An H
                    U3(target_qubit, theta=-theta / 2, phi=0.0, gamma=-(lam + phi) / 2),
                    U3(target_qubit, theta=math.pi / 2, phi=0.0, gamma=math.pi),  # An H
                    CZ(control_qubit, target_qubit),
                    U3(target_qubit, theta=math.pi / 2, phi=0.0, gamma=math.pi),  # An H
                    U3(target_qubit, theta=theta / 2, phi=phi, gamma=0.0)
                    ]
        return sequence if not adjointed else self._rewrite_list(sequence, adjointed=adjointed)
