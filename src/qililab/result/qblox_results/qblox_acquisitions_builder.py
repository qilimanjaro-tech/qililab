""" Qblox Acquisitions Builder """


from typing import List

from qililab.result.qblox_results.bin_data import BinData
from qililab.result.qblox_results.qblox_bins_acquisitions import QbloxBinsAcquisitions
from qililab.result.qblox_results.qblox_scope_acquisitions import QbloxScopeAcquisitions
from qililab.result.qblox_results.scope_data import ScopeData


class QbloxAcquisitionsBuilder:
    """Qblox Acquisitions Results Builder"""

    def __post_init__(self):
        """Cast dictionaries to their corresponding class."""

    @classmethod
    def get(
        cls, pulse_length: int, scope: dict | None, bins: List[dict] | None = None
    ) -> QbloxScopeAcquisitions | QbloxBinsAcquisitions:
        """Cast dictionaries to their corresponding class."""
        if scope is not None:
            return QbloxScopeAcquisitions(pulse_length=pulse_length, scope=ScopeData(**scope))
        if bins is not None:
            return QbloxBinsAcquisitions(pulse_length=pulse_length, bins=[BinData(**bin) for bin in bins])
        raise ValueError("Neither 'scope' or 'bins' are defined. One of them MUST be defined.")
