"""Unit tests for the ``ExperimentAnalysis`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import RX, RY, I, M, X, Y
from qibo.models import Circuit

from qililab import build_platform
from qililab.experiment.portfolio import ExperimentAnalysis
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
        ax = fig.axes[0]
        assert len(ax.lines) == 2
        line0 = ax.lines[0]
        assert np.allclose(line0.get_xdata(), x)
        assert np.allclose(line0.get_ydata(), q)
        line1 = ax.lines[1]
        assert np.allclose(line1.get_xdata(), x)
        assert np.allclose(line1.get_ydata(), popt[0] * np.sin(popt[1] * x))

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
