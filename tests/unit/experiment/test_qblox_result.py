""" Test Results """

import numpy as np
import pandas as pd

from qililab.constants import QBLOXCONSTANTS, RESULTSDATAFRAME
from qililab.result.qblox_results.qblox_result import QbloxResult

from ...utils import compare_pair_of_arrays, complete_array


class TestsQbloxResult:
    """Test `QbloxResults` functionalities."""

    def test_qblox_result_instantiation(self, qblox_result_scope: QbloxResult):
        """Tests the instantiation of a QbloxResult object.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance.
        """
        assert isinstance(qblox_result_scope, QbloxResult)

    def test_qblox_result_scoped_has_scope_and_bins(self, qblox_result_scope: QbloxResult):
        """Tests that a QbloxResult with scope has qblox_scope_acquisitions and qblox_bins_acquisitions.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available.
        """
        assert qblox_result_scope.qblox_scope_acquisitions is not None
        assert qblox_result_scope.qblox_bins_acquisitions is not None

    def test_qblox_result_noscoped_has_no_scope_but_bins(self, qblox_result_noscope: QbloxResult):
        """Tests that a QbloxResult without scope doesn't has qblox_scope_acquisitions but has qblox_bins_acquisitions.

        Args:
            qblox_result_noscope (QbloxResult): QbloxResult instance without scope available.
        """
        assert qblox_result_noscope.qblox_scope_acquisitions is None
        assert qblox_result_noscope.qblox_bins_acquisitions is not None

    def test_qblox_result_acquisitions_type(self, qblox_result_noscope: QbloxResult):
        """Tests that a QbloxResult acquisitions method returns a Pandas Dataframe.

        Args:
            qblox_result_noscope (QbloxResult): QbloxResult instance.
        """
        acquisitions = qblox_result_noscope.acquisitions()
        assert isinstance(acquisitions, pd.DataFrame)

    def test_qblox_result_acquisitions(self, qblox_result_noscope: QbloxResult):
        """Tests that the dataframe returned by QbloxResult.acquisitions is valid.

        Args:
            qblox_result_noscope (QbloxResult): QbloxResult instance.
        """
        acquisitions = qblox_result_noscope.acquisitions()
        assert acquisitions.keys().tolist() == [
            RESULTSDATAFRAME.ACQUISITION_INDEX,
            RESULTSDATAFRAME.BINS_INDEX,
            "i",
            "q",
            "amplitude",
            "phase",
        ]
        assert np.isclose(acquisitions["i"].iloc[0], 1.0, 1e-10)
        assert np.isclose(acquisitions["q"].iloc[0], 0.0, 1e-10)
        assert np.isclose(acquisitions["amplitude"].iloc[0], 1.0, 1e-10)
        assert np.isclose(acquisitions["phase"].iloc[0], 0.0, 1e-10)

    def test_qblox_result_acquisitions_scope(self, qblox_result_scope: QbloxResult):
        """Tests that the default acquisitions_scope method of QbloxResult returns the scope as it is.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope()
        assert acquisition is not None
        assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
        assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
        time = np.arange(0, 1e-6, 1e-9)
        expected_i = (np.cos(2 * np.pi * 10e6 * time) / np.sqrt(2)).tolist()
        expected_q = (np.sin(2 * np.pi * 10e6 * time) / np.sqrt(2)).tolist()
        expected_i = complete_array(expected_i, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        expected_q = complete_array(expected_q, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_demod(self, qblox_result_scope: QbloxResult):
        """Tests the demodulation of acquisitions_scope.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope(demod_freq=10e6)
        assert acquisition is not None
        assert len(acquisition[0]) == QBLOXCONSTANTS.SCOPE_LENGTH
        assert len(acquisition[1]) == QBLOXCONSTANTS.SCOPE_LENGTH
        expected_i = [1.0 for _ in range(1000)]
        expected_q = [0.0 for _ in range(1000)]
        expected_i = complete_array(expected_i, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        expected_q = complete_array(expected_q, 0.0, QBLOXCONSTANTS.SCOPE_LENGTH)
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=(expected_i, expected_q), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_integrated(self, qblox_result_scope: QbloxResult):
        """Tests the integration of acquisitions_scope.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope(integrate=True, integration_range=(0, 1000))
        assert acquisition is not None
        assert len(acquisition[0]) == 1
        assert len(acquisition[1]) == 1
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=([0.0], [0.0]), tolerance=1e-5)

    def test_qblox_result_acquisitions_scope_demod_integrated(self, qblox_result_scope: QbloxResult):
        """Tests the demodulation and integration of acquisitions_scope.

        Args:
            qblox_result_scope (QbloxResult): QbloxResult instance with scope available and equal to a readout of 1us
                modulated at 10MHz.
        """
        acquisition = qblox_result_scope.acquisitions_scope(
            demod_freq=10e6, integrate=True, integration_range=(0, 1000)
        )
        assert acquisition is not None
        assert compare_pair_of_arrays(pair_a=acquisition, pair_b=([1.0], [0.0]), tolerance=1e-5)
