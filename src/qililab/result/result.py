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

"""Result class."""
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from qililab.result.counts import Counts
from qililab.typings.enums import ResultName
from qililab.typings.factory_element import FactoryElement
from qililab.utils import nested_dict_to_pandas_dataframe


class Result(FactoryElement, ABC):
    """Abstract class used to hold the results of a single execution."""

    name: ResultName
    data_dataframe_indices: set[str]

    def probabilities(self) -> dict[str, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            dict[str, float]: Dictionary containing the quantum states as the keys of the dictionary, and the
                probabilities obtained for each state as the values of the dictionary.
        """
        return self.counts_object().probabilities()

    def counts_object(self) -> Counts:
        """Returns a Counts object containing the amount of times each state was measured.

        Raises:
            NotImplementedError: Not implemented.

        Returns:
            Counts: Counts object containing the amount of times each state was measured.
        """
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """

    def to_dataframe(self) -> pd.DataFrame:
        """
        Returns:
            DataFrame: dataframe containing all the results.
        """

        return nested_dict_to_pandas_dataframe(self.to_dict())

    @property
    @abstractmethod
    def array(self) -> np.ndarray:
        """Returns the results in a numpy array format.

        Returns:
            np.ndarray: Numpy array containing the results.
        """
