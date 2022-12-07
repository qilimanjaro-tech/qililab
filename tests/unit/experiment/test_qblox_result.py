""" Test Results """

import numpy as np
import pandas as pd
import pytest

from qililab.constants import QBLOXCONSTANTS
from qililab.result.qblox_results.qblox_result import QbloxResult

from ...utils import compare_pair_of_arrays, complete_array


class TestsQbloxResult:
    """Test `QbloxResults` functionalities."""

    def test_qblox_result_instantiation(self, qblox_result_scope: QbloxResult):
        assert isinstance(qblox_result_scope, QbloxResult)

    def test_qblox_result_scoped_has_scope_and_bins(self, qblox_result_scope: QbloxResult):
        assert qblox_result_scope.qblox_scope_acquisitions is not None
        assert qblox_result_scope.qblox_bins_acquisitions is not None

    def test_qblox_result_noscoped_has_no_scope_but_bins(self, qblox_result_noscope: QbloxResult):
        assert qblox_result_noscope.qblox_scope_acquisitions is None
        assert qblox_result_noscope.qblox_bins_acquisitions is not None

    def test_qblox_result_acquisitions_type(self, qblox_result_noscope: QbloxResult):
        acquisitions = qblox_result_noscope.acquisitions()
        assert isinstance(acquisitions, pd.DataFrame)

    def test_qblox_result_acquisitions(self, qblox_result_noscope: QbloxResult):
        acquisitions = qblox_result_noscope.acquisitions()
        assert acquisitions.keys().tolist() == ["i", "q", "amplitude", "phase"]
        assert np.isclose(acquisitions["i"].iloc[0], 1.0, 1e-10)
        assert np.isclose(acquisitions["q"].iloc[0], 0.0, 1e-10)
        assert np.isclose(acquisitions["amplitude"].iloc[0], 1.0, 1e-10)
        assert np.isclose(acquisitions["phase"].iloc[0], 0.0, 1e-10)

    def test_qblox_result_acquisitions_scope(self, qblox_result_scope: QbloxResult):
        acquisition = qblox_result_scope.acquisitions_scope()
        assert acquisition is not None
        assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
        assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
        time = np.arange(0, 1e-6, 1e-9)
        expected_i = np.cos(2 * np.pi * 10e6 * time) / np.sqrt(2)
        expected_q = np.sin(2 * np.pi * 10e6 * time) / np.sqrt(2)
        expected_i = complete_array(expected_i, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        expected_q = complete_array(expected_q, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_demod(self, qblox_result_scope: QbloxResult):
        acquisition = qblox_result_scope.acquisitions_scope(demod_freq=10e6)
        assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
        assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
        expected_i = [1.0 for _ in range(1000)]
        expected_q = [0.0 for _ in range(1000)]
        expected_i = complete_array(np.array(expected_i), 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        expected_q = complete_array(np.array(expected_q), 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_integrated(self, qblox_result_scope: QbloxResult):
        acquisition = qblox_result_scope.acquisitions_scope(integrate=True, integration_range=(0, 1000))
        assert len(acquisition[0]) == 1
        assert len(acquisition[1]) == 1
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(np.array([0.0]), np.array([0.0])), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_demod_integrated(self, qblox_result_scope: QbloxResult):
        acquisition = qblox_result_scope.acquisitions_scope(
            demod_freq=10e6, integrate=True, integration_range=(0, 1000)
        )
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(np.array([1.0]), np.array([0.0])), tolerance=1e-5)
