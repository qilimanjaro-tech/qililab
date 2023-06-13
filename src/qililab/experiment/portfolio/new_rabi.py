"""This file contains a pre-defined version of a rabi experiment."""
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

from qililab import Drag
from qililab.experiment.portfolio import Cos, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class Rabi(ExperimentAnalysis, Cos):
    def __init__(
        self,
        qubit: int,
        platform: Platform,
        amp_values: np.ndarray,
        if_values: np.ndarray | None = None,
        repetition_duration=1000,
        hardware_average=1000,
        measurement_buffer=100,
        num_bins=1,
    ):
        self.qubit = qubit
        self.amplitude_values = amp_values
        self.if_values = if_values

        circuit = Circuit(qubit + 1)
        circuit.add(Drag(qubit, theta=np.pi, phase=0))
        circuit.add(Wait(qubit, measurement_buffer))
        circuit.add(M(qubit))

        qubit_sequencer_mw_mapping = {0: 0, 1: 1, 2: 0, 3: 0, 4: 1}
        sequencer_mw = qubit_sequencer_mw_mapping[qubit]

        amplitude_loop = Loop(alias=f"Drag({qubit})", parameter=Parameter.AMPLITUDE, values=amp_values)
        if self.if_values is not None:
            if_loop = Loop(
                alias=f"drive_line_q{qubit}_bus",
                parameter=Parameter.IF,
                values=if_values,
                loop=amplitude_loop,
                channel_id=sequencer_mw,
            )

        experiment_options = ExperimentOptions(
            name="rabi",
            loops=[if_loop if (self.if_values is not None) else amplitude_loop],
            settings=ExperimentSettings(
                repetition_duration=repetition_duration, hardware_average=hardware_average, num_bins=num_bins
            ),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )

    def post_process_results(self):
        super().post_process_results()
        if self.if_values is not None:
            self.post_processed_results = self.post_processed_results.reshape(
                len(self.if_values), len(self.amplitude_values)
            )
        return self.post_processed_results

    def plot(self, savefile: str | None = None):
        if self.if_values is not None:
            im = plt.pcolormesh(self.amplitude_values, self.if_values, self.post_processed_results, cmap="coolwarm")
            plt.xlabel("Amplitude")
            plt.ylabel("IF")
            plt.colorbar(im, label="|S2| [dB]")
        else:
            super().plot()
        try:
            plt.title(plt.gca().get_title() + rf" $A_\pi$ = {1 / (2 * self.popt[1]):.3f}")
        except Exception:
            print("No fitting was demanded")
