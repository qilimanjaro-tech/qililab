""" Test Results """

import json

import numpy as np
import pytest

from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult


@pytest.fixture(name="quantum_machines_measurement_result")
def fixture_quantum_machines_measurement_result():
    """fixture_quantum_machines_measurement_result

    Returns:
        quantum_machines_measurement_result: QuantumMachinesResult
    """
    return QuantumMachinesMeasurementResult(I=np.zeros(10), Q=np.zeros(10))


class TestsQMResult:
    """Test `QuantumMachinesResult` functionalities."""

    def test_init(self, quantum_machines_measurement_result: QuantumMachinesMeasurementResult):
        """Test the instantiation of QuantumMachinesMeasurementResult."""
        assert isinstance(quantum_machines_measurement_result, QuantumMachinesMeasurementResult)
        assert np.allclose(quantum_machines_measurement_result.I, np.zeros(10))
        assert np.allclose(quantum_machines_measurement_result.Q, np.zeros(10))

    def test_array(self, quantum_machines_measurement_result: QuantumMachinesMeasurementResult):
        """Test the array property returns the correct data."""
        assert isinstance(quantum_machines_measurement_result.array, np.ndarray)
        assert quantum_machines_measurement_result.array.shape == (2, 10)

    def test_serialization_method(self, quantum_machines_measurement_result: QuantumMachinesMeasurementResult):
        """Test serialization and deserialization works."""
        serialized_dictionary = quantum_machines_measurement_result.to_dict()
        assert "type" in serialized_dictionary
        assert "attributes" in serialized_dictionary

        deserialized_qp = QuantumMachinesMeasurementResult.from_dict(serialized_dictionary["attributes"])
        assert isinstance(deserialized_qp, QuantumMachinesMeasurementResult)

        again_serialized_dictionary = deserialized_qp.to_dict()
        assert serialized_dictionary == again_serialized_dictionary

        as_json = json.dumps(again_serialized_dictionary)
        dictionary_from_json = json.loads(as_json)
        assert serialized_dictionary == dictionary_from_json
