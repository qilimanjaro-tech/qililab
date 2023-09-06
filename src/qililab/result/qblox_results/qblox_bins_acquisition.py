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

""" Qblox Bin Acquisition Result """

from dataclasses import dataclass

import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisition import Acquisition


@dataclass
class QbloxBinAcquisition(Acquisition):
    """Qblox Bin Acquisition normalized"""

    def _create_acquisition(self) -> pd.DataFrame:
        """transposes each of the acquired results arrays so that we have for each value
        a structure with i, q, amplitude, phase.
        """
        acquisition_dataframe = super()._create_acquisition()
        acquisition_dataframe.index.rename(RESULTSDATAFRAME.BINS_INDEX, inplace=True)
        acquisition_dataframe.reset_index(inplace=True)
        return acquisition_dataframe
