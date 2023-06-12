"""This file contains a pre-defined version of a rabi experiment."""
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

from qililab.experiment.portfolio import Cos, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop


class ResonatorSpectroscopy(ExperimentAnalysis, Cos):
    """Class used to run a rabi experiment on the given qubit. This experiment modifies the amplitude of the pulse
    associated to the X gate.

    Args:
        platform (Platform): platform used to run the experiment
        frequencies (numpy.ndarray): array of frequencies to loop through in the experiment,
                                     which modifies the frequency of the local oscilator
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        qubit: int,
        platform: Platform,
        freq_values: np.ndarray,
        gain_values: np.ndarray | None = None,
        attenuation_values: np.ndarray | None = None,
        sweep_if: bool = False,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        self.freq_values = freq_values
        self.gain_values = gain_values
        self.attenuation_values = attenuation_values

        # Define circuit used in this experiment
        circuit = Circuit(qubit + 1)
        circuit.add(M(qubit))

        # Define loop used in the experiment
        qubit_readout_sequencer_mapping = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}
        sequencer = qubit_readout_sequencer_mapping[qubit]

        if sweep_if:
            loop = Loop(alias="feedline_bus", parameter=Parameter.IF, values=freq_values, channel_id=sequencer)
        else:
            loop = Loop(alias="feedline_bus", parameter=Parameter.LO_FREQUENCY, values=freq_values, channel_id=qubit)

        if attenuation_values is not None:
            att_loop = Loop(
                alias="feedline_bus",
                parameter=Parameter.ATTENUATION,
                values=attenuation_values,
                channel_id=qubit,
                loop=loop,
            )
            loops = [att_loop]

        elif gain_values is not None:
            gain_loop_I = Loop(
                alias="feedline_bus", parameter=Parameter.GAIN_I, values=gain_values, channel_id=qubit, loop=loop
            )
            gain_loop_Q = Loop(alias="feedline_bus", parameter=Parameter.GAIN_Q, values=gain_values, channel_id=qubit)
            loops = [gain_loop_I, gain_loop_Q]
        else:
            loops = [loop]

        experiment_options = ExperimentOptions(
            name="resonator_spectroscopy",
            loops=loops,
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )

    def post_process_results(self):
        super().post_process_results()
        if self.gain_values is not None:
            self.post_processed_results = self.post_processed_results.reshape(
                len(self.gain_values), len(self.freq_values)
            )
        if self.attenuation_values is not None:
            self.post_processed_results = self.post_processed_results.reshape(
                len(self.attenuation_values), len(self.freq_values)
            )
        return self.post_processed_results

    def plot(self):
        if self.gain_values is not None:
            im = plt.pcolormesh(self.freq_values, self.gain_values, self.post_processed_results, cmap="coolwarm")
            plt.xlabel("Frequency (Hz)")
            plt.ylabel("Gain")
            plt.yscale("log")
            plt.colorbar(im, label="|S2| [dB]")
        elif self.attenuation_values is not None:
            im = plt.pcolormesh(self.freq_values, self.attenuation_values, self.post_processed_results, cmap="coolwarm")
            plt.xlabel("Frequency (Hz)")
            plt.ylabel("Attenuation (dB)")
            plt.colorbar(im, label="|S2| [dB]")
        else:
            s21 = self.post_processed_results.flatten()
            idx_max = np.argmin(s21)
            min_freq = self.freq_values[idx_max]
            plt.plot(self.freq_values, self.post_processed_results.flatten(), "o-", label="Data")
            plt.plot(min_freq, s21[idx_max], "r*", label=f"Resonance = {min_freq*1e-9:.6f} GHz")
            plt.xlabel("Frequency")
            plt.ylabel("|S21|")
            plt.legend()
            plt.title(self.results_path)
            # save_figure_from_exp(plt.gcf(),self)

        plt.show()
        return plt
