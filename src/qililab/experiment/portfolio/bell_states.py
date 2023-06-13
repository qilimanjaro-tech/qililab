from itertools import product
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import CZ, M
from qibo.models import Circuit

import qililab as ql
from qililab.experiment.portfolio import Exp, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait

bell_state_names = ["phi_plus", "phi_minus", "psi_plus", "psi_minus"]


class xBellStates(ExperimentAnalysis, Exp):
    """Class to prepare a bell state and run a CHSH protocol.

    control_qubit: (int) qubit where the Ry(theta) gate is applied before measurment
    target_qubit: (int) the other qubit
    platform: (Platform) platform specs for qililab
    theta_loop_values: (np.ndarray) values of theta for the Ry(theta) on the control qubit
    bell_state: (str) either 'phi_plus', 'phi_minus', 'psi_plus' or 'psi_minus', the Bell state to prepare
    repetition_duration: (int)
    hardware_average: (int)
    num_bins: (int)
    """

    def __init__(
        self,
        control_qubit: int,
        target_qubit: int,
        platform: Platform,
        theta_loop_values: np.ndarray,
        bell_state: str = "phi_plus",
        repetition_duration=200_000,
        hardware_average=1,
        num_bins=2_000,
    ) -> None:
        if bell_state not in bell_state_names:
            raise ValueError(f"bell_state needs to be in {bell_state_names}")

        self.control_qubit = control_qubit
        self.target_qubit = target_qubit
        self.theta_loop_values = theta_loop_values
        self.bell_state = bell_state
        self.platform = platform
        self.nqubits = max(control_qubit, target_qubit)

        theta_loop = Loop(alias="6", parameter=Parameter.GATE_PARAMETER, values=theta_loop_values)
        basis_loop_control = Loop(
            alias="8", parameter=Parameter.GATE_PARAMETER, values=np.array([0, -np.pi / 2]), loop=theta_loop
        )
        basis_loop_target = Loop(
            alias="10", parameter=Parameter.GATE_PARAMETER, values=np.array([0, -np.pi / 2]), loop=basis_loop_control
        )

        chsh_circuit = self._get_chsh_circuit()
        decoder_circuit = self._get_decoder_circuits()
        circuit = chsh_circuit + decoder_circuit

        experiment_options = ExperimentOptions(
            name="bell_state",
            settings=ExperimentSettings(
                repetition_duration=repetition_duration, hardware_average=hardware_average, num_bins=num_bins
            ),
            loops=[basis_loop_target],
        )

        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )

    def _get_chsh_circuit(self) -> Circuit:
        circuit = Circuit(self.nqubits + 1)
        # TODO: find out why phi_plus and minus are switched if we simulate them with qibo
        if self.bell_state in ["phi_plus", "psi_plus"]:
            G1 = ql.Drag(self.control_qubit, theta=np.pi / 2, phase=np.pi / 2)
        else:
            G1 = ql.Drag(self.control_qubit, theta=-np.pi / 2, phase=np.pi / 2)

        if self.bell_state in ["phi_plus", "phi_minus"]:
            G2_prime = ql.Drag(self.target_qubit, theta=-np.pi / 2, phase=np.pi / 2)
        else:
            G2_prime = ql.Drag(self.target_qubit, theta=np.pi / 2, phase=np.pi / 2)

        circuit.add(G1)  # parameters 0 and 1
        circuit.add(ql.Drag(self.target_qubit, theta=np.pi / 2, phase=np.pi / 2))  # parameters 2 and 3
        circuit.add(CZ(self.control_qubit, self.target_qubit))
        circuit.add(G2_prime)  # parameters 4 and 5
        return circuit

    def _get_decoder_circuits(self) -> Circuit:
        # ZZ measurments
        circuit = Circuit(self.nqubits + 1)
        # add parameterized R_Y for measurment
        circuit.add(ql.Drag(self.control_qubit, theta=0, phase=np.pi / 2))  # parameters 6 and 7
        # add rotations to mimick I or H for change of measurment basis
        circuit.add(ql.Drag(self.control_qubit, theta=0, phase=np.pi / 2))  # parameters 8 and 9
        circuit.add(ql.Drag(self.target_qubit, theta=0, phase=np.pi / 2))  # parameters 10 and 11
        circuit.add(M(self.control_qubit))
        circuit.add(M(self.target_qubit))

        return circuit

    def post_process_results(self):
        self.post_processed_results = np.zeros((2, 2, len(self.theta_loop_values)))
        for idx, (i, j, k) in enumerate(product(range(2), range(2), range(len(self.theta_loop_values)))):
            self.post_processed_results[i, j, k] = (
                self.results.results[idx].probabilities()["00"]
                - self.results.results[idx].probabilities()["01"]
                - self.results.results[idx].probabilities()["10"]
                + self.results.results[idx].probabilities()["11"]
            )
        return self.post_processed_results

    def get_chsh_witness(self) -> Tuple[np.ndarray, np.ndarray]:
        self.chsh1 = (
            self.post_processed_results[0, 0]
            + self.post_processed_results[0, 1]
            - self.post_processed_results[1, 0]
            + self.post_processed_results[1, 1]
        )
        self.chsh2 = (
            self.post_processed_results[0, 0]
            - self.post_processed_results[0, 1]
            + self.post_processed_results[1, 0]
            + self.post_processed_results[1, 1]
        )
        return self.chsh1, self.chsh2

    def plot(self):
        plt.plot(self.theta_loop_values, self.chsh1, "o--", label="witness 1")
        plt.plot(self.theta_loop_values, self.chsh2, "o--", label="witness 2")
        plt.xlabel(r"$\theta$")
        plt.ylabel("CHSH witness")
        plt.axhline(2, color="red", linestyle="--", label="classical bounds")
        plt.axhline(-2, color="red", linestyle="--")
        plt.axhline(2 * np.sqrt(2), color="blue", linestyle="-.", label="quantum bounds")
        plt.axhline(-2 * np.sqrt(2), color="blue", linestyle="-.")
        plt.legend()
        plt.show()
