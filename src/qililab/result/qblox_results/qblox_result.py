"""QbloxResult class."""
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Set, Tuple

import numpy as np
import numpy.typing as npt
import pandas as pd

from qililab.constants import QBLOXRESULT, RUNCARD
from qililab.instruments.qblox.constants import SCOPE_ACQ_MAX_DURATION
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
    qblox_raw_results: List[dict]
    qblox_bins_acquisitions: QbloxBinsAcquisitions = field(init=False, compare=False)
    qblox_scope_acquisitions: QbloxScopeAcquisitions | None = field(init=False, compare=False)

    def __post_init__(self):
        """Create a Qblox Acquisition class from dictionaries data"""
        self.qblox_scope_acquisitions = QbloxAcquisitionsBuilder.get_scope(
            pulse_length=self.pulse_length, qblox_raw_results=self.qblox_raw_results
        )
        self.qblox_bins_acquisitions = QbloxAcquisitionsBuilder.get_bins(
            pulse_length=self.pulse_length, qblox_raw_results=self.qblox_raw_results
        )
        self._qblox_scope_acquisition_copy = deepcopy(self.qblox_bins_acquisitions)
        self.data_dataframe_indices = self.qblox_acquisitions.data_dataframe_indices

    def _demodulated_scope(self, frequency: float, phase_offset: float = 0.0) -> QbloxScopeAcquisitions:
        """Returns the scope acquisitions demodulated in the given frequency with the given phase offset.

        Returns:
            QbloxScopeAcquisitions: demodulated scope acquisitions."""
        if self.qblox_scope_acquisitions is None:
            raise ValueError("Scope acquisitions cannot be demodulated because it doesn't exist.")
        return self.qblox_scope_acquisitions.demodulated(frequency=frequency, phase_offset=phase_offset)

    def _integrated_scope(
        self, integrate_from: int = 0, integrate_to: int = SCOPE_ACQ_MAX_DURATION
    ) -> QbloxScopeAcquisitions:
        if self.qblox_scope_acquisitions is None:
            raise ValueError("Scope acquisitions cannot be integrated because it doesn't exist.")
        return self.qblox_scope_acquisitions.integrated(integrate_from=integrate_from, integrate_to=integrate_to)

    def acquisitions(self) -> pd.DataFrame:
        """Return acquisition values.

        Returns:
            NDArray[numpy.float32]: I, Q, amplitude and phase.
        """
        return self.qblox_bins_acquisitions.acquisitions()

    def acquisitions_scope(
        self,
        demod_freq: float = 0.0,
        demod_phase_offset: float = 0.0,
        integrate: bool = False,
        integration_range: Tuple[int, int] = (0, SCOPE_ACQ_MAX_DURATION),
    ) -> npt.NDArray[np.float32] | None:
        acquisitions = self.qblox_scope_acquisitions
        if acquisitions is None:
            return None
        if demod_freq != 0.0:
            acquisitions = self._demodulated_scope(frequency=demod_freq, phase_offset=demod_phase_offset)
        if integrate:
            integrate_from, integrate_to = integration_range
            acquisitions = self._integrated_scope(integrate_from=integrate_from, integrate_to=integrate_to)
        return acquisitions

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return self.qblox_bins_acquisitions.probabilities()

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
        return {
            RUNCARD.NAME: self.name.value,
            QBLOXRESULT.PULSE_LENGTH: self.pulse_length.item()
            if isinstance(self.pulse_length, np.number)
            else self.pulse_length,
        } | {QBLOXRESULT.RAW: self.qblox_raw_results}
