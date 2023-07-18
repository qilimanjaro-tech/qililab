from unittest.mock import MagicMock
from qcodes import Instrument
from qcodes.tests.instrument_mocks import DummyInstrument
import qcodes.validators as vals

from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.rohde_schwarz.sgs100a import RhodeSchwarzSGS100A
from qililab.drivers.interfaces import LocalOscillator

class MockRhodeSchwarzSGS100A(DummyInstrument):
    def __init__(self, name, address="test", **kwargs):
        super().__init__(name, **kwargs)

        self.add_parameter(
            name="frequency",
            label="Frequency",
            unit="Hz",
            get_cmd=None,
            set_cmd=None,
            get_parser=float,
            vals=vals.Numbers(0, 20e9),
        )

class TestDriveBus:
    """Unit tests checking the DriveBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_rhode_schwarz_bases = RhodeSchwarzSGS100A.__bases__
        cls.old_qblox_sequencer_qcm_bases = SequencerQCM.__bases__
        RhodeSchwarzSGS100A.__bases__ = (MockRhodeSchwarzSGS100A, LocalOscillator)
        SequencerQCM.__bases__ = (MockRhodeSchwarzSGS100A, LocalOscillator)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        RhodeSchwarzSGS100A.__bases__ = cls.old_rhode_schwarz_bases

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init(self):
        """Test init method without dummy configuration"""
        sequencer = SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)
        local_oscillator = RhodeSchwarzSGS100A(name="test_local_oscillator", address=None)
