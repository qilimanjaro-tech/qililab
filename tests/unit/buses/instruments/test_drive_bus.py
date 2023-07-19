from unittest.mock import MagicMock
from qcodes import Instrument
from qcodes.tests.instrument_mocks import DummyInstrument
import qcodes.validators as vals
from qililab.buses.instruments.drive_bus import DriveBus
from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM

class MockQcmQrmRF(DummyInstrument):

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

class TestDriveBus:
    """Unit tests checking the DriveBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init(self):
        """Test init method"""
        channel_lo = "out0"
        channel_att = "out1"
        qcm_qrm = "qcm"
        qubit = 0
        sequencer = SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)
        lo_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel_lo}", qcm_qrm=qcm_qrm)
        local_oscillator = QcmQrmRfLo(name=f"test_lo_{channel_lo}", parent=lo_parent, channel=channel_lo)
        att_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel_att}", qcm_qrm=qcm_qrm)
        attenuator = QcmQrmRfAtt(name=f"test_att_{channel_att}", parent=att_parent, channel=channel_att)
        drive_bus = DriveBus(qubit=qubit, awg=sequencer, local_oscillator=local_oscillator, attenuator=attenuator)

        assert (drive_bus.qubit == qubit)
        assert isinstance(drive_bus.awg, SequencerQCM)
        assert isinstance(drive_bus.lo, QcmQrmRfLo)
        assert isinstance(drive_bus.attenuator, QcmQrmRfAtt)
