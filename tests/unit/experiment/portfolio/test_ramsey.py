"""Unit tests for the ``Ramsey`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M

from qililab import build_platform
from qililab.experiment.portfolio import Ramsey
from qililab.transpiler.native_gates import Drag
from qililab.typings.enums import Parameter
from qililab.utils import Wait
from tests.data import Galadriel

QUBIT = 0

WAIT_LOOP_START = 1
WAIT_LOOP_STOP = 1000
WAIT_LOOP_NUM = 101

IF_LOOP_START = 101e6
IF_LOOP_STOP = 200e6
IF_LOOP_NUM = 101

DELTA_ARTIFICIAL = 1.0

I_AMPLITUDE, I_DECAY, I_FREQUENCY, I_PHASE, I_OFFSET = (1, 1, 200e6, 0, 0)
Q_AMPLITUDE, Q_DECAY, Q_FREQUENCY, Q_PHASE, Q_OFFSET = (1, 1, 200e6, 0, 0)

x = np.linspace(WAIT_LOOP_START, WAIT_LOOP_STOP, WAIT_LOOP_NUM)

i = I_AMPLITUDE * np.exp(-x / I_DECAY) * np.cos(2 * np.pi * I_FREQUENCY * x + I_PHASE) + I_OFFSET
q = Q_AMPLITUDE * np.exp(-x / Q_DECAY) * np.cos(2 * np.pi * Q_FREQUENCY * x + Q_PHASE) + Q_OFFSET


@pytest.fixture(name="ramsey_1d")
def fixture_ramsey_1d():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = Ramsey(
        platform=platform,
        qubit=QUBIT,
        wait_loop_values=np.linspace(start=WAIT_LOOP_START, stop=WAIT_LOOP_STOP, num=WAIT_LOOP_NUM),
        delta_artificial=DELTA_ARTIFICIAL,
    )
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


@pytest.fixture(name="ramsey_2d")
def fixture_ramsey_2d():
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = Ramsey(
        platform=platform,
        qubit=QUBIT,
        wait_loop_values=np.linspace(start=WAIT_LOOP_START, stop=WAIT_LOOP_STOP, num=WAIT_LOOP_NUM),
        if_frequency_values=np.linspace(start=IF_LOOP_START, stop=IF_LOOP_STOP, num=IF_LOOP_NUM),
        delta_artificial=DELTA_ARTIFICIAL,
    )
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestRamsey1D:
    """Unit tests for the `Ramsey` class."""

    def test_init(self, ramsey_1d: Ramsey):
        """Test the `__init__` method."""
        # Test that the correct circuit is created (gates and qubit)
        assert len(ramsey_1d.circuits) == 1
        expected_gates = [Drag, Wait, Drag, Wait, M]
        for obtained_gate, expected_type in zip(ramsey_1d.circuits[0].queue, expected_gates):
            assert isinstance(obtained_gate, expected_type)
            assert obtained_gate.qubits == (QUBIT,)

        # Test the loop options
        assert ramsey_1d.options.loops is not None
        assert len(ramsey_1d.options.loops) == 2
        assert ramsey_1d.loops[0].alias == "2"
        assert ramsey_1d.loops[0].parameter == Parameter.GATE_PARAMETER
        assert ramsey_1d.loops[0].start == WAIT_LOOP_START
        assert ramsey_1d.loops[0].stop == WAIT_LOOP_STOP
        assert ramsey_1d.loops[0].num == WAIT_LOOP_NUM

    def test_func(self, ramsey_1d: Ramsey):
        """Test the `func` method."""
        assert np.allclose(
            ramsey_1d.func(
                xdata=x, amplitude=I_AMPLITUDE, decay=I_DECAY, frequency=I_FREQUENCY, phase=I_PHASE, offset=I_OFFSET
            ),
            i,
        )
        assert np.allclose(
            ramsey_1d.func(
                xdata=x, amplitude=Q_AMPLITUDE, decay=Q_DECAY, frequency=Q_FREQUENCY, phase=Q_PHASE, offset=Q_OFFSET
            ),
            q,
        )

    def test_plot(self, ramsey_1d: Ramsey):
        """Test plot method."""
        ramsey_1d.post_processed_results = q
        try:
            popt = ramsey_1d.fit(
                p0=(
                    (
                        I_AMPLITUDE * 0.9,
                        I_DECAY * 1.1,
                        I_FREQUENCY * 0.92,
                        I_PHASE * 1.05,
                        I_OFFSET * 0.99,
                    )
                )
            )
        except RuntimeError:
            assert False, "Fitting failed"
        fig = ramsey_1d.plot()
        scatter_data = fig.findobj(match=lambda x: hasattr(x, "get_offsets"))[0].get_offsets()
        assert np.allclose(scatter_data[:, 0], x)
        assert np.allclose(scatter_data[:, 1], q)
        ax = fig.axes[0]
        line = ax.lines[0]
        assert np.allclose(line.get_xdata(), x)
        assert np.allclose(line.get_ydata(), ramsey_1d.func(x, *popt[0]))


class TestRamsey2D:
    """Unit tests for the `Ramsey` class."""

    def test_init(self, ramsey_2d: Ramsey):
        """Test the `__init__` method."""
        # Test that the correct circuit is created (gates and qubit)
        assert len(ramsey_2d.circuits) == 1
        expected_gates = [Drag, Wait, Drag, Wait, M]
        for obtained_gate, expected_type in zip(ramsey_2d.circuits[0].queue, expected_gates):
            assert isinstance(obtained_gate, expected_type)
            assert obtained_gate.qubits == (QUBIT,)

        # Test the loop options
        assert ramsey_2d.options.loops is not None
        assert len(ramsey_2d.options.loops) == 2
        assert ramsey_2d.loops[0].alias == f"drive_line_q{QUBIT}_bus"
        assert ramsey_2d.loops[0].parameter == Parameter.LO_FREQUENCY
        assert ramsey_2d.loops[0].start == IF_LOOP_START
        assert ramsey_2d.loops[0].stop == IF_LOOP_STOP
        assert ramsey_2d.loops[0].num == IF_LOOP_NUM
        assert ramsey_2d.loops[0].loop is not None
        assert ramsey_2d.loops[0].loop.alias == "2"
        assert ramsey_2d.loops[0].loop.parameter == Parameter.GATE_PARAMETER
        assert ramsey_2d.loops[0].loop.start == WAIT_LOOP_START
        assert ramsey_2d.loops[0].loop.stop == WAIT_LOOP_STOP
        assert ramsey_2d.loops[0].loop.num == WAIT_LOOP_NUM

    def test_func(self, ramsey_2d: Ramsey):
        """Test the `func` method."""
        assert np.allclose(
            ramsey_2d.func(
                xdata=x, amplitude=I_AMPLITUDE, decay=I_DECAY, frequency=I_FREQUENCY, phase=I_PHASE, offset=I_OFFSET
            ),
            i,
        )
        assert np.allclose(
            ramsey_2d.func(
                xdata=x, amplitude=Q_AMPLITUDE, decay=Q_DECAY, frequency=Q_FREQUENCY, phase=Q_PHASE, offset=Q_OFFSET
            ),
            q,
        )

    def test_plot(self, ramsey_2d: Ramsey):
        res = ramsey_2d.post_process_results().flatten()
        im = ramsey_2d.plot()
        assert np.array_equal(im.get_array(), res)
