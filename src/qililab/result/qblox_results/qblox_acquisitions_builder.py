""" Qblox Acquisitions Builder """
from qililab.result.qblox_results.bin_data import BinData
from qililab.result.qblox_results.qblox_bins_acquisitions import QbloxBinsAcquisitions
from qililab.result.qblox_results.qblox_scope_acquisitions import QbloxScopeAcquisitions
from qililab.result.qblox_results.scope_data import ScopeData


class QbloxAcquisitionsBuilder:
    """Qblox Acquisitions Results Builder"""

    @classmethod
    def get_scope(cls, pulse_length: int, qblox_raw_results: dict) -> QbloxScopeAcquisitions | None:
        """Cast dictionaries to their corresponding class."""
        if cls._is_scope_data_available(qblox_raw_results=qblox_raw_results):
            scope_data = qblox_raw_results[0]["scope"]
            return QbloxScopeAcquisitions(pulse_length=pulse_length, scope=ScopeData(**scope_data))
        return None

    @classmethod
    def get_bins(cls, pulse_length: int, qblox_raw_results: list[dict]) -> QbloxBinsAcquisitions:
        """Cast dictionaries to their corresponding class."""
        bins_data = [sequencer_acq["bins"] for sequencer_acq in qblox_raw_results]
        return QbloxBinsAcquisitions(pulse_length=pulse_length, bins=[BinData(**bin_data) for bin_data in bins_data])

    @classmethod
    def _is_scope_data_available(cls, qblox_raw_results: dict) -> bool:
        """Checks if there is scope data available from sequencer 0.

        Returns:
            bool: True if scope data available, False otherwise.
        """
        return any(qblox_raw_results[0]["scope"]["path0"]["data"])
