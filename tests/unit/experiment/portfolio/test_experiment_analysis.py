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

x = np.linspa
i = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
q = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])


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
        options=LoopOptions(start=4, stop=1000, step=40),
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
        experiment_analysis.post_process_results()
        popt = experiment_analysis.fit()
        assert all(popt == [1, 1])
