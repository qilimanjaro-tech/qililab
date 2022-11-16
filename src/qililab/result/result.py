"""Result class."""
from dataclasses import asdict, dataclass, field
from typing import List, Tuple

import pandas as pd

from qililab.constants import RUNCARD
from qililab.typings.enums import ResultName
from qililab.typings.factory_element import FactoryElement
from qililab.utils import nested_dict_to_pandas_dataframe


# FIXME: Cannot use dataclass and ABC at the same time
@dataclass
class Result(FactoryElement):
    """Result class."""

    name: ResultName = field(init=False)

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """
        return asdict(self) | {RUNCARD.NAME: self.name.value}

    def to_dataframe(self) -> pd.DataFrame:
        """
        Returns:
            DataFrame: dataframe containing all the results.
        """

        return nested_dict_to_pandas_dataframe(self.to_dict())
