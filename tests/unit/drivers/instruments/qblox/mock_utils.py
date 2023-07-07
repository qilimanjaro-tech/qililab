from unittest.mock import MagicMock

from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyInstrument

NUM_SLOTS = 20


class MockQcmQrm(DummyInstrument):
    """Mock class for QcmQrm"""

    def __init__(self, parent, name, slot_idx, **kwargs):
        """Mock init method"""

        super().__init__(name, **kwargs)

        # Store sequencer index
        self._slot_idx = slot_idx
        self.submodules = {"test_submodule": MagicMock()}
        self.is_qcm_type = True
        self.is_qrm_type = False
        self.is_rf_type = False

    def arm_sequencer(self):
        """Mock arm_sequencer method"""

        return None

    def start_sequencer(self):
        """Mock start_sequencer method"""

        return None


class MockCluster(DummyInstrument):
    """Mock class for Cluster"""

    def __init__(self, name, address=None, **kwargs):
        """Mock init method"""

        super().__init__(name)

        self.address = address
        self._num_slots = NUM_SLOTS
        self.submodules = {"test_submodule": MagicMock()}
        self._present_at_init = MagicMock()
