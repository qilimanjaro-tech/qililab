"""Unit tests for the ``T2Echo`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M

from qililab import build_platform
from qililab.experiment import T2Echo
from qililab.transpiler.native_gates import Drag
from qililab.typings.enums import Parameter
from qililab.utils import Wait
from tests.data import Galadriel

START, STOP, NUM = (1, 1000, 101)
I_AMPLITUDE, I_RATE, I_OFFSET = (5, -2, 0)
Q_AMPLITUDE, Q_RATE, Q_OFFSET = (9, -2, 0)

x = np.linspace(START, STOP, NUM)
i = I_AMPLITUDE * np.exp(I_RATE * x)
q = Q_AMPLITUDE * np.exp(Q_RATE * x)


@pytest.fixture(name="t2echo")
def fixture_t2echo():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="_")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = T2Echo(platform=platform, qubit=0, wait_loop_values=np.linspace(start=START, stop=STOP, num=NUM))
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestT2Echo:
    """Unit tests for the ``T2Echo`` portfolio experiment class."""

    def test_init(self, t2echo: T2Echo):
        """Test the ``__init__`` method."""
        # Test that the correct circuit is created
        assert len(t2echo.circuits) == 1
        for idx, gate in enumerate(t2echo.circuits[0].queue):
            assert isinstance(gate, [Drag, Wait, Drag, Wait, Drag, Wait, M][idx])
            assert gate.qubits == (0,)

        # Test the experiment options
        assert len(t2echo.options.loops) == 2

        assert t2echo.options.loops[0].alias == "2"
        assert t2echo.options.loops[1].alias == "5"

        assert t2echo.options.loops[0].parameter == Parameter.GATE_PARAMETER
        assert t2echo.options.loops[1].parameter == Parameter.GATE_PARAMETER

        assert t2echo.options.loops[0].start == START
        assert t2echo.options.loops[1].start == START

        assert t2echo.options.loops[0].stop == STOP
        assert t2echo.options.loops[1].stop == STOP

        assert t2echo.options.loops[0].num == NUM
        assert t2echo.options.loops[1].num == NUM

    def test_func(self, t2echo: T2Echo):
        """Test the ``func`` method."""
        assert np.allclose(
            t2echo.func(xdata=x, amplitude=I_AMPLITUDE, rate=I_RATE, offset=I_OFFSET),
            i,
        )

    def test_fit(self, t2echo: T2Echo):
        """Test the ``fit`` method."""
        with patch("qililab.experiment.portfolio.experiment_analysis.ExperimentAnalysis.fit") as mock_parent_fit:
            mocked_fitted_params = np.array([0.1, 0.5])
            mock_parent_fit.return_value = mocked_fitted_params
            t2_test = t2echo.fit()
            mock_parent_fit.assert_called_with(p0=(-52, 2000, 0), quadrature="i")

            assert t2_test == 2 * mocked_fitted_params[1]
