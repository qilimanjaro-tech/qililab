"""Tests for the ExecutionManager class."""
from unittest.mock import MagicMock, patch

import pytest
from qpysequence import Sequence

from qililab.execution import ExecutionManager
from qililab.instruments import AWG
from qililab.result.qblox_results import QbloxResult
from qililab.system_control import ReadoutSystemControl


class TestExecutionManager:
    """Unit tests checking the Experiment attributes and methods."""

    def test_waveforms_method(self, execution_manager: ExecutionManager):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            execution_manager.waveforms_dict(resolution=resolution)

    def test_draw_method(self, execution_manager: ExecutionManager):
        """Test draw method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            execution_manager.draw(resolution=resolution)


qblox_acquisition = {
    "single": {
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
    """Unit tests for the methods used in the workflow of an `Execution` class."""

    def test_compile(self, execution_manager: ExecutionManager):
        """Test the compile method of the ``Execution`` class."""
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
            for seq_idx in range(awg.num_sequencers):
                awg.device.sequencers[seq_idx].sequence.assert_called_once()

    def test_run(self, mocked_execution_manager: ExecutionManager):
        """Test that the run method returns a ``Result`` object."""
        # Test that the run method returns a ``Result`` object
        result = mocked_execution_manager.run(plot=None, path=None)
        assert isinstance(result, QbloxResult)
        assert result.qblox_raw_results == [qblox_acquisition["single"]["acquisition"]]

        # Make sure the mocked devices were called
        readout_awgs = [
            bus.system_control.instruments[0]
            for bus in mocked_execution_manager.buses
            if isinstance(bus.system_control, ReadoutSystemControl)
        ]
        for awg in readout_awgs:
            awg.device.get_acquisitions.assert_called_once()

    def test_run_multiple_readout_buses_raises_error(self, mocked_execution_manager: ExecutionManager):
        """Test that an error is raised when calling ``run`` with multiple readout buses."""
        readout_bus = mocked_execution_manager.readout_buses[0]
        mocked_execution_manager.buses += [readout_bus]  # add extra readout bus
        with patch("qililab.execution.execution_manager.logger") as mocked_logger:
            mocked_execution_manager.run(plot=None, path=None)
            mocked_logger.error.assert_called_once_with(
                "Only One Readout Bus allowed. Reading only from the first one."
            )

    def test_run_no_readout_buses_raises_error(self, mocked_execution_manager: ExecutionManager):
        """Test that an error is raised when calling ``run`` with no readout buses."""
        mocked_execution_manager.buses = []
        with pytest.raises(ValueError, match="No Results acquired"):
            mocked_execution_manager.run(plot=None, path=None)
