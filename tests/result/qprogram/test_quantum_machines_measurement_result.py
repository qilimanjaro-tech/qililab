""" Test Results """

import os

import numpy as np
import pytest

from qililab.result.qprogram.quantum_machines_measurement_result import QuantumMachinesMeasurementResult
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


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
        serialized = serialize(quantum_machines_measurement_result)
        deserialized_quantum_machines_measurement_result = deserialize(serialized, QuantumMachinesMeasurementResult)

        assert isinstance(deserialized_quantum_machines_measurement_result, QuantumMachinesMeasurementResult)

        serialize_to(quantum_machines_measurement_result, file="quantum_machines_measurement_result.yml")
        deserialized_quantum_machines_measurement_result = deserialize_from(
            "quantum_machines_measurement_result.yml", QuantumMachinesMeasurementResult
        )

        assert isinstance(deserialized_quantum_machines_measurement_result, QuantumMachinesMeasurementResult)

        os.remove("quantum_machines_measurement_result.yml")
