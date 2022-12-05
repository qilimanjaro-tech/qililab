""" Qblox Scope Acquisitions Result """

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import numpy.typing as npt
import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.instruments.qblox.constants import SCOPE_ACQ_MAX_DURATION
from qililab.result.acquisition import Acquisition
from qililab.result.acquisitions import Acquisitions
from qililab.result.qblox_results.scope_data import ScopeData
from qililab.utils.signal_processing import demodulate


@dataclass
class QbloxScopeAcquisitions(Acquisitions):
    """Qblox Scope Acquisitions Result
    Args:
        scope: ScopeData
        pulse_length (int): Duration (in ns) of the pulse

    """

    scope: ScopeData
    pulse_length: int

    def __post_init__(self):
        """Create acquisitions"""
        i_values, q_values = self._iq_values()
        self._acquisitions = [Acquisition(pulse_length=self.pulse_length, i_values=i_values, q_values=q_values)]
        self.data_dataframe_indices = set().union(*[acq.data_dataframe_indices for acq in self._acquisitions])

    def demodulated(self, frequency: float, phase_offset: float = 0.0) -> QbloxScopeAcquisitions:
        """Returns a demodulated QbloxScopeAcquisitions object.

        Args:
            frequency (float): demodulation frequency
            phase_offset (float, optional): demodulation phase offset. Defaults to 0.0.

        Returns:
            QbloxScopeAcquisitions: demodulated QbloxScopeAcquisitions object.
        """
        i_values, q_values = self._iq_values()
        i_demod, q_demod = demodulate(i=i_values, q=q_values, frequency=frequency, phase_offset=phase_offset)
        common_out_of_range = self.scope.path0.out_of_range or self.scope.path1.out_of_range
        i_demod_pathdata = ScopeData.PathData(
            data=i_demod.tolist(), avg_cnt=self.scope.path0.avg_cnt, out_of_range=common_out_of_range
        )
        q_demod_pathdata = ScopeData.PathData(
            data=q_demod.tolist(), avg_cnt=self.scope.path1.avg_cnt, out_of_range=common_out_of_range
        )
        demod_scope_data = ScopeData(path0=i_demod_pathdata, path1=q_demod_pathdata)
        return QbloxScopeAcquisitions(scope=demod_scope_data, pulse_length=self.pulse_length)

    def integrated(self, integrate_from: int = 0, integrate_to: int = SCOPE_ACQ_MAX_DURATION) -> QbloxScopeAcquisitions:
        """Returns an integrated QbloxScopeAcquisitions object.

        Args:
            integrate_from (int, optional): index of the beginning of the integration. Defaults to 0.
            integrate_to (int, optional): index of the end of the integration. Defaults to SCOPE_ACQ_MAX_DURATION.

        Raises:
            IndexError: Integration range is out of bounds.
            IndexError: 'integrate_from' must be smaller than 'integrate_to'.

        Returns:
            QbloxScopeAcquisitions: integrated QbloxScopeAcquisitions object.
        """
        i_values, q_values = self._iq_values()
        if len(i_values) <= integrate_from or len(i_values) < integrate_to:
            raise IndexError("Integration range is out of bounds.")
        if integrate_from >= integrate_to:
            raise IndexError("'integrate_from' must be smaller than 'integrate_to'.")
        integrated_i = np.mean(i_values[integrate_from:integrate_to])
        integrated_q = np.mean(q_values[integrate_from:integrate_to])
        integrated_acquisitions = deepcopy(self)
        integrated_acquisitions.scope.path0.data = [integrated_i]
        integrated_acquisitions.scope.path1.data = [integrated_q]
        return integrated_acquisitions

    def _iq_values(self) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
        i_values = np.array(self.scope.path0.data, dtype=np.float32)
        q_values = np.array(self.scope.path1.data, dtype=np.float32)
        return i_values, q_values

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        acquisitions = self.acquisitions()
        probs_df = pd.DataFrame()
        probs_df[RESULTSDATAFRAME.P0] = acquisitions[RESULTSDATAFRAME.AMPLITUDE].values
        probs_df[RESULTSDATAFRAME.P1] = acquisitions[RESULTSDATAFRAME.AMPLITUDE].values
        probs_df.index.rename(RESULTSDATAFRAME.ACQUISITION_INDEX, inplace=True)
        return probs_df.iloc[-1:]
