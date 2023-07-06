"""Unit tests for SpiRack, D5aModule, D5aDacChannel, S4gModule and S4gDacChannel"""

from unittest.mock import MagicMock

from qcodes import Instrument

from qililab.drivers.instruments.qblox.spi_rack import (
    D5aDacChannel,
    D5aModule,
    S4gDacChannel,
    S4gModule,
    SpiRack,
)

from .mock_utils import (
    NUM_DACS_D5AMODULE,
    NUM_DACS_S4GMODULE,
    MockD5aDacChannel,
    MockD5aModule,
    MockS4gDacChannel,
    MockS4gModule,
    MockSpiRack,
)


class TestSpiRack:
    """Unit tests checking the qililab SpiRack attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_spi_rack_bases: tuple[type, ...] = SpiRack.__bases__
        SpiRack.__bases__ = (MockSpiRack,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        SpiRack.__bases__ = cls.old_spi_rack_bases

    def test_init(self):
        """Unit tests for init method"""

        spi_rack = SpiRack(name="test_spi_rack", address="192.168.1.68")

        assert spi_rack._MODULES_MAP["S4g"] == S4gModule
        assert spi_rack._MODULES_MAP["D5a"] == D5aModule


class TestD5aModule:
    """Unit tests checking the qililab D5aModule attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_d5a_module_bases: tuple[type, ...] = D5aModule.__bases__
        D5aModule.__bases__ = (MockD5aModule,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        D5aModule.__bases__ = cls.old_d5a_module_bases

    def test_init(self):
        """Unit tests for init method"""

        d5a_module = D5aModule(parent=MagicMock(), name="test_d5a_module", address=0)
        submodules = d5a_module.submodules
        dac_idxs = list(submodules.keys())
        channels = d5a_module._channels

        assert len(submodules) == NUM_DACS_D5AMODULE
        assert len(channels) == NUM_DACS_D5AMODULE
        assert all(isinstance(submodules[dac_idx], D5aDacChannel) for dac_idx in dac_idxs)
        assert all(isinstance(channels[dac_idx], D5aDacChannel) for dac_idx in range(NUM_DACS_D5AMODULE))


class TestS4gModule:
    """Unit tests checking the qililab S4gModule attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_s4g_module_bases: tuple[type, ...] = S4gModule.__bases__
        S4gModule.__bases__ = (MockS4gModule,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        S4gModule.__bases__ = cls.old_s4g_module_bases

    def test_init(self):
        """Unit tests for init method"""

        s4g_module = S4gModule(parent=MagicMock(), name="test_s4g_module", address=0)
        submodules = s4g_module.submodules
        dac_idxs = list(submodules.keys())
        channels = s4g_module._channels

        assert len(submodules) == NUM_DACS_S4GMODULE
        assert len(channels) == NUM_DACS_S4GMODULE
        assert all(isinstance(submodules[dac_idx], S4gDacChannel) for dac_idx in dac_idxs)
        assert all(isinstance(channels[dac_idx], S4gDacChannel) for dac_idx in range(NUM_DACS_S4GMODULE))


class TestD5aDacChannel:
    """Unit tests checking the qililab D5aDacChannel attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_d5a_dac_channel: tuple[type, ...] = D5aDacChannel.__bases__
        D5aDacChannel.__bases__ = (MockD5aDacChannel,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        D5aDacChannel.__bases__ = cls.old_d5a_dac_channel

    def test_off(self):
        """Unit tests for turning of the channel instrument"""

        d5a_dac_channel = D5aDacChannel(parent=MagicMock(), name="test_d5a_dac_channel", dac=0)
        d5a_dac_channel.off()

        assert d5a_dac_channel.get("voltage") == 0


class TestS4gDacChannel:
    """Unit tests checking the qililab S4gDacChannel attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_s4g_dac_channel: tuple[type, ...] = S4gDacChannel.__bases__
        S4gDacChannel.__bases__ = (MockS4gDacChannel,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        S4gDacChannel.__bases__ = cls.old_s4g_dac_channel

    def test_off(self):
        """Unit tests for turning of the channel instrument"""

        S4gDacChannel.__bases__ = (MockS4gDacChannel,)
        s4g_dac_channel = S4gDacChannel(parent=MagicMock(), name="test_s4g_dac_channel", dac=0)
        s4g_dac_channel.off()

        assert s4g_dac_channel.get("current") == 0
