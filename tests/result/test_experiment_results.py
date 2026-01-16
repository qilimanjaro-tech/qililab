# pylint: disable=protected-access
import os
from datetime import datetime
from pathlib import Path
from types import MethodType
from unittest.mock import MagicMock, create_autospec, patch

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest

from qililab.result.experiment_results import DimensionInfo, ExperimentResults
from qililab.result.experiment_results_writer import ExperimentMetadata, ExperimentResultsWriter

mpl.use("Agg")  # Use non-interactive backend for testing


# Dummy path for testing
EXPERIMENT_RESULTS_PATH = "dummy.hdf5"


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


@pytest.fixture(name="experiment_results")
def mock_experiment_results(metadata, override_settings):
    """Create a mock HDF5 file structure for testing"""
    with override_settings(experiment_live_plot_enabled=False, experiment_live_plot_on_slurm=False):
        with ExperimentResultsWriter(
            path=EXPERIMENT_RESULTS_PATH,
            metadata=metadata,
            db_metadata=None,
            db_manager=None,
        ):
            ...
    yield EXPERIMENT_RESULTS_PATH
    Path(EXPERIMENT_RESULTS_PATH).unlink()


class TestExperimentResults:
    """Test ExperimentResults class"""

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
            value = exp_results["QProgram_0", "Measurement_0", 0, 0, 0]
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

    def test_get_method(self, experiment_results):
        """Test get method"""
        with ExperimentResults(experiment_results) as exp_results:
            data, dims = exp_results.get()
            assert data.shape == (3, 4, 2)
            assert len(dims) == 3
            assert dims[0].labels[0] == "x"
            assert dims[1].labels[0] == "y"
            assert dims[2].labels[0] == "I/Q"

            data, dims = exp_results.get(qprogram=0, measurement=0)
            assert data.shape == (3, 4, 2)
            assert len(dims) == 3
            assert dims[0].labels[0] == "x"
            assert dims[1].labels[0] == "y"
            assert dims[2].labels[0] == "I/Q"

            data, dims = exp_results.get(qprogram="QProgram_0", measurement="Measurement_0")
            assert data.shape == (3, 4, 2)
            assert len(dims) == 3
            assert dims[0].labels[0] == "x"
            assert dims[1].labels[0] == "y"
            assert dims[2].labels[0] == "I/Q"

    def test_plot_S21_one_dimension(self):
        """Test plot_S21 with 1D data and verify the plot correctness."""
        experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

        # Manually set the plot_S21 method to the real one
        experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

        # Mock the get method to return 1D data
        data = np.random.rand(100, 2)  # 100 data points, real and imaginary parts
        dims = [
            DimensionInfo(labels=["Frequency (Hz)"], values=[np.linspace(1e6, 1e7, 100)]),
            DimensionInfo(labels=["I/Q"], values=[]),
        ]

        experiment_results.get.return_value = (data, dims)

        # Call the plot_S21 method
        experiment_results.plot_S21()

        # Ensure get was called correctly
        experiment_results.get.assert_called_with(qprogram=0, measurement=0)

        # Retrieve the current figure and axes
        fig = plt.gcf()
        ax1 = fig.axes[0]

        # Check the title, labels, and line data
        assert ax1.get_title() == experiment_results.path
        assert ax1.get_xlabel() == "Frequency (Hz)"
        assert ax1.get_ylabel() == r"$|S_{21}|$"

        lines = ax1.get_lines()
        assert len(lines) == 1  # Should have one line plotted

        # Verify the data plotted
        x_plotted = lines[0].get_xdata()
        y_plotted = lines[0].get_ydata()

        # Recompute s21 to compare
        s21 = data[:, 0] + 1j * data[:, 1]
        s21_db = 20 * np.log10(np.abs(s21))
        x_expected = dims[0].values[0]

        np.testing.assert_array_almost_equal(x_plotted, x_expected)
        np.testing.assert_array_almost_equal(y_plotted, s21_db)

        # Close the plot
        plt.close(fig)

        # Verify that the plot was saved to a file.
        plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
        assert os.path.exists(plot_path)

        # Remove the file
        os.remove(plot_path)

        # Verify that if `save_plot == False` then the plot is not saved.
        experiment_results.plot_S21(save_plot=False)
        assert not os.path.exists(plot_path)

        # Close the plot
        plt.close(plt.gcf())

    def test_plot_S21_one_dimension_secondary_axis(self):
        """Test plot_S21 with 1D data and secondary x-axis."""
        experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

        # Manually set the plot_S21 method to the real one
        experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

        # Mock the get method to return 1D data with secondary axis data
        data = np.random.rand(100, 2)  # 100 data points, real and imaginary parts
        dims = [
            DimensionInfo(
                labels=["Frequency (Hz)", "Time (s)"], values=[np.linspace(1e6, 1e7, 100), np.linspace(0, 1, 100)]
            ),
            DimensionInfo(labels=["I/Q"], values=[]),
        ]

        experiment_results.get.return_value = (data, dims)

        # Call the plot_S21 method
        experiment_results.plot_S21()

        # Retrieve the current figure and axes
        fig = plt.gcf()
        ax1 = fig.axes[0]
        ax2 = fig.axes[1]

        # Verify that the secondary axis is created
        assert ax2 is not None, "Secondary x-axis was not created."

        # Check labels
        assert ax1.get_xlabel() == "Frequency (Hz)"
        assert ax2.get_xlabel() == "Time (s)"

        # Check limits
        np.testing.assert_almost_equal(ax2.get_xlim(), [0, 1])

        # Check ticks
        expected_ticks = np.linspace(0, 1, num=6)
        np.testing.assert_array_almost_equal(ax2.get_xticks(), expected_ticks)

        # Close the plot
        plt.close(fig)

        # Verify that the plot was saved to a file.
        plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
        assert os.path.exists(plot_path)

        # Remove the file
        os.remove(plot_path)

        # Verify that if `save_plot == False` then the plot is not saved.
        experiment_results.plot_S21(save_plot=False)
        assert not os.path.exists(plot_path)

        # Close the plot
        plt.close(plt.gcf())

    def test_plot_S21_two_dimensions(self):
        """Test plot_S21 with 2D data and verify the plot correctness."""
        experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

        # Manually set the plot_S21 method to the real one
        experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

        # Mock the get method to return 2D data
        data = np.random.rand(50, 50, 2)  # 50x50 data points, real and imaginary parts
        dims = [
            DimensionInfo(labels=["Frequency (Hz)"], values=[np.linspace(1e6, 1e7, 50)]),
            DimensionInfo(labels=["Voltage (V)"], values=[np.linspace(0, 1, 50)]),
            DimensionInfo(labels=["I/Q"], values=[]),
        ]

        experiment_results.get.return_value = (data, dims)

        # Call the plot_S21 method
        experiment_results.plot_S21()

        # Ensure get was called correctly
        experiment_results.get.assert_called_with(qprogram=0, measurement=0)

        # Retrieve the current figure and axes
        fig = plt.gcf()
        ax1 = fig.axes[0]
        colorbar = fig.axes[1]

        # Check the title and labels
        assert ax1.get_title() == experiment_results.path
        assert ax1.get_xlabel() == "Frequency (Hz)"
        assert ax1.get_ylabel() == "Voltage (V)"

        # Retrieve the QuadMesh object from pcolormesh
        quadmesh = ax1.collections[0]
        assert isinstance(quadmesh, mpl.collections.QuadMesh)

        # Verify the data plotted
        s21 = data[:, :, 0] + 1j * data[:, :, 1]
        s21_db = 20 * np.log10(np.abs(s21))

        # Get the mesh data
        mesh_array = quadmesh.get_array().reshape(s21_db.T.shape)

        # Compare the mesh data to s21_db
        np.testing.assert_array_almost_equal(mesh_array, s21_db.T)

        # Verify that the colorbar axes exist and have correct properties
        assert colorbar is not None, "Colorbar axes was not created."

        # Colorbar axes usually have no labels
        assert not colorbar.get_xlabel(), "Colorbar axes should not have an x-label."
        assert not colorbar.get_ylabel(), "Colorbar axes should not have a y-label."

        # Close the plot
        plt.close(fig)

        # Verify that the plot was saved to a file.
        plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
        assert os.path.exists(plot_path)

        # Remove the file
        os.remove(plot_path)

        # Verify that if `save_plot == False` then the plot is not saved.
        experiment_results.plot_S21(save_plot=False)
        assert not os.path.exists(plot_path)

        # Close the plot
        plt.close(plt.gcf())

    def test_plot_S21_two_dimensions_secondary_axes(self):
        """Test plot_S21 with 2D data and secondary axes."""
        experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

        # Manually set the plot_S21 method to the real one
        experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

        # Mock the get method to return 2D data with secondary axis data
        data = np.random.rand(50, 50, 2)  # 50x50 data points, real and imaginary parts
        dims = [
            DimensionInfo(
                labels=["Frequency (Hz)", "Wavelength (m)"],
                values=[np.linspace(1e6, 1e7, 50), np.linspace(300e-9, 800e-9, 50)],
            ),
            DimensionInfo(
                labels=["Voltage (V)", "Current (A)"], values=[np.linspace(0, 1, 50), np.linspace(0, 10, 50)]
            ),
            DimensionInfo(labels=["I/Q"], values=[]),
        ]

        experiment_results.get.return_value = (data, dims)

        # Call the plot_S21 method
        experiment_results.plot_S21()

        # Retrieve the current figure and axes
        fig = plt.gcf()
        ax1 = fig.axes[0]
        colorbar = fig.axes[1]
        ax2 = fig.axes[2]
        ax3 = fig.axes[3]

        # Verify that the secondary axes are created
        assert ax2 is not None, "Secondary x-axis was not created."
        assert ax3 is not None, "Secondary y-axis was not created."

        # Check labels
        assert ax1.get_xlabel() == "Frequency (Hz)"
        assert ax1.get_ylabel() == "Voltage (V)"
        assert ax2.get_xlabel() == "Wavelength (m)"
        assert ax3.get_ylabel() == "Current (A)"

        # Check limits
        np.testing.assert_almost_equal(ax2.get_xlim(), [300e-9, 800e-9])
        np.testing.assert_almost_equal(ax3.get_ylim(), [0, 10])

        # Check ticks for ax2 (secondary x-axis)
        expected_xticks = np.linspace(300e-9, 800e-9, num=6)
        np.testing.assert_array_almost_equal(ax2.get_xticks(), expected_xticks)

        # Check ticks for ax3 (secondary y-axis)
        expected_yticks = np.linspace(0, 10, num=6)
        np.testing.assert_array_almost_equal(ax3.get_yticks(), expected_yticks)

        # Verify that the colorbar axes exist and have correct properties
        assert colorbar is not None, "Colorbar axes was not created."

        # Colorbar axes usually have no labels
        assert not colorbar.get_xlabel(), "Colorbar axes should not have an x-label."
        assert not colorbar.get_ylabel(), "Colorbar axes should not have a y-label."

        # Close the plot
        plt.close(fig)

        # Verify that the plot was saved to a file.
        plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
        assert os.path.exists(plot_path)

        # Remove the file
        os.remove(plot_path)

        # Verify that if `save_plot == False` then the plot is not saved.
        experiment_results.plot_S21(save_plot=False)
        assert not os.path.exists(plot_path)

        # Close the plot
        plt.close(plt.gcf())

    def test_plot_S21_three_dimensions(self):
        """Test plot_S21 with 3D data, should raise NotImplementedError."""
        experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

        # Manually set the plot_S21 method to the real one
        experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

        # Mock the get method to return 3D data
        data = np.random.rand(10, 10, 10, 2)
        dims = [
            {"labels": ["Frequency (Hz)"], "values": [np.linspace(1e6, 1e7, 10)]},
            {"labels": ["Voltage (V)"], "values": [np.linspace(0, 1, 10)]},
            {"labels": ["Temperature (K)"], "values": [np.linspace(0, 300, 10)]},
            {"labels": ["I/Q"], "values": []},
        ]

        experiment_results.get.return_value = (data, dims)

        # Check that NotImplementedError is raised
        with pytest.raises(NotImplementedError):
            experiment_results.plot_S21()

        # Ensure get was called correctly
        experiment_results.get.assert_called_with(qprogram=0, measurement=0)

    def test_plot_S21_with_qprogram_and_measurement_strings(self):
        """Test plot_S21 with string qprogram and measurement and verify the plot correctness."""
        experiment_results = create_autospec(ExperimentResults, instance=True, path="test.h5")

        # Manually set the plot_S21 method to the real one
        experiment_results.plot_S21 = MethodType(ExperimentResults.plot_S21, experiment_results)

        # Mock the get method to return 1D data
        data = np.random.rand(100, 2)
        dims = [
            DimensionInfo(labels=["Frequency (Hz)"], values=[np.linspace(1e6, 1e7, 100)]),
            DimensionInfo(labels=["I/Q"], values=[]),
        ]

        experiment_results.get = MagicMock(return_value=(data, dims))

        # Call the plot_S21 method with string parameters
        qprogram = "program1"
        measurement = "measurement1"
        experiment_results.plot_S21(qprogram=qprogram, measurement=measurement)

        # Ensure get was called correctly
        experiment_results.get.assert_called_with(qprogram=qprogram, measurement=measurement)

        # Retrieve the current figure and axes
        fig = plt.gcf()
        ax1 = fig.axes[0]

        # Check the title, labels, and line data
        assert ax1.get_title() == experiment_results.path
        assert ax1.get_xlabel() == "Frequency (Hz)"
        assert ax1.get_ylabel() == r"$|S_{21}|$"

        lines = ax1.get_lines()
        assert len(lines) == 1  # Should have one line plotted

        # Verify the data plotted
        x_plotted = lines[0].get_xdata()
        y_plotted = lines[0].get_ydata()

        # Recompute s21 to compare
        s21 = data[:, 0] + 1j * data[:, 1]
        s21_db = 20 * np.log10(np.abs(s21))
        x_expected = dims[0].values[0]

        np.testing.assert_array_almost_equal(x_plotted, x_expected)
        np.testing.assert_array_almost_equal(y_plotted, s21_db)

        # Close the plot
        plt.close(fig)

        # Verify that the plot was saved to a file.
        plot_path = os.path.join(os.path.dirname(experiment_results.path), ExperimentResults.S21_PLOT_NAME)
        assert os.path.exists(plot_path)

        # Remove the file
        os.remove(plot_path)

        # Verify that if `save_plot == False` then the plot is not saved.
        experiment_results.plot_S21(save_plot=False)
        assert not os.path.exists(plot_path)

        # Close the plot
        plt.close(plt.gcf())


class TestExperimentResultsWriter:
    """Test ExperimentResultsWriter class"""

    @patch("h5py.File")
    def test_create_results_file(self, mock_h5file, metadata, override_settings):
        """Test file creation"""
        # Test that the results file is created with the correct structure
        with override_settings(experiment_live_plot_enabled=False, experiment_live_plot_on_slurm=False):
            with ExperimentResultsWriter(
                path="mock_path",
                metadata=metadata,
                db_metadata=None,
                db_manager=None,
            ):
                pass  # Just initializing should create the file structure

        assert mock_h5file.called
        mock_h5file.assert_called_with("mock_path", mode="w", libver="latest")

    def test_setters(self, experiment_results, override_settings):
        """Test setters"""
        with override_settings(experiment_live_plot_enabled=False, experiment_live_plot_on_slurm=False):
            with ExperimentResultsWriter(
                path=experiment_results,
                metadata={},
                db_metadata=None,
                db_manager=None,
            ) as exp_writer:
                # test experiment property
                exp_writer.experiment = "new_experiment"
                assert exp_writer.experiment == "new_experiment"

                # write again to assert that HDF5 old partition is deleted correctly
                exp_writer.experiment = "newer_experiment"
                assert exp_writer.experiment == "newer_experiment"

                # test platform property
                exp_writer.platform = "new_platform"
                assert exp_writer.platform == "new_platform"

                # write again to assert that HDF5 old partition is deleted correctly
                exp_writer.platform = "newer_platform"
                assert exp_writer.platform == "newer_platform"

                # test crosstalk property
                exp_writer.crosstalk = "new_crosstalk"
                assert exp_writer.crosstalk == "new_crosstalk"

                # write again to assert that HDF5 old partition is deleted correctly
                exp_writer.crosstalk = "newer_crosstalk"
                assert exp_writer.crosstalk == "newer_crosstalk"

                # test executed_at property
                exp_writer.executed_at = datetime(2025, 1, 1, 0, 0, 0)
                assert exp_writer.executed_at == datetime(2025, 1, 1, 0, 0, 0)

                # write again to assert that HDF5 old partition is deleted correctly
                exp_writer.executed_at = datetime(2026, 1, 1, 0, 0, 0)
                assert exp_writer.executed_at == datetime(2026, 1, 1, 0, 0, 0)

                # test execution_time property
                exp_writer.execution_time = 1.23
                assert exp_writer.execution_time == 1.23

                # write again to assert that HDF5 old partition is deleted correctly
                exp_writer.execution_time = 4.56
                assert exp_writer.execution_time == 4.56

    @patch("qililab.result.experiment_live_plot.ExperimentLivePlot.live_plot")
    @patch("qililab.result.experiment_live_plot.ExperimentLivePlot.live_plot_figures")
    def test_setitem_calls_live_plot(self, mock_figures, mock_live_plot, metadata, override_settings):
        """Test that __setitem__ calls results_liveplot.live_plot when live_plot is True"""
        path = "test_live_plot_writer.h5"  # ✅ temp path

        with override_settings(experiment_live_plot_enabled=True, experiment_live_plot_on_slurm=False):
            with ExperimentResultsWriter(
                path=str(path),
                metadata=metadata,
                db_metadata=None,
                db_manager=None,
            ) as writer:
                writer["QProgram_0", "Measurement_0", 0, 0, 0] = 1.0

                # Assert live_plot was called
                mock_live_plot.assert_called_once()

        path_obj = Path(path)
        if path_obj.exists():
            path_obj.unlink()
