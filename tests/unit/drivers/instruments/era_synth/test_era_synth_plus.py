import qcodes.validators as vals
from qcodes.instrument import DelegateParameter, Instrument
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers.instruments import ERASynthPlus
from qililab.drivers.interfaces import LocalOscillator

old_bases = ERASynthPlus.__bases__


def teardown_module():
    """Closes all instruments after tests terminate (either successfully or stop because of an error)."""
    Instrument.close_all()
    ERASynthPlus.__bases__ = old_bases


class MockInstrument(DummyInstrument):
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


class TestERASynthPlus:
    def test_init(self):
        # Substitute base of the instrument by a mock instrument so that we can run tests without connecting
        # to the actual instrument
        ERASynthPlus.__bases__ = (MockInstrument, LocalOscillator)
        es = ERASynthPlus(name="dummy_ERASynthPlus", address="none")
        assert isinstance(es.parameters["lo_frequency"], DelegateParameter)
        # test set get with frequency and lo_frequency
        es.set("frequency", 2)
        assert es.get("lo_frequency") == 2
        assert es.lo_frequency.label == "Delegated parameter for local oscillator frequency"
