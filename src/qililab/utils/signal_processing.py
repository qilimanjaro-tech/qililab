"""Signal processing module."""

from typing import Tuple

import numpy as np
import numpy.typing as npt


def demodulate(
    i: npt.NDArray[np.float32], q: npt.NDArray[np.float32], frequency: float, phase_offset: float
) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    time = np.arange(len(i)) * 1e-9
    cosalpha = np.cos(2 * np.pi * frequency * time + phase_offset)
    sinalpha = np.sin(2 * np.pi * frequency * time + phase_offset)
    mod_matrix = np.sqrt(2) * np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
    i_demod, q_demod = np.transpose(np.einsum("abt,bt->ta", mod_matrix, [i, q]))
    return i_demod, q_demod
