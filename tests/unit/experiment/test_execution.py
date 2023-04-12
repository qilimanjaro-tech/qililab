"""Tests for the Experiment class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from qpysequence import Sequence

from qililab.constants import RESULTSDATAFRAME
from qililab.execution import ExecutionManager
from qililab.experiment import Experiment
from qililab.instruments import AWG
from qililab.result.results import Results
from tests.utils import mock_instruments


@pytest.fixture(name="execution")
def fixture_execution_manager(experiment: Experiment) -> ExecutionManager:
    """Fixture that returns an instance of an Execution class."""
    experiment.build_execution()
    return experiment.execution


@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
@patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.experiment.experiment.yaml.safe_dump")
@patch("qililab.execution.execution_manager.open")
@patch("qililab.experiment.experiment.open")
@patch("qililab.experiment.experiment.os.makedirs")
class TestExecutionManager:
    """Unit tests checking the execution of a platform with instruments."""

    @patch("qililab.platform.platform.API")
    def test_execute_with_remote_save(
        self,
        mocked_remote_connection: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_0: MagicMock,
        mock_open_1: MagicMock,
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
        mock_open_1.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_nested_loop(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
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
        assert acquisitions[RESULTSDATAFRAME.LOOP_INDEX + "2"].unique().size == 2
        probabilities = results.probabilities(mean=True)
        assert probabilities[RESULTSDATAFRAME.LOOP_INDEX + "0"].unique().size == 2
        assert probabilities[RESULTSDATAFRAME.LOOP_INDEX + "1"].unique().size == 2
        assert probabilities[RESULTSDATAFRAME.LOOP_INDEX + "2"].unique().size == 2
        mock_dump_1.assert_called()
        mock_open_1.assert_called()
        mock_open_2.assert_called()
        mock_makedirs.assert_called()
        assert (
            results.ranges
            == np.array(
                [
                    nested_experiment.options.loops[0].range,  # type: ignore
                    nested_experiment.options.loops[0].loop.range,  # type: ignore
                    nested_experiment.options.loops[0].loop.loop.range,  # type: ignore
                ]
            )
        ).all()

    def test_execute_method_with_instruments(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
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
        mock_open_2.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_from_dict_experiment(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
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
        mock_open_2.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_keyboard_interrupt(
        self,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
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
            mock_open_2.assert_not_called()
            mock_makedirs.assert_called()


class TestWorkflow:
    """Unit tests for the methods used in the workflow of an `Execution` class."""

    def test_compile(self, execution: ExecutionManager):
        """Test the compile method of the ``Execution`` class."""
        sequences = execution.compile(idx=0, nshots=1000, repetition_duration=2000)
        assert isinstance(sequences, dict)
        assert len(sequences) == len(execution.buses)
        for alias, sequences in sequences.items():
            assert alias in {bus.alias for bus in execution.buses}
            assert isinstance(sequences, list)
            assert len(sequences) == 1
            assert isinstance(sequences[0], Sequence)
            assert sequences[0]._program.duration == 2000 * 1000 + 4  # additional 4ns for the initial wait_sync

    def test_upload(self, execution: ExecutionManager):
        """Test upload method."""
        awgs = [bus.system_control.instruments[0] for bus in execution.buses]
        for awg in awgs:
            assert isinstance(awg, AWG)
            awg.device = MagicMock()
        _ = execution.compile(idx=0, nshots=1000, repetition_duration=2000)
        execution.upload()
        for awg in awgs:
            for seq_idx in range(awg.num_sequencers):
                awg.device.sequencers[seq_idx].sequence.assert_called_once()
