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


class MockQCMQRMRF(DummyInstrument):
    is_rf_type = True

    def __init__(self, name, qcm_qrm, parent=None, slot_idx=0):
        super().__init__(name=name, gates=["dac1"])

        # local oscillator parameters
        lo_channels = ["out0_in0"] if qcm_qrm == "qrm" else ["out0", "out1"]
        for channel in lo_channels:
            self.add_parameter(
                name=f"{channel}_lo_freq",
                label="Frequency",
                unit="Hz",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )
            self.add_parameter(
                f"{channel}_lo_en",
                label="Status",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )

        # attenuator parameters
        att_channels = ["out0", "in0"] if qcm_qrm == "qrm" else ["out0", "out1"]
        for channel in att_channels:
            self.add_parameter(
                name=f"{channel}_att",
                label="Attenuation",
                unit="dB",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )


class MockQCMRF(MockQCMQRMRF):
    is_rf_type = True
    is_qrm_type = False
    is_qcm_type = True

    def __init__(self, name, parent=None, slot_idx=0):
        super().__init__(name, qcm_qrm="qcm", parent=None, slot_idx=0)


class MockQRMRF(MockQCMQRMRF):
    is_rf_type = True
    is_qrm_type = True
    is_qcm_type = False

    def __init__(self, name, parent=None, slot_idx=0):
        super().__init__(name=name, qcm_qrm="qrm", parent=None, slot_idx=0)
