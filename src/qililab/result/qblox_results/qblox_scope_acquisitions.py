""" Qblox Scope Acquisitions Result """

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from qililab.result.acquisition import Acquisition
from qililab.result.acquisitions import Acquisitions
from qililab.result.qblox_results.scope_data import ScopeData


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
        i_values = np.array(self.scope.path0.data, dtype=np.float32)
        q_values = np.array(self.scope.path1.data, dtype=np.float32)

        self._acquisitions = [Acquisition(pulse_length=self.pulse_length, i_values=i_values, q_values=q_values)]

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        acquisitions = self.acquisitions()
        probs: List[Tuple[float, float]] = []
        # TODO: Integrate data when scope
        probs.extend((acq[0][-1], acq[0][-1]) for acq in acquisitions)
        return probs
