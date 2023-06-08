"""Unit tests for the ``xy_experiment`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M

import qililab as ql
from qililab import build_platform
from qililab.experiment import AllXYExperiment
from qililab.system_control import ReadoutSystemControl
from qililab.utils import Loop
from qililab.utils import Wait
from tests.data import Galadriel

START = 1
STOP = 5
NUM = 1000
NUM_CIRCUITS = 21
nested_values = np.linspace(START, STOP, NUM * NUM_CIRCUITS)
if_values = np.linspace(START, STOP, NUM)
i_amplitude = 5
q_amplitude = 9
i_q_freq = 7
i = i_amplitude * np.sin(i_q_freq * nested_values)
q = q_amplitude * np.sin(i_q_freq * nested_values)

@pytest.fixture(name="all_xy_experiment")
def fixture_all_xy():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()

    analysis = AllXYExperiment(platform=platform, qubit=0, if_values=if_values)
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }

    return analysis


class TestAllXY:
    """Unit tests for the ``all_xy_experiment`` class."""

    def test_init(self, all_xy_experiment: AllXYExperiment):
        """Test the ``__init__`` method."""
        # Test that the correct circuits are created
        expected_circuits_names = ["II", "XpXp", "YpYp",
                                   "XpYp", "YpXp", "X9I",
                                   "Y9I", "X9Y9", "Y9X9",
                                   "X9Yp", "Y9Xp", "XpY9",
                                   "YpX9", "X9Xp", "XpX9",
                                   "Y9Yp", "YpY9", "XpI",
                                   "YpI", "X9X9", "Y9Y9",
        ]
        default_repetition_duration = 10000
        default_hardware_average = 10000

        all_xy_circuits = all_xy_experiment.circuits
        all_xy_circuits_names = all_xy_experiment.circuit_names
        assert len(all_xy_circuits) == NUM_CIRCUITS
        assert all_xy_circuits_names == expected_circuits_names

        for circuit in all_xy_experiment.circuits:
            for gate in circuit.queue:
                assert isinstance(gate, (ql.Drag, M, Wait))
                assert gate.qubits == (0,)

        # Test the bus attributes
        assert not isinstance(all_xy_experiment.control_bus.system_control, ReadoutSystemControl)
        assert isinstance(all_xy_experiment.readout_bus.system_control, ReadoutSystemControl)
        # Test the experiment options
        assert len(all_xy_experiment.options.loops) == 1
        assert all_xy_experiment.loop.parameter == ql.Parameter.A
        assert all_xy_experiment.loop.start == expected_circuits_names[0]
        assert all_xy_experiment.loop.stop == expected_circuits_names[-1]
        assert all_xy_experiment.loop.num == NUM_CIRCUITS
        assert all_xy_experiment.options.settings.repetition_duration == default_repetition_duration
        assert all_xy_experiment.options.settings.hardware_average == default_hardware_average
        
    def test_post_process_results(self, all_xy_experiment: AllXYExperiment):
        """Test post_process_results method."""
        res = all_xy_experiment.post_process_results()
        assert res.shape == (len(if_values), 21)
