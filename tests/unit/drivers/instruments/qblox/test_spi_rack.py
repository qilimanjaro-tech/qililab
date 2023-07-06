from unittest.mock import MagicMock

from qililab.drivers.instruments.qblox.spi_rack import (
    D5aDacChannel,
    D5aModule,
    S4gDacChannel,
    S4gModule,
)

from .mock_utils import (
    NUM_DACS_D5AMODULE,
    NUM_DACS_S4GMODULE,
    MockD5aModule,
    MockS4gModule,
)


class TestD5aModule:
    """Unit tests checking the qililab D5aModule attributes and methods"""

    def test_init(self):
        """Unit tests for init method"""

        D5aModule.__bases__ = (MockD5aModule,)
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

    def test_init(self):
        """Unit tests for init method"""

        S4gModule.__bases__ = (MockS4gModule,)
        s4g_module = S4gModule(parent=MagicMock(), name="test_s4g_module", address=0)
        submodules = s4g_module.submodules
        dac_idxs = list(submodules.keys())
        channels = s4g_module._channels
        assert len(submodules) == NUM_DACS_S4GMODULE
        assert len(channels) == NUM_DACS_S4GMODULE
        assert all(isinstance(submodules[dac_idx], S4gDacChannel) for dac_idx in dac_idxs)
        assert all(isinstance(channels[dac_idx], S4gDacChannel) for dac_idx in range(NUM_DACS_S4GMODULE))
