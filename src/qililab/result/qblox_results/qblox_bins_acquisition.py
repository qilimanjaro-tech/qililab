""" Qblox Bin Acquisition Result """

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from qililab.result.acquisition import Acquisition
import pandas as pd


@dataclass
class QbloxBinAcquisition(Acquisition):
    """Qblox Bin Acquisition normalized"""

    def _create_acquisition(self) -> pd.DataFrame:
        """transposes each of the acquired results arrays so that we have for each value
        a structure with i, q, amplitude, phase.
        """
        return pd.DataFrame({
            "i_values": self.i_values,
            "q_values": self.q_values,
            "amplitude_values": self.amplitude_values,
            "phase_values": self.phase_values,
        })
