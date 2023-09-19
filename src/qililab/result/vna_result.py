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

"""VNA Result class."""
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class VNAResult(Result):  # TODO: Remove this class (it is useless)
    """VNAResult class."""

    name = ResultName.VECTOR_NETWORK_ANALYZER
    data: npt.NDArray[np.float32]

    def acquisitions(self) -> np.ndarray:
        """Return acquisition values."""
        return self.data

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError

    @property
    def array(self) -> np.ndarray:
        return np.array([])

    def to_dict(self) -> dict:
        return {}
