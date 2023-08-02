"""Mocking utilities for SpiRack and children classes"""

from unittest.mock import MagicMock

from qblox_instruments.qcodes_drivers.spi_rack_modules import (
    D5aModule,
    DummySpiModule,
    S4gModule,
)
from qcodes.tests.instrument_mocks import DummyChannel, DummyInstrument

from qililab.drivers.instruments.qblox.spi_rack import D5aDacChannel, S4gDacChannel

NUM_DACS_D5AMODULE = 16
NUM_DACS_S4GMODULE = 4


class MockSpiRack(DummyInstrument):
    """Mocking classes for SpiRack"""

    def __init__(self, name, address, **kwargs):
        """Init method for the mock SpiRack module"""
        self.api = MagicMock()
        super().__init__(name, **kwargs)

        self._MODULES_MAP = {
            "S4g": S4gModule,
            "D5a": D5aModule,
            "dummy": DummySpiModule,
        }


class MockD5aModule(DummyInstrument):
    """Mocking classes for D5a module"""

    def __init__(self, parent, name, address, **kwargs):
        """Init method for the mock D5a module"""
        self.api = MagicMock()
        super().__init__(name, **kwargs)

        self._channels = []
        for dac in range(NUM_DACS_D5AMODULE):
            ch_name = f"dac{dac}"
            channel = D5aDacChannel(self, ch_name, dac)
            self._channels.append(channel)


class MockS4gModule(DummyInstrument):
    """Mocking classes for S4g module"""

    def __init__(self, parent, name, address, **kwargs):
        """Init method for the mock S4g module"""
        self.api = MagicMock()
        super().__init__(name, **kwargs)

        self._channels = []
        for dac in range(NUM_DACS_S4GMODULE):
            ch_name = f"dac{dac}"
            channel = S4gDacChannel(self, ch_name, dac)
            self._channels.append(channel)


class MockD5aDacChannel(DummyChannel):
    """Mocking classes for D5aDacChannel"""

    def __init__(self, parent, name, dac, **kwargs):
        """Init method for the mock D5aDacChannel"""
        super().__init__(parent, name, "test_channel", **kwargs)

        self.add_parameter(
            "voltage",
            get_cmd=None,
            set_cmd=None,
            unit="V",
            vals=None,
            docstring="Sets the output voltage of the dac channel. Depending "
            "on the value of ramping_enabled, the output value is either "
            "achieved through slowly ramping, or instantaneously set.",
        )


class MockS4gDacChannel(DummyChannel):
    """Mocking classes for S4gDacChannel"""

    def __init__(self, parent, name, dac, **kwargs):
        """Init method for the mock S4gDacChannel"""
        super().__init__(parent, name, "test_channel", **kwargs)

        self.add_parameter(
            "current",
            get_cmd=None,
            set_cmd=None,
            unit="A",
            vals=None,
            docstring="Sets the output current of the dac channel. Depending "
            "on the value of ramping_enabled, the output value is either "
            "achieved through slowly ramping, or instantaneously set.",
        )
