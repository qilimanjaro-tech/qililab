""" Test Results """

import json

import numpy as np
import pytest

from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult


@pytest.fixture(name="raw_measurement_data")
def fixture_raw_measurement_data() -> dict:
    """Dictionary of raw measurement data as returned from QRM instruments."""
    return {"bins": {"integration": {"path0": [1, 2, 3], "path1": [4, 5, 6]}, "threshold": [0.1, 0.2, 0.3]}}


@pytest.fixture(name="qblox_measurement_result")
def fixture_qblox_result_noscope(raw_measurement_data: dict):
    """Instance of QbloxMeasurementResult."""
    return QbloxMeasurementResult(raw_measurement_data=raw_measurement_data)


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
        assert np.allclose(qblox_measurement_result.array, expected_array)

    def test_serialization_method(self, qblox_measurement_result: QbloxMeasurementResult):
        """Test serialization and deserialization works."""
        serialized_dictionary = qblox_measurement_result.to_dict()
        assert "type" in serialized_dictionary
        assert "attributes" in serialized_dictionary

        deserialized_qp = QbloxMeasurementResult.from_dict(serialized_dictionary["attributes"])
        assert isinstance(deserialized_qp, QbloxMeasurementResult)

        again_serialized_dictionary = deserialized_qp.to_dict()
        assert serialized_dictionary == again_serialized_dictionary

        as_json = json.dumps(again_serialized_dictionary)
        dictionary_from_json = json.loads(as_json)
        assert serialized_dictionary == dictionary_from_json

    def test_threshold(self, qblox_measurement_result: QbloxMeasurementResult):
        """Test the thresholded data as an np.ndarray"""
        thresholded_data = qblox_measurement_result.threshold

        assert isinstance(thresholded_data, np.ndarray)
        assert np.all(thresholded_data == np.array(qblox_measurement_result.raw_measurement_data["bins"]["threshold"]))
