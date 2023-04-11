"""This file contains the ``ExperimentAnalysis`` class used to analyze the results of an experiment."""
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from qililab.experiment.experiment import Experiment


class ExperimentAnalysis(ABC, Experiment):
    """Class used to analyze the results of an experiment. The analysis of an experiment consist of the following steps:

    1. Acquire results: either by running an experiment or loading one.
    2. Post-process results: post-process the results of the experiment.
    3. Fit results: fit the post-processed results of the experiment.
    4. Plot results: plot the post-processed results of the experiment together with the fitted function.
    """

    post_processed_results: np.ndarray
    popt: np.ndarray  # fitted parameters

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
        r"""Method used to fit the results of an experiment.

        This method uses the scipy function ``curve_fit`` to fit the function ``self.func`` to the post-processed data.

        Args:
            p0 (tuple, optional): Initial guess for the parameters. Defaults to None.

        Returns:
            float: optimal values for the parameters so that the sum of the squared residuals of
                ``f(xdata, *popt) - ydata is minimized.
        """
        self.popt, _ = curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
            self.func, xdata=self.options.loops[0].range, ydata=self.post_processed_results, p0=p0
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
        # Get loop data
        loop = self.options.loops[0]
        x_axis = loop.range

        # Plot data
        fig, axes = plt.subplots(figsize=(9, 7))
        axes.set_title(self.options.name)
        axes.set_xlabel(f"{loop.alias}: {loop.parameter.value}")
        axes.set_ylabel(f"{self.options.plot_y_label}")
        axes.plot(x_axis, self.post_process_results, "-o")
        if hasattr(self, "popt"):
            axes.plot(x_axis, self.func(x_axis, *self.popt), "--")
        return fig
