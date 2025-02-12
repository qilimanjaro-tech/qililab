# pylint: disable=protected-access
import os
from datetime import datetime
from pathlib import Path
from types import MethodType
from unittest.mock import MagicMock, create_autospec, patch

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import pytest

from qililab.result.experiment_live_plot import ExperimentLivePlot
from qililab.result.experiment_results import DimensionInfo
from qililab.result.experiment_results_writer import ExperimentMetadata, ExperimentResultsWriter

mpl.use("Agg")  # Use non-interactive backend for testing


# Dummy path for testing
PLOT_RESULTS_PATH = "dummy.hdf5"


@pytest.fixture(name="metadata")
def sample_metadata():
    """Create a mock metadata dictionary for testing"""
    return ExperimentMetadata(
        experiment="experiment",
        platform="platform",
        executed_at=datetime(2024, 1, 1, 0, 0, 0, 0),
        execution_time=1.23,
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
                },
            }
        },
    )


@pytest.fixture(name="experiment_live_plot")
def mock_experiment_live_plot(metadata):
    """Create a mock ExperimentResultsWriter structure for testing"""
    with ExperimentResultsWriter(path=PLOT_RESULTS_PATH, metadata=metadata, live_plot=True, slurm_execution=False):
        ...
    yield PLOT_RESULTS_PATH
    Path(PLOT_RESULTS_PATH).unlink()


@pytest.fixture(name="experiment_live_plot_slurm")
def mock_experiment_live_plot_slurm(metadata):
    """Create a mock ExperimentResultsWriter structure for testing"""
    with ExperimentResultsWriter(path=PLOT_RESULTS_PATH, metadata=metadata, live_plot=True, slurm_execution=True):
        ...
    yield PLOT_RESULTS_PATH
    Path(PLOT_RESULTS_PATH).unlink()


class TestExperimentLivePlot:
    """Test ExperimentLivePlot class"""

    @patch("h5py.File")
    def test_live_plot_1d(self, mock_h5file, metadata):
        """Test the plots generated with 1D data."""
        experiment_live_plot = create_autospec(ExperimentLivePlot, instance=True)
        experiment_live_plot._slurm_execution = False
        experiment_live_plot.path = "test.h5"
        experiment_live_plot.live_plot_dict = {}

        experiment_live_plot.live_plot_figures = MethodType(ExperimentLivePlot.live_plot_figures, experiment_live_plot)

        # Mock the get method to return 1D data
        mock_h5group = mock_h5file.create_group("mockpath_group")

        dims_dict = {}
        for qprogram_name, qprogram_data in metadata["qprograms"].items():
            qgroup = mock_h5group.create_group(qprogram_name)

            for measurement_name, measurement_data in qprogram_data["measurements"].items():
                mgroup = qgroup.create_group(measurement_name)
                mock_h5dataset = mgroup.create_dataset("mockpath_dataset", shape=measurement_data["shape"])

                # Create the labels
                for idx, dim_variables in enumerate(qprogram_data["dims"]):
                    mock_h5dataset.dims[idx].label = ",".join(list(dim_variables))
                for idx, dim_variables in enumerate(measurement_data["dims"]):
                    mock_h5dataset.dims[len(qprogram_data["dims"]) + idx].label = ",".join(list(dim_variables))

                # Attach the extra dimension (usually for I/Q) to the results dataset
                mock_h5dataset.dims[len(qprogram_data["dims"]) + len(measurement_data["dims"])].label = "I/Q"

                dims_dict[qprogram_name, measurement_name] = mock_h5dataset.dims

                # Mock the values of the loops for a 1D measure
                dims_dict[qprogram_name, measurement_name][0].values.return_value = [np.linspace(0, 10, 20)]
                dims_dict[qprogram_name, measurement_name].__len__.return_value = 2

        # Create the figures
        experiment_live_plot.live_plot_figures(dims_dict)

        # Make sure the figures run
        experiment_live_plot.live_plot(np.linspace(0, 10, 20), qprogram_name, measurement_name)

        # Make sure right plot is created
        assert isinstance(experiment_live_plot._live_plot_fig, go.FigureWidget)

    @patch("h5py.File")
    def test_live_plot_2d(self, mock_h5file, metadata):
        """Test the plots generated with 2D data."""
        experiment_live_plot = create_autospec(ExperimentLivePlot, instance=True)
        experiment_live_plot._slurm_execution = False
        experiment_live_plot.path = "test.h5"
        experiment_live_plot.live_plot_dict = {}

        experiment_live_plot.live_plot_figures = MethodType(ExperimentLivePlot.live_plot_figures, experiment_live_plot)

        # Mock the get method to return 2D data
        mock_h5group = mock_h5file.create_group("mockpath_group")

        dims_dict = {}
        for qprogram_name, qprogram_data in metadata["qprograms"].items():
            qgroup = mock_h5group.create_group(qprogram_name)

            for measurement_name, measurement_data in qprogram_data["measurements"].items():
                mgroup = qgroup.create_group(measurement_name)
                mock_h5dataset = mgroup.create_dataset("mockpath_dataset", shape=measurement_data["shape"])

                # Create the labels
                for idx, dim_variables in enumerate(qprogram_data["dims"]):
                    mock_h5dataset.dims[idx].label = ",".join(list(dim_variables))
                for idx, dim_variables in enumerate(measurement_data["dims"]):
                    mock_h5dataset.dims[len(qprogram_data["dims"]) + idx].label = ",".join(list(dim_variables))

                # Attach the extra dimension (usually for I/Q) to the results dataset
                mock_h5dataset.dims[len(qprogram_data["dims"]) + len(measurement_data["dims"])].label = "I/Q"

                dims_dict[qprogram_name, measurement_name] = mock_h5dataset.dims

                # Mock the values of the loops for a 2D measure
                dims_dict[qprogram_name, measurement_name][0].values.return_value = [np.linspace(0, 10, 20)]
                dims_dict[qprogram_name, measurement_name][1].values.return_value = [np.linspace(0, 10, 20)]
                dims_dict[qprogram_name, measurement_name].__len__.return_value = 3

        experiment_live_plot.live_plot_figures(dims_dict)
        experiment_live_plot.live_plot(np.linspace(0, 10, 20), qprogram_name, measurement_name)

        # Make sure right plot is created
        assert isinstance(experiment_live_plot._live_plot_fig, go.FigureWidget)

    @patch("h5py.File")
    def test_live_plot_figures_throw_error_for_dim_bigger_than_2d(self, mock_h5file, metadata):
        """Test plot_S21 with 3D data, should raise NotImplementedError."""
        experiment_live_plot = create_autospec(ExperimentLivePlot, instance=True)
        experiment_live_plot._slurm_execution = False
        experiment_live_plot.path = "test.h5"
        experiment_live_plot.live_plot_dict = {}

        experiment_live_plot.live_plot_figures = MethodType(ExperimentLivePlot.live_plot_figures, experiment_live_plot)

        # Mock the get method to return 3D data
        mock_h5group = mock_h5file.create_group("mockpath_group")

        dims_dict = {}
        for qprogram_name, qprogram_data in metadata["qprograms"].items():
            qgroup = mock_h5group.create_group(qprogram_name)

            for measurement_name, measurement_data in qprogram_data["measurements"].items():
                mgroup = qgroup.create_group(measurement_name)
                mock_h5dataset = mgroup.create_dataset("mockpath_dataset", shape=measurement_data["shape"])

                # Create the labels
                for idx, dim_variables in enumerate(qprogram_data["dims"]):
                    mock_h5dataset.dims[idx].label = ",".join(list(dim_variables))
                for idx, dim_variables in enumerate(measurement_data["dims"]):
                    mock_h5dataset.dims[len(qprogram_data["dims"]) + idx].label = ",".join(list(dim_variables))

                # Attach the extra dimension (usually for I/Q) to the results dataset
                mock_h5dataset.dims[len(qprogram_data["dims"]) + len(measurement_data["dims"])].label = "I/Q"

                dims_dict[qprogram_name, measurement_name] = mock_h5dataset.dims

                # Mock the values of the loops for a 2D measure
                dims_dict[qprogram_name, measurement_name][0].values.return_value = [np.linspace(0, 10, 20)]
                dims_dict[qprogram_name, measurement_name][1].values.return_value = [np.linspace(0, 10, 20)]
                dims_dict[qprogram_name, measurement_name][2].values.return_value = [np.linspace(0, 10, 20)]
                dims_dict[qprogram_name, measurement_name].__len__.return_value = 4

        with pytest.raises(NotImplementedError):
            experiment_live_plot.live_plot_figures(dims_dict)


class TestExperimentResultsWriterLivePlot:
    """Test ExperimentResultsWriter class"""

    @patch("qililab.result.experiment_live_plot.ExperimentLivePlot.live_plot_figures", autospec=True)
    def test_set_live_plot(self, mocker_live_plot_figures: MagicMock, metadata):
        """Test setters"""
        with ExperimentResultsWriter(path="mock_path", metadata=metadata, live_plot=True, slurm_execution=True):
            pass  # Just initializing should create the file structure

        # test ExperimentLivePlot call
        mocker_live_plot_figures.assert_called_once()
