import os

import lmfit
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import numpy as np

import qililab as ql
from qililab import Drag
from qililab.platform import Platform
from qililab.automatic_calibration import CalibrationNode, Controller
from qililab.automatic_calibration.calibration_utils.calibration_utils import get_raw_data, get_iq_from_raw, plot_iq, plot_fit, get_timestamp, visualize_calibration_graph

from qibo.models import Circuit
from qibo.gates import M
from qililab.pulse.circuit_to_pulses import CircuitToPulses
import yaml


##################################### ANALYSIS ##################################################

rabi_values = {"start": 0,
               "stop": 0.25,
               "step": (0.25-0)/31 # It's written like this because it's derived from a np.linspace definition
               }

with open("./tests/automatic_calibration/data/test_sequence_pulse_schedule_1_node/1693241829.041737/rabi_1.yml", "r") as f:
    results = yaml.safe_load(f)
experiment_name= "rabi"
parameter= "amplitude" 
sweep_values = np.arange(rabi_values["start"], rabi_values["stop"], rabi_values["step"])
plot_figure_path = "qililab/tests/automatic_calibration/IS_IT_RIGHT.png"
fit_quadrature="i"

"""
Analyzes the Rabi experiment data.

Args:
    results: Where the data experimental is stored. If it's a string, it represents the path of the yml file where the data is. 
                Otherwise it's a list with only 1 element. This element is a dictionary containing the data.
                For now this only supports experiment run on QBlox hardware. The dictionary is a standard structure in which the data 
                is stored by the QBlox hardware. For more details see this documentation: 
                https://qblox-qblox-instruments.readthedocs-hosted.com/en/master/api_reference/pulsar.html#qblox_instruments.native.Pulsar.get_acquisitions
                The list only has 1 element because each element represents the acquisitions dictionary of one readout bus, 
                and for the moment multiple readout buses are not supported.
    plot_figure_path (str): The path where the plot figure PNG file will be saved.
    experiment_name: The name of the experiment of which this function will analyze the data. The name is used to label the figure that 
                        this function will produce, which will contain the plot.
                
Returns:
    fitted_pi_pulse_amplitude (int)
"""

# Get flattened data and shape it
this_shape = len(sweep_values)
i = np.array(results[0])
q = np.array(results[1])
i = i.reshape(this_shape)
q = q.reshape(this_shape)

fit_signal = i if fit_quadrature == "i" else q
fit_signal_idx = 0 if fit_quadrature == "i" else 1

# Fit
def sinus(x, a, b, c, d):
    return a * np.sin(2 * np.pi * b * np.array(x) - c) + d

# TODO: hint values are pretty random, they should be tuned better. Trial and error seems to be the best way.
mod = lmfit.Model(sinus)
mod.set_param_hint("a", value=0.3, vary=True, min=0)
mod.set_param_hint("b", value=0, vary=True)
mod.set_param_hint("c", value=0, vary=True)
mod.set_param_hint("d", value=1 / 2, vary=True, min=0)

params = mod.make_params()
fit = mod.fit(data=fit_signal, params=params, x=sweep_values)

a_value = fit.params["a"].value
b_value = fit.params["b"].value
c_value = fit.params["c"].value
d_value = fit.params["d"].value

optimal_parameters = [a_value, b_value, c_value, d_value]
fitted_pi_pulse_amplitude = np.abs(1 / (2 * optimal_parameters[1]))

# Plot
title_label = experiment_name
fig, axes = plot_iq(sweep_values, i, q, title_label, parameter)
# plot_fit(
#     sweep_values, optimal_parameters, axes[fit_signal_idx], fitted_pi_pulse_amplitude
# )

#plt.plot(sweep_values, np.abs(i+1j*q), title_label, parameter)

# The user can change this to save to a custom location
fig.savefig(plot_figure_path)

#return fitted_pi_pulse_amplitude
