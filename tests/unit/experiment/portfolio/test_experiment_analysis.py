"""Unit tests for the ``ExperimentAnalysis`` class."""
from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import RX, RY, I, M, X, Y
from qibo.models import Circuit

from qililab import build_platform
from qililab.experiment.portfolio import ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, LoopOptions, Parameter
from qililab.utils import Loop
from tests.data import Galadriel

circuit = Circuit(1)
circuit.add(I(0))
circuit.add(X(0))
circuit.add(Y(0))
circuit.add(RX(0, 23))
circuit.add(RY(0, 15))
circuit.add(M(0))

START = 1
STOP = 5
NUM = 1000
x = np.linspace(START, STOP, NUM)
i = 5 * np.sin(7 * x)
q = 9 * np.sin(7 * x)


class DummyExperimentAnalysis(ExperimentAnalysis):
    """Dummy class used to test the ``ExperimentAnalysis`` class."""

    @staticmethod
    def func(xdata: np.ndarray, a: float, b: float) -> np.ndarray:  # type: ignore # pylint: disable=arguments-differ
        return a * np.sin(b * xdata)


@pytest.fixture(name="experiment_analysis")
def fixture_experiment_analysis():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="X",
        parameter=Parameter.DURATION,
        options=LoopOptions(start=START, stop=STOP, num=NUM),
    )
    options = ExperimentOptions(loops=[loop])
    analysis = DummyExperimentAnalysis(platform=platform, circuits=[circuit], options=options)
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestExperimentAnalysis:
    """Unit tests for the ``ExperimentAnalysis`` class."""

    def test_post_process_results(self, experiment_analysis: DummyExperimentAnalysis):
        """Test post_process_results method."""
        res = experiment_analysis.post_process_results()
        assert all(res == 20 * np.log10(np.sqrt(i**2 + q**2)))

    def test_fit(self, experiment_analysis: DummyExperimentAnalysis):
        """Test fit method."""
        experiment_analysis.post_processed_results = q
        popt = experiment_analysis.fit(p0=(8, 7.5))  # p0 is an initial guess
        assert all(popt == (9, 7))

    def test_fit_raises_error_when_no_post_processing(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``fit`` method raises an error when the results are not post processed."""
        with pytest.raises(AttributeError, match="The post-processed results must be computed before fitting."):
            experiment_analysis.fit(p0=(8, 7.5))

    def test_fit_raises_error_when_no_loops(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``fit`` method raises an error when the results are not post processed."""
        experiment_analysis.options.loops = None
        experiment_analysis.post_processed_results = q
        with pytest.raises(ValueError, match="The experiment must have at least one loop."):
            experiment_analysis.fit(p0=(8, 7.5))

    def test_fit_raises_error_more_than_one_loop(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``fit`` method raises an error when the results are not post processed."""
        experiment_analysis.options.loops.append(
            Loop(
                alias="Y",
                parameter=Parameter.DURATION,
                options=LoopOptions(start=START, stop=STOP, num=NUM),
            )
        )
        experiment_analysis.post_processed_results = q
        with pytest.raises(ValueError, match="Analysis of nested loops is not supported."):
            experiment_analysis.fit(p0=(8, 7.5))

    def test_plot(self, experiment_analysis: DummyExperimentAnalysis):
        """Test plot method."""
        experiment_analysis.post_processed_results = q
        popt = experiment_analysis.fit()
        fig = experiment_analysis.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], x)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), x)
        assert np.allclose(line.get_ydata(), popt[0] * np.sin(popt[1] * x))

    def test_plot_raises_error_when_no_post_processing(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``plot`` method raises an error when the results are not post processed."""
        with pytest.raises(AttributeError, match="The post-processed results must be computed before fitting."):
            experiment_analysis.plot()

    def test_plot_raises_error_when_no_loops(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``plot`` method raises an error when the results are not post processed."""
        experiment_analysis.options.loops = None
        experiment_analysis.post_processed_results = q
        with pytest.raises(ValueError, match="The experiment must have at least one loop."):
            experiment_analysis.plot()

    def test_plot_raises_error_more_than_one_loop(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``plot`` method raises an error when the results are not post processed."""
        experiment_analysis.options.loops.append(
            Loop(
                alias="Y",
                parameter=Parameter.DURATION,
                options=LoopOptions(start=START, stop=STOP, num=NUM),
            )
        )
        experiment_analysis.post_processed_results = q
        with pytest.raises(ValueError, match="Analysis of nested loops is not supported."):
            experiment_analysis.plot()

    def test_bus_setup_with_control_true(self, experiment_analysis: DummyExperimentAnalysis):
        """Test the ``bus_setup`` method with ``control=True``."""
        experiment_analysis.control_bus = MagicMock()
        experiment_analysis.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=True)
        experiment_analysis.control_bus.set_parameter.assert_called_once_with(parameter=Parameter.AMPLITUDE, value=0.6)

    def test_bus_setup_with_control_false(self, experiment_analysis: DummyExperimentAnalysis):
        """Test the ``bus_setup`` method with ``control=False``."""
        experiment_analysis.readout_bus = MagicMock()
        experiment_analysis.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=False)
        experiment_analysis.readout_bus.set_parameter.assert_called_once_with(parameter=Parameter.AMPLITUDE, value=0.6)

    def test_bus_setup_raises_error_when_no_bus_is_found(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``bus_setup`` method raises an error when no bus is found."""
        with pytest.raises(ValueError, match="The experiment doesn't have a readout bus"):
            experiment_analysis.bus_setup(parameters={Parameter.AMPLITUDE: 0.6})

    def test_control_gate_setup(self, experiment_analysis: DummyExperimentAnalysis):
        """Test the ``control_gate_setup`` method."""
        assert not hasattr(experiment_analysis, "execution")  # ``build_execution`` has not been called
        experiment_analysis.gate_setup(gate="X", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis, "execution")  # ``build_execution`` has been called
        assert experiment_analysis.platform.get_element("X").amplitude == 123

    def test_measurement_setup(self, experiment_analysis: DummyExperimentAnalysis):
        """Test the ``measurement_setup`` method."""
        assert not hasattr(experiment_analysis, "execution")  # ``build_execution`` has not been called
        experiment_analysis.gate_setup(gate="M", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis, "execution")  # ``build_execution`` has been called
        assert experiment_analysis.platform.get_element("M").amplitude == 123
