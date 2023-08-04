""" Test empty abstract class, Yokogawa GS200"""
from unittest.mock import MagicMock

from qcodes import Instrument
from qcodes.instrument_drivers.yokogawa.GS200 import GS200_Monitor, GS200Program
from qcodes.tests.instrument_mocks import DummyChannelInstrument, DummyInstrument

from qililab.drivers import GS200

NUM_SUBMODULES = 2
MONITOR_NAME = "measure"
PROGRAM_NAME = "program"


class MockGS200Monitor(DummyChannelInstrument):  # pylint: disable=abstract-method
    """Mocking classes for Yokowaga GS200Monitor"""

    def __init__(self, parent: Instrument, name: str, present: bool = False):  # pylint: disable=unused-argument
        """Init method for the mock Yokowaga GS200Monitor"""
        super().__init__(name)
        self.present = present
        self._enabled = False

        # Set up monitoring parameters
        if present:
            self.add_parameter(
                "enabled",
                label="Measurement Enabled",
                get_cmd=self.state,
                set_cmd=lambda x: self.on() if x else self.off(),
                val_mapping={
                    "off": 0,
                    "on": 1,
                },
            )

    def write(self, cmd: str) -> None:
        return None

    def off(self) -> None:
        """Turn measurement off"""
        self._enabled = False

    def on(self) -> None:
        """Turn measurement on"""
        self._enabled = True

    def state(self) -> int:
        """Check measurement state"""
        return self._enabled


class TestGS200:
    """Unit tests checking the qililab Yokogawa GS200 attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""
        cls.old_yokowaga_gs_200_bases: tuple[type, ...] = GS200.__bases__
        GS200.__bases__ = (DummyInstrument,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""
        Instrument.close_all()
        GS200.__bases__ = cls.old_yokowaga_gs_200_bases

    def test_init(self):
        """Unit tests for init method"""
        yokogawa_name = "test_yokowaga"
        yokogawa_gs_200 = GS200(name=yokogawa_name, address="")
        submodules = yokogawa_gs_200.submodules
        instrument_modules = yokogawa_gs_200.instrument_modules
        submodules_expected_names = [f"{yokogawa_name}_{MONITOR_NAME}", f"{yokogawa_name}_{PROGRAM_NAME}"]
        registered_submodules_names = [submodules[key].name for key in list(submodules.keys())]
        registered_instrument_modules_names = [submodules[key].name for key in list(instrument_modules.keys())]
        yokogawa_monitor = yokogawa_gs_200.submodules[MONITOR_NAME]

        assert len(submodules) == len(instrument_modules) == NUM_SUBMODULES
        assert submodules_expected_names == registered_submodules_names == registered_instrument_modules_names
        assert all(isinstance(submodules[name], GS200_Monitor | GS200Program) for name in list(submodules.keys()))
        assert all(
            isinstance(instrument_modules[name], GS200_Monitor | GS200Program)
            for name in list(instrument_modules.keys())
        )
        assert yokogawa_monitor.present is True
        assert yokogawa_gs_200._channel_lists == {}


class TestGS200Monitor:
    """Unit tests checking the qililab Yokogawa GS200 attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""
        cls.old_yokowaga_gs_200_monitor_bases: tuple[type, ...] = GS200_Monitor.__bases__
        GS200_Monitor.__bases__ = (MockGS200Monitor,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""
        Instrument.close_all()
        GS200_Monitor.__bases__ = cls.old_yokowaga_gs_200_monitor_bases

    def test_off(self):
        """Unit tests for on method"""
        yokogawa_name_monitor = "test_yokowaga_monitor_on"
        yokogawa_gs_200 = GS200_Monitor(parent=MagicMock(), name=yokogawa_name_monitor, present=True)

        # testing the whole on/off cycle works fine
        assert yokogawa_gs_200.get("enabled") == "off"
        yokogawa_gs_200.on()
        assert yokogawa_gs_200.get("enabled") == "on"
        yokogawa_gs_200.off()
        assert yokogawa_gs_200.get("enabled") == "off"

    def test_on(self):
        """Unit tests for on method"""
        yokogawa_name_monitor = "test_yokowaga_monitor_on"
        yokogawa_gs_200 = GS200_Monitor(parent=MagicMock(), name=yokogawa_name_monitor, present=True)

        yokogawa_gs_200.on()
        assert yokogawa_gs_200.get("enabled") == "on"
