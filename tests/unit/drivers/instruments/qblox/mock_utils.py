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


class MockSequencer(DummyInstrument):
    """Mock class for Sequencer"""

    def __init__(self, parent, name, seq_idx, **kwargs):
        """Mock init method"""

        super().__init__(name, **kwargs)

        # Store sequencer index
        self.seq_idx = seq_idx
        self._parent = parent
        self.add_parameter(
            "channel_map_path0_out0_en",
            label="Sequencer path 0 output 0 enable",
            docstring="Sets/gets sequencer channel map enable of path 0 to " "output 0.",
            unit="",
            vals=vals.Bool(),
            set_parser=bool,
            get_parser=bool,
            set_cmd=None,
            get_cmd=None,
        )

        self.add_parameter(
            "channel_map_path1_out1_en",
            label="Sequencer path 1 output 1 enable",
            docstring="Sets/gets sequencer channel map enable of path 1 to " "output 1.",
            unit="",
            vals=vals.Bool(),
            set_parser=bool,
            get_parser=bool,
            set_cmd=None,
            get_cmd=None,
        )

        if parent.is_qcm_type:
            self.add_parameter(
                "channel_map_path0_out2_en",
                label="Sequencer path 0 output 2 enable.",
                docstring="Sets/gets sequencer channel map enable of path 0 " "to output 2.",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )

            self.add_parameter(
                "channel_map_path1_out3_en",
                label="Sequencer path 1 output 3 enable.",
                docstring="Sets/gets sequencer channel map enable of path 1 " "to output 3.",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )
