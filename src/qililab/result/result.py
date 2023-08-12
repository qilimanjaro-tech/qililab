"""Result class."""
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from qililab.result.counts import Counts
from qililab.typings.enums import ResultName
from qililab.typings.factory_element import FactoryElement
from qililab.utils import nested_dict_to_pandas_dataframe


class Result(FactoryElement, ABC):
    """Result class."""

    name: ResultName
    data_dataframe_indices: set[str]

    def probabilities(self) -> dict[str, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return self.counts().probabilities()

    def counts(self) -> Counts:
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
