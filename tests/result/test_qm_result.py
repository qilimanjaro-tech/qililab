""" Test Results """

import json

import numpy as np
import pytest

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

    def test_serialization_method(self, qm_result: QuantumMachinesMeasurementResult):
        """Test serialization and deserialization works."""
        serialized_dictionary = qm_result.to_dict()
        assert "type" in serialized_dictionary
        assert "attributes" in serialized_dictionary

        deserialized_qp = QuantumMachinesMeasurementResult.from_dict(serialized_dictionary["attributes"])
        assert isinstance(deserialized_qp, QuantumMachinesMeasurementResult)

        again_serialized_dictionary = deserialized_qp.to_dict()
        assert serialized_dictionary == again_serialized_dictionary

        as_json = json.dumps(again_serialized_dictionary)
        dictionary_from_json = json.loads(as_json)
        assert serialized_dictionary == dictionary_from_json
