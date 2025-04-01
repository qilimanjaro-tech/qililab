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

"""CircuitOptimizer class"""

from copy import deepcopy
from typing import TypeVar

import numpy as np
from qibo import Circuit, gates

from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings

from .native_gates import Drag, _GateHandler

T_circuit = TypeVar("T_circuit", Circuit, list[gates.Gate])


class CircuitOptimizer:
    """Optimizes a circuit, cancelling redundant gates.

    Args:
        settings (DigitalCompilationSettings): Object containing the Digital Compilations Settings and the info on chip's physical qubits.
            It can be obtained from the ``digital_compilation_settings`` attribute of a ``Platform`` object.
    """

    def __init__(self, settings: DigitalCompilationSettings):
        self.settings: DigitalCompilationSettings = settings
        """Object containing the digital compilations settings and the info on chip's physical qubits."""

    @staticmethod
    def optimize_gates(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Main method to optimize the gates of a Quantum Circuit before unrolling to native gates.

        The total optimization can/might be expanded in the future to include more complex gate optimization.

        Check public docstring in :meth:`.CircuitTranspiler.optimize_gates()` for more information.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the Qibo circuit to cancel gates.

        Returns:
            list[gates.Gate]: list of the gates of the Qibo circuit, optimized.
        """
        # Add more future methods of optimizing gates here, like 2local optimizations, cliffords ...:

        circuit_gates = CircuitOptimizer.cancel_pairs_of_hermitian_gates(circuit_gates)
        circuit_gates = CircuitOptimizer.remove_redundant_start_controlled_gates(circuit_gates)
        # circuit_gates = cls.2local_gate_optimization(circuit_gates) TODO:
        return circuit_gates

    @staticmethod
    def cancel_pairs_of_hermitian_gates(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Optimizes circuit by cancelling adjacent hermitian gates.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the Qibo circuit to cancel pairs of hermitians.

        Returns:
            list[gates.Gate]: list of the gates of the Qibo circuit, optimized.
        """
        # Initial and final circuit gates lists, from which to, one by one, after checks, pass non-cancelled gates:
        gates_info: list[tuple] = _GateHandler.get_circuit_gates_info(circuit_gates)

        # We want to do the sweep circuit cancelling gates least once always:
        old_gates_info = deepcopy(gates_info)
        new_gates_info = CircuitOptimizer._sweep_circuit_cancelling_pairs_of_hermitian_gates(gates_info)

        # And then keep iterating, sweeping over the circuit (cancelling gates) each time, until there is full sweep without any cancellations:
        while new_gates_info != old_gates_info:
            old_gates_info = deepcopy(new_gates_info)
            new_gates_info = CircuitOptimizer._sweep_circuit_cancelling_pairs_of_hermitian_gates(new_gates_info)

        # Create optimized circuit, from the obtained non-cancelled list:
        return _GateHandler.create_qibo_gates_from_gates_info(new_gates_info)

    def add_phases_from_RZs_and_CZs_to_drags(self, circuit_gates: list[gates.Gate], nqubits: int) -> list[gates.Gate]:
        """This method adds the phases from RZs and CZs gates of the circuit to the next Drag gates.

            - The CZs added phases on the Drags, come from a correction from their calibration, stored on the setting of the CZs.
            - The RZs added phases on the Drags, come from commuting all the RZs all the way to the end of the circuit, so they can be deleted as "virtual Z gates".

        Check public docstring in :meth:`.CircuitTranspiler.add_phases_from_RZs_and_CZs_to_drags()` for more information.

        Args:
            circuit_gates (list[gates.Gate]): list of native gates of the circuit, to pass phases to the Drag gates.
            nqubits (int): Number of qubits of the circuit.

        Returns:
            list[gates.Gate]: list of re-ordered gates
        """
        supported_gates = ["rz", "drag", "cz", "wait", "measure"]
        new_gates = []
        shift = dict.fromkeys(range(nqubits), 0)
        for gate in circuit_gates:
            if gate.name not in supported_gates:
                raise NotImplementedError(f"{gate.name} not part of native supported gates {supported_gates}")
            if isinstance(gate, gates.RZ):
                shift[gate.qubits[0]] += gate.parameters[0]
            # add CZ phase correction
            elif isinstance(gate, gates.CZ):
                gate_settings = self.settings.get_gate(name=gate.__class__.__name__, qubits=gate.qubits)
                control_qubit, target_qubit = gate.qubits
                corrections = next(
                    (
                        event.pulse.options
                        for event in gate_settings
                        if (
                            event.pulse.options is not None
                            and f"q{control_qubit}_phase_correction" in event.pulse.options
                        )
                    ),
                    None,
                )
                if corrections is not None:
                    shift[control_qubit] += corrections[f"q{control_qubit}_phase_correction"]
                    shift[target_qubit] += corrections[f"q{target_qubit}_phase_correction"]
                new_gates.append(gate)
            else:
                # if gate is drag pulse, shift parameters by accumulated Zs
                if isinstance(gate, Drag):
                    # create new drag pulse rather than modify parameters of the old one
                    gate = Drag(gate.qubits[0], gate.parameters[0], gate.parameters[1] - shift[gate.qubits[0]])

                # append gate to optimized list
                new_gates.append(gate)

        return new_gates

    @staticmethod
    def optimize_transpiled_gates(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Main method to optimize the gates of a Quantum Circuit after having unrolled to native gates.

        The total optimization can/might be expanded in the future to include more complex optimizations.

        Check public docstring in :meth:`.CircuitTranspiler.optimize_transpiled_gates()` for more information.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the transpiled circuit, to optimize.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, optimized.
        """
        # Add more optimizations of the transpiled circuit here:
        circuit_gates = CircuitOptimizer.normalize_angles_of_drags(circuit_gates)
        circuit_gates = CircuitOptimizer.bunch_drag_gates(circuit_gates)
        # TODO: Add bunching of Drag Gates for diff phis!
        circuit_gates = CircuitOptimizer.delete_gates_with_no_amplitude(circuit_gates)
        return circuit_gates

    @staticmethod
    def bunch_drag_gates(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Bunches consecutive Drag gates together into a single one.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the transpiled circuit, to bunch drag gates.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, with drag gates bunched."""

        for idx1, drag1 in enumerate(circuit_gates):
            # We are in the last gate, so there is no next one to merge with:
            if idx1 == len(circuit_gates) - 1:
                break

            # Find a Drag gate to merge with:
            if not isinstance(drag1, Drag):
                continue

            for idx2, drag2 in enumerate(circuit_gates[idx1 + 1 :]):
                # Find next gate in the same qubit
                if drag2 is None or drag2.qubits != drag1.qubits:
                    continue

                # If the next gate in the same qubit is not a Drag gate, we can't optimize:
                if not isinstance(drag2, Drag):
                    break

                # If the next gate in the same qubit is a Drag gate, we can merge them:
                new_drag: Drag | None = CircuitOptimizer.merge_consecutive_drags(drag1, drag2)

                # If not successful bunching, we can't merge this gate, go next one:
                if new_drag is None:
                    break

                # If successful bunching, substitute old gates with new one:
                circuit_gates[idx1], drag1 = new_drag, new_drag
                circuit_gates[idx2 + idx1 + 1] = None

        # Remove None values from the list:
        return [gate for gate in circuit_gates if gate is not None]

    @staticmethod
    def merge_consecutive_drags(drag1: Drag, drag2: Drag) -> Drag | None:
        """Merges two consecutive Drag gates into a single one.

        Args:
            drag1 (Drag): First Drag gate.
            drag2 (Drag): Second Drag gate.

        Returns:
            Drag | None: Merged Drag gate. None, if not possible to merge.
        """
        if drag1.qubits != drag2.qubits:
            raise ValueError("Cannot merge Drag gates acting on different qubits.")

        # For the same phi, we just need to add the theta parameters:
        if np.isclose(drag1.parameters[1], drag2.parameters[1]):
            new_normalized_theta = _GateHandler.normalize_angle(drag1.parameters[0] + drag2.parameters[0])
            return Drag(drag1.qubits[0], new_normalized_theta, drag1.parameters[1])

        # For opposite phi, we just need to subtract the theta parameters:
        if np.isclose(drag1.parameters[1], _GateHandler.normalize_angle(drag2.parameters[1] + np.pi)):
            new_normalized_theta = _GateHandler.normalize_angle(drag1.parameters[0] - drag2.parameters[0])
            return Drag(drag1.qubits[0], new_normalized_theta, drag1.parameters[1])

        # TODO: ADD BUNCHING DRAG GATES FOR GENERAL DIFFERENT PHI's!
        return None  # This should return the merged Drag gate, for different phi's!

    @staticmethod
    def normalize_angles_of_drags(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Normalizes angles in the gates of the circuit.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the transpiled circuit, to normalize the angles.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, with normalized angles.
        """
        for gate in circuit_gates:
            if isinstance(gate, Drag):
                gate.parameters = (
                    _GateHandler.normalize_angle(gate.parameters[0]),
                    _GateHandler.normalize_angle(gate.parameters[1]),
                )
        return circuit_gates

    @staticmethod
    def delete_gates_with_no_amplitude(circuit_gates: list[gates.Gate]) -> list[gates.Gate]:
        """Deletes gates without amplitude.

        Args:
            circuit_gates (list[gates.Gate]): list of gates of the transpiled circuit, to delete gates without amplitude.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, with gates without amplitude deleted."""
        for idx, gate in enumerate(circuit_gates):
            if isinstance(gate, Drag) and np.isclose(gate.parameters[0], 0):
                circuit_gates[idx] = None
        return [gate for gate in circuit_gates if gate]

    @staticmethod
    def _sweep_circuit_cancelling_pairs_of_hermitian_gates(circuit_gates: list[tuple]) -> list[tuple]:
        """Cancels adjacent gates in a circuit.

        Args:
            circuit_gates (list[tuple]): List of gates in the circuit. Where each gate is a tuple of ('name', 'init_args', 'initi_kwargs')

        Returns:
            list[tuple]: List of gates in the circuit, after cancelling adjacent gates. Where each gate is a tuple of ('name', 'init_args', 'initi_kwargs')
        """
        # List of gates, that are available for cancellation:
        hermitian_gates: list = ["H", "X", "Y", "Z", "CNOT", "CZ", "SWAP"]

        output_circuit_gates: list[tuple] = []

        while circuit_gates:  # If original circuit list, is empty or has one gate remaining, we are done:
            if len(circuit_gates) == 1:
                output_circuit_gates.append(circuit_gates[0])
                break

            # Gate of the original circuit, to find a match for:
            gate, gate_args, gate_kwargs = circuit_gates.pop(0)
            gate_qubits = _GateHandler.extract_qubits_from_gate_args(
                gate_args
            )  # Assuming qubits are the first two args

            # If gate is not hermitian (can't be cancelled), add it to the output circuit and continue:
            if gate not in hermitian_gates:
                output_circuit_gates.append((gate, gate_args, gate_kwargs))
                continue

            subend = False
            for i in range(len(circuit_gates)):
                # Next gates, to compare the original with:
                comp_gate, comp_args, comp_kwargs = circuit_gates[i]
                comp_qubits = _GateHandler.extract_qubits_from_gate_args(
                    comp_args
                )  # Assuming qubits are the first two args

                # Simplify duplication, if same gate and qubits found, without any other in between:
                if gate == comp_gate and gate_args == comp_args and gate_kwargs == comp_kwargs:
                    circuit_gates.pop(i)
                    break

                # Add gate, if there is no other gate that acts on the same qubits:
                if i == len(circuit_gates) - 1:
                    output_circuit_gates.append((gate, gate_args, gate_kwargs))
                    break

                # Add gate and leave comparison_gate loop, if we find a gate in common qubit, that prevents contraction:
                for gate_qubit in gate_qubits:
                    if gate_qubit in comp_qubits:
                        output_circuit_gates.append((gate, gate_args, gate_kwargs))
                        subend = True
                        break
                if subend:
                    break

        return output_circuit_gates

    @staticmethod
    def remove_redundant_start_controlled_gates(
        transpiled_circ: T_circuit, gates_to_remove: tuple[gates.Gate] | gates.Gate | None = None
    ) -> T_circuit:
        """Removes redundant controlled gates at the start of the transpiled circuit.

        Args:
            transpiled_circ (Circuit): Transpiled circuit.
            gates_to_remove (tuple[gates.Gate] | gates.Gate, optional): Tuple of gates to remove. Defaults to all controlled gates.

        Returns:
            Circuit | list[gates.Gate] : Transpiled circuit without redundant gates.
        """

        finished_qubits: set = set()
        is_circuit = isinstance(transpiled_circ, Circuit)

        queue: list[gates.Gate] = deepcopy(transpiled_circ.queue) if is_circuit else deepcopy(transpiled_circ)  # type: ignore [attr-defined]
        wire_names = deepcopy(transpiled_circ.wire_names) if is_circuit else None  # type: ignore [attr-defined]

        for idx, gate in enumerate(queue):
            # When all qubits have finished, we stop:
            if is_circuit and len(finished_qubits) == transpiled_circ.nqubits:  # type: ignore [attr-defined]
                break

            # The condition will be, the gate is one of the given, or the gate has a control qubit.
            is_gate_to_remove_OR_has_control_q = (
                isinstance(gate, gates_to_remove) if gates_to_remove else len(gate.control_qubits) != 0
            )
            # If  gate fulfills the condition, and has no gate before, we remove gate:
            if is_gate_to_remove_OR_has_control_q and all(qubit not in finished_qubits for qubit in gate.qubits):
                CircuitOptimizer._make_gate_None_in_queue(gate, idx, queue, wire_names)  # type: ignore[arg-type]
            # If gate not fulfills the condition, or has another non-removed gate before, we stop for that qubit:
            else:
                finished_qubits.update(gate.qubits)

        queue = [x for x in queue if x is not None]

        # If a circuit is originally passed, return a circuit with the wire_names updated:
        if is_circuit:
            return _GateHandler.create_circuit_from_gates(queue, transpiled_circ.nqubits, wire_names)  # type: ignore [attr-defined]
        # If a queue was passed, return a list.
        return queue

    @staticmethod
    def _make_gate_None_in_queue(gate: gates.Gate, idx: int, queue: list[gates.Gate], wire_names: list[int]) -> None:
        """Removes a gate from the circuit queue and updates wire names if the gate is a SWAP gate.

        Args:
            gate (gates.Gate): The gate to be removed from the circuit.
            idx (int): The index of the gate in the queue.
            queue (list[gates.Gate]): The list representing the circuit queue.
            wire_names (list[int]): Wire names of the transpiled circuit.

        Returns:
            None
        """
        queue[idx] = None
        # If we remove a SWAP gate at the start, change wire names:
        if isinstance(gate, gates.SWAP) and wire_names:
            qubits = gate.qubits
            wire_names[qubits[0]], wire_names[qubits[1]] = wire_names[qubits[1]], wire_names[qubits[0]]
