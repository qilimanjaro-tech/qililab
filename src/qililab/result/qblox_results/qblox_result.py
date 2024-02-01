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

"""QbloxResult class."""
from copy import deepcopy

import numpy as np
import pandas as pd

from qililab.constants import QBLOXRESULT, RUNCARD
from qililab.exceptions import DataUnavailable
from qililab.result.counts import Counts
from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory

from .constants import SCOPE_ACQ_MAX_DURATION
from .qblox_acquisitions_builder import QbloxAcquisitionsBuilder
from .qblox_scope_acquisitions import QbloxScopeAcquisitions


@Factory.register
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
        qblox_raw_results (list[dict]): Raw results obtained from a Qblox digitiser.
        integration_lengths (list[int]): Integration lengths used to get the given results.
    """

    name = ResultName.QBLOX

    def __init__(self, qblox_raw_results: list[dict], integration_lengths: list[int]):
        self.qblox_raw_results = qblox_raw_results
        self.integration_lengths = integration_lengths
        self.qblox_scope_acquisitions = QbloxAcquisitionsBuilder.get_scope(
            integration_lengths=integration_lengths, qblox_raw_results=qblox_raw_results
        )
        self.qblox_bins_acquisitions = QbloxAcquisitionsBuilder.get_bins(
            integration_lengths=integration_lengths, qblox_raw_results=qblox_raw_results
        )
        self._qblox_scope_acquisition_copy = deepcopy(self.qblox_scope_acquisitions)
        self.data_dataframe_indices = self.qblox_bins_acquisitions.data_dataframe_indices

    def _demodulated_scope(self, frequency: float, phase_offset: float = 0.0) -> QbloxScopeAcquisitions:
        """Returns the scope acquisitions demodulated in the given frequency with the given phase offset.

        Returns:
            QbloxScopeAcquisitions: demodulated scope acquisitions."""
        if self.qblox_scope_acquisitions is None:
            raise ValueError("Scope acquisitions cannot be demodulated because it doesn't exist.")
        return self.qblox_scope_acquisitions.demodulated(frequency=frequency, phase_offset=phase_offset)

    def _integrated_scope(
        self, scope_acquisitions=None, integrate_from: int = 0, integrate_to: int = SCOPE_ACQ_MAX_DURATION
    ) -> QbloxScopeAcquisitions:
        """Integrated Scope

        Args:
            scope_acquisitions (_type_, optional): _description_. Defaults to None.
            integrate_from (int, optional): _description_. Defaults to 0.
            integrate_to (int, optional): _description_. Defaults to SCOPE_ACQ_MAX_DURATION.

        Raises:
            ValueError: _description_

        Returns:
            QbloxScopeAcquisitions: _description_
        """
        if scope_acquisitions is None:
            scope_acquisitions = self.qblox_scope_acquisitions
        if scope_acquisitions is None:
            raise ValueError("Scope acquisitions cannot be integrated because it doesn't exist.")
        return scope_acquisitions.integrated(integrate_from=integrate_from, integrate_to=integrate_to)

    def acquisitions(self) -> pd.DataFrame:
        """Return acquisition values.

        Returns:
            pd.DataFrame: I, Q, amplitude and phase.
        """
        return self.qblox_bins_acquisitions.acquisitions()

    def acquisitions_scope(
        self,
        demod_freq: float = 0.0,
        demod_phase_offset: float = 0.0,
        integrate: bool = False,
        integration_range: tuple[int, int] = (0, SCOPE_ACQ_MAX_DURATION),
    ) -> tuple[list[float], list[float]]:
        """Acquisitions Scope

        Args:
            demod_freq (float, optional): _description_. Defaults to 0.0.
            demod_phase_offset (float, optional): _description_. Defaults to 0.0.
            integrate (bool, optional): _description_. Defaults to False.
            integration_range (tuple[int, int], optional): _description_. Defaults to (0, SCOPE_ACQ_MAX_DURATION).

        Raises:
            DataUnavailable: Scope data is not available since it was not stored for this acquisition.

        Returns:
            tuple[list[float], list[float]]
        """
        acquisitions = self.qblox_scope_acquisitions
        if acquisitions is None:
            raise DataUnavailable("Scope data is not available since it was not stored for this acquisition.")
        if demod_freq != 0.0:
            acquisitions = self._demodulated_scope(frequency=-demod_freq, phase_offset=demod_phase_offset)
        if integrate:
            integrate_from, integrate_to = integration_range
            acquisitions = self._integrated_scope(
                scope_acquisitions=acquisitions, integrate_from=integrate_from, integrate_to=integrate_to
            )
        return acquisitions.scope.path0.data, acquisitions.scope.path1.data

    def counts_object(self) -> Counts:
        """Returns a Counts object containing the counts of each state.

        Returns:
            Counts: Counts object containing the counts of each state.
        Raises:
            NotImplementedError: this method is not implemented for n measurements on the same qubit
        """
        if sum(result["measurement"] for result in self.qblox_raw_results) != 0:
            raise NotImplementedError("Counts for multiple measurements on a single qubit are not supported")
        return self.qblox_bins_acquisitions.counts()

    def counts(self) -> dict:
        """Returns a Counts object containing the counts of each state.

        Returns:
            Counts: Counts object containing the counts of each state.
        Raises:
            NotImplementedError: this method is not implemented for n measurements on the same qubit
        """
        if sum(result["measurement"] for result in self.qblox_raw_results) != 0:
            raise NotImplementedError("Counts for multiple measurements on a single qubit are not supported")
        return self.qblox_bins_acquisitions.counts().as_dict()

    def samples(self) -> np.ndarray:
        """Returns an array containing the measured samples.
        The shape of the returned array is ``(# sequencers, # bins)``.

        Returns:
            np.ndarray: An array containing the measured samples (0 or 1).
        Raises:
            NotImplementedError: this method is not implemented for n measurements on the same qubit
        """
        if sum(result["measurement"] for result in self.qblox_raw_results) != 0:
            raise NotImplementedError("Samples for multiple measurements on a single qubit are not supported")
        return self.qblox_bins_acquisitions.samples()

    @property
    def array(self) -> np.ndarray:
        # Save array data
        if self.qblox_scope_acquisitions is not None:
            if sum(result["measurement"] for result in self.qblox_raw_results) != 0:
                raise NotImplementedError(
                    "Scope acquisition for multiple measurements on a single qubit are not supported"
                )
            # The dimensions of the array are: (2, N) where N is the length of the scope.
            path0 = self.qblox_scope_acquisitions.scope.path0.data
            path1 = self.qblox_scope_acquisitions.scope.path1.data
            return np.array([path0, path1])

        bins_len = [len(bins) for bins in self.qblox_bins_acquisitions.bins]
        # Check that all measurements have the same number of bins.
        if len(set(bins_len)) != 1:
            raise IndexError(
                f"All measurements must have the same number of bins to return an array. Obtained {len(bins_len)} "
                f"measurements with {bins_len} bins respectively."
            )
        # The dimensions of the array are the following: (#sequencers*#measurements, 2, #bins)
        # #measurements are the number of measurements done for a particular single qubit
        bins = [[result.integration.path0, result.integration.path1] for result in self.qblox_bins_acquisitions.bins]

        return np.array(bins[0] if len(bins) == 1 else bins)

    @property
    def shape(self) -> list[int]:
        """QbloxResult 'shape' property.

        Returns:
            list[int]: Shape of the acquisitions.
        """
        return list(self.acquisitions().shape)

    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """
        return {
            RUNCARD.NAME: self.name.value,
            QBLOXRESULT.INTEGRATION_LENGTHS: self.integration_lengths,
            QBLOXRESULT.QBLOX_RAW_RESULTS: self.qblox_raw_results,
        }
