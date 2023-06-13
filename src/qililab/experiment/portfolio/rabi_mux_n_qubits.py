"""This file contains a pre-defined version of a rabi experiment."""
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

from qililab.experiment.portfolio import Cos, ExperimentAnalysis
from qililab.platform import Platform
from qililab.transpiler import Drag
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class RabiMuxNQubits(ExperimentAnalysis, Cos):
    """Class used to run a rabi mux experiment on the n given qubits.

    This experiment modifies the amplitude of the pulse associated to the Drag gate for the first qubit and then
    makes the same but with a factor of 2 for the other qubit. So we can see, that we are actually acting on two different qubits.

    Args:
        qubits (list[int]): list of the qubits index used in the experiment where we apply the different theta loops.
        platform (Platform): platform used to run the experiment
        theta_values (numpy.ndarray): array of values to loop through in the experiment, which modifies the amplitude of Drag gate
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 1000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 1000.
        measurement_buffer (int, optional): the time to wait (ns) until the measurements. Defaults to 100.
        num_bins (int, optional): number of bins/shoots of the experiment. Defaults to 1.
    """

    def __init__(
        self,
        qubits: list[int],
        platform: Platform,
        theta_values: np.ndarray,
        repetition_duration=1000,
        hardware_average=1000,
        measurement_buffer=100,
        num_bins=1,
    ):
        self.theta_values = theta_values
        self.num_qubits = len(qubits)

        circuit = Circuit(int(np.max(qubits)) + 1)
        for qubit in qubits:
            circuit.add(Drag(qubit, theta=np.pi, phase=0))
            circuit.add(Wait(qubit, measurement_buffer))
            circuit.add(M(qubit))

        loops = [
            Loop(alias=str(3 * i), parameter=Parameter.GATE_PARAMETER, values=(i + 1) * theta_values)
            for i, _ in enumerate(qubits)
        ]

        experiment_options = ExperimentOptions(
            name="rabi_mux_n_qubits",
            loops=loops,
            settings=ExperimentSettings(
                repetition_duration=repetition_duration,
                hardware_average=hardware_average,
                num_bins=num_bins,
            ),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )

    def post_process_results(self):
        """Process the results of the experiment and reshape it in n dimensional arrays (n=num_qubits)"""
        super().post_process_results()
        self.post_processed_results = self.post_processed_results.reshape(len(self.theta_values), self.num_qubits)
        return self.post_processed_results

    def plot(self):
        """Plots the results of the experiment for all qubits one over the others"""
        for i in self.num_qubits:
            plt.plot(self.theta_values, self.post_processed_results[:, i], label=f"qubit_{i}")
        plt.title(self.options.name)
        plt.xlabel(f"{self.loop.alias}:{self.loop.parameter.value}")
        plt.ylabel("|S21| [dB]")
        plt.legend(loc="upper right")
