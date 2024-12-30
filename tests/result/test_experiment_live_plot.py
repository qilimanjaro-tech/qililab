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

    def test_live_plot_figures(self):
        """Test plot_S21 with 1D data and verify the plot correctness."""
        experiment_live_plot = create_autospec(ExperimentLivePlot, instance=True)
        experiment_live_plot._slurm_execution = False
        experiment_live_plot.path = "test.h5"
        experiment_live_plot.live_plot_dict = {}

        # Manually set the plot_S21 method to the real one
        experiment_live_plot._live_plot_figures = MethodType(
            ExperimentLivePlot._live_plot_figures, experiment_live_plot
        )

        # Mock the get method to return 1D data
        dims = {
            ("Qprogram_0", "Measurement_0"): [
                DimensionInfo(labels=["Frequency (Hz)"], values=[np.linspace(1e6, 1e7, 100)]),
                DimensionInfo(labels=["I/Q"], values=[]),
            ]
        }  # MAAAAAAAL

        # experiment_live_plot.get.return_value = (data, dims)

        # Call the plot_S21 method
        experiment_live_plot._live_plot_figures(dims)

        # Make sure right plot is created
        assert isinstance(experiment_live_plot._live_plot_fig, go.FigureWidget)

    #     # Retrieve the current figure and axes
    #     fig = plt.gcf()
    #     ax1 = fig.axes[0]

    #     # Check the title, labels, and line data
    #     assert ax1.get_title() == experiment_results.path
    #     assert ax1.get_xlabel() == "Frequency (Hz)"
    #     assert ax1.get_ylabel() == r"$|S_{21}|$"

    #     lines = ax1.get_lines()
    #     assert len(lines) == 1  # Should have one line plotted

    #     # Verify the data plotted
    #     x_plotted = lines[0].get_xdata()
    #     y_plotted = lines[0].get_ydata()

    #     # Recompute s21 to compare
    #     s21 = data[:, 0] + 1j * data[:, 1]
    #     s21_db = 20 * np.log10(np.abs(s21))
    #     x_expected = dims[0].values[0]

    #     np.testing.assert_array_almost_equal(x_plotted, x_expected)
    #     np.testing.assert_array_almost_equal(y_plotted, s21_db)

    #     # Close the plot
    #     plt.close(fig)

    #     # Verify that the plot was saved to a file.
    #     plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
    #     assert os.path.exists(plot_path)

    #     # Remove the file
    #     os.remove(plot_path)

    #     # Verify that if `save_plot == False` then the plot is not saved.
    #     experiment_results.plot_S21(save_plot=False)
    #     assert not os.path.exists(plot_path)

    #     # Close the plot
    #     plt.close(plt.gcf())

    # def test_live_plot_figures_slurm(self):
    #     """Test plot_S21 with 1D data and verify the plot correctness."""
    #     experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

    #     # Manually set the plot_S21 method to the real one
    #     experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

    #     # Mock the get method to return 1D data
    #     data = np.random.rand(100, 2)  # 100 data points, real and imaginary parts
    #     dims = [
    #         DimensionInfo(labels=["Frequency (Hz)"], values=[np.linspace(1e6, 1e7, 100)]),
    #         DimensionInfo(labels=["I/Q"], values=[]),
    #     ]

    #     experiment_results.get.return_value = (data, dims)

    #     # Call the plot_S21 method
    #     experiment_results.plot_S21()

    #     # Ensure get was called correctly
    #     experiment_results.get.assert_called_with(qprogram=0, measurement=0)

    #     # Retrieve the current figure and axes
    #     fig = plt.gcf()
    #     ax1 = fig.axes[0]

    #     # Check the title, labels, and line data
    #     assert ax1.get_title() == experiment_results.path
    #     assert ax1.get_xlabel() == "Frequency (Hz)"
    #     assert ax1.get_ylabel() == r"$|S_{21}|$"

    #     lines = ax1.get_lines()
    #     assert len(lines) == 1  # Should have one line plotted

    #     # Verify the data plotted
    #     x_plotted = lines[0].get_xdata()
    #     y_plotted = lines[0].get_ydata()

    #     # Recompute s21 to compare
    #     s21 = data[:, 0] + 1j * data[:, 1]
    #     s21_db = 20 * np.log10(np.abs(s21))
    #     x_expected = dims[0].values[0]

    #     np.testing.assert_array_almost_equal(x_plotted, x_expected)
    #     np.testing.assert_array_almost_equal(y_plotted, s21_db)

    #     # Close the plot
    #     plt.close(fig)

    #     # Verify that the plot was saved to a file.
    #     plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
    #     assert os.path.exists(plot_path)

    #     # Remove the file
    #     os.remove(plot_path)

    #     # Verify that if `save_plot == False` then the plot is not saved.
    #     experiment_results.plot_S21(save_plot=False)
    #     assert not os.path.exists(plot_path)

    #     # Close the plot
    #     plt.close(plt.gcf())

    # def test_live_plot(self):
    #     """Test plot_S21 with 1D data and secondary x-axis."""
    #     experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

    #     # Manually set the plot_S21 method to the real one
    #     experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

    #     # Mock the get method to return 1D data with secondary axis data
    #     data = np.random.rand(100, 2)  # 100 data points, real and imaginary parts
    #     dims = [
    #         DimensionInfo(
    #             labels=["Frequency (Hz)", "Time (s)"], values=[np.linspace(1e6, 1e7, 100), np.linspace(0, 1, 100)]
    #         ),
    #         DimensionInfo(labels=["I/Q"], values=[]),
    #     ]

    #     experiment_results.get.return_value = (data, dims)

    #     # Call the plot_S21 method
    #     experiment_results.plot_S21()

    #     # Retrieve the current figure and axes
    #     fig = plt.gcf()
    #     ax1 = fig.axes[0]
    #     ax2 = fig.axes[1]

    #     # Verify that the secondary axis is created
    #     assert ax2 is not None, "Secondary x-axis was not created."

    #     # Check labels
    #     assert ax1.get_xlabel() == "Frequency (Hz)"
    #     assert ax2.get_xlabel() == "Time (s)"

    #     # Check limits
    #     np.testing.assert_almost_equal(ax2.get_xlim(), [0, 1])

    #     # Check ticks
    #     expected_ticks = np.linspace(0, 1, num=6)
    #     np.testing.assert_array_almost_equal(ax2.get_xticks(), expected_ticks)

    #     # Close the plot
    #     plt.close(fig)

    #     # Verify that the plot was saved to a file.
    #     plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
    #     assert os.path.exists(plot_path)

    #     # Remove the file
    #     os.remove(plot_path)

    #     # Verify that if `save_plot == False` then the plot is not saved.
    #     experiment_results.plot_S21(save_plot=False)
    #     assert not os.path.exists(plot_path)

    #     # Close the plot
    #     plt.close(plt.gcf())

    # def test_live_plot_slurm(self):
    #     """Test plot_S21 with 1D data and secondary x-axis."""
    #     experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

    #     # Manually set the plot_S21 method to the real one
    #     experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

    #     # Mock the get method to return 1D data with secondary axis data
    #     data = np.random.rand(100, 2)  # 100 data points, real and imaginary parts
    #     dims = [
    #         DimensionInfo(
    #             labels=["Frequency (Hz)", "Time (s)"], values=[np.linspace(1e6, 1e7, 100), np.linspace(0, 1, 100)]
    #         ),
    #         DimensionInfo(labels=["I/Q"], values=[]),
    #     ]

    #     experiment_results.get.return_value = (data, dims)

    #     # Call the plot_S21 method
    #     experiment_results.plot_S21()

    #     # Retrieve the current figure and axes
    #     fig = plt.gcf()
    #     ax1 = fig.axes[0]
    #     ax2 = fig.axes[1]

    #     # Verify that the secondary axis is created
    #     assert ax2 is not None, "Secondary x-axis was not created."

    #     # Check labels
    #     assert ax1.get_xlabel() == "Frequency (Hz)"
    #     assert ax2.get_xlabel() == "Time (s)"

    #     # Check limits
    #     np.testing.assert_almost_equal(ax2.get_xlim(), [0, 1])

    #     # Check ticks
    #     expected_ticks = np.linspace(0, 1, num=6)
    #     np.testing.assert_array_almost_equal(ax2.get_xticks(), expected_ticks)

    #     # Close the plot
    #     plt.close(fig)

    #     # Verify that the plot was saved to a file.
    #     plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
    #     assert os.path.exists(plot_path)

    #     # Remove the file
    #     os.remove(plot_path)

    #     # Verify that if `save_plot == False` then the plot is not saved.
    #     experiment_results.plot_S21(save_plot=False)
    #     assert not os.path.exists(plot_path)

    #     # Close the plot
    #     plt.close(plt.gcf())


class TestExperimentResultsWriterLivePlot:
    """Test ExperimentResultsWriter class"""

    @patch("qililab.result.experiment_live_plot.ExperimentLivePlot._live_plot_figures", autospec=True)
    def test_set_live_plot(self, mocker_live_plot_figures: MagicMock, metadata):
        """Test setters"""
        with ExperimentResultsWriter(path="mock_path", metadata=metadata, live_plot=True, slurm_execution=True):
            pass  # Just initializing should create the file structure

        # test ExperimentLivePlot call
        mocker_live_plot_figures.assert_called_once()
