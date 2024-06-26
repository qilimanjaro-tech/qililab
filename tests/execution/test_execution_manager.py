"""Tests for the ExecutionManager class."""
from unittest.mock import MagicMock, patch

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from qililab.constants import RESULTSDATAFRAME
from qililab.execution import ExecutionManager
from qililab.experiment.experiment import Experiment
from qililab.instruments import AWG
from qililab.result.results import Results
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import experiment_params
from tests.test_utils import build_platform, mock_instruments


@pytest.fixture(name="execution_manager")
def fixture_execution_manager(experiment: Experiment) -> ExecutionManager:
    """Load ExecutionManager.

    Returns:
        ExecutionManager: Instance of the ExecutionManager class.
    """
    experiment.build_execution()
    return experiment.execution_manager  # pylint: disable=protected-access


@pytest.fixture(name="nested_experiment", params=experiment_params)
def fixture_nested_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    platform = build_platform(runcard)
    loop2 = Loop(
        alias="platform",
        parameter=Parameter.DELAY_BEFORE_READOUT,
        values=np.arange(start=40, stop=100, step=40),
    )
    loop = Loop(
        alias=f"{InstrumentName.QBLOX_QRM.value}_0",
        parameter=Parameter.GAIN,
        values=np.linspace(start=0, stop=1, num=2),
        channel_id=0,
        loop=loop2,
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )


@pytest.fixture(name="experiment", params=experiment_params)
def fixture_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    platform = build_platform(runcard)
    loop = Loop(
        alias="X(0)",
        parameter=Parameter.DURATION,
        values=np.arange(start=4, stop=1000, step=40),
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )


class TestExecutionManager:
    """Unit tests checking the ExecutionManager attributes and methods."""

    def test_waveforms_method(self, execution_manager: ExecutionManager):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            execution_manager._waveforms_dict(resolution=resolution)

    def test_draw_method(self, execution_manager: ExecutionManager):
        """Test draw method."""
        figures = [
            execution_manager.draw(),
            execution_manager.draw(
                modulation=False,
                linestyle=":",
                resolution=0.8,
            ),
            execution_manager.draw(
                real=False,
                imag=False,
                absolute=True,
                modulation=False,
                linestyle="x",
                resolution=10.1,
            ),
        ]

        for figure in figures:
            assert figure is not None
            assert isinstance(figure, plt.Figure)

        plt.close()


@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
@patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.experiment.base_experiment.YAML.dump", autospec=True)
@patch("qililab.experiment.base_experiment.open")
@patch("qililab.experiment.base_experiment.os.makedirs")
class TestExecutionManagerPlatform:
    """Unit tests checking a platform with instruments of the ExecutionManager."""

    def test_execute_method_with_nested_loop(
        self,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        mock_dump: MagicMock,
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
        probabilities = results.probabilities()
        for qubit_string in probabilities.keys():
            assert len(qubit_string) == nested_experiment.circuits[0].nqubits
        assert sum(probabilities.values()) == 1.0
        mock_dump.assert_called()
        mock_open.assert_called()
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
        mock_open: MagicMock,
        mock_dump: MagicMock,
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
        assert isinstance(probabilities, dict)
        assert isinstance(acquisitions, pd.DataFrame)
        mock_dump.assert_called()
        mock_open.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_from_dict_experiment(
        self,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        mock_dump: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        nested_experiment: Experiment,
    ):  # pylint: disable=too-many-locals
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        nested_experiment_dict = nested_experiment.to_dict()
        experiment = Experiment.from_dict(nested_experiment_dict)
        results = experiment.execute()
        results_2 = nested_experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert results.to_dict() == results_2.to_dict()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, dict)
        assert isinstance(acquisitions, pd.DataFrame)
        mock_dump.assert_called()
        mock_open.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_keyboard_interrupt(
        self,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        mock_dump: MagicMock,
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
            mock_open.assert_called()
            mock_dump.assert_not_called()
            mock_makedirs.assert_called()


qblox_acquisition = {
    "acq_q0_0": {
        "index": 0,
        "acquisition": {
            "scope": {
                "path0": {"data": [0] * 1000, "out-of-range": False, "avg_cnt": 1000},
                "path1": {"data": [0] * 1000, "out-of-range": False, "avg_cnt": 1000},
            },
            "bins": {
                "integration": {"path0": [1, 2, 3], "path1": [4, 5, 6]},
                "threshold": [1, 1, 1],
                "avg_cnt": [1, 1, 1],
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
        awg.device.sequencers = [MagicMock(), MagicMock()]
        awg.device.get_acquisitions.return_value = qblox_acquisition
    return execution_manager
