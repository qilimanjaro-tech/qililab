from unittest.mock import Mock, call, create_autospec

import numpy as np
import pytest

from qililab.platform.platform import Platform
from qililab.qprogram.experiment import Experiment
from qililab.qprogram.experiment_executor import ExperimentExecutor
from qililab.qprogram.qprogram import Domain, QProgram
from qililab.result.qprogram import QProgramResults, QuantumMachinesMeasurementResult
from qililab.typings.enums import Parameter


@pytest.fixture(name="platform")
def mock_platform():
    """Fixture to create a mock Platform."""
    qprogram_results = QProgramResults()
    qprogram_results.append_result(
        "readout_bus", QuantumMachinesMeasurementResult(I=np.arange(0, 11), Q=np.arange(100, 111))
    )

    platform = create_autospec(Platform)
    platform.set_parameter = Mock()
    platform.execute_qprogram = Mock(return_value=qprogram_results)

    return platform


@pytest.fixture(name="qprogram")
def fixture_qprogram():
    """Fixture to create a mock QProgram."""
    qp = QProgram()
    bias_x = qp.variable(label="bias_x voltage", domain=Domain.Voltage)
    with qp.for_loop(bias_x, 0, 10, 1):
        qp.set_gain(bus="readout_bus", gain=bias_x)

    return qp


@pytest.fixture(name="experiment")
def fixture_experiment(qprogram: QProgram):
    """Fixture to create a mock Experiment."""
    experiment = Experiment()
    experiment = Experiment()
    bias_z = experiment.variable(label="bias_z voltage", domain=Domain.Voltage)
    frequency = experiment.variable(label="LO Frequency", domain=Domain.Frequency)
    experiment.set_parameter(alias="drive_q0", parameter=Parameter.VOLTAGE, value=0.5)
    experiment.set_parameter(alias="drive_q1", parameter=Parameter.VOLTAGE, value=0.5)
    experiment.set_parameter(alias="drive_q2", parameter=Parameter.VOLTAGE, value=0.5)
    with experiment.for_loop(bias_z, 0.0, 1.0, 0.5):
        experiment.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=bias_z)
        with experiment.loop(frequency, values=np.array([2e9, 3e9])):
            experiment.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=frequency)
            experiment.execute_qprogram(qprogram)

    return experiment


class TestExperimentExecutor:
    def test_prepare(self, platform, experiment):
        """Test the prepare method to ensure it calculates the correct loop values and shape."""
        executor = ExperimentExecutor(platform=platform, experiment=experiment, results_path="/tmp/")
        executor._prepare()

        np.testing.assert_array_equal(executor.loop_values["bias_z voltage"], np.array([0.0, 0.5, 1.0]))
        np.testing.assert_array_equal(executor.loop_values["LO Frequency"], np.array([2e9, 3e9]))

        # First two dimensions are the experiment's loops, third is the qprogram's loop, fourth is the I/Q channels
        assert executor.shape == (3, 2, 11, 2)

    def test_execute(self, platform, experiment, qprogram):
        """Test the execute method to ensure the experiment is executed correctly and results are stored."""
        executor = ExperimentExecutor(platform=platform, experiment=experiment, results_path="/tmp/")
        path = executor.execute()

        # Check if the correct file path is returned
        assert path.startswith("/tmp/")
        assert path.endswith("data.h5")

        # Check that platform methods were called in the correct order
        expected_calls = [
            # First loop: bias_z, second loop: frequency
            # The order of calls follows the nested loop structure
            # Calls in the first iteration of the outer loop (bias_z = 0.0)
            call.set_parameter(alias="drive_q0", parameter=Parameter.VOLTAGE, value=0.5),
            call.set_parameter(alias="drive_q1", parameter=Parameter.VOLTAGE, value=0.5),
            call.set_parameter(alias="drive_q2", parameter=Parameter.VOLTAGE, value=0.5),
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=0.0),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=2e9),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=3e9),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=0.5),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=2e9),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=3e9),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.VOLTAGE, value=1.0),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=2e9),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
            call.set_parameter(alias="readout_bus", parameter=Parameter.LO_FREQUENCY, value=3e9),
            call.execute_qprogram(qprogram=qprogram, bus_mapping=None, calibration=None, debug=False),
        ]

        # If you want to ensure the exact sequence across all calls
        platform.assert_has_calls(expected_calls, any_order=False)
