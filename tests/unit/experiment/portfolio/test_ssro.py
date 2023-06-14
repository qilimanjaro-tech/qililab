"""Unit tests for the ``SSRO`` class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.gates import M

from qililab import build_platform
from qililab.experiment import SSRO
from qililab.transpiler.native_gates import Drag
from qililab.typings.enums import Parameter
from qililab.utils import Wait
from tests.data import Galadriel

START, STOP, NUM = (1, 1000, 101)
I_AMPLITUDE, I_FREQ, I_PHASE, I_OFFSET = (5, 7 / (2 * np.pi), -np.pi / 2, 0)
Q_AMPLITUDE, Q_FREQ, Q_PHASE, Q_OFFSET = (9, 7 / (2 * np.pi), -np.pi / 2, 0)

x = np.linspace(START, STOP, NUM)
i = I_AMPLITUDE * np.cos(2 * np.pi * I_FREQ * x + I_PHASE)
q = Q_AMPLITUDE * np.cos(2 * np.pi * Q_FREQ * x + Q_PHASE)


@pytest.fixture(
    name="ssro",
    params=[Parameter.DURATION, Parameter.AMPLITUDE, Parameter.IF, Parameter.LO_FREQUENCY, Parameter.ATTENUATION, None],
)
def fixture_ssro(request: pytest.FixtureRequest):
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = SSRO(
        platform=platform,
        qubit=0,
        loop_values=np.linspace(start=START, stop=STOP, num=NUM),
        loop_parameter=request.param,
    )
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestSSRO:
    """Unit tests for the ``SSRO`` portfolio experiment class."""

    def test_init(self, ssro: SSRO):
        """Test the ``__init__`` method."""
        # Test that the correct circuits are created
        assert len(ssro.circuits) == 2
        for circuit in ssro.circuits:
            for idx, gate in enumerate(circuit.queue):
                assert isinstance(gate, [Drag, Wait, M][idx])
                assert gate.qubits == (0,)
        # Test atributes
        assert hasattr(ssro, "qubit")
        assert hasattr(ssro, "loop_parameter")
        assert hasattr(ssro, "loop_values")

        # Test the experiment options
        if ssro.loop_parameter == Parameter.DURATION:
            assert len(ssro.options.loops) == 2
        else:
            assert len(ssro.options.loops) == 1

        # Check loops depending on the parameter
        if ssro.loop_parameter is None:
            assert ssro.loop.alias == "external"
            assert ssro.loop.parameter == Parameter.EXTERNAL
            assert ssro.loop.values == np.array([1])
            # Loop values
            assert ssro.loop.start == 1
            assert ssro.loop.stop == 1
            assert ssro.loop.num == 1
        else:
            if ssro.loop_parameter == Parameter.DURATION:
                # Test both loops are well created
                assert ssro.loop.alias == f"M({ssro.qubit})"
                assert ssro.options.loops[1].alias == "feedline_bus"

                assert ssro.loop.parameter == Parameter.DURATION
                assert ssro.options.loops[1].parameter == Parameter.INTEGRATION_LENGTH

                assert ssro.options.loops[1].channel_id == ssro.qubit

                assert ssro.options.loops[1].start == START
                assert ssro.options.loops[1].stop == STOP
                assert ssro.options.loops[1].num == NUM

            elif ssro.loop_parameter == Parameter.AMPLITUDE:
                assert ssro.loop.alias == f"M({ssro.qubit})"
                assert ssro.loop.parameter == ssro.loop_parameter

            elif ssro.loop_parameter == Parameter.IF:
                assert ssro.loop.alias == "feedline_bus"
                assert ssro.loop.parameter == ssro.loop_parameter
                assert ssro.loop.channel_id == ssro.qubit

            elif ssro.loop_parameter == Parameter.LO_FREQUENCY:
                assert ssro.loop.alias == "rs_1"
                assert ssro.loop.parameter == ssro.loop_parameter
                assert ssro.loop.channel_id is None

            elif ssro.loop_parameter == Parameter.ATTENUATION:
                assert ssro.loop.alias == "attenuator"
                assert ssro.loop.parameter == ssro.loop_parameter
            # Loop values
            assert ssro.loop.start == START
            assert ssro.loop.stop == STOP
            assert ssro.loop.num == NUM

    def test_func(self, ssro: SSRO):
        """Test the ``func`` method."""
        assert np.allclose(
            ssro.func(xdata=x, amplitude=I_AMPLITUDE, frequency=I_FREQ, phase=I_PHASE, offset=I_OFFSET),
            i,
        )
