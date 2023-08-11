"""Tests for the SystemControl class."""
from unittest.mock import MagicMock

import pytest
from qpysequence import Sequence

from qililab.instruments import AWG, Instrument
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent
from qililab.system_control import SystemControl
from qililab.typings.enums import Category
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0)
    return PulseBusSchedule(timeline=[pulse_event], port=0)


@pytest.fixture(name="system_control")
def fixture_system_control(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {
        "id_": 1,
        "category": "system_control",
        "instruments": ["QCM", "rs_1"],
    }
    return SystemControl(settings=settings, platform_instruments=platform.instruments)


@pytest.fixture(name="system_control_without_awg")
def fixture_system_control_without_awg(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {
        "id_": 1,
        "alias": "test_alias",
        "category": "system_control",
        "instruments": ["rs_1"],
    }
    return SystemControl(settings=settings, platform_instruments=platform.instruments)


class TestInitialization:
    """Unit tests checking the ``SystemControl`` initialization."""

    def test_init(self, system_control: SystemControl):
        """Test initialization."""
        assert isinstance(system_control.settings, SystemControl.SystemControlSettings)
        assert system_control.settings.id_ == 1
        assert system_control.settings.alias is None
        assert system_control.name.value == "system_control"
        assert isinstance(system_control.settings.category, Category)
        assert system_control.settings.category == Category.SYSTEM_CONTROL
        for instrument in system_control.settings.instruments:
            assert isinstance(instrument, Instrument)
        assert not hasattr(system_control.settings, "platform_instruments")


@pytest.fixture(name="base_system_control")
def fixture_base_system_control(platform: Platform) -> SystemControl:
    """Load SystemControl.

    Returns:
        SystemControl: Instance of the ControlSystemControl class.
    """
    return platform.buses[0].system_control


class TestMethods:
    """Unit tests checking the ``SystemControl`` methods."""

    def test_iter_method(self, system_control: SystemControl):
        """Test __iter__ method."""
        for instrument in system_control:
            assert isinstance(instrument, Instrument)

    def test_compile_raises_error(self, system_control_without_awg: SystemControl):
        """Test that the ``compile`` method raises an error when the system control doesn't have an AWG."""
        with pytest.raises(
            AttributeError,
            match="The system control with alias test_alias doesn't have any AWG to compile the given pulse sequence",
        ):
            system_control_without_awg.compile(
                PulseBusSchedule(port=0), nshots=1000, repetition_duration=1000, num_bins=1
            )

    def test_compile(self, system_control: SystemControl, pulse_bus_schedule: PulseBusSchedule):
        """Test the ``compile`` method of the ``SystemControl`` class."""
        sequences = system_control.compile(
            pulse_bus_schedule=pulse_bus_schedule, nshots=1000, repetition_duration=2000, num_bins=1
        )
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)
        assert sequences[0]._program.duration == 1000 * 2000 + 4

    def test_upload_raises_error(self, system_control_without_awg: SystemControl):
        """Test that the ``upload`` method raises an error when the system control doesn't have an AWG."""
        with pytest.raises(
            AttributeError,
            match="The system control with alias test_alias doesn't have any AWG to upload a program",
        ):
            system_control_without_awg.upload(port=0)

    def test_upload(self, system_control: SystemControl, pulse_bus_schedule: PulseBusSchedule):
        """Test upload method."""
        awg = system_control.instruments[0]
        assert isinstance(awg, AWG)
        awg.device = MagicMock()
        _ = system_control.compile(pulse_bus_schedule, nshots=1000, repetition_duration=2000, num_bins=1)
        system_control.upload(port=pulse_bus_schedule.port)
        for seq_idx in range(awg.num_sequencers):
            awg.device.sequencers[seq_idx].sequence.assert_called_once()

    def test_run_raises_error(self, system_control_without_awg: SystemControl):
        """Test that the ``run`` method raises an error when the system control doesn't have an AWG."""
        with pytest.raises(
            AttributeError,
            match="The system control with alias test_alias doesn't have any AWG to run a program",
        ):
            system_control_without_awg.run(port=0)


class TestProperties:
    """Unit tests checking the SystemControl attributes and methods"""

    def test_category_property(self, system_control: SystemControl):
        """Test category property."""
        assert system_control.category == system_control.settings.category

    def test_id_property(self, system_control: SystemControl):
        """Test id property."""
        assert system_control.id_ == system_control.settings.id_

    def test_instruments_property(self, system_control: SystemControl):
        """Test instruments property."""
        assert system_control.instruments == system_control.settings.instruments
