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
        experiment="experiment",
        platform="platform",
        executed_at=datetime(2024, 1, 1, 0, 0, 0, 0),
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
        },
    )


@pytest.fixture(name="experiment_results")
def mock_experiment_results(metadata):
    # Create a mock HDF5 file structure for testing
    with ExperimentResultsWriter(path=EXPERIMENT_RESULTS_PATH, metadata=metadata) as experiment_results:
        experiment_results.execution_time = 12.34
    yield EXPERIMENT_RESULTS_PATH
    Path(EXPERIMENT_RESULTS_PATH).unlink()


class TestExperimentResults:
    def test_enter_exit(self, experiment_results):
        """Test __enter__ and __exit__"""
        # Test that opening and closing the file works as expected
        with ExperimentResults(experiment_results) as exp_results:
            assert exp_results._file is not None
            assert exp_results._file.id.valid
        # After exiting the context manager, the file should be closed
        assert not exp_results._file.id.valid

    def test_get_item(self, experiment_results):
        """Test __get_item__"""
        with ExperimentResults(experiment_results) as exp_results:
            value = exp_results[("QProgram_0", "Measurement_0", 0, 0, 0)]
            assert value == 0.0

    def test_len(self, experiment_results):
        """Test __len__"""
        with ExperimentResults(experiment_results) as exp_results:
            assert len(exp_results) == 3

    def test_iter(self, experiment_results):
        """Test __iter__"""
        with ExperimentResults(experiment_results) as exp_results:
            results = list(iter(exp_results))
            assert len(results) == 3
            assert results[0][0] == ("QProgram_0", "Measurement_0")

    def test_properties(self, experiment_results):
        """Test properties"""
        with ExperimentResults(experiment_results) as exp_results:
            assert exp_results.experiment == "experiment"
            assert exp_results.platform == "platform"
            assert exp_results.executed_at == datetime(2024, 1, 1, 0, 0, 0, 0)


class TestExperimentResultsWriter:
    @mock.patch("h5py.File")
    def test_create_results_file(self, mock_h5file, metadata):
        """Test file creation"""
        # Test that the results file is created with the correct structure
        with ExperimentResultsWriter(path="mock_path", metadata=metadata):
            pass  # Just initializing should create the file structure

        assert mock_h5file.called
        mock_h5file.assert_called_with("mock_path", mode="w")

    def test_setters(self, experiment_results):
        """Test setters"""
        with ExperimentResultsWriter(path=experiment_results, metadata={}) as exp_writer:
            exp_writer.experiment = "new_experiment"
            assert exp_writer.experiment == "new_experiment"

            exp_writer.platform = "new_platform"
            assert exp_writer.platform == "new_platform"

            exp_writer.executed_at = datetime(2025, 1, 1, 0, 0, 0)
            assert exp_writer.executed_at == datetime(2025, 1, 1, 0, 0, 0)

            exp_writer.execution_time = 1.23
            assert exp_writer.execution_time == 1.23
