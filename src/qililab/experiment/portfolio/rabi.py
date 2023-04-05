"""This file contains a pre-defined version of a rabi experiment."""
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M, X
from qibo.models import Circuit

from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, LoopOptions, Parameter
from qililab.utils import Loop


class Rabi(Experiment):
    """Class used to run a rabi experiment on the given qubit. This can be done in two different ways:

    * ``use_frequency=False``: by modifying the amplitude of the pulse associated to the X gate
    * ``use_frequency=True``: by modifying the intermediate frequency of the driving bus that is connected to the given
        qubit

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        loop_options (LoopOptions): options of the loop used in the experiment, which modifies the amplitude of X gate
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
        use_frequency (bool, optional): whether to use the frequency of the driving bus to perform the experiment (True)
            or the amplitude of the X gate (False). Defaults to False.
    """

    def __init__(
        self,
        platform: Platform,
        qubit: int,
        loop_options: LoopOptions,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Define circuit used in this experiment
        circuit = Circuit(1)
        circuit.add(X(qubit))
        circuit.add(M(qubit))

        self.control_bus, self.readout_bus = platform.get_bus_by_qubit_index(qubit)

        # Define loop used in the experiment
        loop = Loop(alias="X", parameter=Parameter.AMPLITUDE, options=loop_options)

        experiment_options = ExperimentOptions(
            name="Rabi",
            loops=[loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
            plot_y_label="Integrated Voltage (mV)",
        )

        # Initialize experiment
        super().__init__(platform=platform, circuits=[circuit], options=experiment_options)

    def bus_setup(self, parameters: dict, control=False) -> None:
        """Method used to change parameters of the bus used in the experiment. Some possible bus parameters are:

            * Parameter.CURRENT
            * Parameter.ATTENUATION
            * Parameter.IF
            * Parameter.GAIN
            * Parameter.LO_FREQUENCY
            * Parameter.POWER

        Args:
            parameters (dict): dictionary containing parameter names as keys and parameter values as values
            control (bool, optional): whether to change the parameters of the control bus (True) or the readout
                bus (False)
        """
        bus = self.control_bus if control else self.readout_bus

        for parameter, value in parameters.items():
            bus.set_parameter(parameter=parameter, value=value)

    def control_gate_setup(self, parameters: dict) -> None:
        """Method used to change parameters of the control gate used in the experiment. Some possible gate
        parameters are:

            * Parameter.AMPLITUDE
            * Parameter.DURATION
            * Parameter.PHASE

        Args:
            parameters (dict): dictionary containing parameter names as keys and parameter values as values
        """
        for parameter, value in parameters.items():
            self.platform.set_parameter(alias="X", parameter=parameter, value=value)

    def measurement_setup(self, parameters: dict) -> None:
        """Method used to change parameters of the measurement gate used in the experiment. Some possible gate
        parameters are:

            * Parameter.AMPLITUDE
            * Parameter.DURATION
            * Parameter.PHASE

        Args:
            parameters (dict): dictionary containing parameter names as keys and parameter values as values
        """
        for parameter, value in parameters.items():
            self.platform.set_parameter(alias="M", parameter=parameter, value=value)

    def post_process_results(self):
        """Method used to post-process the results of a rabi experiment."""

    def fit(self):
        """Method used to fit the results of a rabi experiment.

        This method fits
        """

    def plot(self):
        """Method used to plot the results of a rabi experiment."""
        # Prepare acquisition data
        acquisitions = self.results.acquisitions()
        i = np.array(acquisitions["i"])
        q = np.array(acquisitions["q"])

        # Get loop data
        loop = self.options.loops[0]
        x_axis = loop.range

        # Plot data
        figure = plt.figure(figsize=(9, 7))
        plt.title("Rabi experiment.")
        plt.xlabel("QCM gain")
        plt.ylabel("|S21| [dB]")
        plt.plot(x_axis, 20 * np.log10(np.sqrt(i**2 + q**2)), "-o")
        return figure
