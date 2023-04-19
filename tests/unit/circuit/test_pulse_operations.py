"""Tests for the PulseOperation class and its subclasses."""
import numpy as np
import pytest

from qililab.circuit.operations import DRAGPulse, GaussianPulse, PulseOperation, SquarePulse
from qililab.utils.waveforms import Waveforms


@pytest.fixture(
    name="pulse_operation",
    params=[
        SquarePulse(amplitude=1.0, duration=40, phase=0.0, frequency=8.5e9),
        GaussianPulse(amplitude=1.0, duration=40, phase=0.0, frequency=8.5e9, sigma=1.0),
        DRAGPulse(amplitude=1.0, duration=40, phase=0.0, frequency=8.5e9, sigma=1.0, delta=2.0),
    ],
)
def fixture_pulse_operation(request: pytest.FixtureRequest) -> PulseOperation:
    """Return PulseOperation object."""
    return request.param  # type: ignore


class TestPulseOperation:
    """Unit tests checking the PulseOperation attributes and methods"""

    def test_envelope_method(self, pulse_operation: PulseOperation):
        """Test envelope method"""
        envelope = pulse_operation.envelope(resolution=0.5)
        assert isinstance(envelope, np.ndarray)

    def test_modulated_waveforms_method(self, pulse_operation: PulseOperation):
        """Test modulated_waveforms method"""
        modulated_waveforms = pulse_operation.modulated_waveforms(resolution=0.5)
        assert isinstance(modulated_waveforms, Waveforms)
