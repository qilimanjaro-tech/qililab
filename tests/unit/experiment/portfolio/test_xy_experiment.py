"""Unit tests for the ``xy_experiment`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M

import qililab as ql
from qililab import build_platform
from qililab.experiment import AllXYExperiment
from qililab.system_control import ReadoutSystemControl
from qililab.utils import Wait
from tests.data import Galadriel

START = 1
STOP = 5
NUM = 1000
if_values = np.linspace(START, STOP, NUM)
i_amplitude = 5
q_amplitude = 9
i_q_freq = 7
i = i_amplitude * np.sin(i_q_freq * if_values)
q = q_amplitude * np.sin(i_q_freq * if_values)


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
        expected_num_experiments = 21
        expected_circuits_names = [
            "II",
            "XpXp",
            "YpYp",
            "XpYp",
            "YpXp",
            "X9I",
            "Y9I",
            "X9Y9",
            "Y9X9",
            "X9Yp",
            "Y9Xp",
            "XpY9",
            "YpX9",
            "X9Xp",
            "XpX9",
            "Y9Yp",
            "YpY9",
            "XpI",
            "YpI",
            "X9X9",
            "Y9Y9",
        ]
        default_repetition_duration = 10000
        default_hardware_average = 10000

        all_xy_circuits = all_xy_experiment.circuit
        all_xy_circuits_names = all_xy_experiment.circuits_names
        assert len(all_xy_circuits) == expected_num_experiments
        assert all_xy_circuits_names == expected_circuits_names

        for circuit in all_xy_experiment.circuits:
            for gate in circuit:
                assert isinstance(gate, (ql.Drag, M, Wait))
                assert gate.qubits == (0,)

        # Test the bus attributes
        assert not isinstance(all_xy_experiment.control_bus.system_control, ReadoutSystemControl)
        assert isinstance(all_xy_experiment.readout_bus.system_control, ReadoutSystemControl)
        # Test the experiment options
        assert len(all_xy_experiment.options.loops) == 1
        assert all_xy_experiment.loop.alias == f"drive_line_q{all_xy_experiment.qubit}_bus"
        assert all_xy_experiment.loop.parameter == ql.Parameter.IF
        assert all_xy_experiment.loop.start == START
        assert all_xy_experiment.loop.stop == STOP
        assert all_xy_experiment.loop.num == NUM
        assert all_xy_experiment.options.settings.repetition_duration == default_repetition_duration
        assert all_xy_experiment.options.settings.hardware_average == default_hardware_average

    def test_func(self, all_xy_experiment: AllXYExperiment):
        """Test the ``func`` method."""
        assert np.allclose(
            all_xy_experiment.func(
                xdata=if_values, amplitude=i_amplitude, frequency=i_q_freq / (2 * np.pi), phase=-np.pi / 2, offset=0
            ),
            i,
        )

    def test_fit(self, all_xy_experiment: AllXYExperiment):
        """Test fit method."""
        all_xy_experiment.post_processed_results = q
        popt = all_xy_experiment.fit(p0=(8, 7.5 / (2 * np.pi), -np.pi / 2, 0))  # p0 is an initial guess
        assert np.allclose(popt, (q_amplitude, i_q_freq / (2 * np.pi), -np.pi / 2, 0), atol=1e-5)

    def test_plot(self, all_xy_experiment: AllXYExperiment):
        """Test plot method."""
        all_xy_experiment.post_processed_results = q
        popt = all_xy_experiment.fit()
        fig = all_xy_experiment.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], if_values)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), if_values)
        assert np.allclose(line.get_ydata(), popt[0] * np.cos(2 * np.pi * popt[1] * if_values + popt[2]) + popt[3])