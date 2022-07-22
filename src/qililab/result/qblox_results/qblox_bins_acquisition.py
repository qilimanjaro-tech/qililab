""" Qblox Bin Acquisition Result """

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from qililab.result.acquisition import Acquisition


@dataclass
class QbloxBinAcquisition(Acquisition):
    """Qblox Bin Acquisition normalized"""

    def _create_acquisition(self) -> npt.NDArray[np.float32]:
        """transposes each of the acquired results arrays so that we have for each value
        a structure with i, q, amplitude, phase.
        """
        return np.array([self.i_values, self.q_values, self.amplitude_values, self.phase_values]).transpose().squeeze()
