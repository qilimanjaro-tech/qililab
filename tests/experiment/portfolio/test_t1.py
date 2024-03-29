"""Unit tests for the ``Rabi`` class."""
from unittest.mock import MagicMock

import numpy as np
import pytest
from qibo.gates import M

from qililab.circuit_transpiler.native_gates import Drag, Wait
from qililab.experiment import T1
from qililab.typings.enums import Parameter
from tests.data import Galadriel
from tests.test_utils import build_platform

START, STOP, NUM = (1, 1000, 101)
I_AMPLITUDE, I_RATE, I_OFFSET = (5, -2, 0)
Q_AMPLITUDE, Q_RATE, Q_OFFSET = (9, -2, 0)

x = np.linspace(START, STOP, NUM)
i_data = I_AMPLITUDE * np.exp(I_RATE * x)
q_data = Q_AMPLITUDE * np.exp(Q_RATE * x)


@pytest.fixture(name="t1")
def fixture_t1():
    """Return Experiment object."""
    platform = build_platform(Galadriel.runcard)
    analysis = T1(platform=platform, qubit=0, wait_loop_values=np.linspace(start=START, stop=STOP, num=NUM))
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i_data,
        "q": q_data,
    }
    return analysis


class TestT1:
    """Unit tests for the ``T1`` portfolio experiment class."""

    def test_init(self, t1: T1):
        """Test the ``__init__`` method."""
        # Test that the correct circuit is created
        assert len(t1.circuits) == 1
        for i, gate in enumerate(t1.circuits[0].queue):
            assert isinstance(gate, [Drag, Wait, M][i])
            assert gate.qubits == (0,)

        # Test the experiment options
        assert len(t1.options.loops) == 1
        assert t1.loop.alias == "2"
        assert t1.loop.parameter == Parameter.GATE_PARAMETER
        assert t1.loop.start == START
        assert t1.loop.stop == STOP
        assert t1.loop.num == NUM

    def test_func(self, t1: T1):
        """Test the ``func`` method."""
        assert np.allclose(
            t1.func(xdata=x, amplitude=I_AMPLITUDE, rate=I_RATE, offset=I_OFFSET),
            i_data,
        )
