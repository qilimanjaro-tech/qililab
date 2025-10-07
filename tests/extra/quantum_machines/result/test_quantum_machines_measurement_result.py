""" Test Results """

import os
from warnings import catch_warnings

import numpy as np
import pytest

from qililab.extra.quantum_machines import QuantumMachinesMeasurementResult
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


@pytest.fixture(name="quantum_machines_measurement_result")
def fixture_quantum_machines_measurement_result():
    """fixture_quantum_machines_measurement_result

    Returns:
        quantum_machines_measurement_result: QuantumMachinesResult
    """
    return QuantumMachinesMeasurementResult(bus="readout", I=np.zeros(10), Q=np.zeros(10))


class TestsQMResult:
    """Test `QuantumMachinesResult` functionalities."""

    def test_init(self, quantum_machines_measurement_result: QuantumMachinesMeasurementResult):
        """Test the instantiation of QuantumMachinesMeasurementResult."""
        assert isinstance(quantum_machines_measurement_result, QuantumMachinesMeasurementResult)
        assert np.allclose(quantum_machines_measurement_result.I, np.zeros(10))
        assert np.allclose(quantum_machines_measurement_result.Q, np.zeros(10))

    def test_set_classification_threshold(self, quantum_machines_measurement_result: QuantumMachinesMeasurementResult):
        """Test the set_classification_threshold method."""
        quantum_machines_measurement_result.set_classification_threshold(0.3)
        assert quantum_machines_measurement_result._classification_threshold == 0.3

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

    @pytest.mark.parametrize(
        "threshold, I, expected",
        [
            (0.0, np.ones(10), np.ones(10)),
            (0.5, np.zeros(10), np.zeros(10)),
            (0.5, np.array([0.2, 0.4, 0.6, 0.5, 0.9]), np.array([0.0, 0.0, 1.0, 1.0, 1.0])),
            (None, np.array([0.2, 0.4, 0.6, 0.5, 0.9]), np.array([0.0, 0.0, 0.0, 0.0, 0.0])),
        ],
    )
    def test_threshold_property(
        self, threshold, I, expected, quantum_machines_measurement_result: QuantumMachinesMeasurementResult
    ):
        """Test the `threshold` property."""
        quantum_machines_measurement_result._classification_threshold = threshold
        quantum_machines_measurement_result.I = I
        if threshold is not None:
            np.testing.assert_equal(quantum_machines_measurement_result.threshold, expected)

        else:
            with catch_warnings(record=True) as w:
                np.testing.assert_equal(quantum_machines_measurement_result.threshold, expected)
                assert (
                    w[0].message.args[0] == "Classification threshold is not specified, returning a `np.zeros` array."  # type: ignore
                )
