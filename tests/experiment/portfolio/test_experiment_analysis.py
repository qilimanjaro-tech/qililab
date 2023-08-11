"""Unit tests for the ``ExperimentAnalysis`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import RX, RY, I, M, X, Y
from qibo.models import Circuit

from qililab.experiment.portfolio import ExperimentAnalysis, FittingModel
from qililab.typings import ExperimentOptions, Parameter
from qililab.utils import Loop
from tests.data import Galadriel
from tests.test_utils import build_platform

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


class DummyFittingModel(FittingModel):
    @staticmethod
    def func(xdata: np.ndarray, a: float, b: float):  # type: ignore  # pylint: disable=arguments-differ
        return a * np.sin(b * xdata)


class DummyExperimentAnalysis(ExperimentAnalysis, DummyFittingModel):
    """Dummy class used to test the ``ExperimentAnalysis`` class."""


@pytest.fixture(name="experiment_analysis")
def fixture_experiment_analysis():
    """Return Experiment object."""
    platform = build_platform(Galadriel.runcard)
    loop = Loop(
        alias="X(0)",
        parameter=Parameter.DURATION,
        values=np.linspace(start=START, stop=STOP, num=NUM),
    )
    options = ExperimentOptions(loops=[loop])
    analysis = DummyExperimentAnalysis(platform=platform, circuits=[circuit], options=options)
    analysis.results = MagicMock()  # pylint: disable=attribute-defined-outside-init
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestExperimentAnalysis:
    """Unit tests for the ``ExperimentAnalysis`` class."""

    def test_init_raises_error_when_no_loops(self):
        """Test that the ``__init__`` method raises an error when no loops are provided."""
        with pytest.raises(
            ValueError,
            match="A loop must be provided. Either an experiment loop in the `ExperimentOptions` class, "
            "or an external loop in the `experiment_loop` argument.",
        ):
            DummyExperimentAnalysis(platform=MagicMock(), circuits=[circuit], options=ExperimentOptions())

    def test_post_process_results(self, experiment_analysis: DummyExperimentAnalysis):
        """Test post_process_results method."""
        res = experiment_analysis.post_process_results()
        assert all(res == 20 * np.log10(np.sqrt(i**2 + q**2)))

    def test_fit(self, experiment_analysis: DummyExperimentAnalysis):
        """Test fit method."""
        experiment_analysis.post_processed_results = q
        popt = experiment_analysis.fit(p0=(8, 7.5))  # p0 is an initial guess
        assert np.allclose(popt, (9, 7), atol=1e-5)

    def test_fit_raises_error_when_no_post_processing(self, experiment_analysis: DummyExperimentAnalysis):
        """Test that the ``fit`` method raises an error when the results are not post processed."""
        with pytest.raises(AttributeError, match="The post-processed results must be computed before fitting."):
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
        assert not hasattr(experiment_analysis, "execution_manager")  # ``build_execution`` has not been called
        experiment_analysis.gate_setup(gate="X(0)", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis, "execution_manager")  # ``build_execution`` has been called
        assert experiment_analysis.platform.get_element("X(0)")[0].pulse.amplitude == 123

    def test_measurement_setup(self, experiment_analysis: DummyExperimentAnalysis):
        """Test the ``measurement_setup`` method."""
        assert not hasattr(experiment_analysis, "execution_manager")  # ``build_execution`` has not been called
        experiment_analysis.gate_setup(gate="M(0)", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis, "execution_manager")  # ``build_execution`` has been called
        assert experiment_analysis.platform.get_element("M(0)")[0].pulse.amplitude == 123
