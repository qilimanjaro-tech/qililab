"""This file contains a pre-defined version of a Flipping experiment."""
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

import qililab as ql
from qililab.experiment.portfolio import Cos, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class FlippingExperiment(ExperimentAnalysis, Cos):
    """Class used to run a flipping experiment on the given qubit.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        flips_values (np.ndarray):
        amplitude_values (np.ndarray):
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        measurement_buffer (ini, optional):  Defaults to 100.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        platform: Platform,
        qubit: int,
        flips_values: np.ndarray,
        amplitude_values: np.ndarray,
        repetition_duration=10000,
        measurement_buffer=100,
        hardware_average=10000,
    ):
        # Define circuits used in this experiment
        self.amplitude_values = amplitude_values
        self.flips_values = flips_values
        self.qubit = qubit

        loop_flips = Loop(alias="N", parameter=Parameter.EXTERNAL, values=flips_values)
        loop_amplitude = Loop(alias=f"Drag({qubit})", parameter=Parameter.AMPLITUDE, values=amplitude_values)
        circuits = []
        for n in loop_flips.values:
            circuit = Circuit(qubit + 1)
            circuit.add(ql.Drag(q=qubit, theta=np.pi / 2, phase=0))
            for _ in range(n):
                circuit.add(ql.Drag(q=qubit, theta=np.pi, phase=0))
                circuit.add(ql.Drag(q=qubit, theta=np.pi, phase=0))
            circuit.add(Wait(qubit, t=measurement_buffer))
            circuit.add(M(qubit))
            circuits.append(circuit)

        _, control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        experiment_options = ExperimentOptions(
            name="Flipping Sequence",
            loops=[loop_amplitude],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=circuits,
            options=experiment_options,
            control_bus=control_bus,
            readout_bus=readout_bus,
        )

    def post_process_results(self):
        super().post_process_results()
        self.post_processed_results = self.post_processed_results.reshape(
            len(self.amplitude_values), len(self.flips_values)
        )
        return self.post_processed_results

    def plot(self, savefile: str | None = None):
        im = plt.pcolor(self.flips_values, self.amplitude_values, self.post_processed_results, cmap="coolwarm")
        plt.xlabel("Number of Flips")
        plt.ylabel("X amplitude")
        plt.title(f"Flipping sequence Qubit {self.qubit}")
        plt.colorbar(im)
        # if savefile:
        #     plt.savefig(savefile) # why this? always save!
        # this_timestamp = get_timestamp_from_file(self.results_path)
        # ax = plt.gca()
        # ax.set_title(this_timestamp + ' ' +ax.get_title())
        # save_figure_from_exp(plt.gcf(),self)
        plt.show()
        return plt

    def plot_lines(self):
        for _ in range(len(self.amplitude_values)):
            plt.plot(self.flips_values, self.post_processed_results[_, :])
        plt.show()
        return plt
