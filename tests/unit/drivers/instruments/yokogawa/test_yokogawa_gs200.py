""" Test empty abstract class, YokogawaGS200"""
from unittest.mock import MagicMock

from qcodes import Instrument
from qcodes.instrument_drivers.yokogawa.GS200 import GS200Program
from qcodes.tests.instrument_mocks import DummyChannelInstrument, DummyInstrument

from qililab.drivers import YokogawaGS200
from qililab.drivers.instruments.yokogawa.yokogawa_gs200 import YokogawaGS200Monitor

NUM_SUBMODULES = 2
MONITOR_NAME = "measure"
PROGRAM_NAME = "program"


class MockYokowagaGS200Monitor(DummyChannelInstrument):
    """Mocking classes for YokowagaGS200Monitor"""

    def __init__(self, parent: Instrument, name: str, present: bool = False):
        """Init method for the mock YokowagaGS200Monitor"""

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


class TestYokogawaGS200:
    """Unit tests checking the qililab YokogawaGS200 attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_yokowaga_gs_200_bases: tuple[type, ...] = YokogawaGS200.__bases__
        YokogawaGS200.__bases__ = (DummyInstrument,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        YokogawaGS200.__bases__ = cls.old_yokowaga_gs_200_bases

    def test_init(self):
        """Unit tests for init method"""
        yokogawa_name = "test_yokowaga"
        yokogawa_gs_200 = YokogawaGS200(name=yokogawa_name, address="")
        submodules = yokogawa_gs_200.submodules
        expected_names = [f"{yokogawa_name}_{MONITOR_NAME}", f"{yokogawa_name}_{PROGRAM_NAME}"]
        registered_names = [submodules[key].name for key in list(submodules.keys())]
        yokogawa_monitor = yokogawa_gs_200.submodules[MONITOR_NAME]

        assert len(submodules) == NUM_SUBMODULES
        assert all(
            isinstance(submodules[name], YokogawaGS200Monitor | GS200Program) for name in list(submodules.keys())
        )
        assert expected_names == registered_names
        assert yokogawa_monitor.present is True


class TestYokogawaGS200Monitor:
    """Unit tests checking the qililab YokogawaGS200 attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""
        cls.old_yokowaga_gs_200_monitor_bases: tuple[type, ...] = YokogawaGS200Monitor.__bases__
        YokogawaGS200Monitor.__bases__ = (MockYokowagaGS200Monitor,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""
        Instrument.close_all()
        YokogawaGS200Monitor.__bases__ = cls.old_yokowaga_gs_200_monitor_bases

    def test_off(self):
        """Unit tests for on method"""
        yokogawa_name_monitor = "test_yokowaga_monitor_on"
        yokogawa_gs_200 = YokogawaGS200Monitor(parent=MagicMock(), name=yokogawa_name_monitor, present=True)

        # testing the whole on/off cycle works fine
        assert yokogawa_gs_200.get("enabled") == "off"
        yokogawa_gs_200.on()
        assert yokogawa_gs_200.get("enabled") == "on"
        yokogawa_gs_200.off()
        assert yokogawa_gs_200.get("enabled") == "off"

    def test_on(self):
        """Unit tests for on method"""
        yokogawa_name_monitor = "test_yokowaga_monitor_on"
        yokogawa_gs_200 = YokogawaGS200Monitor(parent=MagicMock(), name=yokogawa_name_monitor, present=True)

        yokogawa_gs_200.on()
        assert yokogawa_gs_200.get("enabled") == "on"
