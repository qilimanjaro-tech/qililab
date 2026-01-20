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

import functools
import operator

import matplotlib.pyplot as plt
import numpy as np


def _round_to_fixed_point_accuracy(x, accuracy=2**-15):
    return np.round(x / accuracy) * accuracy


def convert_integration_weights(integration_weights, ntuples=100, accuracy=2**-15, plot=False):
    """Convert per-cycle integration weights to (weight, time_ns) tuples.

    Each sample corresponds to a 4 ns clock cycle. This can be used to convert
    the old format (up to QOP 1.10) to the tuple format introduced in QOP 1.20.

    Args:
        integration_weights (list[float]): Integration weights per 4 ns sample.
        ntuples (int): Maximum number of tuples to return. If the generated list
            is too long, it is compressed with `compress_integration_weights`.
        accuracy (float): Fixed-point rounding accuracy. Defaults to 2**-15,
            matching the OPX integration-weights precision.
        plot (bool): Whether to plot weights before and after conversion.

    Returns:
        list[tuple[float, int]]: Integration weights as (weight, time_ns) tuples.
    """
    integration_weights = np.array(integration_weights)
    integration_weights = _round_to_fixed_point_accuracy(integration_weights, accuracy)
    changes_indices = np.nonzero(np.abs(np.diff(integration_weights)) > 0)[0].tolist()
    prev_index = -1
    new_integration_weights = []
    for curr_index in [*changes_indices, len(integration_weights) - 1]:
        constant_part = (
            integration_weights[curr_index].tolist(),
            round(4 * (curr_index - prev_index)),
        )
        new_integration_weights.append(constant_part)
        prev_index = curr_index

    new_integration_weights = compress_integration_weights(new_integration_weights, max_length=ntuples, plot=plot)

    return new_integration_weights


def compress_integration_weights(integration_weights, max_length=100, plot=False):
    """Compress (weight, time_ns) tuples to a list shorter than `max_length`.

    Compression iteratively finds the closest pair of weights and merges them
    using a time-weighted average.

    Args:
        integration_weights (list[tuple[float, int]]): Weights to be compressed.
        max_length (int): Maximum list length required.
        plot (bool): Whether to plot weights before and after compression.

    Returns:
        list[tuple[float, int]]: Compressed list of integration weights.
    """
    integration_weights_before = integration_weights
    integration_weights = np.array(integration_weights)
    while len(integration_weights) > max_length:
        diffs = np.abs(np.diff(integration_weights, axis=0)[:, 0])
        min_diff = np.min(diffs)
        min_diff_indices = np.nonzero(diffs == min_diff)[0][0]
        times1 = integration_weights[min_diff_indices, 1]
        times2 = integration_weights[min_diff_indices + 1, 1]
        weights1 = integration_weights[min_diff_indices, 0]
        weights2 = integration_weights[min_diff_indices + 1, 0]
        integration_weights[min_diff_indices, 0] = (weights1 * times1 + weights2 * times2) / (times1 + times2)
        integration_weights[min_diff_indices, 1] = times1 + times2
        integration_weights = np.delete(integration_weights, min_diff_indices + 1, 0)
    integration_weights = list(
        zip(
            integration_weights.T[0].tolist(),
            integration_weights.T[1].astype(int).tolist(),
        )
    )
    if plot:
        plt.figure()
        plot_integration_weights(integration_weights_before, label="Original")
        plot_integration_weights(integration_weights, label="Compressed")
        plt.show()
    return integration_weights


def plot_integration_weights(integration_weights, label=None):
    """Plot integration weights in units of ns for either supported format.

    Args:
        integration_weights (list[tuple[float, int]] | list[float]): Weights in
            tuple format or per-sample float format.
        label (str | None): Optional legend label.

    Raises:
        RuntimeError: If the input format is not recognized.
    """

    if isinstance(integration_weights[0], tuple):
        a = [[i[0]] * i[1] for i in integration_weights]
        unpacked_weights = functools.reduce(operator.iadd, a, [])
    elif isinstance(integration_weights[0], float):
        a = [[i] * 4 for i in integration_weights]
        unpacked_weights = functools.reduce(operator.iadd, a, [])
    else:
        raise RuntimeError("Unknown input")

    plt.plot(unpacked_weights, label=label)
    if label is not None:
        plt.legend()
