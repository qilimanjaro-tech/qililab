import qcodes.validators as vals
from qcodes.instrument import DelegateParameter, Instrument
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers.instruments import ERASynthPlus
from qililab.drivers.interfaces import LocalOscillator


class MockInstrument(DummyInstrument):  # pylint: disable=abstract-method
    def __init__(self, name, address="test", **kwargs):  # pylint: disable=unused-argument
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
    """Unit tests for the ERASynthPlus driver. These tests mock the qcodes class to be able to instantiate the
    driver."""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_era_synth_bases = ERASynthPlus.__bases__
        ERASynthPlus.__bases__ = (MockInstrument, LocalOscillator)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        ERASynthPlus.__bases__ = cls.old_era_synth_bases

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init(self):
        """Test the init method of the ERASynthPlus class."""
        es = ERASynthPlus(name="dummy_ERASynthPlus", address="none")
        assert isinstance(es.parameters["lo_frequency"], DelegateParameter)
        # test set get with frequency and lo_frequency
        es.set("frequency", 2)
        assert es.get("lo_frequency") == 2
        assert es.lo_frequency.label == "Delegated parameter for local oscillator frequency"

    def test_params(self):
        """Unittest to test the params property."""
        es = ERASynthPlus(name="dummy_ERASynthPlus", address="none")
        assert es.params == es.parameters

    def test_alias(self):
        """Unittest to test the alias property."""
        es = ERASynthPlus(name="dummy_ERASynthPlus", address="none")
        assert es.alias == es.name
