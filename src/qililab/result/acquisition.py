""" Acquisition Result """

from dataclasses import dataclass, field
from typing import List

import numpy as np
import numpy.typing as npt


@dataclass
class Acquisition:
    """Acquisition normalized
    Args:
        pulse_length (int): Duration (in ns) of the pulse.
        i_values: (NDArray[numpy.float32]): I data normalized
        q_values: (NDArray[numpy.float32]): I data normalize
        amplitude_values: (NDArray[numpy.float32]): amplitude values from I/Q normalized
        phase_values: (NDArray[numpy.float32]): phase values from I/Q normalized

    """

    pulse_length: int
    i_values: npt.NDArray[np.float32]
    q_values: npt.NDArray[np.float32]
    amplitude_values: npt.NDArray[np.float32] = field(init=False)
    phase_values: npt.NDArray[np.float32] = field(init=False)
    acquisition: npt.NDArray[np.float32] = field(init=False)

    def __post_init__(self):
        """Create acquisitions"""
        self.i_values = self._normalized_data(data=self.i_values)
        self.q_values = self._normalized_data(data=self.q_values)
        self.amplitude_values = self._amplitudes(i_normalized=self.i_values, q_normalized=self.q_values)
        self.phase_values = self._phases(i_normalized=self.i_values, q_normalized=self.q_values)
        self.acquisition = self._create_acquisition()

    def _create_acquisition(self) -> npt.NDArray[np.float32]:
        """Transposes each of the acquired results arrays so that we have for each value a structure with i, q,
        amplitude, phase.
        For multiple values you may need to redefine this method.
        """
        return np.array([self.i_values, self.q_values, self.amplitude_values, self.phase_values]).transpose()

    def _normalized_data(self, data: List[float]):
        """Normalizes the given data with the integration length,
        which should be the same as the pulse length.

        Args:
            data (List[float]): I or Q data from acquisition.

        Returns:
            NDArray[flaot]: Normalized data
        """
        return np.array(data) / self.pulse_length

    def _amplitudes(self, i_normalized: npt.NDArray[np.float32], q_normalized: npt.NDArray[np.float32]):
        """Computes the amplitudes of a given I and Q data

        Args:
            i_normalized: (NDArray[numpy.float32]): I data normalized
            q_normalized: (NDArray[numpy.float32]): I data normalized

        Returns:
            NDArray[numpy.float]: amplitude
        """
        return np.sqrt(i_normalized**2 + q_normalized**2)

    def _phases(self, i_normalized: npt.NDArray[np.float32], q_normalized: npt.NDArray[np.float32]):
        """Computes the phases of a given I and Q data

        Args:
            i_normalized: (NDArray[numpy.float32]): I data normalized
            q_normalized: (NDArray[numpy.float32]): I data normalized

        Returns:
            NDArray[numpy.float]: amplitude
        """
        return np.arctan2(q_normalized, i_normalized)
