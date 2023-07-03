from unittest.mock import patch

import pytest
import qcodes.validators as vals
from qcodes.instrument import DelegateParameter, Instrument
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers import QcmQrm, parameters
from qililab.drivers.instruments.qblox.qcm_qrm import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.interfaces import Attenuator, LocalOscillator


def teardown_module():
    """teardown any state that was previously setup with a setup_module
    method.
    """
    Instrument.close_all()


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


@pytest.mark.parametrize(
    "channel",
    ["out0_in0", "out0", "out1"],
)
def test_qcmqrflo(channel):
    BaseInstrument = MockQRMRF if channel == "out0_in0" else MockQCMRF
    lo_parent = BaseInstrument(f"test_qcmqrflo_{channel}")
    lo = QcmQrmRfLo(name=f"test_lo_{channel}", parent=lo_parent, channel=channel)
    lo_frequency = parameters.drivers.lo.frequency
    freq_parameter = f"{channel}_lo_freq"
    assert isinstance(lo.parameters[lo_frequency], DelegateParameter)
    # test set get with frequency and lo_frequency
    lo_parent.set(freq_parameter, 2)
    assert lo.get(lo_frequency) == 2
    assert lo.lo_frequency.label == "Delegated parameter for local oscillator frequency"
    # close instruments
    lo_parent.close()


@pytest.mark.parametrize(
    "channel",
    ["out0", "in0", "out1"],
)
def test_qcmqrfatt(channel):
    BaseInstrument = MockQRMRF if channel in ["out0", "in0"] else MockQCMRF
    att_parent = BaseInstrument(f"test_qcmqrfatt_{channel}")
    att = QcmQrmRfAtt(name=f"test_att_{channel}", parent=att_parent, channel=channel)
    attenuation = parameters.drivers.att.attenuation
    att_parameter = f"{channel}_att"
    assert isinstance(att.parameters[attenuation], DelegateParameter)
    # test set get with frequency and lo_frequency
    att_parent.set(att_parameter, 2)
    assert att.get(attenuation) == 2
    assert att.attenuation.label == "Delegated parameter for attenuation"
    att_parent.close()


class TestQcmQrm:
    @pytest.mark.parametrize(
        ("qrm_qcm", "channels"),
        [
            ("qrm", ["out0_in0_lo_freq", "out0_in0_lo_en", "out0_att", "in0_att"]),
            ("qcm", ["out0_lo_freq", "out0_lo_en", "out1_lo_freq", "out1_lo_en", "out0_att", "out1_att"]),
        ],
    )
    def test_init_rf_modules(self, qrm_qcm, channels):
        """Test init for the lo and attenuator in the rf instrument"""
        BaseInstrument = MockQRMRF if qrm_qcm == "qrm" else MockQCMRF if qrm_qcm == "qcm" else None
        QcmQrm.__bases__ = (BaseInstrument,)
        qcmqrm_rf = QcmQrm(parent=None, name=f"{qrm_qcm}_test_init_rf", slot_idx=0)

        assert all((channel in qcmqrm_rf.parameters.keys() for channel in channels))

        qcmqrm_rf.close()
