import qcodes.validators as vals
from qcodes.instrument import DelegateParameter
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers.instruments import RhodeSchwarzSGS100A
from qililab.drivers.interfaces import LocalOscillator


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


class TestRhodeSchwarzSGS100A:
    def test_init(self):
        RhodeSchwarzSGS100A.__bases__ = (MockInstrument, LocalOscillator)
        rs = RhodeSchwarzSGS100A(name="dummy_SGS100A", address="none")
        assert isinstance(rs.parameters["lo_frequency"], DelegateParameter)
        # test set get with frequency and lo_frequency
        rs.set("frequency", 2)
        assert rs.get("lo_frequency") == 2
        assert rs.lo_frequency.label == "Delegated parameter for local oscillator frequency"
