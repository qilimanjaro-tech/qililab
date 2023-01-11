"""Signal processing module."""

from typing import Tuple

import numpy as np
import numpy.typing as npt


def demodulate(
    i: npt.NDArray[np.float32], q: npt.NDArray[np.float32], frequency: float, phase_offset: float
) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """Demodulates an (i, q) signal with a certain frequency and phase offset.

    Args:
        i (npt.NDArray[np.float32]): I component of the signal.
        q (npt.NDArray[np.float32]): Q component of the signal.
        frequency (float): demodulation frequency.
        phase_offset (float): demodulation phase offset.

    Returns:
        Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]: Demodulated signal.
    """
    time = np.arange(len(i)) * 1e-9
    cosalpha = np.cos(2 * np.pi * frequency * time + phase_offset)
    sinalpha = np.sin(2 * np.pi * frequency * time + phase_offset)
    mod_matrix = np.sqrt(2) * np.array([[cosalpha, -sinalpha], [sinalpha, cosalpha]])
    i_demod, q_demod = np.transpose(np.einsum("abt,bt->ta", mod_matrix, [i, q]))
    return i_demod, q_demod


def modulate(
    i: npt.NDArray[np.float32], q: npt.NDArray[np.float32], frequency: float, phase_offset: float
) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """Modulates an (i, q) signal with a certain frequency and phase offset.

    Args:
        i (npt.NDArray[np.float32]): I component of the signal.
        q (npt.NDArray[np.float32]): Q component of the signal.
        frequency (float): modulation frequency.
        phase_offset (float): modulation phase offset.

    Returns:
        Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]: Modulated signal.
    """
    time = np.arange(len(i)) * 1e-9
    cosalpha = np.cos(2 * np.pi * frequency * time + phase_offset)
    sinalpha = np.sin(2 * np.pi * frequency * time + phase_offset)
    mod_matrix = (1.0 / np.sqrt(2)) * np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
    i_mod, q_mod = np.transpose(np.einsum("abt,bt->ta", mod_matrix, [i, q]))
    return i_mod, q_mod
