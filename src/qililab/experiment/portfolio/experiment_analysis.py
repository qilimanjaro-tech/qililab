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

"""This file contains the ``ExperimentAnalysis`` class used to analyze the results of an experiment."""
import inspect

import matplotlib.pyplot as plt
import numpy as np
from qibo.models import Circuit
from scipy.optimize import curve_fit

from qililab.experiment.experiment import Experiment
from qililab.platform import Bus, Platform
from qililab.typings import ExperimentOptions, Parameter
from qililab.utils import Loop

from .fitting_models import FittingModel


class ExperimentAnalysis(Experiment, FittingModel):
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
        experiment_loop (.Loop, optional): external loop used in the experiment. This argument can be used for
            experiments that use a loop to define multiple circuits, such as the Flipping Sequence experiment.
            Defaults to None.
    """

    post_processed_results: np.ndarray
    popt: np.ndarray  # fitted parameters

    def __init__(  # pylint: disable=too-many-arguments
        self,
        platform: Platform,
        circuits: list[Circuit],
        options: ExperimentOptions,
        control_bus: Bus | None = None,  # TODO: This will probably change for 2-qubit experiments
        readout_bus: Bus | None = None,
        experiment_loop: Loop | None = None,
    ):
        if experiment_loop is None:
            if options.loops is None:
                raise ValueError(
                    "A loop must be provided. Either an experiment loop in the `ExperimentOptions` class, or "
                    "an external loop in the `experiment_loop` argument."
                )
            self.loop = options.loops[0]  # TODO: Support nested loops
        else:
            self.loop = experiment_loop
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

        This method uses the scipy function `curve_fit` to fit the function `self.func` to the post-processed data.

        Args:
            p0 (tuple, optional): Initial guess for the parameters. Defaults to None.

        Returns:
            float: Optimal values for the parameters so that the sum of the squared residuals of
                `f(xdata, *popt) - ydata` is minimized.
        """
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )

        self.popt, _ = curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
            self.func, xdata=self.loop.values, ydata=self.post_processed_results, p0=p0
        )

        return self.popt

    def plot(self):
        """Method used to plot the results of an experiment.

        By default this method creates a figure with size (9, 7) and plots the magnitude of the IQ data.
        """
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )
        xdata = self.loop.values

        # Plot data
        fig, axes = plt.subplots(figsize=(9, 7))
        axes.set_title(self.options.name)
        axes.set_xlabel(f"{self.loop.alias}: {self.loop.parameter.value}")
        axes.set_ylabel("|S21| [dB]")  # TODO: Change label for 2D plots
        axes.scatter(xdata, self.post_processed_results, color="blue")
        if hasattr(self, "popt"):
            # Create label text
            args = list(inspect.signature(self.func).parameters.keys())[1:]
            text = "".join(f"{arg}: {value:.5f}\n" for arg, value in zip(args, self.popt))
            axes.plot(xdata, self.func(xdata, *self.popt), "--", label=text, color="red")
            axes.legend(loc="upper right")
        return fig

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
