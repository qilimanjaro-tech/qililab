from qcodes.tests.instrument_mocks import DummyInstrument
from qililab.drivers.instruments.qblox.spi_rack import D5aDacChannel, D5aModule
from unittest.mock import MagicMock

NUM_SUBMODULES = 6

class MockSpiRack(DummyInstrument):
    def __init__(self, name, address=None, **kwargs):
        super().__init__(name, **kwargs)

        self.address = address
        self.submodules = {"test_submodule": MagicMock()}

class MockD5aModule(DummyInstrument):
    def __init__(self, parent, name, address, **kwargs):
        super().__init__(name, **kwargs)

class TestD5aModule:
    """Unit tests checking the qililab D5aModule attributes and methods"""

    def test_init(self):
        """Unit tests for init method"""

        D5aModule.__bases__ = (MockD5aModule,)
        mock_rack_spi = MockSpiRack(name="test_rack")
        d5a_module = D5aModule(parent=mock_rack_spi, name="test_d5amodule", address=0)
        submodules = d5a_module.submodules
