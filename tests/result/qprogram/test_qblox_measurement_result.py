""" Test Results """
import os

import numpy as np
import pytest

from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


@pytest.fixture(name="raw_measurement_data")
def fixture_raw_measurement_data() -> dict:
    """Dictionary of raw measurement data as returned from QRM instruments."""
    return {"bins": {"integration": {"path0": [1, 2, 3,], "path1": [4, 5, 6]}, "threshold": [0.1, 0.2, 0.3]}}

@pytest.fixture(name="raw_measurement_data_nested_loops")
def fixture_raw_measurement_data_nested() -> dict:
    """Dictionary of raw measurement data as returned from QRM instruments."""
    return {"bins": {"integration": {"path0": [1, 2, 3, 4, 5, 6], "path1": [7, 8, 9, 10, 11, 12]}, "threshold": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]}}

@pytest.fixture(name="raw_measurement_data_complete")
def fixture_raw_measurement_data_complete() -> dict:
    """Dictionary of raw measurement data as returned from QRM instruments."""
    return {"bins": {"integration": {"path0": [1, 2, 3, 4], "path1": [4, 5, 6, 7]}, "threshold": [0.1, 0.2, 0.3, 0.4], "avg_cnt": [0.1, 0.2, 0.3, 0.4]}, "scope":{"path0": {"data": [1, 2, 3, 4],}, "path1": {"data": [4, 5, 6, 7]}}}

@pytest.fixture(name="qblox_measurement_result")
def fixture_qblox_result_noscope(raw_measurement_data: dict):
    """Instance of QbloxMeasurementResult."""
    return QbloxMeasurementResult(bus="readout", raw_measurement_data=raw_measurement_data, intertwined=1)

@pytest.fixture(name="qblox_measurement_result_shape")
def fixture_qblox_result_with_shape(raw_measurement_data: dict):
    """Instance of QbloxMeasurementResult."""
    return QbloxMeasurementResult(bus="readout", raw_measurement_data=raw_measurement_data, shape=(1, 3), intertwined=1)

@pytest.fixture(name="qblox_measurement_result_nested_loops")
def fixture_qblox_result_with_nested_loop(raw_measurement_data_nested_loops: dict):
    """Instance of QbloxMeasurementResult."""
    return QbloxMeasurementResult(bus="readout", raw_measurement_data=raw_measurement_data_nested_loops, shape=(2, 3), intertwined=1)

@pytest.fixture(name="qblox_measurement_result_intertwined")
def fixture_qblox_result_intertwined(raw_measurement_data_complete: dict):
    """Instance of QbloxMeasurementResult."""
    return QbloxMeasurementResult(bus="readout", raw_measurement_data=raw_measurement_data_complete, intertwined=2)


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

    def test_array_property_with_shape(self, raw_measurement_data: dict, qblox_measurement_result_shape: QbloxMeasurementResult):
        """Test the array property returns the correct data."""
        path0 = raw_measurement_data["bins"]["integration"]["path0"]
        path1 = raw_measurement_data["bins"]["integration"]["path1"]
        expected_array = np.array([[path0], [path1]])

        assert np.allclose(qblox_measurement_result_shape.array, expected_array)
        assert qblox_measurement_result_shape.array.shape == expected_array.shape

    def test_array_property_nested_loops(self, raw_measurement_data_nested_loops: dict, qblox_measurement_result_nested_loops: QbloxMeasurementResult):
        """Test the array property returns the correct data."""
        path0 = raw_measurement_data_nested_loops["bins"]["integration"]["path0"]
        path1 = raw_measurement_data_nested_loops["bins"]["integration"]["path1"]
        expected_array = np.array([path0, path1]).reshape((2, 2, 3))

        assert np.allclose(qblox_measurement_result_nested_loops.array, expected_array)
        assert qblox_measurement_result_nested_loops.array.shape == expected_array.shape

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
        expected_thresholds = np.array(qblox_measurement_result.raw_measurement_data["bins"]["threshold"])

        assert isinstance(thresholded_data, np.ndarray)
        assert np.all(thresholded_data == expected_thresholds)
        assert thresholded_data.shape == expected_thresholds.shape

    def test_threshold_nested_loops(self, qblox_measurement_result_nested_loops: QbloxMeasurementResult):
        """Test the thresholded data as an np.ndarray"""
        thresholded_data = qblox_measurement_result_nested_loops.threshold
        expected_thresholds = np.array(qblox_measurement_result_nested_loops.raw_measurement_data["bins"]["threshold"])
        expected_thresholds = expected_thresholds.reshape((1, 2, 3))

        assert isinstance(thresholded_data, np.ndarray)
        assert np.all(thresholded_data == expected_thresholds)
        assert thresholded_data.shape == expected_thresholds.shape

    def test_intertwined_results(self, qblox_measurement_result_intertwined: QbloxMeasurementResult):
        """Test that the results get unintertwined for the bins"""

        assert qblox_measurement_result_intertwined.intertwined == 2

        unintertwined_results = qblox_measurement_result_intertwined.unintertwined

        np.testing.assert_allclose(unintertwined_results[0].threshold, [0.1, 0.3])
        np.testing.assert_allclose(unintertwined_results[1].threshold, [0.2, 0.4])

        np.testing.assert_allclose(unintertwined_results[0].array, np.array([[1, 3], [4, 6]]))
        np.testing.assert_allclose(unintertwined_results[1].array, np.array([[2, 4], [5, 7]]))

        np.testing.assert_allclose(unintertwined_results[0].raw_measurement_data["bins"]["avg_cnt"], np.array([0.1, 0.3]))
        np.testing.assert_allclose(unintertwined_results[1].raw_measurement_data["bins"]["avg_cnt"], np.array([0.2, 0.4]))

        assert unintertwined_results[0].intertwined == 1
        assert unintertwined_results[1].intertwined == 1

    def test_intertwined_results_scope(self, qblox_measurement_result_intertwined: QbloxMeasurementResult):
        """Test that the results get unintertwinedF for the scope"""
        unintertwined_results = qblox_measurement_result_intertwined.unintertwined

        np.testing.assert_allclose(unintertwined_results[0].raw_measurement_data["scope"]["path0"]["data"], np.array([1, 3]))
        np.testing.assert_allclose(unintertwined_results[0].raw_measurement_data["scope"]["path1"]["data"], np.array([4, 6]))
        np.testing.assert_allclose(unintertwined_results[1].raw_measurement_data["scope"]["path0"]["data"], np.array([2, 4]))
        np.testing.assert_allclose(unintertwined_results[1].raw_measurement_data["scope"]["path1"]["data"], np.array([5, 7]))

        assert unintertwined_results[0].intertwined == 1
        assert unintertwined_results[1].intertwined == 1
