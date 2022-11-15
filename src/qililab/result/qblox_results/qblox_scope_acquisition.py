""" Qblox Bin Acquisition Result """

from dataclasses import dataclass

from qililab.result.acquisition import Acquisition
from qililab.constants import RESULTSDATAFRAME
import pandas as pd


@dataclass
class QbloxScopeAcquisition(Acquisition):
    """Qblox Bin Acquisition normalized"""

    def _create_acquisition(self) -> pd.DataFrame:
        """transposes each of the acquired results arrays so that we have for each value
        a structure with i, q, amplitude, phase.
        """
        acquisition_dataframe = super()._create_acquisition()
        acquisition_dataframe.index.rename(RESULTSDATAFRAME.SCOPE_INDEX, inplace=True)
        return acquisition_dataframe
