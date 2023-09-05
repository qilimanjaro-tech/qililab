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

""" Acquisition Result """

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt
import pandas as pd

from qililab.constants import RESULTSDATAFRAME


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

    integration_length: int
    i_values: npt.NDArray[np.float32]
    q_values: npt.NDArray[np.float32]
    amplitude_values: npt.NDArray[np.float32] = field(init=False)
    phase_values: npt.NDArray[np.float32] = field(init=False)
    acquisition: pd.DataFrame = field(init=False)
    data_dataframe_indices: set = field(init=False, default_factory=set)

    def __post_init__(self):
        """Create acquisitions"""
        self.i_values = self._normalized_data(data=self.i_values)
        self.q_values = self._normalized_data(data=self.q_values)
        self.amplitude_values = self._amplitudes(i_normalized=self.i_values, q_normalized=self.q_values)
        self.phase_values = self._phases(i_normalized=self.i_values, q_normalized=self.q_values)
        self.acquisition = self._create_acquisition()
        self.data_dataframe_indices = {
            RESULTSDATAFRAME.I,
            RESULTSDATAFRAME.Q,
            RESULTSDATAFRAME.AMPLITUDE,
            RESULTSDATAFRAME.PHASE,
        }

    def _create_acquisition(self) -> pd.DataFrame:
        """Transposes each of the acquired results arrays so that we have for each value a structure with i, q,
        amplitude, phase.
        For multiple values you may need to redefine this method.
        """

        return pd.DataFrame(
            {
                RESULTSDATAFRAME.I: self.i_values,
                RESULTSDATAFRAME.Q: self.q_values,
                RESULTSDATAFRAME.AMPLITUDE: self.amplitude_values,
                RESULTSDATAFRAME.PHASE: self.phase_values,
            }
        )

    def _normalized_data(self, data: npt.NDArray):
        """Normalizes the given data with the integration length,
        which should be the same as the pulse length.

        Args:
            data (list[float]): I or Q data from acquisition.

        Returns:
            NDArray[flaot]: Normalized data
        """
        return np.array(data) / self.integration_length

    def _amplitudes(self, i_normalized: npt.NDArray[np.float32], q_normalized: npt.NDArray[np.float32]):
        """Computes the amplitudes of a given I and Q data

        Args:
            i_normalized: (NDArray[numpy.float32]): I data normalized
            q_normalized: (NDArray[numpy.float32]): I data normalized

        Returns:
            NDArray[numpy.float]: amplitude
        """
        return 20 * np.log10(np.sqrt(i_normalized**2 + q_normalized**2))

    def _phases(self, i_normalized: npt.NDArray[np.float32], q_normalized: npt.NDArray[np.float32]):
        """Computes the phases of a given I and Q data

        Args:
            i_normalized: (NDArray[numpy.float32]): I data normalized
            q_normalized: (NDArray[numpy.float32]): I data normalized

        Returns:
            NDArray[numpy.float]: amplitude
        """
        return np.arctan2(q_normalized, i_normalized)
