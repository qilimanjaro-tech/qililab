from datetime import datetime
from pathlib import Path
from unittest import mock

import h5py
import numpy as np
import pytest

from qililab.result.experiment_results import ExperimentMetadata, ExperimentResults, ExperimentResultsWriter

# Dummy path for testing
EXPERIMENT_RESULTS_PATH = "dummy.hdf5"


@pytest.fixture(name="metadata")
def sample_metadata():
    return ExperimentMetadata(
        qprograms={
            "QProgram_0": {
                "variables": [{"label": "x", "values": np.array([1, 2, 3])}],
                "dims": [["x"]],
                "measurements": {
                    # This simulates a single loop
                    "Measurement_0": {
                        "variables": [{"label": "y", "values": np.array([10, 20, 30, 40])}],
                        "dims": [["y"]],
                        "shape": (3, 4, 2),
                        "shots": 100,
                    },
                    # This simulates an inner loop
                    "Measurement_1": {
                        "variables": [
                            {"label": "y", "values": np.array([10, 20, 30, 40])},
                            {"label": "z", "values": np.array([110, 120, 130, 140])},
                        ],
                        "dims": [["y"], ["z"]],
                        "shape": (3, 4, 4, 2),
                        "shots": 100,
                    },
                    # This simulates a parallel loop
                    "Measurement_2": {
                        "variables": [
                            {"label": "y", "values": np.array([10, 20, 30, 40])},
                            {"label": "z", "values": np.array([110, 120, 130, 140])},
                        ],
                        "dims": [["y", "z"]],
                        "shape": (3, 4, 2),
                        "shots": 100,
                    },
                },
            }
        }
    )


@pytest.fixture(name="experiment_results")
def mock_experiment_results(metadata):
    # Create a mock HDF5 file structure for testing
    with ExperimentResultsWriter(metadata, EXPERIMENT_RESULTS_PATH) as experiment_results:
        experiment_results.execution_time = 12.34
    yield EXPERIMENT_RESULTS_PATH
    Path(EXPERIMENT_RESULTS_PATH).unlink()


class TestExperimentResults:
    def test_enter_exit(self, experiment_results):
        # Test that opening and closing the file works as expected
        with ExperimentResults(experiment_results) as exp_results:
            assert exp_results._file is not None
            assert exp_results._file.id.valid
        # After exiting the context manager, the file should be closed
        assert not exp_results._file.id.valid

    def test_get_item(self, experiment_results):
        with ExperimentResults(experiment_results) as exp_results:
            value = exp_results[("QProgram_0", "Measurement_0", 0, 0, 0)]
            assert value == 0.0

    def test_len(self, experiment_results):
        with ExperimentResults(experiment_results) as exp_results:
            assert len(exp_results) == 3

    def test_iter(self, experiment_results):
        with ExperimentResults(experiment_results) as exp_results:
            results = list(iter(exp_results))
            assert len(results) == 3
            assert results[0][0] == ("QProgram_0", "Measurement_0")

    def test_properties(self, experiment_results):
        with ExperimentResults(experiment_results) as exp_results:
            assert exp_results.yaml == "experiment_yaml"
            assert exp_results.executed_at == datetime(2023, 1, 1, 0, 0)


class TestExperimentResultsWriter:
    @mock.patch("h5py.File")
    def test_create_results_file(self, mock_h5file, metadata):
        # Test that the results file is created with the correct structure
        with ExperimentResultsWriter(metadata, "mock_path"):
            pass  # Just initializing should create the file structure

        assert mock_h5file.called
        mock_h5file.assert_called_with("mock_path", mode="a")

    def test_set_item(self, experiment_results):
        # Open a writable HDF5 and test the __setitem__ method
        with ExperimentResultsWriter({}, experiment_results) as exp_writer:
            exp_writer[("QProgram_0", "Measurement_0", 0, 0, 0)] = 99.0
            assert exp_writer[("QProgram_0", "Measurement_0", 0, 0, 0)] == 99.0

    def test_yaml_setter(self, experiment_results):
        # Test setting yaml content
        with ExperimentResultsWriter({}, experiment_results) as exp_writer:
            exp_writer.yaml = "new_yaml"
            assert exp_writer.yaml == "new_yaml"

    def test_executed_at_setter(self, experiment_results):
        # Test setting the execution timestamp
        with ExperimentResultsWriter({}, experiment_results) as exp_writer:
            exp_writer.executed_at = datetime(2024, 1, 1)
            assert exp_writer.executed_at == "2024-01-01 00:00:00"

    def test_execution_time_setter(self, experiment_results):
        # Test setting the execution time
        with ExperimentResultsWriter({}, experiment_results) as exp_writer:
            exp_writer.execution_time = 42.0
            assert exp_writer.execution_time == 42.0
