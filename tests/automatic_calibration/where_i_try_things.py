# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS
# TODO: DELETE THIS

from qililab.automatic_calibration.calibration_utils.calibration_utils import get_raw_data, get_iq_from_raw, plot_iq, plot_fit
import numpy as np

import lmfit
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
from scipy.signal import find_peaks

results = "./tests/automatic_calibration/rabi.yml"
#print("HERE")
iq = get_iq_from_raw(get_raw_data(results))
i = [k[0] for k in iq[0]]
q = [k[0] for k in iq[1]]
iq_array = [i, q]    
#print(iq_array)
#pipo = [i, q]
#print(pipo)
#["qblox_raw_results"][index]["bins"]["integration"]["path0"] for item in data_raw["results"]]


def is_within_threshold(a, b, threshold):
    return b - threshold <= a <= b + threshold


tolerance = 0
random_points = [0.0166667, 0.0333333] # these are points chosen randomly from the sweep interval used in rabi.yml



fit_quadrature = 'i'

data_raw = get_raw_data("./tests/automatic_calibration/rabi.yml")
amplitude_loop_values = np.array(data_raw["loops"][0]["values"])
swept_variable = data_raw["loops"][0]["parameter"]
this_shape = len(amplitude_loop_values)

# Get flattened data and shape it
i, q = get_iq_from_raw(data_raw)
i = i.reshape(this_shape)
q = q.reshape(this_shape)

fit_signal = i if fit_quadrature == "i" else q
fit_signal_idx = 0 if fit_quadrature == "i" else 1

# Fit
def sinus(x, a, b, c, d):
    return a * np.sin(2 * np.pi * b * np.array(x) - c) + d

# TODO: hint values are pretty random, they should be tuned better. Trial and error seems to be the best way.
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

optimal_parameters = [a_value, b_value, c_value, d_value]
fitted_pi_pulse_amplitude = np.abs(1 / (2 * optimal_parameters[1]))
label = ''
# Plot
title_label = f"{label}"
fig, axes = plot_iq(amplitude_loop_values, i, q, title_label, swept_variable)
plot_fit(
    amplitude_loop_values, optimal_parameters, axes[fit_signal_idx], fitted_pi_pulse_amplitude
)
# plot_filepath = results = "./tests/automatic_calibration/drag.PNG"
# fig.savefig(plot_filepath, format="PNG")
# plot_image = mpimg.imread(plot_filepath)
# plt.imshow(plot_image)
# plt.show()
#print(1 - fit.residual.var() / np.var(fit_signal))


rabi_values = {"start": 0,
               "stop": 0.25,
               "step": (0.25-0)/31 # It's written like this because it's derived from a np.linspace definition
               }
dummy_data_path = "./tests/automatic_calibration/rabi.yml"

#print(amplitude_loop_values)
nightmare = np.arange(rabi_values["start"], rabi_values["stop"], rabi_values["step"]).tolist()
old = amplitude_loop_values.tolist()
#print(nightmare)
a = old
b = np.linspace(0, 0.25, 31).tolist()
c = [x - y for x, y in zip(a, b)]
d = [x - y for x, y in zip(a, nightmare)]
print(sum([x**2 for x in c]))
print(sum([x**2 for x in d]))
