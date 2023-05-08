"""Tests for the SimulatedSystemControl class."""
from unittest.mock import MagicMock

import numpy as np
import pytest
from qilisimulator.evolution import Evolution

from qililab.platform import Platform
from qililab.pulse import PulseBusSchedule
from qililab.result.simulator_result import SimulatorResult
from qililab.system_control import SimulatedSystemControl
from qililab.typings.enums import SystemControlName


@pytest.fixture(name="simulated_system_control")
def fixture_simulated_system_control():
    settings = {
        "id_": 0,
        "category": "system_control",
        "qubit": "csfq4jj",
        "qubit_params": {"n_cut": 10, "phi_x": 6.28318530718, "phi_z": -0.25132741228},
        "drive": "zport",
        "drive_params": {"dimension": 10},
        "resolution": 1,
        "store_states": False,
    }
    return SimulatedSystemControl(settings=settings, platform_instruments=None)


class TestSimulatedSystemControl:
    """Unit tests checking the SimulatedSystemControl attributes and methods"""

    def test_init(self, simulated_system_control: SimulatedSystemControl):
        """Test initialization"""
        assert isinstance(simulated_system_control.settings, SimulatedSystemControl.SimulatedSystemControlSettings)
        assert isinstance(simulated_system_control._evo, Evolution)  # pylint: disable=protected-access

    def test_compile_method(
        self, simulated_system_control: SimulatedSystemControl, pulse_bus_schedule: PulseBusSchedule
    ):
        """Test compile method."""
        sequences = simulated_system_control.compile(pulse_bus_schedule=pulse_bus_schedule)
        assert isinstance(sequences, list)
        assert len(sequences) == 0
        assert isinstance(simulated_system_control.sequence, list)
        assert isinstance(simulated_system_control.sequence[0], np.ndarray)

    def test_upload_method(self, simulated_system_control: SimulatedSystemControl):
        """Test upload method."""
        simulated_system_control.upload()  # this method does nothing

    def test_run_method(self, simulated_system_control: SimulatedSystemControl, pulse_bus_schedule: PulseBusSchedule):
        """Test run method."""
        simulated_system_control._evo = MagicMock()
        simulated_system_control.compile(pulse_bus_schedule=pulse_bus_schedule)
        simulated_system_control.run()
        result = simulated_system_control.acquire_result()
        assert isinstance(result, SimulatorResult)

    def test_name_property(self, simulated_system_control: SimulatedSystemControl):
        """Test name property."""
        assert simulated_system_control.name == SystemControlName.SIMULATED_SYSTEM_CONTROL

    def test_probabilities(
        self, simulated_system_control: SimulatedSystemControl, pulse_bus_schedule: PulseBusSchedule
    ):
        """Test probabilities method."""
        simulated_system_control._evo = MagicMock()
        simulated_system_control.compile(pulse_bus_schedule=pulse_bus_schedule)
        simulated_system_control.compile(pulse_bus_schedule=pulse_bus_schedule)
        simulated_system_control.run()
        result = simulated_system_control.acquire_result()
        assert result.probabilities() == {}
