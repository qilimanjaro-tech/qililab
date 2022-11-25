""" Qblox Bin Acquisition Result """

from dataclasses import dataclass

import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisition import Acquisition


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
