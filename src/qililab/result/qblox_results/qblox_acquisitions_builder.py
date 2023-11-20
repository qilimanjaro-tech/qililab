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

""" Qblox Acquisitions Builder """
from qililab.result.qblox_results.bins_data import BinsData
from qililab.result.qblox_results.qblox_bins_acquisitions import QbloxBinsAcquisitions
from qililab.result.qblox_results.qblox_scope_acquisitions import QbloxScopeAcquisitions
from qililab.result.qblox_results.scope_data import ScopeData


class QbloxAcquisitionsBuilder:
    """Qblox Acquisitions Results Builder"""

    @classmethod
    def get_scope(cls, integration_lengths: list[int], qblox_raw_results: list[dict]) -> QbloxScopeAcquisitions | None:
        """Cast dictionaries to their corresponding class."""
        sequencer_scope = cls._get_sequencer_with_scope_data_available(qblox_raw_results)
        if sequencer_scope is not None:
            scope_data = qblox_raw_results[sequencer_scope]["scope"]
            return QbloxScopeAcquisitions(
                pulse_length=integration_lengths[sequencer_scope], scope=ScopeData(**scope_data)
            )
        return None

    @classmethod
    def get_bins(cls, integration_lengths: list[int], qblox_raw_results: list[dict]) -> QbloxBinsAcquisitions:
        """Cast dictionaries to their corresponding class."""
        bins_data = [sequencer_acq["bins"] for sequencer_acq in qblox_raw_results]
        return QbloxBinsAcquisitions(
            integration_lengths=integration_lengths,
            bins=[BinsData(**sequencer_bins_data) for sequencer_bins_data in bins_data],
        )

    @classmethod
    def _get_sequencer_with_scope_data_available(cls, qblox_raw_results: list[dict]) -> int | None:
        """Returns the sequencer with scope data available.

        Returns:
            int | None: Number of the sequencer with scope data. None if there is no scope data available in any sequencer.
        """
        return next(
            (
                sequencer
                for sequencer, acquitision in enumerate(qblox_raw_results)
                if any(acquitision["scope"]["path0"]["data"])
            ),
            None,
        )
