""" Qblox Bin Acquisition Result """

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisition import Acquisition


@dataclass
class QbloxBinAcquisition(Acquisition):
    """Qblox Bin Acquisition normalized
    Args:
        binary_classification_values (NDArray[np.float32]): Thresholded values in case of
    """

    binary_classification_values: npt.NDArray[np.float32]

    def __post_init__(self):
        """Create acquisitions"""
        super().__post_init__()
        self.data_dataframe_indices.add(RESULTSDATAFRAME.BINARY_CLASSIFICATION)

    def _create_acquisition(self) -> pd.DataFrame:
        """transposes each of the acquired results arrays so that we have for each value
        a structure with:  bin, i, q, amplitude, phase.
        """
        acquisition_dataframe = pd.DataFrame(
            {
                RESULTSDATAFRAME.I: self.i_values,
                RESULTSDATAFRAME.Q: self.q_values,
                RESULTSDATAFRAME.AMPLITUDE: self.amplitude_values,
                RESULTSDATAFRAME.PHASE: self.phase_values,
                RESULTSDATAFRAME.BINARY_CLASSIFICATION: self.binary_classification_values,
            }
        )
        acquisition_dataframe.index.rename(RESULTSDATAFRAME.BIN, inplace=True)
        acquisition_dataframe.reset_index(inplace=True)
        return acquisition_dataframe
