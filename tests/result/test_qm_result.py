""" Test Results """

import numpy as np
import pytest

from qililab.constants import QMRESULT, RUNCARD
from qililab.result.quantum_machines_results import QuantumMachinesMeasurementResult


@pytest.fixture(name="qm_result")
def fixture_qm_result():
    """fixture_qm_result

    Returns:
        qm_result: QuantumMachinesResult
    """
    return QuantumMachinesMeasurementResult(I=np.zeros(10), Q=np.zeros(10))


class TestsQMResult:
    """Test `QuantumMachinesResult` functionalities."""

    def test_qm_result_instantiation(self, qm_result: QuantumMachinesMeasurementResult):
        """Tests the instantiation of a QuantumMachinesResult object.

        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        assert isinstance(qm_result, QuantumMachinesMeasurementResult)

    def test_array(self, qm_result: QuantumMachinesMeasurementResult):
        """Tests that array method in QuantumMachinesResult returns a valid numpy array.
        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        assert isinstance(qm_result.array, np.ndarray)
        assert qm_result.array.shape == (2, 10)

    def test_to_dict(self, qm_result: QuantumMachinesMeasurementResult):
        """Tests that to_dict method serializes a QuantumMachinesResult class.

        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        qm_result_dict = qm_result.to_dict()

        assert RUNCARD.NAME in qm_result_dict
        assert QMRESULT.I in qm_result_dict
        assert QMRESULT.Q in qm_result_dict
        assert QMRESULT.ADC1 in qm_result_dict
        assert QMRESULT.ADC2 in qm_result_dict
        assert isinstance(qm_result_dict[RUNCARD.NAME], str)
        assert isinstance(qm_result_dict[QMRESULT.I], np.ndarray)
        assert isinstance(qm_result_dict[QMRESULT.Q], np.ndarray)
        assert qm_result_dict[QMRESULT.I] is None
        assert qm_result_dict[QMRESULT.I] is None

    def test_probabilities(self, qm_result: QuantumMachinesMeasurementResult):
        """Tests that probabilities method raises a not implemented error.

        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        with pytest.raises(
            NotImplementedError, match="Probabilities are not yet supported for Quantum Machines instruments."
        ):
            _ = qm_result.probabilities()

    def test_counts_object(self, qm_result: QuantumMachinesMeasurementResult):
        """Tests that counts_object method raises a not implemented error.

        Args:
            qm_result (QuantumMachinesResult): QuantumMachinesResult instance.
        """
        with pytest.raises(NotImplementedError, match="Counts are not yet supported for Quantum Machines instruments."):
            _ = qm_result.counts_object()
