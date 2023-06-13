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


class RabiMux(ExperimentAnalysis, Cos):
    """Class used to run a rabi mux experiment on the two given qubits.

    This experiment modifies the amplitude of the pulse associated to the Drag gate for the first qubit and then makes
    the same but with a factor of 2 for the other qubit. So we can see, that we are actually acting on two different qubits.

    This is done with the following operations for each qubit (the second one with theta_values doubled):
    1. Send a Drag gate with theta = value of the loop (theta_values) and phase = 0.
    2. Send a Wait gate of time = measurement_buffer.
    3. Measure the qubit

    Args:
        qubits_theta (int): qubit index used in the experiment where we apply the normal loop with theta_values
        qubit_2theta (int): qubit index used in the experiment where we apply the loop with 2*theta_values
        platform (Platform): platform used to run the experiment
        theta_values (numpy.ndarray): array of values to loop through in the experiment, which modifies the amplitude of Drag gate
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 1000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 1000.
        measurement_buffer (int, optional): the time to wait (ns) until the measurements. Defaults to 100.
        num_bins (int, optional): number of bins/shoots of the experiment. Defaults to 1.
    """

    def __init__(
        self,
        qubit_theta: int,
        qubit_2theta: int,
        platform: Platform,
        theta_values: np.ndarray,
        repetition_duration=1000,
        hardware_average=1000,
        measurement_buffer=100,
        num_bins=1,
    ):
        self.theta_values = theta_values

        circuit = Circuit(int(np.max([qubit_theta, qubit_2theta])) + 1)
        circuit.add(Drag(qubit_theta, theta=np.pi, phase=0))
        circuit.add(Drag(qubit_2theta, theta=2 * np.pi, phase=0))
        circuit.add(Wait(qubit_theta, measurement_buffer))
        circuit.add(Wait(qubit_2theta, measurement_buffer))
        circuit.add(M(qubit_theta))
        circuit.add(M(qubit_2theta))

        theta_loop = Loop(alias="0", parameter=Parameter.GATE_PARAMETER, values=theta_values)
        theta2_loop = Loop(alias="2", parameter=Parameter.GATE_PARAMETER, values=2 * theta_values)

        experiment_options = ExperimentOptions(
            name="rabi_mux",
            loops=[theta_loop, theta2_loop],
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

    def post_process_results(self) -> np.ndarray:
        """Process the results of the experiment and reshape it in two dimensional arrays"""
        super().post_process_results()
        self.post_processed_results = self.post_processed_results.reshape(len(self.theta_values), 2)
        return self.post_processed_results

    def plot(self):
        """Plots the results of the experiment for both qubits one over the other"""
        plt.plot(self.theta_values, self.post_processed_results[:, 0], label="2*theta")
        plt.plot(self.theta_values, self.post_processed_results[:, 1], label="theta")
        plt.title(self.options.name)
        plt.xlabel(f"{self.loop.alias}:{self.loop.parameter.value}")
        plt.ylabel("|S21| [dB]")
        plt.legend(loc="upper right")
