"""Drive amplitude calibration via Rabi experiment
"""
import json
import os

import hwdatatools.save_load as save_tools
import lmfit
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from hwdatatools import (
    AllXYExperiment,
    CalibrationPoints,
    CzConditionalExperiment,
    CzConditionalSNZExperimentB,
    DragCoefficient,
    FlippingExperiment,
    Rabi,
    Ramsey,
)
from hwdatatools.save_load import (
    get_last_results,
    get_last_timestamp,
    get_timestamp_from_file,
    load_yaml_to_pd,
    save_figure_from_exp,
)
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

import qililab as ql
import qililab.automatic_calibration.calibration_utils.calibration_utils as calibration_utils
import qililab.automatic_calibration.calibration_utils.yaml_editor as ye
from qililab.automatic_calibration.experiment import Experiment
from qililab.experiment.portfolio.fitting_models import Cos as CosModel


class RabiExperiment(Experiment):
    def __init__(self) -> None:
        pass

    def rabi_Experiment(self):
        # Run the experiment with a QProgram
        pass

    def analyze_rabi(datapath=None, fit_quadrature="i", label=""):
        """
        Analyzes the Rabi experiment data.

        Args:
            datapath (str, optional): Path to the calibration data YAML file. If not provided, the last results file is used.
        """

        # Get the path of the raw data file
        timestamp = get_last_timestamp()
        if datapath is None:
            datapath = get_last_results()
        parent_directory = os.path.dirname(datapath)
        figure_filepath = os.path.join(parent_directory, "Rabi.PNG")

        # Get the actual raw data file
        data_raw = calibration_utils.get_raw_data(datapath)

        # This is experiment specific and will go differently for every scheme of sweeps for tune-up
        # TODO: make not harcoded if possible
        amplitude_loop_values = np.array(data_raw["loops"][0]["values"])
        swept_variable = data_raw["loops"][0]["parameter"]
        this_shape = len(amplitude_loop_values)

        # Get flattened data and shape it
        i, q = calibration_utils.get_iq_from_raw(data_raw)
        i = i.reshape(this_shape)
        q = q.reshape(this_shape)

        fit_signal = i if fit_quadrature == "i" else q
        fit_signal_idx = 0 if fit_quadrature == "i" else 1

        # fit
        # WHAT IN GOD'S NAME IS THIS
        def sinus(x, a, b, c, d):
            return a * np.sin(2 * np.pi * b * np.array(x) - c) + d

        a_guess = np.amax(fit_signal) - np.amin(fit_signal)

        # Sinus fit
        mod = lmfit.Model(sinus)
        mod.set_param_hint("a", value=1 / 2, vary=True, min=0)
        mod.set_param_hint("b", value=0, vary=True)
        mod.set_param_hint("c", value=0, vary=True)
        mod.set_param_hint("d", value=1 / 2, vary=True, min=0)

        params = mod.make_params()
        fit = mod.fit(data=fit_signal, params=params, x=amplitude_loop_values)

        a_value = fit.params["a"].value
        b_value = fit.params["b"].value
        c_value = fit.params["c"].value
        d_value = fit.params["d"].value

        print(fit.params)

        popt = [a_value, b_value, c_value, d_value]
        fitted_pi_pulse_amplitude = np.abs(1 / (2 * popt[1]))

        # # fit
        # initial_guess = None  # (amp_guess,freq_guess,phase_guess,offset_guess)
        # fit_signal = i if fit_quadrature == "i" else q
        # fit_signal_idx = 0 if fit_quadrature == "i" else 1
        # popt = fit_rabi(amplitude_loop_values, fit_signal, initial_guess)
        # fitted_pi_pulse_amplitude = np.abs(1 / (2 * popt[1]))

        # plot
        title_label = f"{timestamp} {label}"
        fig, axes = calibration_utils.plot_iq(amplitude_loop_values, i, q, title_label, swept_variable)
        calibration_utils.plot_fit(amplitude_loop_values, popt, axes[fit_signal_idx], fitted_pi_pulse_amplitude)
        # print(figure_filepath)
        fig.savefig(figure_filepath, format="PNG")
        return fitted_pi_pulse_amplitude
        # At the end we have a value that we can upload to a yaml file, which contains all the calibration parameters.
