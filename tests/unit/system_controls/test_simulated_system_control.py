"""Tests for the SimulatedSystemControl class."""

from qilisimulator.evolution import Evolution

from qililab.pulse import PulseBusSchedule
from qililab.result import SimulatorResult
from qililab.system_controls.system_control_types import SimulatedSystemControl
from qililab.typings.enums import SystemControlName


class TestSimulatedSystemControl:
    """Unit tests checking the SimulatedSystemControl attributes and methods"""

    def test_init(self, simulated_system_control: SimulatedSystemControl):
        """Test initialization"""
        assert isinstance(simulated_system_control.settings, SimulatedSystemControl.SimulatedSystemControlSettings)
        assert isinstance(simulated_system_control._evo, Evolution)  # pylint: disable=protected-access

    def test_run_method(self, simulated_system_control: SimulatedSystemControl, pulse_bus_schedule: PulseBusSchedule):
        """Test run method."""
        simulated_system_control.generate_program(pulse_bus_schedule=pulse_bus_schedule, frequency=6.0e09)
        simulated_system_control.run()
        result = simulated_system_control.acquire_result()
        assert isinstance(result, SimulatorResult)

    def test_name_property(self, simulated_system_control: SimulatedSystemControl):
        """Test name property."""
        assert simulated_system_control.name == SystemControlName.SIMULATED_SYSTEM_CONTROL
