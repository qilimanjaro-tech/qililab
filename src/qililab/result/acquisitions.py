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

""" Acquisitions Result """

from dataclasses import dataclass, field

import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisition import Acquisition
from qililab.utils.dataframe_manipulation import concatenate_creating_new_name_index


@dataclass
class Acquisitions:
    """Acquisitions Results
    Args:
        acquisitions (list[Acquisition]): list of all the acquisition results

    """

    _acquisitions: list[Acquisition] = field(init=False)
    data_dataframe_indices: set[str] = field(init=False, default_factory=set)

    def acquisitions(self) -> pd.DataFrame:
        """return the acquisitions with a structure
        I, Q, Amplitude, Phase
        """
        acquisition_list = [acquisition.acquisition for acquisition in self._acquisitions]

        return concatenate_creating_new_name_index(
            dataframe_list=acquisition_list, new_index_name=RESULTSDATAFRAME.ACQUISITION_INDEX
        )

    def probabilities(self) -> dict[str, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError
