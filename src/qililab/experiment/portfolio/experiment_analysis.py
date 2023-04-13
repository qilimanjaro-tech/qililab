"""This file contains the ``ExperimentAnalysis`` class used to analyze the results of an experiment."""
from abc import ABC, abstractmethod
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
from qibo.models import Circuit
from scipy.optimize import curve_fit

from qililab.experiment.experiment import Experiment
from qililab.platform import Bus, Platform
from qililab.typings import ExperimentOptions, Parameter


class ExperimentAnalysis(ABC, Experiment):
    """Class used to analyze the results of an experiment. The analysis of an experiment consist of the following steps:

    1. Acquire results: either by running an experiment or loading one.
    2. Post-process results: post-process the results of the experiment.
    3. Fit results: fit the post-processed results of the experiment.
    4. Plot results: plot the post-processed results of the experiment together with the fitted function.

    Args:
        platform (Platform): platform used to run the experiment
        circuits (List[Circuit]): list of circuits used in the experiment
        options (ExperimentOptions): options of the experiment
        control_bus (Bus, optional): control bus used in the experiment. Defaults to None.
        readout_bus (Bus, optional): readout bus used in the experiment. Defaults to None.
    """

    post_processed_results: np.ndarray
    popt: np.ndarray  # fitted parameters

    def __init__(
        self,
        platform: Platform,
        circuits: List[Circuit],
        options: ExperimentOptions,
        control_bus: Bus | None = None,  # TODO: This will probably change for 2-qubit experiments
        readout_bus: Bus | None = None,
    ):
        self.control_bus = control_bus
        self.readout_bus = readout_bus
        super().__init__(platform=platform, circuits=circuits, options=options)

    def post_process_results(self):
        """Method used to post-process the results of an experiment.

        By default this method computes the magnitude of the IQ data and saves it into the ``post_processed_results``
        attribute.

        Returns:
            np.ndarray: post-processed results
        """
        acquisitions = self.results.acquisitions()
        i = np.array(acquisitions["i"])
        q = np.array(acquisitions["q"])
        self.post_processed_results = 20 * np.log10(np.sqrt(i**2 + q**2))
        return self.post_processed_results

    def fit(self, p0: tuple | None = None):
        """Method used to fit the results of an experiment.

        This method uses the scipy function ``curve_fit`` to fit the function ``self.func`` to the post-processed data.

        Args:
            p0 (tuple, optional): Initial guess for the parameters. Defaults to None.

        Returns:
            float: optimal values for the parameters so that the sum of the squared residuals of
                ``f(xdata, *popt) - ydata is minimized.
        """
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )
        # TODO: Support nested loops
        loops = self.options.loops
        if loops is None:
            raise ValueError("The experiment must have at least one loop.")
        if len(loops) > 1:
            raise ValueError("Analysis of nested loops is not supported.")
        self.popt, _ = curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
            self.func, xdata=loops[0].range, ydata=self.post_processed_results, p0=p0
        )

        return self.popt

    @staticmethod
    @abstractmethod
    def func(xdata: np.ndarray, *args):
        """The model function, func(x, …) used to fit the post-processed data.

        It must take the independent variable as the first argument and the parameters to fit as separate remaining
        arguments.

        Args:
            xdata (np.ndarray): independent variable
            *args: parameters to fit

        Returns:
            np.ndarray: model function evaluated at xdata
        """

    def plot(self):
        """Method used to plot the results of an experiment.

        By default this method creates a figure with size (9, 7) and plots the magnitude of the IQ data.
        """
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )
        # Get loop data
        # TODO: Support nested loops
        loops = self.options.loops
        if loops is None:
            raise ValueError("The experiment must have at least one loop.")
        if len(loops) > 1:
            raise ValueError("Analysis of nested loops is not supported.")

        loop = loops[0]
        x_axis = loop.range

        # Plot data
        fig, axes = plt.subplots(figsize=(9, 7))
        axes.set_title(self.options.name)
        axes.set_xlabel(f"{loop.alias}: {loop.parameter.value}")
        axes.set_ylabel(f"{self.options.plot_y_label}")
        axes.plot(x_axis, self.post_processed_results, "-o")
        if hasattr(self, "popt"):
            axes.plot(x_axis, self.func(x_axis, *self.popt), "--")
        return fig

    def bus_setup(self, parameters: Dict[Parameter, float | str | bool], control=False) -> None:
        """Method used to change parameters of the bus used in the experiment. Some possible bus parameters are:

            * Parameter.CURRENT
            * Parameter.ATTENUATION
            * Parameter.IF
            * Parameter.GAIN
            * Parameter.LO_FREQUENCY
            * Parameter.POWER

        Args:
            parameters (Dict[Parameter, float | str | bool]): dictionary containing parameter names as keys and
                parameter values as values
            control (bool, optional): whether to change the parameters of the control bus (True) or the readout
                bus (False)
        """
        bus = self.control_bus if control else self.readout_bus

        if bus is None:
            raise ValueError(f"The experiment doesn't have a {'control' if control else 'readout'} bus.")

        for parameter, value in parameters.items():
            bus.set_parameter(parameter=parameter, value=value)

    def gate_setup(self, gate: str, parameters: Dict[Parameter, float | str | bool]) -> None:
        """Method used to change the parameters of the given gate. Some possible gate parameters are:

            * Parameter.AMPLITUDE
            * Parameter.DURATION
            * Parameter.PHASE

        Args:
            gate (str): name of the gate to change
            parameters (Dict[Parameter, float | str | bool]): dictionary containing parameter names as keys and
                parameter values as values
        """
        for parameter, value in parameters.items():
            self.platform.set_parameter(alias=gate, parameter=parameter, value=value)
        self.build_execution()
