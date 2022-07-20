"""plot function"""
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from qililab.constants import UNITS
from qililab.result.results import Results
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
        _ = count_zeros(num=loop.range[0])
        for axis, values, label in zip(axes, result_values[idx], DATA[idx]):
            axis.plot(loop.range, values)
            axis.set_xlabel(f"{loop.parameter.value} {UNITS.get(loop.parameter.value, None)}")
            axis.set_ylabel(label)
            axis.set_xticks(np.round(loop.range[::4], 3))
            axis.grid(which="both")

    elif loop.loop is not None:
        fig, axes = plt.subplots(ncols=2, nrows=len(idx) // 2, figsize=(13, 13))
        for axis, values, label in zip(axes.ravel(), result_values[idx], DATA[idx]):
            mappable = axis.pcolormesh(loop.loop.range, loop.range, values, shading="nearest")
            axis.set_ylabel(loop.parameter.value)
            axis.set_xlabel(loop.loop.parameter.value)
            fig.colorbar(mappable, ax=axis)

    plt.tight_layout()
    plt.show()


def count_zeros(num: float) -> int:
    """Count number of zeros of a given float.

    Args:
        num (float): Float number.

    Returns:
        int: Number of zeros.
    """
    count = 0
    while num > 1:
        count += 1
        num /= 10
    return count
