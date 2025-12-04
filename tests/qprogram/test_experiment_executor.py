import datetime
import os
import tempfile
from unittest.mock import MagicMock, Mock, call, create_autospec, patch

import numpy as np
import pytest

from qililab.qililab_settings import get_settings
from qililab.extra.quantum_machines import QuantumMachinesMeasurementResult
from qililab.platform.platform import Platform
from qililab.qprogram.blocks import ForLoop, Loop
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.experiment import Experiment
from qililab.qprogram.experiment_executor import ExperimentExecutor
from qililab.qprogram.qprogram import QProgram
from qililab.core.variables import Domain
from qililab.result.experiment_results import ExperimentResults
from qililab.result.qprogram import QProgramResults
from qililab.typings.enums import Parameter
from qililab.waveforms import IQPair, Square


@pytest.fixture(name="platform")
def mock_platform():
    """Fixture to create a mock Platform."""
    qprogram_results = QProgramResults()
    qprogram_results.append_result(
        "readout_bus", QuantumMachinesMeasurementResult(bus="readout", I=np.arange(0, 11), Q=np.arange(100, 111))
    )
    qprogram_results.append_result(
        "readout_bus", QuantumMachinesMeasurementResult(bus="readout", I=np.arange(0, 11), Q=np.arange(100, 111))
    )

    platform = create_autospec(Platform)
    platform.set_parameter = Mock()
    platform.get_parameter = Mock(return_value=1.23)
    platform.execute_qprogram = Mock(return_value=qprogram_results)
    platform.to_dict = Mock(return_value={"name": "platform"})
    platform.experiment_results_base_path = tempfile.gettempdir()
    platform.experiment_results_path_format = "{date}/{time}/{label}.h5"
    platform.set_crosstalk = Mock()
    platform.db_manager = Mock()

    return platform


@pytest.fixture(name="qprogram")
def fixture_qprogram():
    """Fixture to create a mock QProgram."""
    qp = QProgram()
    gain = qp.variable(label="gain", domain=Domain.Voltage)
    with qp.for_loop(gain, 0, 1.0, 0.1):
        qp.set_gain(bus="readout_bus", gain=gain)
        qp.measure(
            "readout_bus",
            waveform=IQPair(Square(1.0, 40), Square(1.0, 40)),
            weights=IQPair(Square(1.0, 100), Square(1.0, 100)),
        )
    with qp.average(shots=1000):
        with qp.loop(gain, values=np.linspace(0.0, 1.0, 11)):
            qp.set_gain(bus="readout_bus", gain=gain)
            qp.measure(
                "readout_bus",
                waveform=IQPair(Square(1.0, 40), Square(1.0, 40)),
                weights=IQPair(Square(1.0, 100), Square(1.0, 100)),
            )

    return qp


@pytest.fixture(name="crosstalk")
def fixture_crosstalk():
    return CrosstalkMatrix.from_array(
        buses=["flux_q0", "flux_q1"], matrix_array=np.array([[1.47046905, 0.12276261], [-0.55322207, 1.58247856]])
    )


def get_qprogram_nshots_by_loop(nshots: int, qprogram: QProgram):
    with qprogram.average(nshots):
        pass
    return qprogram


def get_qprogram_gain_by_get_parameter(gain: float, qprogram: QProgram):
    qprogram.set_gain(bus="readout_bus", gain=gain)
    return qprogram


def get_qprogram_frequency_and_bias_by_loop(frequency: float, bias: float, qprogram: QProgram):
    qprogram.set_frequency(bus="readout", frequency=frequency)
    qprogram.set_gain(bus="readout", gain=bias)
    return qprogram


@pytest.fixture(name="experiment")
def fixture_experiment(qprogram: QProgram, crosstalk: CrosstalkMatrix):
    """Fixture to create a mock Experiment."""
    experiment = Experiment(label="experiment")
    bias = experiment.variable(label="Bias (mV)", domain=Domain.Voltage)
    frequency = experiment.variable(label="Frequency (Hz)", domain=Domain.Frequency)
    nshots = experiment.variable(label="nshots", domain=Domain.Scalar, type=int)

    # Test SetCrosstalk
    experiment.set_crosstalk(crosstalk=crosstalk)

    # Test SetParameter
    experiment.set_parameter(alias="drive_q0", parameter=Parameter.VOLTAGE, value=0.0)
    experiment.set_parameter(alias="drive_q1", parameter=Parameter.VOLTAGE, value=0.5)
    experiment.set_parameter(alias="drive_q2", parameter=Parameter.VOLTAGE, value=1.0)
    experiment.set_parameter(alias="flux_q0", parameter=Parameter.FLUX, value=0.0)

    # Test GetParameter returns a variable that can be reused
    gain = experiment.get_parameter(alias="flux_q0", parameter=Parameter.GAIN)
    # Reused in SetParameter
    experiment.set_parameter(alias="flux_q1", parameter=Parameter.GAIN, value=gain)
    # Reused in ExecuteQProgram
    experiment.execute_qprogram(lambda gain=gain: get_qprogram_gain_by_get_parameter(gain=gain, qprogram=qprogram))

    # Test inner loops
    with experiment.for_loop(bias, 0.0, 1.0, 0.5):
        experiment.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=bias)
        with experiment.loop(frequency, values=np.array([2e9, 3e9])):
            experiment.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=frequency)
            experiment.execute_qprogram(qprogram)
    # Test parallel loops
    with experiment.parallel(loops=[ForLoop(bias, 0.0, 1.0, 0.5), Loop(frequency, values=np.array([2e9, 3e9, 4e9]))]):
        experiment.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=bias)
        experiment.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=frequency)
        experiment.execute_qprogram(qprogram)

    # Test qprogram lambda with variable from loop
    with experiment.for_loop(nshots, 0, 3):
        experiment.execute_qprogram(lambda nshots=nshots: get_qprogram_nshots_by_loop(nshots=nshots, qprogram=qprogram))  # type: ignore

    # Test qprogram lambda with two variables from loop
    with experiment.parallel(loops=[ForLoop(bias, 0.0, 1.0, 0.5), Loop(frequency, values=np.array([2e9, 3e9, 4e9]))]):
        experiment.execute_qprogram(
            lambda frequency=frequency, bias=bias: get_qprogram_frequency_and_bias_by_loop(
                frequency=frequency, bias=bias, qprogram=qprogram
            )
        )

    return experiment


class TestExperimentExecutor:
    """Test ExperimentExecutor class"""

    def test_execute(self, platform, experiment, qprogram, crosstalk, override_settings):
        """Test the execute method to ensure the experiment is executed correctly and results are stored."""
        platform.save_experiment_results_in_database = False
        with override_settings(
            experiment_results_save_in_database=False,
            experiment_live_plot_enabled=False,
            experiment_live_plot_on_slurm=False,
        ):
            executor = ExperimentExecutor(platform=platform, experiment=experiment)
            resuls_path = executor.execute()

        # Check if the correct file path is returned
        assert resuls_path.startswith(os.path.abspath(tempfile.gettempdir()))
        assert resuls_path.endswith(".h5")

        # Check that platform methods were called in the correct order
        expected_calls = [
            call.to_dict(),
            call.set_crosstalk(crosstalk=crosstalk),
            call.set_parameter(alias="drive_q0", parameter=Parameter.VOLTAGE, value=0.0, channel_id=None, output_id=None),
            call.set_parameter(alias="drive_q1", parameter=Parameter.VOLTAGE, value=0.5, channel_id=None, output_id=None),
            call.set_parameter(alias="drive_q2", parameter=Parameter.VOLTAGE, value=1.0, channel_id=None, output_id=None),
            call.set_parameter(alias="flux_q0", parameter=Parameter.FLUX, value=0.0, channel_id=None, output_id=None),
            # Check that get_parameter returns a variable that can be reused
            call.get_parameter(alias="flux_q0", parameter=Parameter.GAIN, channel_id=None, output_id=None),
            call.set_parameter(alias="flux_q1", parameter=Parameter.GAIN, value=1.23, channel_id=None, output_id=None),
            call.execute_qprogram(
                qprogram=get_qprogram_gain_by_get_parameter(gain=1.23, qprogram=qprogram),
                bus_mapping=None,
                calibration=None,
                debug=False,
            ),
            # Start of nested loops
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=0.0, channel_id=None, output_id=None),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=3e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=0.5, channel_id=None, output_id=None),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=3e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=1.0, channel_id=None, output_id=None),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=3e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            # End of nested loops
            # Start of parallel loop
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=0.0, channel_id=None, output_id=None),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=2e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=0.5, channel_id=None, output_id=None),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=3e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=1.0, channel_id=None, output_id=None),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=4e9, channel_id=None, output_id=None),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            # End of parallel loop
            # Start of nshots loop with lambda execution
            call.execute_qprogram(
                qprogram=get_qprogram_nshots_by_loop(nshots=0, qprogram=qprogram),
                bus_mapping=None,
                calibration=None,
                debug=False,
            ),
            call.execute_qprogram(
                qprogram=get_qprogram_nshots_by_loop(nshots=1, qprogram=qprogram),
                bus_mapping=None,
                calibration=None,
                debug=False,
            ),
            call.execute_qprogram(
                qprogram=get_qprogram_nshots_by_loop(nshots=2, qprogram=qprogram),
                bus_mapping=None,
                calibration=None,
                debug=False,
            ),
            # End of nshots loop
            # Start of parallel loop with lambda execution
            call.execute_qprogram(
                qprogram=get_qprogram_frequency_and_bias_by_loop(frequency=2e9, bias=0.0, qprogram=qprogram),
                bus_mapping=None,
                calibration=None,
                debug=False,
            ),
            call.execute_qprogram(
                qprogram=get_qprogram_frequency_and_bias_by_loop(frequency=3e9, bias=0.5, qprogram=qprogram),
                bus_mapping=None,
                calibration=None,
                debug=False,
            ),
            call.execute_qprogram(
                qprogram=get_qprogram_frequency_and_bias_by_loop(frequency=4e9, bias=1.0, qprogram=qprogram),
                bus_mapping=None,
                calibration=None,
                debug=False,
            ),
            # End of parallel loop
        ]

        # If you want to ensure the exact sequence across all calls
        platform.assert_has_calls(expected_calls, any_order=False)

        with ExperimentResults(resuls_path) as experiment_results:
            measurement_data = np.column_stack((np.arange(0, 11), np.arange(100, 111)))

            # Single QProgram
            qprogram0_measurement0_data, _ = experiment_results.get(0, 0)
            assert qprogram0_measurement0_data.shape == (11, 2)
            assert np.allclose(qprogram0_measurement0_data, measurement_data[:, :])

            qprogram0_measurement1_data, _ = experiment_results.get(0, 1)
            assert qprogram0_measurement1_data.shape == (11, 2)
            assert np.allclose(qprogram0_measurement1_data, measurement_data[:, :])

            # QProgram within nested loops
            qprogram1_measurement0_data, _ = experiment_results.get(1, 0)
            assert qprogram1_measurement0_data.shape == (3, 2, 11, 2)
            assert np.allclose(qprogram1_measurement0_data, measurement_data[None, None, :, :])

            qprogram1_measurement1_data, _ = experiment_results.get(1, 1)
            assert qprogram1_measurement1_data.shape == (3, 2, 11, 2)
            assert np.allclose(qprogram1_measurement1_data, measurement_data[None, None, :, :])

            # QProgram within parallel loops
            qprogram2_measurement0_data, _ = experiment_results.get(2, 0)
            assert qprogram2_measurement0_data.shape == (3, 11, 2)
            assert np.allclose(qprogram2_measurement0_data, measurement_data[None, :, :])

            qprogram2_measurement1_data, _ = experiment_results.get(2, 1)
            assert qprogram2_measurement1_data.shape == (3, 11, 2)
            assert np.allclose(qprogram2_measurement1_data, measurement_data[None, :, :])

    @patch("qililab.platform.platform.get_db_manager")
    @patch("qililab.result.experiment_results_writer.h5py.File")
    def test_execute_database_metadata_only(
        self, mock_h5_file, mock_get_db_manager, platform, experiment, override_settings
    ):
        """Test the execute with database as True."""

        platform.db_optional_identifier = "test"
        expected_result_path = "/tmp/20250710/155901/experiment.h5"
        mock_measurement = Mock()
        mock_measurement.result_path = expected_result_path

        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        platform.db_manager = mock_db_manager

        mock_file = MagicMock()
        mock_h5_file.return_value = mock_file

        experiment.label = "experiment"
        experiment.description = "Test"

        with (
            patch.object(ExperimentExecutor, "_prepare_operations", return_value=[]),
            patch.object(ExperimentExecutor, "_execute_operations", return_value=None),
            patch.object(ExperimentExecutor, "_create_results_path", return_value=expected_result_path),
        ):

            mock_writer = MagicMock()
            mock_writer.__enter__.return_value = mock_writer
            mock_writer.__exit__.return_value = None
            mock_writer.results_path = expected_result_path
            mock_writer.execution_time = 0.0
            mock_writer_cls = MagicMock()
            mock_writer_cls.return_value = mock_writer

            with override_settings(experiment_results_save_in_database=True):

                executor = ExperimentExecutor(
                    platform=platform,
                    experiment=experiment,
                    job_id=1,
                    sample="sample_test",
                    cooldown="cooldown_test",
                )
                executor.loop_indices = True
                executor.execute()

            assert executor._db_metadata == {
                "job_id": 1,
                "cooldown": "cooldown_test",
                "experiment_name": "experiment",
                "sample_name": "sample_test",
            }

    @patch("qililab.platform.platform.get_db_manager")
    @patch("qililab.result.experiment_results_writer.h5py.File")
    def test_execute_database_no_job_id_raises_error(
        self, mock_h5_file, mock_get_db_manager, platform, experiment, override_settings
    ):
        """Test the execute with database as True."""

        get_settings().experiment_results_save_in_database = True
        platform.db_optional_identifier = "test"
        expected_result_path = "/tmp/20250710/155901/experiment.h5"
        mock_measurement = Mock()
        mock_measurement.result_path = expected_result_path

        mock_db_manager = Mock()
        mock_get_db_manager.return_value = mock_db_manager
        platform.db_manager = mock_db_manager

        mock_file = MagicMock()
        mock_h5_file.return_value = mock_file

        experiment.label = "experiment"
        experiment.description = "Test"

        with (
            patch.object(ExperimentExecutor, "_prepare_operations", return_value=[]),
            patch.object(ExperimentExecutor, "_execute_operations", return_value=None),
            patch.object(ExperimentExecutor, "_create_results_path", return_value=expected_result_path),
        ):

            mock_writer = MagicMock()
            mock_writer.__enter__.return_value = mock_writer
            mock_writer.__exit__.return_value = None
            mock_writer.results_path = expected_result_path
            mock_writer.execution_time = 0.0
            mock_writer_cls = MagicMock()
            mock_writer_cls.return_value = mock_writer

            with override_settings(experiment_results_save_in_database=True):

                executor = ExperimentExecutor(
                    platform=platform,
                    experiment=experiment,
                    sample="sample_test",
                    cooldown="cooldown_test",
                )
                executor.loop_indices = True

                with pytest.raises(ValueError, match="Job id has not been defined."):
                    executor.execute()
