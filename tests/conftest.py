"""Pytest configuration fixtures."""
from unittest.mock import MagicMock, patch

import pytest

from qililab import build_platform
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseEvent

from .data import FluxQubitSimulator


@pytest.fixture(name="pulse")
def fixture_pulse() -> Pulse:
    """Load Pulse.

    Returns:
        Pulse: Instance of the Pulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="simulated_platform")
@patch("qililab.system_control.simulated_system_control.Evolution", autospec=True)
def fixture_simulated_platform(mock_evolution: MagicMock) -> Platform:
    """Return Platform object."""

    # Mocked Evolution needs: system.qubit.frequency, psi0, states, times
    mock_system = MagicMock()
    mock_system.qubit.frequency = 0
    mock_evolution.return_value.system = mock_system
    mock_evolution.return_value.states = []
    mock_evolution.return_value.times = []
    mock_evolution.return_value.psi0 = None

    with patch(
        "qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=FluxQubitSimulator.runcard
    ) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform
