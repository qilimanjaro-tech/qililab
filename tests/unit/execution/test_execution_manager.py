"""Tests for the ExecutionManager class."""
from queue import Queue
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from qpysequence import Sequence

from qililab.constants import RESULTSDATAFRAME
from qililab.execution import ExecutionManager
from qililab.experiment import Experiment
from qililab.instruments import AWG
from qililab.result.qblox_results import QbloxResult
from qililab.result.results import Results
from qililab.system_control import ReadoutSystemControl
from tests.utils import mock_instruments


class TestExecutionManager:
    """Unit tests checking the ExecutionManager attributes and methods."""

    def test_waveforms_method(self, execution_manager: ExecutionManager):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            execution_manager.waveforms_dict(resolution=resolution)

    def test_draw_method(self, execution_manager: ExecutionManager):
        """Test draw method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            execution_manager.draw(resolution=resolution)


@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
@patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.experiment.experiment.yaml.safe_dump")
@patch("qililab.experiment.experiment.open")
@patch("qililab.experiment.experiment.os.makedirs")
class TestExecutionManagerPlatform:
    """Unit tests checking a platform with instruments of the ExecutionManager."""

    @patch("qililab.platform.platform.API")
    def test_execute_with_remote_save(
        self,
        mocked_remote_connection: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        nested_experiment: Experiment,
    ):
        """Test execute method with nested loops."""
        saved_experiment_id = 0

        mocked_remote_connection.save_experiment.return_value = saved_experiment_id
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)

        nested_experiment.options.settings.software_average = 1
        nested_experiment.options.remote_save = True
        nested_experiment.options.name = "TEST"
        nested_experiment.options.description = "TEST desc"
        nested_experiment.platform.connection = mocked_remote_connection
        nested_experiment.execute()  # type: ignore
        nested_experiment.to_dict()

        mocked_remote_connection.save_experiment.assert_called()
        assert nested_experiment._remote_id == saved_experiment_id

        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        mock_dump_0.assert_called()
        mock_open_0.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_nested_loop(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        nested_experiment: Experiment,
    ):
        """Test execute method with nested loops."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        nested_experiment.options.settings.software_average = 1
        results = nested_experiment.execute()  # type: ignore
        nested_experiment.to_dict()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert isinstance(results, Results)
        acquisitions = results.acquisitions(mean=True)
        assert acquisitions[RESULTSDATAFRAME.LOOP_INDEX + "0"].unique().size == 2
        assert acquisitions[RESULTSDATAFRAME.LOOP_INDEX + "1"].unique().size == 2
        probabilities = results.probabilities(mean=True)
        assert probabilities[RESULTSDATAFRAME.LOOP_INDEX + "0"].unique().size == 2
        assert probabilities[RESULTSDATAFRAME.LOOP_INDEX + "1"].unique().size == 2
        mock_dump_1.assert_called()
        mock_open_1.assert_called()
        mock_makedirs.assert_called()
        assert (
            results.ranges
            == np.array(
                [
                    nested_experiment.options.loops[0].loop.values,  # type: ignore
                    nested_experiment.options.loops[0].values,  # type: ignore
                ]
            )
        ).all()

    def test_execute_method_with_instruments(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        results = experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, pd.DataFrame)
        assert isinstance(acquisitions, pd.DataFrame)
        mock_dump_1.assert_called()
        mock_open_1.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_from_dict_experiment(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        nested_experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        nested_experiment_dict = nested_experiment.to_dict()
        experiment = Experiment.from_dict(nested_experiment_dict)
        results = experiment.execute()
        results_2 = nested_experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert results == results_2
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, pd.DataFrame)
        assert isinstance(acquisitions, pd.DataFrame)
        mock_dump_1.assert_called()
        mock_open_1.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_keyboard_interrupt(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        mock_pulsar.return_value.get_acquisitions.side_effect = KeyboardInterrupt()
        with pytest.raises(KeyboardInterrupt):
            results = experiment.execute()
            mock_urllib.request.Request.assert_called()
            mock_urllib.request.urlopen.assert_called()
            mock_rs.assert_called()
            mock_pulsar.assert_called()
            assert isinstance(results, Results)
            mock_open_1.assert_called()
            mock_dump_1.assert_not_called()
            mock_makedirs.assert_called()


qblox_acquisition = {
    "default": {
        "index": 0,
        "acquisition": {
            "scope": {
                "path0": {"data": [0] * 1000, "out-of-range": False, "avg_cnt": 1000},
                "path1": {"data": [0] * 1000, "out-of-range": False, "avg_cnt": 1000},
            },
            "bins": {
                "integration": {"path0": [1, 2, 3], "path1": [4, 5, 6]},
                "threshold": [1, 1, 1],
                "avg_cnt": [1000, 1000, 1000],
            },
        },
    }
}


@pytest.fixture(name="mocked_execution_manager")
def fixture_mocked_execution_manager(execution_manager: ExecutionManager):
    """Fixture that returns an instance of an ExecutionManager class, where all the drivers of the
    instruments are mocked."""
    # Mock all the devices
    awgs = [bus.system_control.instruments[0] for bus in execution_manager.buses]
    for awg in awgs:
        assert isinstance(awg, AWG)
        awg.device = MagicMock()
        awg.device.get_acquisitions.return_value = qblox_acquisition
    return execution_manager


class TestWorkflow:
    """Unit tests for the methods used in the workflow of an `ExecutionManager` class."""

    def test_compile(self, execution_manager: ExecutionManager):
        """Test the compile method of the ``ExecutionManager`` class."""
        sequences = execution_manager.compile(idx=0, nshots=1000, repetition_duration=2000)
        assert isinstance(sequences, dict)
        assert len(sequences) == len(execution_manager.buses)
        for alias, sequences in sequences.items():
            assert alias in {bus.alias for bus in execution_manager.buses}
            assert isinstance(sequences, list)
            assert len(sequences) == 1
            assert isinstance(sequences[0], Sequence)
            assert sequences[0]._program.duration == 2000 * 1000 + 4  # additional 4ns for the initial wait_sync

    def test_upload(self, mocked_execution_manager: ExecutionManager):
        """Test upload method."""
        _ = mocked_execution_manager.compile(idx=0, nshots=1000, repetition_duration=2000)
        mocked_execution_manager.upload()

        awgs = [bus.system_control.instruments[0] for bus in mocked_execution_manager.buses]

        for awg in awgs:
            for seq_idx in range(awg.num_sequencers):  # type: ignore
                assert awg.device.sequencers[seq_idx].sequence.call_count == awg.num_sequencers  # type: ignore

    def test_run(self, mocked_execution_manager: ExecutionManager):
        """Test that the run method returns a ``Result`` object."""
        # Test that the run method returns a ``Result`` object
        mocked_queue = MagicMock()
        result = mocked_execution_manager.run(queue=mocked_queue)
        assert isinstance(result, QbloxResult)
        # mocked_queue.put_nowait.assert_called_with(result)
        assert [result.qblox_raw_results[0]] == [qblox_acquisition["default"]["acquisition"]]

        # Make sure the mocked devices were called
        readout_awgs = [
            bus.system_control.instruments[0]
            for bus in mocked_execution_manager.buses
            if isinstance(bus.system_control, ReadoutSystemControl)
        ]
        for awg in readout_awgs:
            assert awg.device.get_acquisitions.call_count == 2  # type: ignore

    def test_run_multiple_readout_buses_raises_error(self, mocked_execution_manager: ExecutionManager):
        """Test that an error is raised when calling ``run`` with multiple readout buses."""
        readout_bus = mocked_execution_manager.readout_buses[0]
        mocked_execution_manager.buses += [readout_bus]  # add extra readout bus
        with patch("qililab.execution.execution_manager.logger") as mocked_logger:
            mocked_execution_manager.run(queue=Queue())
            mocked_logger.error.assert_called_once_with(
                "Only One Readout Bus allowed. Reading only from the first one."
            )

    def test_run_no_readout_buses_raises_error(self, mocked_execution_manager: ExecutionManager):
        """Test that an error is raised when calling ``run`` with no readout buses."""
        mocked_execution_manager.buses = []
        with pytest.raises(ValueError, match="No Results acquired"):
            mocked_execution_manager.run(queue=Queue())
