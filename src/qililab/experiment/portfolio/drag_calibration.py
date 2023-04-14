"""This file contains a pre-defined version of a drag calibration experiment."""
import inspect

import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import RX, RY, M, X, Y
from qibo.models import Circuit
from scipy.optimize import curve_fit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, LoopOptions, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import CosFunc


class DragCalibration(ExperimentAnalysis, CosFunc):
    """Class used to run a drag calibration experiment on the given qubit.

    This experiment runs two circuits: --|X|--|RY(pi/2)|--|M|-- and --|Y|--|RX(pi/2)|--|M|--. It changes the drag
    coefficient of both the X and the Y gate.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        loop_options (LoopOptions): options of the loop used in the experiment, which changes the drag coefficient of
            the X and Y gate
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        platform: Platform,
        qubit: int,
        loop_options: LoopOptions,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Define circuits used in this experiment
        circuit1 = Circuit(1)
        circuit1.add(X(qubit))
        circuit1.add(RY(qubit, theta=np.pi / 2))
        circuit1.add(M(qubit))
        circuit2 = Circuit(1)
        circuit2.add(Y(qubit))
        circuit2.add(RX(qubit, theta=np.pi / 2))
        circuit2.add(M(qubit))
        circuits = [circuit1, circuit2]

        control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        loop1 = Loop(alias="X", parameter=Parameter.DRAG_COEFFICIENT, options=loop_options)
        loop2 = Loop(alias="Y", parameter=Parameter.DRAG_COEFFICIENT, options=loop_options)
        experiment_options = ExperimentOptions(
            name="Drag Calibration",
            loops=[loop1, loop2],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
            plot_y_label="|S21| [dB]",
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=circuits,
            options=experiment_options,
            control_bus=control_bus,
            readout_bus=readout_bus,
        )

    def fit(self, p0: tuple | None = None) -> np.ndarray:
        """Fits the data of each executed circuit to a cosine function.

        Args:
            p0 (tuple, optional): initial guess for the fitting parameters. Defaults to None.

        Returns:
            ndarray: optimal values for the parameters so that the sum of the squared residuals of
                ``f(xdata, *popt) - ydata`` is minimized.
        """
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )

        results1 = self.post_processed_results[0]
        popt1, _ = curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
            self.func, xdata=self.loop.range, ydata=results1, p0=p0
        )
        results2 = self.post_processed_results[1]
        popt2, _ = curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
            self.func, xdata=self.loop.range, ydata=results2, p0=p0
        )
        self.popt = np.concatenate((popt1, popt2))

        return self.popt

    def plot(self):
        if not hasattr(self, "post_processed_results"):
            raise AttributeError(
                "The post-processed results must be computed before fitting. "
                "Please call ``post_process_results`` first."
            )
        xdata = self.loop.range

        # Plot data
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(9, 7))
        colors = ["blue", "green"]
        for i, axis in enumerate((ax1, ax2)):
            axis.set_title(self.options.name)
            axis.set_xlabel(f"{self.loop.alias}: {self.loop.parameter.value}")
            axis.set_ylabel(f"{self.options.plot_y_label}")
            axis.scatter(xdata, self.post_processed_results[i], color=colors[i])
        if hasattr(self, "popt"):
            # Create label text
            args = list(inspect.signature(self.func).parameters.keys())[1:]
            pop1 = self.popt[: len(args)]
            pop2 = self.popt[len(args) :]
            colors = ["red", "orange"]
            for i, axis in enumerate((ax1, ax2)):
                text = "".join(f"{arg}: {value:.5f}\n" for arg, value in zip(args, pop1 if i == 0 else pop2))
                axis.plot(xdata, self.func(xdata, *pop1 if i == 0 else pop2), "--", label=text, color=colors[i])

        ax1.legend(loc="upper right")
        ax2.legend(loc="upper left")
        return fig
