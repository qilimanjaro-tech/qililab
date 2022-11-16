"""QbloxResult class."""
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
import pandas as pd

from qililab.constants import QBLOXRESULT, RUNCARD
from qililab.result.qblox_results.qblox_acquisitions_builder import (
    QbloxAcquisitionsBuilder,
)
from qililab.result.qblox_results.qblox_bins_acquisitions import QbloxBinsAcquisitions
from qililab.result.qblox_results.qblox_scope_acquisitions import QbloxScopeAcquisitions
from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class QbloxResult(Result):
    """QbloxResult class. Contains the binning acquisition results obtained from the `Pulsar.get_acquisitions` method.

    The input to the constructor should be a dictionary with the following structure:

    - integration: integration data.
        - path_0: input path 0 integration result bin list.
        - path_1: input path 1 integration result bin list.
    - threshold: threshold result bin list.
    - valid: list of valid indications per bin.
    - avg_cnt: list of number of averages per bin.
    Args:
        pulse_length (int): Duration (in ns) of the pulse.
    """

    name = ResultName.QBLOX
    pulse_length: int | np.number
    scope: dict | None = None
    bins: List[dict] | None = None
    qblox_acquisitions: QbloxScopeAcquisitions | QbloxBinsAcquisitions = field(init=False)

    def __post_init__(self):
        """Create a Qblox Acquisition class from dictionaries data"""
        self.qblox_acquisitions = QbloxAcquisitionsBuilder.get(
            pulse_length=self.pulse_length, scope=self.scope, bins=self.bins
        )

    def acquisitions(self) -> pd.DataFrame:
        """Return acquisition values.

        Returns:
            Tuple[float]: I, Q, amplitude and phase.
        """
        return self.qblox_acquisitions.acquisitions()

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return self.qblox_acquisitions.probabilities()

    @property
    def shape(self) -> List[int]:
        """QbloxResult 'shape' property.

        Returns:
            List[int]: Shape of the acquisitions.
        """
        return list(self.acquisitions().shape)

    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """

        results_dict: dict[str, str | int | dict | List[dict]] = {
            RUNCARD.NAME: self.name.value,
            QBLOXRESULT.PULSE_LENGTH: self.pulse_length.item()
            if isinstance(self.pulse_length, np.number)
            else self.pulse_length,
        }

        if self.scope is not None:
            results_dict |= {
                QBLOXRESULT.SCOPE: self.scope,
            }
        if self.bins is not None:
            results_dict |= {
                QBLOXRESULT.BINS: self.bins,
            }
        return results_dict

    def __eq__(self, other: object) -> bool:
        """compare two Qblox Results"""
        return (
            (
                self.name == other.name
                and self.pulse_length == other.pulse_length
                and self.scope == other.scope
                and self.bins == other.bins
            )
            if isinstance(other, QbloxResult)
            else False
        )
