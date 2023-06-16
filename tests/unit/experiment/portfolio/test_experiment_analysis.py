"""Unit tests for the ``ExperimentAnalysis`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import RX, RY, I, M, X, Y
from qibo.models import Circuit

from qililab import build_platform
from qililab.experiment.portfolio import ExperimentAnalysis, FittingModel
from qililab.typings import ExperimentOptions, Parameter
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
I_AMPLITUDE, I_RATE = (5, 7)
Q_AMPLITUDE, Q_RATE = (9, 7)
i = I_AMPLITUDE * np.sin(I_RATE * x)
q = Q_AMPLITUDE * np.sin(Q_RATE * x)
outer_loop_high_dim = 51
inner_loop_high_dim = 41
outer_loop_low_dim = 50
inner_loop_low_dim = 40


class DummyFittingModel(FittingModel):
    @staticmethod
    def func(xdata: np.ndarray, a: float, b: float):  # type: ignore  # pylint: disable=arguments-differ
        return a * np.sin(b * xdata)


class DummyExperimentAnalysis(ExperimentAnalysis, DummyFittingModel):
    """Dummy class used to test the ``ExperimentAnalysis`` class."""


@pytest.fixture(name="experiment_analysis_1D")
def fixture_experiment_analysis_1D():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="X(0)",
        parameter=Parameter.DURATION,
        values=np.linspace(start=START, stop=STOP, num=NUM),
    )
    options = ExperimentOptions(loops=[loop])
    analysis = DummyExperimentAnalysis(platform=platform, circuits=[circuit], options=options)
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


@pytest.fixture(name="experiment_analysis_2D")
def fixture_experiment_analysis_2D():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()

    inner_loop_0 = Loop(
        alias="Y(0)",
        parameter=Parameter.DURATION,
        values=x[:inner_loop_low_dim],
    )

    inner_loop_1 = Loop(
        alias="Y(1)",
        parameter=Parameter.DURATION,
        values=x[:inner_loop_high_dim],
    )

    outer_loop_0 = Loop(alias="X(0)", parameter=Parameter.DURATION, values=x[:outer_loop_low_dim], loop=inner_loop_0)

    outer_loop_1 = Loop(alias="X(1)", parameter=Parameter.DURATION, values=x[:outer_loop_high_dim], loop=inner_loop_1)

    options = ExperimentOptions(loops=[outer_loop_0, outer_loop_1])
    analysis = DummyExperimentAnalysis(platform=platform, circuits=[circuit], options=options)
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {"i": np.concatenate((i, i)), "q": np.concatenate((q, q))}
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

    def test_post_process_results(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test post_process_results method."""
        res = experiment_analysis_1D.post_process_results()
        assert all(res == 20 * np.log10(np.sqrt(i**2 + q**2)))

        res = experiment_analysis_2D.post_process_results()
        assert res.shape == (outer_loop_low_dim, inner_loop_low_dim)
        assert all(res[0] == 20 * np.log10(np.sqrt(i[:inner_loop_low_dim] ** 2 + q[:inner_loop_low_dim] ** 2)))

    def test_fit(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test fit method."""
        experiment_analysis_1D.post_processed_results = q
        popts = experiment_analysis_1D.fit(p0=(8, 7.5))  # p0 is an initial guess
        assert np.allclose(popts, (9, 7), atol=1e-5)

        experiment_analysis_2D.shorter_loop = [x, x]
        experiment_analysis_2D.post_processed_results = [q, q]
        popts = experiment_analysis_2D.fit(p0=(8, 7.5))  # p0 is an initial guess
        assert len(popts) == 2
        assert np.allclose(popts[0], (9, 7), atol=1e-5)
        assert np.allclose(popts[1], (9, 7), atol=1e-5)

    def test_fit_raises_error_when_no_post_processing(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test that the ``fit`` method raises an error when the results are not post processed."""
        with pytest.raises(AttributeError, match="The post-processed results must be computed before fitting."):
            experiment_analysis_1D.fit(p0=(8, 7.5))
        with pytest.raises(AttributeError, match="The post-processed results must be computed before fitting."):
            experiment_analysis_2D.fit(p0=(8, 7.5))

    def test_plot(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test plot method."""
        experiment_analysis_1D.post_processed_results = q
        popts = experiment_analysis_1D.fit()
        fig = experiment_analysis_1D.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], x)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), x)
        assert np.allclose(line.get_ydata(), popts[0][0] * np.sin(popts[0][1] * x))

        res = experiment_analysis_2D.post_process_results().flatten()
        im = experiment_analysis_2D.plot()
        assert np.array_equal(im.get_array(), res)

    def test_plot_raises_error_when_no_post_processing(self, experiment_analysis_1D: DummyExperimentAnalysis):
        """Test that the ``plot`` method raises an error when the results are not post processed."""
        with pytest.raises(AttributeError, match="The post-processed results must be computed before fitting."):
            experiment_analysis_1D.plot()

    def test_bus_setup_with_control_true(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test the ``bus_setup`` method with ``control=True``."""
        experiment_analysis_1D.control_bus = MagicMock()
        experiment_analysis_1D.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=True)
        experiment_analysis_1D.control_bus.set_parameter.assert_called_once_with(
            parameter=Parameter.AMPLITUDE, value=0.6
        )

        experiment_analysis_2D.control_bus = MagicMock()
        experiment_analysis_2D.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=True)
        experiment_analysis_2D.control_bus.set_parameter.assert_called_once_with(
            parameter=Parameter.AMPLITUDE, value=0.6
        )

    def test_bus_setup_with_control_false(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test the ``bus_setup`` method with ``control=False``."""
        experiment_analysis_1D.readout_bus = MagicMock()
        experiment_analysis_1D.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=False)
        experiment_analysis_1D.readout_bus.set_parameter.assert_called_once_with(
            parameter=Parameter.AMPLITUDE, value=0.6
        )

        experiment_analysis_2D.readout_bus = MagicMock()
        experiment_analysis_2D.bus_setup(parameters={Parameter.AMPLITUDE: 0.6}, control=False)
        experiment_analysis_2D.readout_bus.set_parameter.assert_called_once_with(
            parameter=Parameter.AMPLITUDE, value=0.6
        )

    def test_bus_setup_raises_error_when_no_bus_is_found(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test that the ``bus_setup`` method raises an error when no bus is found."""
        with pytest.raises(ValueError, match="The experiment doesn't have a readout bus"):
            experiment_analysis_1D.bus_setup(parameters={Parameter.AMPLITUDE: 0.6})
        with pytest.raises(ValueError, match="The experiment doesn't have a readout bus"):
            experiment_analysis_2D.bus_setup(parameters={Parameter.AMPLITUDE: 0.6})

    def test_control_gate_setup(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test the ``control_gate_setup`` method."""
        assert not hasattr(experiment_analysis_1D, "execution_manager")  # ``build_execution`` has not been called
        experiment_analysis_1D.gate_setup(gate="X(0)", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis_1D, "execution_manager")  # ``build_execution`` has been called
        assert experiment_analysis_1D.platform.get_element("X(0)").amplitude == 123

        assert not hasattr(experiment_analysis_2D, "execution_manager")  # ``build_execution`` has not been called
        experiment_analysis_2D.gate_setup(gate="X(0)", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis_2D, "execution_manager")  # ``build_execution`` has been called
        assert experiment_analysis_2D.platform.get_element("X(0)").amplitude == 123

    def test_measurement_setup(
        self, experiment_analysis_1D: DummyExperimentAnalysis, experiment_analysis_2D: DummyExperimentAnalysis
    ):
        """Test the ``measurement_setup`` method."""
        assert not hasattr(experiment_analysis_1D, "execution_manager")  # ``build_execution`` has not been called
        experiment_analysis_1D.gate_setup(gate="M(0)", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis_1D, "execution_manager")  # ``build_execution`` has been called
        assert experiment_analysis_1D.platform.get_element("M(0)").amplitude == 123

        assert not hasattr(experiment_analysis_2D, "execution_manager")  # ``build_execution`` has not been called
        experiment_analysis_2D.gate_setup(gate="M(0)", parameters={Parameter.AMPLITUDE: 123})
        assert hasattr(experiment_analysis_2D, "execution_manager")  # ``build_execution`` has been called
        assert experiment_analysis_2D.platform.get_element("M(0)").amplitude == 123
