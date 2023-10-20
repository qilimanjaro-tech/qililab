""" Test Results """

import numpy as np
import pytest

from qililab.constants import QMRESULT, RUNCARD
from qililab.result.quantum_machines_results import QuantumMachinesResult


@pytest.fixture(name="qm_result")
def fixture_qm_result():
    """fixture_qm_result

    Returns:
        qm_result: QuantumMachinesResult
    """
    return QuantumMachinesResult(raw_results=np.zeros((2, 10)))


class TestsQMResult:
    """Test `QuantumMachinesResult` functionalities."""

    def test_qm_result_instantiation(self, qm_result: QuantumMachinesResult):
        """Tests the instantiation of a QuantumMachinesResult object.

        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        assert isinstance(qm_result, QuantumMachinesResult)

    def test_array(self, qm_result: QuantumMachinesResult):
        """Tests that array method in QuantumMachinesResult returns a valid numpy array.
        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        assert isinstance(qm_result.array, np.ndarray)
        assert qm_result.array.shape == (2, 10)

    def test_to_dict(self, qm_result: QuantumMachinesResult):
        """Tests that to_dict method serializes a QuantumMachinesResult class.

        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        qm_result_dict = qm_result.to_dict()

        assert RUNCARD.NAME in qm_result_dict
        assert QMRESULT.QM_RAW_RESULTS in qm_result_dict
        assert isinstance(qm_result_dict[RUNCARD.NAME], str)
        assert isinstance(qm_result_dict[QMRESULT.QM_RAW_RESULTS], np.ndarray)
