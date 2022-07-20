"""Tests for the SimulatedSystemControl class."""
from pathlib import Path

import pytest
import qutip

from qililab.instruments import SimulatedSystemControl
from qililab.pulse import PulseSequence
from qililab.result import SimulatorResult


class TestSimulatedSystemControl:
    """Unit tests checking the SimulatedSystemControl attributes and methods"""

    def test_setup_method(self, simulated_system_control: SimulatedSystemControl):
        """Test setup method."""
        simulated_system_control.setup(frequencies=[0])
        assert isinstance(simulated_system_control.options, qutip.Options)

    def test_run_method(self, simulated_system_control: SimulatedSystemControl, pulse_sequence: PulseSequence):
        """Test run method."""
        result = simulated_system_control.run(
            pulse_sequence=pulse_sequence, nshots=100, repetition_duration=2000, path=Path(__file__).parent
        )
        assert isinstance(result, SimulatorResult)

    def test_amplitude_norm_factor_property(self, simulated_system_control: SimulatedSystemControl):
        """Test amplitude_norm_factor property."""
        assert isinstance(simulated_system_control.amplitude_norm_factor, float)

    def test_hamiltonian_property(self, simulated_system_control: SimulatedSystemControl):
        """Test hamiltonian property."""
        assert simulated_system_control.hamiltonian == simulated_system_control.settings.driving_hamiltonian

    def test_qubit_property(self, simulated_system_control: SimulatedSystemControl):
        """Test qubit property."""
        assert simulated_system_control.qubit == simulated_system_control.settings.qubit

    def test_nsteps_property(self, simulated_system_control: SimulatedSystemControl):
        """Test nsteps property."""
        assert simulated_system_control.nsteps == simulated_system_control.settings.nsteps

    def test_dimension_property(self, simulated_system_control: SimulatedSystemControl):
        """Test dimension property."""
        assert simulated_system_control.dimension == simulated_system_control.settings.dimension

    def test_store_states_property(self, simulated_system_control: SimulatedSystemControl):
        """Test store_states property."""
        assert simulated_system_control.store_states == simulated_system_control.settings.store_states

    def test_frequency_property(self, simulated_system_control: SimulatedSystemControl):
        """Test frequency property."""
        assert simulated_system_control.frequency == simulated_system_control.settings.frequency

    def test_resolution_property(self, simulated_system_control: SimulatedSystemControl):
        """Test resolution property."""
        assert simulated_system_control.resolution == simulated_system_control.settings.resolution

    def test_name_property(self, simulated_system_control: SimulatedSystemControl):
        """Test name property."""
        assert simulated_system_control.name == simulated_system_control.settings.subcategory

    def test_delay_time_property_raises_error(self, simulated_system_control: SimulatedSystemControl):
        """Test acquisition_delay_time property."""
        with pytest.raises(AttributeError):
            _ = simulated_system_control.acquisition_delay_time
