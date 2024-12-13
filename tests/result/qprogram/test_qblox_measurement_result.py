""" Test Results """
import os

import numpy as np
import pytest

from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


@pytest.fixture(name="raw_measurement_data")
def fixture_raw_measurement_data() -> dict:
    """Dictionary of raw measurement data as returned from QRM instruments."""
    return {"bins": {"integration": {"path0": [1, 2, 3], "path1": [4, 5, 6]}, "threshold": [0.1, 0.2, 0.3]}}


@pytest.fixture(name="qblox_measurement_result")
def fixture_qblox_result_noscope(raw_measurement_data: dict):
    """Instance of QbloxMeasurementResult."""
    return QbloxMeasurementResult(bus="readout", raw_measurement_data=raw_measurement_data)


class TestsQbloxQProgramMeasurementResult:
    """Test `QbloxQProgramResults` functionalities."""

    def test_init(self, qblox_measurement_result: QbloxMeasurementResult):
        """Test the instantiation of QbloxMeasurementResult."""
        assert isinstance(qblox_measurement_result, QbloxMeasurementResult)
        assert isinstance(qblox_measurement_result.raw_measurement_data, dict)
        assert "bins" in qblox_measurement_result.raw_measurement_data
        assert "integration" in qblox_measurement_result.raw_measurement_data["bins"]
        assert "path0" in qblox_measurement_result.raw_measurement_data["bins"]["integration"]
        assert "path1" in qblox_measurement_result.raw_measurement_data["bins"]["integration"]

    def test_array_property(self, raw_measurement_data: dict, qblox_measurement_result: QbloxMeasurementResult):
        """Test the array property returns the correct data."""
        path0 = raw_measurement_data["bins"]["integration"]["path0"]
        path1 = raw_measurement_data["bins"]["integration"]["path1"]
        expected_array = np.array([path0, path1])
        print(f"expected_array shape {expected_array.shape}")
        assert np.allclose(qblox_measurement_result.array, expected_array)

    def test_serialization_deserialization(self, qblox_measurement_result: QbloxMeasurementResult):
        """Test serialization and deserialization works."""
        serialized = serialize(qblox_measurement_result)
        deserialized_qblox_measurement_result = deserialize(serialized, QbloxMeasurementResult)

        assert isinstance(deserialized_qblox_measurement_result, QbloxMeasurementResult)

        serialize_to(qblox_measurement_result, file="qblox_measurement_result.yml")
        deserialized_qblox_measurement_result = deserialize_from("qblox_measurement_result.yml", QbloxMeasurementResult)

        assert isinstance(deserialized_qblox_measurement_result, QbloxMeasurementResult)

        os.remove("qblox_measurement_result.yml")

    def test_threshold(self, qblox_measurement_result: QbloxMeasurementResult):
        """Test the thresholded data as an np.ndarray"""
        thresholded_data = qblox_measurement_result.threshold

        assert isinstance(thresholded_data, np.ndarray)
        assert np.all(thresholded_data == np.array(qblox_measurement_result.raw_measurement_data["bins"]["threshold"]))
