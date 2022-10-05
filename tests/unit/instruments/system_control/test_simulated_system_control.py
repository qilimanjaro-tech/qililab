"""Tests for the SimulatedSystemControl class."""
from pathlib import Path

import pytest
from qilisimulator.evolution import Evolution

from qililab.instruments import SimulatedSystemControl
from qililab.pulse import PulseSequence
from qililab.result import SimulatorResult


class TestSimulatedSystemControl:
    """Unit tests checking the SimulatedSystemControl attributes and methods"""

    def test_init(self, simulated_system_control: SimulatedSystemControl):
        """Test initialization"""
        assert isinstance(simulated_system_control.settings, SimulatedSystemControl.SimulatedSystemControlSettings)
        assert isinstance(simulated_system_control._evo, Evolution)

    def test_run_method(self, simulated_system_control: SimulatedSystemControl, pulse_sequence: PulseSequence):
        """Test run method."""
        result = simulated_system_control.run(
            pulse_sequence=pulse_sequence, nshots=1, repetition_duration=2000, path=Path(__file__).parent
        )
        assert isinstance(result, SimulatorResult)

    def test_frequency_property(self, simulated_system_control: SimulatedSystemControl):
        """Test frequency property."""
        assert simulated_system_control.frequency == simulated_system_control._evo.system.qubit.frequency

    def test_name_property(self, simulated_system_control: SimulatedSystemControl):
        """Test name property."""
        assert simulated_system_control.name == simulated_system_control.settings.subcategory

    def test_delay_time_property_raises_error(self, simulated_system_control: SimulatedSystemControl):
        """Test acquisition_delay_time property."""
        with pytest.raises(AttributeError):
            _ = simulated_system_control.acquisition_delay_time
