"""This file contains a pre-defined version of a ssro experiment."""
from copy import deepcopy

import lmfit
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M
from qibo.models import Circuit
from scipy.special import erf

from qililab.experiment.portfolio import Cos, ExperimentAnalysis
from qililab.platform import Platform
from qililab.transpiler.native_gates import Drag
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class SSRO(ExperimentAnalysis, Cos):
    """Experiment to perform SSRO to a qubit.

    The SSRO is performed with the execution of two circuits on the same qubit through the following sequence of operations:
        Circuit 1:
            1. Prepare the qubit in the ground state.
            2. Measure the state of the qubit.
        Circuit 2:
            1. Prepare the qubit in the excited state by sending a π-pulse to the qubit.
            2. Measure the state of the qubit.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        wait_loop_values (numpy.ndarray): array of values to loop through in the experiment, which modifies the t parameter of the Wait gate
        loop_parameter (Parameter | None):
        loop_values (numpy.ndarray):
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 200000.
        hardware_average (int, optional): number of repetitions used to average the result. Default to 1.
        measurment_buffer (int, optional): time to wait before taking a measurment. Defaults to 100.
        num_bins (int, optional): number of bins of the Experiment. Defaults to 2000.
    """

    def __init__(
        self,
        qubit: int,
        platform: Platform,
        loop_parameter: Parameter | None,
        loop_values: np.ndarray,
        repetition_duration=200_000,
        hardware_average=1,
        measurement_buffer=100,
        num_bins=2_000,
    ):
        self.qubit = qubit
        self.loop_parameter = loop_parameter
        self.loop_values = loop_values

        circuit1 = Circuit(qubit + 1)
        circuit1.add(Drag(qubit, theta=0, phase=0))
        circuit1.add(Wait(qubit, t=measurement_buffer))
        circuit1.add(M(qubit))

        circuit2 = Circuit(qubit + 1)
        circuit2.add(Drag(qubit, theta=np.pi, phase=0))
        circuit2.add(Wait(qubit, t=measurement_buffer))
        circuit2.add(M(qubit))

        qubit_sequencer_mapping = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}
        sequencer = qubit_sequencer_mapping[qubit]

        if loop_parameter == Parameter.AMPLITUDE:
            loop = Loop(alias=f"M({qubit})", parameter=Parameter.AMPLITUDE, values=loop_values)
        elif loop_parameter == Parameter.IF:
            loop = Loop(alias="feedline_bus", parameter=Parameter.IF, values=loop_values, channel_id=sequencer)
        elif loop_parameter == Parameter.LO_FREQUENCY:
            loop = Loop(alias="rs_1", parameter=Parameter.LO_FREQUENCY, values=loop_values, channel_id=None)
        elif loop_parameter == Parameter.DURATION:
            loop = Loop(alias=f"M({qubit})", parameter=Parameter.DURATION, values=loop_values)
            loop2 = Loop(
                alias="feedline_bus", parameter=Parameter.INTEGRATION_LENGTH, values=loop_values, channel_id=qubit
            )
        elif loop_parameter == Parameter.ATTENUATION:
            loop = Loop(alias="attenuator", parameter=Parameter.ATTENUATION, values=loop_values)

        elif loop_parameter is None:
            loop = Loop(alias="external", parameter=Parameter.EXTERNAL, values=np.array([1]))

        experiment_options = ExperimentOptions(
            name="ssro",
            loops=[loop, loop2] if loop_parameter == Parameter.DURATION else [loop],
            settings=ExperimentSettings(
                repetition_duration=repetition_duration, hardware_average=hardware_average, num_bins=num_bins
            ),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit1, circuit2],
            options=experiment_options,
        )

    def post_process_results(self):
        """Method used to post-process the results of an experiment.

        This method computes the magnitude of the IQ data, reshapes it into IQ values for both of the states measured and saves it into the ``post_processed_results``
        attribute.

        Returns:
            np.ndarray: post-processed results
        """
        acquisitions = self.results.acquisitions()
        i = np.array(acquisitions["i"])
        q = np.array(acquisitions["q"])
        shots_iq = np.array(i + 1j * q)
        shots_iq = shots_iq.reshape((2, self.num_bins))
        self.post_proccessed_results = shots_iq
        return shots_iq

    def fit(self):
        """Method used to fit the results of an experiment.

        This method uses the scipy function ``erf`` to fit the function ``self.func`` to the post-processed data.

        Returns:
            dictionary: contains the best fitted values aswell as some metadata of the process needed for plotting in case is used.
        """

        def two_gaussians(x, a0, std0, v0, std1, v1):
            a1 = 1 - a0
            cdf_0 = a0 * (1 + erf((x - v0) / (std0 * 2**0.5))) / 2
            cdf_1 = a1 * (1 + erf((x - v1) / (std1 * 2**0.5))) / 2
            return cdf_0 + cdf_1

        def joint_model(x, mmt_relax, thermal_pop, std0, v0, std1, v1, N):
            prep0_m0 = 1 - thermal_pop
            prep1_m0 = mmt_relax
            cdf_prep0 = N * two_gaussians(x, prep0_m0, std0, v0, std1, v1)
            cdf_prep1 = N * two_gaussians(x, prep1_m0, std0, v0, std1, v1)
            return np.concatenate((cdf_prep0, cdf_prep1))

        if not hasattr(self, "post_proccessed_results"):
            raise ValueError(
                "The post-processed results must be computed before fitting.\nPlease call ``post_process_results`` first."
            )

        I_0, Q_0 = np.real(self.post_proccessed_results[0]), np.imag(self.post_proccessed_results[0])
        I_1, Q_1 = np.real(self.post_proccessed_results[1]), np.imag(self.post_proccessed_results[1])
        center_0_i, center_0_q = np.mean(I_0), np.mean(Q_0)
        center_1_i, center_1_q = np.mean(I_1), np.mean(Q_1)

        dist_i = center_1_i - center_0_i
        dist_q = center_1_q - center_0_q

        # x,y are I,Q centered in 0
        x_0 = I_0 - center_0_i
        y_0 = Q_0 - center_0_q
        x_1 = I_1 - center_0_i
        y_1 = Q_1 - center_0_q
        # u,v are x,v rotated
        theta = np.arctan2(dist_q, dist_i)
        u_0 = x_0 * np.cos(theta) + y_0 * np.sin(theta)
        u_1 = x_1 * np.cos(theta) + y_1 * np.sin(theta)

        perc_vec = np.linspace(0, 100, 101)
        cdf_0 = np.percentile(u_0, perc_vec)
        cdf_1 = np.percentile(u_1, perc_vec)

        x_axis = np.linspace(np.min((cdf_0, cdf_1)), np.max((cdf_0, cdf_1)), 101)
        interp_cdf_0 = np.interp(x_axis, cdf_0, perc_vec)
        interp_cdf_1 = np.interp(x_axis, cdf_1, perc_vec)
        diff_cdf = interp_cdf_1 - interp_cdf_0

        idx_max = np.argmax(np.abs(diff_cdf))
        threshold = x_axis[idx_max]
        # Threshold in the u axis, but without the shifts
        threshold_d = threshold + center_0_i * np.cos(theta) + center_0_q * np.sin(theta)
        f_asg = np.abs(diff_cdf[idx_max])
        f_avg = (100 + f_asg) / 2

        cdfs_mod = lmfit.Model(joint_model)

        v0_guess = np.mean(u_0)
        std0_guess = np.std(u_0)
        v1_guess = np.mean(u_1)
        std1_guess = np.std(u_1)

        cdfs_mod.set_param_hint("mmt_relax", value=0.7, min=0, max=1, vary=True)
        cdfs_mod.set_param_hint("thermal_pop", value=0.03, min=0, max=1, vary=True)
        cdfs_mod.set_param_hint("std0", value=std0_guess, vary=True)
        cdfs_mod.set_param_hint("std1", value=std1_guess, vary=True)
        cdfs_mod.set_param_hint("v0", value=v0_guess, vary=True)
        cdfs_mod.set_param_hint("v1", value=v1_guess, vary=True)
        cdfs_mod.set_param_hint("N", value=100, min=0, vary=False)
        params = cdfs_mod.make_params()
        fit_res = cdfs_mod.fit(data=np.concatenate((interp_cdf_1, interp_cdf_0)), x=x_axis, params=params)

        y_axis = joint_model(x_axis, **fit_res.best_values)
        ideal_dict = deepcopy(fit_res.best_values)
        ideal_dict["mmt_relax"] = 0
        ideal_dict["thermal_pop"] = 0

        y_ideal = joint_model(x_axis, **ideal_dict)
        f_asg_ideal = np.max(np.abs(y_ideal[: len(y_ideal) // 2] - y_ideal[len(y_ideal) // 2 :]))
        f_avg_ideal = (100 + f_asg_ideal) / 2

        fitted_data = {}

        fitted_data["fitted_values"] = deepcopy(fit_res.best_values)
        fitted_data["f_avg_discr"] = f_avg_ideal
        fitted_data["f_avg"] = f_avg
        fitted_data["x_axis"] = x_axis
        fitted_data["y_axis"] = y_axis
        fitted_data["us"] = [u_0, u_1]
        fitted_data["cdfs"] = [cdf_0, cdf_1]
        fitted_data["thresholds"] = [threshold, threshold_d]
        self.fitted_data = fitted_data
        return fitted_data

    def plot(self):
        """Method used to plot the results of an experiment.

        By default this method creates a figure with size (15, 4) containing three subplots:
        - An histogram of the measured states for diferent values of voltage
        - A plot of the CDF curves with the best threshold found
        - A 2D histogram of the distribution of measured states

        Returns:
            matplotlib.figure: contains the three subplots
        """
        if not hasattr(self, "fitted_data"):
            raise ValueError("The fitted data results must be computed before plotting.\nPlease call ``fit`` first.")
        # Prepare data
        I_0, Q_0 = np.real(self.post_proccessed_results[0]), np.imag(self.post_proccessed_results[0])
        I_1, Q_1 = np.real(self.post_proccessed_results[1]), np.imag(self.post_proccessed_results[1])
        center_0_i, center_0_q = np.mean(I_0), np.mean(Q_0)
        center_1_i, center_1_q = np.mean(I_1), np.mean(Q_1)

        dist_i = center_1_i - center_0_i
        dist_q = center_1_q - center_0_q
        theta = np.arctan2(dist_q, dist_i)

        fig, axs = plt.subplots(1, 3, figsize=(15, 4))
        # Plot histogram
        ax = axs[0]
        _ = ax.hist(self.fitted_data["us"][0], bins=101, alpha=0.5, label="|1>")
        _ = ax.hist(self.fitted_data["us"][1], bins=101, alpha=0.5, label="|0>")
        mnt_relax = self.fitted_data["fitted_values"]["mmt_relax"]
        thermal_pop = self.fitted_data["fitted_values"]["thermal_pop"]
        ax.set_xlabel("Integrated Voltage (a.u.)")
        ax.set_ylabel("Counts")
        ax.set_title(f"Mmt relaxation={100*mnt_relax:.1f} % | Thermal pop={100*thermal_pop:.1f} %")

        # Plot curves
        ax = axs[1]
        threshold_d = self.fitted_data["thresholds"][1]
        ax.plot(self.fitted_data["cdfs"][0], np.linspace(0, 100, 101), "o", label="|1>", alpha=0.3)
        ax.plot(
            self.fitted_data["x_axis"],
            self.fitted_data["y_axis"][len(self.fitted_data["y_axis"]) // 2 :],
            "--",
            label="Fit |1>",
            color="purple",
        )
        ax.plot(self.fitted_data["cdfs"][1], np.linspace(0, 100, 101), "o", label="|0>", alpha=0.3)
        ax.plot(
            self.fitted_data["x_axis"],
            self.fitted_data["y_axis"][: len(self.fitted_data["y_axis"]) // 2],
            "--",
            label="Fit |0>",
            color="r",
        )
        ax.axvline(self.fitted_data["thresholds"][0], linestyle="--", color="k", label=f"Threshold={threshold_d:.5f}")
        f_avg = self.fitted_data["f_avg"]
        f_avg_ideal = self.fitted_data["f_avg_discr"]
        ax.set_title(f"F_avg = {f_avg:.1f} % | F_discr = {f_avg_ideal:.1f} %")
        ax.legend()
        ax.set_ylabel("CDF (%)")

        # Plot 2D histogram
        ax = axs[2]
        ax.set_title(f"Theta= {theta * 180 / np.pi} deg")
        ax.hist2d(np.concatenate((I_0, I_1)), np.concatenate((Q_0, Q_1)), bins=51)

        return fig
