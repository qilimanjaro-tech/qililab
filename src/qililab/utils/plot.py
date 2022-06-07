"""plot function"""
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from qililab.result import Results
from qililab.utils.loop import Loop

DATA = np.array(["I", "Q", "amplitude", "phase"])


def plot(result: Results, loop: Loop, idx: List[int] | None = None):
    """Plot the results obtained from executing a sequence of pulses.

    Args:
        result (Result): Result object.
        loop (Loop | None): Loop object.
        idx (int | List[int]): Indeces of the data to plot. Available values are 0-3, corresponding to
        I, Q, amplitude and phase data.
    """
    if idx is None:
        idx = [0, 1, 2, 3]

    result_values = result.acquisitions()

    if loop.num_loops == 1:
        _, axes = plt.subplots(ncols=1, nrows=len(idx), figsize=(13, 4 * len(idx)))
        for axis, values, label in zip(axes, result_values[idx], DATA[idx]):
            axis.plot(loop.range, values)
            axis.set_xlabel(loop.parameter)
            axis.set_ylabel(label)
            axis.set_xticks(loop.range[::4])
            axis.grid(which="both")

    elif loop.loop is not None:
        _, axes = plt.subplots(ncols=2, nrows=len(idx) // 2, figsize=(13, 13))
        for axis, values, label in zip(axes, result_values[idx], DATA[idx]):
            axis.pcolormesh(loop.loop.range, loop.range, values, shading="nearest")
            axis.set_ylabel(loop.parameter)
            axis.set_xlabel(loop.loop.parameter)
            axis.colorbar()
            axis.show()

    plt.tight_layout()
    plt.show()
