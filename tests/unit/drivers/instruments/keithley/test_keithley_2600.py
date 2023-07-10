"""Unit tests for Keithley_2600"""

from unittest.mock import MagicMock

from qcodes import Instrument
from qcodes.parameters.val_mapping import create_on_off_val_mapping
from qcodes.tests.instrument_mocks import DummyChannel, DummyInstrument

from qililab.drivers.instruments.keithley import Keithley2600
from qililab.drivers.instruments.keithley.keithley_2600 import Keithley2600Channel

NUM_SUBMODULES = 2


class MockKeithley2600(DummyInstrument):
    """Mocking classes for Keithley2600"""

    def __init__(self, name: str, address: str, **kwargs):
        """Init method for the mock Keithley2600"""

        super().__init__(name, **kwargs)
        self.model = "test_model"
        self._vranges = {"test_model": [0, 1]}
        self._iranges = {"test_model": [0, 1]}
        self._vlimit_minmax = {"test_model": [0, 1]}
        self._ilimit_minmax = {"test_model": [0, 1]}


class MockKeithley2600Channel(DummyChannel):
    """Mocking classes for Keithley2600Channel"""

    def __init__(self, parent: Instrument, name: str, channel: str):
        """Init method for the mock Keithley2600Channel"""

        super().__init__(parent, name, channel=channel)

        self.add_parameter(
            "mode",
            get_cmd=f"{channel}.source.func",
            get_parser=float,
            set_cmd=f"{channel}.source.func={{:d}}",
            val_mapping={"current": 0, "voltage": 1},
            docstring="Selects the output source type. " "Can be either voltage or current.",
        )

        self.add_parameter(
            "output",
            get_cmd=f"{channel}.source.output",
            get_parser=None,
            set_cmd=f"{channel}.source.output={{:d}}",
            val_mapping=create_on_off_val_mapping(on_val=1, off_val=0),
        )
        self.output = "off"

    # Pass any commands to read or write from the instrument up to the parent
    def write(self, cmd: str) -> None:
        if "output" in cmd:
            self.output = cmd[-1] if int(cmd[-1]) == 1 else "0"

    def ask(self, cmd: str) -> str:
        if "output" in cmd:
            return self.output
        else:
            return ""


class TestKeithley2600:
    """Unit tests checking the qililab Keithley2600 attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_keithley_2600_bases: tuple[type, ...] = Keithley2600.__bases__
        Keithley2600.__bases__ = (MockKeithley2600,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        Keithley2600.__bases__ = cls.old_keithley_2600_bases

    def test_init(self):
        """Unit tests for init method"""

        keithley_name = "test_keithley"
        keithley_2600 = Keithley2600(name=keithley_name, address="192.168.1.68")
        submodules = keithley_2600.submodules
        channels_names = [f"smu{ch}" for ch in ["a", "b"]]
        expected_names = [f"{keithley_name}_{name}" for name in channels_names]
        registered_names = [submodules[key].name for key in list(submodules.keys())]

        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[name], Keithley2600Channel) for name in channels_names)
        assert expected_names == registered_names


class TestKeithley2600Channel:
    """Unit tests checking the qililab Keithley2600Channel attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""
        cls.old_keithley_2600_channel_bases: tuple[type, ...] = Keithley2600Channel.__bases__
        Keithley2600Channel.__bases__ = (MockKeithley2600Channel,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        Keithley2600Channel.__bases__ = cls.old_keithley_2600_channel_bases

    def test_on(self):
        """Unit tests for on method"""
        channel_smua = Keithley2600Channel(parent=MagicMock(), name="test_channel_smua", channel="smua")
        channel_smub = Keithley2600Channel(parent=MagicMock(), name="test_channel_smub", channel="smub")
        channel_smua.on()
        channel_smub.on()

        assert (channel_smua.get("output") == True)
        assert (channel_smub.get("output") == True)

    def test_off(self):
        """Unit tests for off method"""
        channel_smua = Keithley2600Channel(parent=MagicMock(), name="test_channel_smua", channel="smua")
        channel_smub = Keithley2600Channel(parent=MagicMock(), name="test_channel_smub", channel="smub")
        # check the whole on/off cycle works as expected
        channel_smua.on()
        channel_smub.on()
        assert (channel_smua.get("output") == True)
        assert (channel_smub.get("output") == True)
        channel_smua.off()
        channel_smub.off()
        assert (channel_smua.get("output") == False)
        assert (channel_smub.get("output") == False)
