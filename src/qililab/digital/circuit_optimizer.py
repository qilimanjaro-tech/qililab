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

import numpy as np
import sympy as sp
from qibo import gates

from qililab import digital
from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings

from .native_gates import Drag


class CircuitOptimizer:
    """Optimizes a circuit, cancelling redundant gates.

    Args:
        settings (DigitalCompilationSettings): Object containing the Digital Compilations Settings and the info on chip's physical qubits.
            It can be obtained from the `digital_compilation_settings` attribute of a `Platform` object.
    """

    def __init__(self, settings: DigitalCompilationSettings):
        self.settings: DigitalCompilationSettings = settings
        """Object containing the digital compilations settings and the info on chip's physical qubits."""

    @classmethod
    def optimize_gates(cls, gate_list: list[gates.Gate]) -> list[gates.Gate]:
        # Docstring related to the public method: :meth:`.CircuitTranspiler.optimize_gates()`. Change it there too.
        """Main method to run the gate optimizations. Currently only consists of cancelling pairs of hermitian gates.

        Can/Might be extended in the future to include more complex gate optimization.

        Args:
            gate_list (list[gates.Gate]): list of gates of the Qibo circuit to cancel gates.

        Returns:
            list[gates.Gate]: list of the gates of the Qibo circuit, optimized.
        """
        # Add more future methods of optimizing gates here, like 2local optimizations, cliffords ...:
        gate_list = cls.cancel_pairs_of_hermitian_gates(gate_list)
        return gate_list

    @classmethod
    def cancel_pairs_of_hermitian_gates(cls, gate_list: list[gates.Gate]) -> list[gates.Gate]:
        """Optimizes circuit by cancelling adjacent hermitian gates.

        Args:
            gate_list (list[gates.Gate]): list of gates of the Qibo circuit to cancel pairs of hermitians.

        Returns:
            list[gates.Gate]: list of the gates of the Qibo circuit, optimized.
        """
        # Initial and final circuit gates lists, from which to, one by one, after checks, pass non-cancelled gates:
        circ_list: list[tuple] = cls._get_circuit_gates(gate_list)

        # We want to do the sweep circuit cancelling gates least once always:
        previous_circ_list = deepcopy(circ_list)
        output_circ_list = cls._sweep_circuit_cancelling_pairs_of_hermitian_gates(circ_list)

        # And then keep iterating, sweeping over the circuit (cancelling gates) each time, until there is full sweep without any cancellations:
        while output_circ_list != previous_circ_list:
            previous_circ_list = deepcopy(output_circ_list)
            output_circ_list = cls._sweep_circuit_cancelling_pairs_of_hermitian_gates(output_circ_list)

        # Create optimized circuit, from the obtained non-cancelled list:
        return cls._create_circuit_gate_list(output_circ_list)

    def add_phases_from_RZs_and_CZs_to_drags(self, gate_list: list[gates.Gate], nqubits: int) -> list[gates.Gate]:
        # Docstring related to the public method: :meth:`.CircuitTranspiler.add_phases_from_RZs_and_CZs_to_drags()`. Change it there too.
        """This method adds the phases from RZs and CZs gates of the circuit to the next Drag gates.

            - The CZs added phases on the Drags, come from a correction from their calibration, stored on the setting of the CZs.
            - The RZs added phases on the Drags, come from commuting all the RZs all the way to the end of the circuit, so they can be deleted as "virtual Z gates".

        This is done by moving all RZ to the left of all operators as a single RZ. The corresponding cumulative rotation
        from each RZ is carried on as phase in all drag pulses left of the RZ operator.

        Virtual Z gates are also applied to correct phase errors from CZ gates.

        The final RZ operator left to be applied as the last operator in the circuit can afterwards be removed since the last
        operation is going to be a measurement, which is performed on the Z basis and is therefore invariant under rotations
        around the Z axis.

        This last step can also be seen from the fact that an RZ operator applied on a single qubit, with no operations carried
        on afterwards induces a phase rotation. Since phase is an imaginary unitary component, its absolute value will be 1
        independent on any (unitary) operations carried on it.

        Mind that moving an operator to the left is equivalent to applying this operator last so
        it is actually moved to the _right_ of ``Circuit.queue`` (last element of list).

        For more information on virtual Z gates, see https://arxiv.org/abs/1612.00858

        Args:
            gate_list (list[gates.Gate]): list of native gates of the circuit, to pass phases to the Drag gates.
            nqubits (int): Number of qubits of the circuit.

        Returns:
            list[gates.Gate]: list of re-ordered gates
        """
        supported_gates = ["rz", "drag", "cz", "wait", "measure"]
        new_gates = []
        shift = dict.fromkeys(range(nqubits), 0)
        for gate in gate_list:
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

    @classmethod
    def optimize_transpiled_gates(cls, gate_list: list[gates.Gate]) -> list[gates.Gate]:
        # Docstring related to the public method: :meth:`.CircuitTranspiler.optimize_transpiled_gates()`. Change it there too.
        """Bunches consecutive Drag gates together into a single one.

        Args:
            gate_list (list[gates.Gate]): list of gates of the transpiled circuit, to optimize.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, optimized.
        """
        # Add more optimizations of the transpiled circuit here:
        gate_list = cls.bunch_drag_gates(gate_list, only_same_phi=True)
        gate_list = cls.bunch_drag_gates(gate_list, only_same_phi=False)
        gate_list = cls.delete_gates_with_no_amplitude(gate_list)
        return gate_list

    @classmethod
    def bunch_drag_gates(cls, gate_list: list[gates.Gate], only_same_phi: bool = False) -> list[gates.Gate]:
        """Bunches consecutive Drag gates together into a single one.

        Args:
            gate_list (list[gates.Gate]): list of gates of the transpiled circuit, to bunch drag gates.
            only_same_phi (bool, optional): If True, only Drag gates with the same phi are bunched. Defaults to False.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, with drag gates bunched."""

        for idx1, drag1 in enumerate(gate_list):
            # We are in the last gate, so there is no next one to merge with:
            if idx1 == len(gate_list) - 1:
                break

            # Find a Drag gate to merge with:
            if not isinstance(drag1, Drag):
                continue

            for idx2, drag2 in enumerate(gate_list[idx1 + 1 :]):
                # Find next gate in the same qubit
                if drag2.qubits != drag1.qubits:
                    continue

                # If the next gate in the same qubit is not a Drag gate, we can't optimize:
                if not isinstance(drag2, Drag):
                    break

                # If the next gate in the same qubit is a Drag gate, we can merge them:
                new_drag = cls.merge_consecutive_drags(drag1, drag2, only_same_phi)
                if new_drag is not None:
                    gate_list[idx1] = new_drag
                    gate_list[idx2] = None

        # Remove None values from the list:
        return [gate for gate in gate_list if gate is not None]

    @staticmethod
    def merge_consecutive_drags(drag1: Drag, drag2: Drag, only_same_phi: bool) -> Drag:
        """Merges two consecutive Drag gates into a single one.

        Args:
            drag1 (Drag): First Drag gate.
            drag2 (Drag): Second Drag gate.
            only_same_phi (bool): If True, only Drag gates with the same phi are merged.

        Returns:
            Drag | None: Merged Drag gate. None, if not possible to merge.
        """
        if drag1.qubits != drag2.qubits:
            raise ValueError("Cannot merge Drag gates acting on different qubits.")

        # For the same phi, we just need to add the theta parameters:
        if drag1.parameters[1] == drag2.parameters[1]:
            return Drag(drag1.qubits[0], drag1.parameters[0] + drag2.parameters[0], drag1.parameters[1])

        # If we are merging only Drag gates with same phi, we can't merge these gates:
        if only_same_phi:
            return None

        # Old parameters
        theta, phi = drag1.parameters
        theta_prime, phi_prime = drag2.parameters

        # New parameters
        new_theta = 2 * sp.acos(
            (
                (1 - np.exp(1j * theta))
                * (1 - np.exp(1j * theta_prime))
                * np.exp(1j * (2 * phi_prime + theta + theta_prime) / 2)
                + (np.exp(1j * theta) + 1)
                * (np.exp(1j * theta_prime) + 1)
                * np.exp(1j * (2 * phi + theta + theta_prime) / 2)
            )
            * np.exp(-1j * (phi + theta + theta_prime))
            / 4
        )
        new_phi = (
            sp.arg(
                (
                    (1 - np.exp(1j * theta)) * (np.exp(1j * theta_prime) + 1) * np.exp(1j * phi)
                    + (1 - np.exp(1j * theta_prime)) * (np.exp(1j * theta) + 1) * np.exp(1j * phi_prime)
                )
                * np.exp(1j * (phi + phi_prime))
                / (
                    (1 - np.exp(1j * theta)) * (np.exp(1j * theta_prime) + 1) * np.exp(1j * phi_prime)
                    + (1 - np.exp(1j * theta_prime)) * (np.exp(1j * theta) + 1) * np.exp(1j * phi)
                )
            )
            / 2
        )

        return Drag(drag1.qubits[0], new_theta, new_phi)

    @staticmethod
    def delete_gates_with_no_amplitude(gate_list: list[gates.Gate]) -> list[gates.Gate]:
        """Deletes gates without amplitude.

        Args:
            gate_list (list[gates.Gate]): list of gates of the transpiled circuit, to delete gates without amplitude.

        Returns:
            list[gates.Gate]: list of gates of the transpiled circuit, with gates without amplitude deleted."""
        for gate in gate_list:
            if isinstance(gate, Drag) and np.isclose(gate.parameters[0], 0):
                gate_list.remove(gate)
        return gate_list

    @staticmethod
    def _get_circuit_gates(gate_list: list[gates.Gate]) -> list[tuple]:
        """Get the gates of the circuit.

        Args:
            gate_list (list[gates.Gate]): list of native gates of the Qibo circuit.

        Returns:
            list[tuple]: List of gates in the circuit. Where each gate is a tuple of ('name', 'init_args', 'init_kwargs').
        """
        return [(type(gate).__name__, gate.init_args, gate.init_kwargs) for gate in gate_list]

    @staticmethod
    def _create_gate(gate_class: str, gate_args: list | int, gate_kwargs: dict) -> gates.Gate:
        """Converts a tuple representation of qibo gate (name, qubits) into a Gate object.

        Args:
            gate_class (str): The class name of the gate. Can be any Qibo or Qililab supported class.
            gate_args (list | int): The qubits the gate acts on.
            gate_kwargs (dict): The kwargs of the gate.

        Returns:
            gates.Gate: The qibo Gate object.
        """
        # Solve Identity gate, argument int issue:
        gate_args = [gate_args] if isinstance(gate_args, int) else gate_args

        return (
            getattr(digital, gate_class)(*gate_args, **gate_kwargs)
            if gate_class in {"Drag", "Wait"}
            else getattr(gates, gate_class)(*gate_args, **gate_kwargs)
        )

    @classmethod
    def _create_circuit_gate_list(cls, gates_list: list[tuple]) -> list[gates.Gate]:
        """Converts a list of gates (name, qubits) into a qibo Circuit object.

        Args:
            gates_list (list[tuple]): List of gates in the circuit. Where each gate is a tuple of ('name', 'init_args', 'initi_kwargs')
            nqubits (int): Number of qubits in the circuit.

        Returns:
            list[gates.Gate]: Gate list of the qibo Circuit.
        """
        # Create optimized circuit, from the obtained non-cancelled list:
        output_gates_list = []
        for gate, gate_args, gate_kwargs in gates_list:
            qibo_gate = cls._create_gate(gate, gate_args, gate_kwargs)
            output_gates_list.append(qibo_gate)

        return output_gates_list

    @classmethod
    def _sweep_circuit_cancelling_pairs_of_hermitian_gates(cls, circ_list: list[tuple]) -> list[tuple]:
        """Cancels adjacent gates in a circuit.

        Args:
            circ_list (list[tuple]): List of gates in the circuit. Where each gate is a tuple of ('name', 'init_args', 'initi_kwargs')

        Returns:
            list[tuple]: List of gates in the circuit, after cancelling adjacent gates. Where each gate is a tuple of ('name', 'init_args', 'initi_kwargs')
        """
        # List of gates, that are available for cancellation:
        hermitian_gates: list = ["H", "X", "Y", "Z", "CNOT", "CZ", "SWAP"]

        output_circ_list: list[tuple] = []

        while circ_list:  # If original circuit list, is empty or has one gate remaining, we are done:
            if len(circ_list) == 1:
                output_circ_list.append(circ_list[0])
                break

            # Gate of the original circuit, to find a match for:
            gate, gate_args, gate_kwargs = circ_list.pop(0)
            gate_qubits = cls._extract_qubits(gate_args)  # Assuming qubits are the first two args

            # If gate is not hermitian (can't be cancelled), add it to the output circuit and continue:
            if gate not in hermitian_gates:
                output_circ_list.append((gate, gate_args, gate_kwargs))
                continue

            subend = False
            for i in range(len(circ_list)):
                # Next gates, to compare the original with:
                comp_gate, comp_args, comp_kwargs = circ_list[i]
                comp_qubits = cls._extract_qubits(comp_args)  # Assuming qubits are the first two args

                # Simplify duplication, if same gate and qubits found, without any other in between:
                if gate == comp_gate and gate_args == comp_args and gate_kwargs == comp_kwargs:
                    circ_list.pop(i)
                    break

                # Add gate, if there is no other gate that acts on the same qubits:
                if i == len(circ_list) - 1:
                    output_circ_list.append((gate, gate_args, gate_kwargs))
                    break

                # Add gate and leave comparison_gate loop, if we find a gate in common qubit, that prevents contraction:
                for gate_qubit in gate_qubits:
                    if gate_qubit in comp_qubits:
                        output_circ_list.append((gate, gate_args, gate_kwargs))
                        subend = True
                        break
                if subend:
                    break

        return output_circ_list

    @staticmethod
    def _extract_qubits(gate_args: list | int) -> list:
        """Extract qubits from gate_args.

        Args:
            gate_args (list | int): The arguments of the gate.

        Returns:
            list: The qubits of the gate in an iterable.
        """
        # Assuming qubits are the first one or two args:
        if isinstance(gate_args, int):
            return [gate_args]
        return gate_args if len(gate_args) <= 2 else gate_args[:2]
