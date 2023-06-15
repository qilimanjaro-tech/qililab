"""This file contains the ``ExperimentAnalysis`` class used to analyze the results of an experiment."""
import inspect
import matplotlib.pyplot as plt
import numpy as np
from qibo.models import Circuit
from scipy.optimize import curve_fit

from qililab.experiment.circuit_experiment import CircuitExperiment
from qililab.platform import Bus, Platform
from qililab.typings import ExperimentOptions, Parameter
from qililab.utils import Loop
from typing import List
from .fitting_models import FittingModel


class ExperimentAnalysis(CircuitExperiment, FittingModel):
    """Class used to analyze the results of an experiment. The analysis of an experiment consist of the following steps:

    1. Acquire results: either by running an experiment or loading one.
    2. Post-process results: post-process the results of the experiment.
    3. Fit results: fit the post-processed results of the experiment.
    4. Plot results: plot the post-processed results of the experiment together with the fitted function.

    Args:
        platform (Platform): platform used to run the experiment
        circuits (list[Circuit]): list of circuits used in the experiment
        options (ExperimentOptions): options of the experiment
        control_bus (Bus, optional): control bus used in the experiment. Defaults to None.
        readout_bus (Bus, optional): readout bus used in the experiment. Defaults to None.
        experiment_loop (Loop, optional): external loop used in the experiment. This argument can be used for
            experiments that use a loop to define multiple circuits, such as the Flipping Sequence experiment.
            Defaults to None.
    """

    post_processed_results: np.ndarray
    popt: np.ndarray  # fitted parameters

    def __init__(
        self,
        platform: Platform,
        circuits: list[Circuit],
        options: ExperimentOptions,
        control_bus: Bus | None = None,
        readout_bus: Bus | None = None,
        experiment_loop: Loop | None = None,
    ):
        if experiment_loop is None:
            if options.loops is None:
                raise ValueError(
                    "A loop must be provided. Either an experiment loop in the `ExperimentOptions` class, or "
                    "an external loop in the `experiment_loop` argument."
                )
            self.loops = options.loops
        else:
            self.loops = [experiment_loop]

        self.control_bus = control_bus
        self.readout_bus = readout_bus
        self.shorter_loop:List[np.ndarray] = [] # indicates 2D experiment if not empty list
        for loop in self.loops:
            if loop.loop is not None:
                if len(self.shorter_loop) == 0 or len(loop.values) < len(self.shorter_loop[0]):
                    self.shorter_loop = [loop.values, loop.loop.values]

        super().__init__(platform=platform, circuits=circuits, options=options)

    def post_process_results(self):
        """Method used to post-process the results of an experiment.

        By default this method computes the magnitude of the IQ data and saves it into the ``post_processed_results``
        attribute. If the experiment is a 2D one, it reshapes the data accordingly.

        Returns:
            np.ndarray: post-processed results
        """
        acquisitions = self.results.acquisitions()
        i = np.array(acquisitions["i"])
        q = np.array(acquisitions["q"])

        self.post_processed_results = 20 * np.log10(np.sqrt(i**2 + q**2))

        if len(self.shorter_loop) > 0:
            self.post_processed_results = self.post_processed_results.reshape(self.shorter_loop[0].size, self.shorter_loop[1].size)

        return self.post_processed_results

    def fit(self, p0: tuple | None = None):
        """Method used to fit the results of an experiment.

        This method uses the scipy function ``curve_fit`` to fit the function ``self.func`` to the post-processed data.

        Args:
            p0 (tuple, optional): Initial guess for the parameters. Defaults to None.

        Returns:
            list(float): list with optimal values for the parameters so that the sum of the squared residuals of
                ``f(xdata, *popt) - ydata is minimized.
        """
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )

        self.popts = []
        if len(self.shorter_loop) > 0:
            for i in range(len(self.shorter_loop)):
                popt, _ = curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
                    self.func, xdata=self.shorter_loop[0], ydata=self.post_processed_results[i], p0=p0
                )
                self.popts.append(popt)
        else:
            popt, _ = curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
                self.func, xdata=self.loops[0].values, ydata=self.post_processed_results, p0=p0
            )
            self.popts.append(popt)

        return self.popts

    def plot_1D(self, y_label: str = ""):
        """Method used to generate default 1D plot.

        By default this method creates a figure with size (9, 7) and plots the magnitude of the IQ data.

        Args:
            y_label (str, optional): string indicating the y_label for 1D plot.

        Returns:
            matplotlib.figure: matplotlib figure with 1D plot.
        """
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )
        loop = self.loops[0]
        xdata = loop.values

        # Plot data
        fig, axes = plt.subplots(figsize=(9, 7))
        axes.set_title(self.options.name)
        axes.set_xlabel(f"{loop.alias}: {loop.parameter.value}")
        axes.set_ylabel(y_label)
        axes.scatter(xdata, self.post_processed_results, color="blue")
        if hasattr(self, "popts"):
            # Create label text
            args = list(inspect.signature(self.func).parameters.keys())[1:]
            text = "".join(f"{arg}: {value:.5f}\n" for arg, value in zip(args, self.popts[0]))
            axes.plot(xdata, self.func(xdata, *self.popts[0]), "--", label=text, color="red")
            axes.legend(loc="upper right")

        return fig

    def plot_2D(self, x_label: str = "", y_label: str = ""):
        """Method used to generate default 2D plots.

        Args:
            x_label (str, optional): string indicating the x_label for the 2D plot.
            y_label (str, optional): string indicating the y_label for the 2D plot.

        Returns:
            matplotlib.figure: matplotlib figure with 2D plot.
        """
        fig = plt.figure()
        for ii in range(len(self.shorter_loop)):
            plt.plot(
                self.shorter_loop[ii],
                self.post_processed_results[ii],
                "-o",
                label=f"{self.loops[0].parameter.value}={ii}",
            )

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.legend(loc="right", bbox_to_anchor=(1.4, 0.5))

        return fig

    def plot(self, x_label: str = "", y_label: str = ""):
        """Method used to generate default plots. It checks if the experiment is 1D or 2D and calls the
        appropiate function.

        Args:
            x_label (str, optional): string indicating the x_label for 2D plots
            y_label (str, optional): string indicating the y_label for 1D and 2D plots

        Returns:
            matplotlib.figure: matplotlib figure with either 1D plot or 2D plots.
        """
        if len(self.shorter_loop) > 0:
            return self.plot_2D(x_label=x_label, y_label=y_label)
        else:
            return self.plot_1D(y_label=y_label)

    def bus_setup(self, parameters: dict[Parameter, float | str | bool], control=False) -> None:
        """Method used to change parameters of the bus used in the experiment. Some possible bus parameters are:

            * Parameter.CURRENT
            * Parameter.ATTENUATION
            * Parameter.IF
            * Parameter.GAIN
            * Parameter.LO_FREQUENCY
            * Parameter.POWER

        Args:
            parameters (dict[Parameter, float | str | bool]): dictionary containing parameter names as keys and
                parameter values as values
            control (bool, optional): whether to change the parameters of the control bus (True) or the readout
                bus (False)
        """
        bus = self.control_bus if control else self.readout_bus

        if bus is None:
            raise ValueError(f"The experiment doesn't have a {'control' if control else 'readout'} bus.")

        for parameter, value in parameters.items():
            bus.set_parameter(parameter=parameter, value=value)

    def gate_setup(self, parameters: dict[Parameter, float | str | bool], gate: str) -> None:
        """Method used to change the parameters of the given gate. Some possible gate parameters are:

            * Parameter.AMPLITUDE
            * Parameter.DURATION
            * Parameter.PHASE

        Args:
            parameters (dict[Parameter, float | str | bool]): dictionary containing parameter names as keys and
                parameter values as values
            gate (str): name of the gate to change
        """
        for parameter, value in parameters.items():
            self.platform.set_parameter(alias=gate, parameter=parameter, value=value)
        self.build_execution()
