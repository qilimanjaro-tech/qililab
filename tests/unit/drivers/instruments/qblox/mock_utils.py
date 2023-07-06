"""Mocking utilities for SpiRack and children classes"""

from unittest.mock import MagicMock

from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers.instruments.qblox.spi_rack import D5aDacChannel, S4gDacChannel

NUM_DACS_D5AMODULE = 16
NUM_DACS_S4GMODULE = 4


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
