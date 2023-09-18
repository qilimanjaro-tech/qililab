"""module to test the pulsar class."""
from qblox_instruments.types import PulsarType
from qcodes import Instrument
from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers.instruments.qblox.pulsar import Pulsar
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.drivers.interfaces.base_instrument import BaseInstrument

NUM_SUBMODULES = 6
PULSAR_NAME = "test"


class MockPulsar(DummyInstrument):  # pylint: disable=abstract-method
    """Mock class for Pulsar"""

    def __init__(
        self, name, identifier=None, port=None, debug=None, dummy_type=None
    ):  # pylint: disable=unused-argument
        """Mock init method"""

        super().__init__(name)
        self.is_qcm_type = False
        self.is_qrm_type = True
        self.is_rf_type = False

        self.add_parameter(
            "reference_source",
            label="Reference source",
            docstring="Sets/gets reference source ('internal' = internal " "10 MHz, 'external' = external 10 MHz).",
            unit="",
            vals=vals.Bool(),
            val_mapping={"internal": True, "external": False},
            set_parser=bool,
            get_parser=bool,
            set_cmd=None,
            get_cmd=None,
        )

        self.add_parameter(
            "out0_offset",
            label="out0_offset",
            docstring="Sets/gets outset for output 0.",
            unit="",
            vals=vals.Numbers(0, 1),
            set_parser=int,
            get_parser=int,
            set_cmd=None,
            get_cmd=None,
        )


class TestPulsar:
    """Unit tests checking the Pulsar attributes and methods. These tests mock the parent class of the `Pulsar`,
    such that the code from `qcodes` is never executed."""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_pulsar_bases = Pulsar.__bases__
        Pulsar.__bases__ = (MockPulsar, BaseInstrument)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Pulsar.__bases__ = cls.old_pulsar_bases

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init_with_sequencers(self):
        """Test init method without dummy configuration and sequencers"""
        sequencers = ["q0_flux", "q1_flux"]
        pulsar = Pulsar(alias="test_pulsar_with_sequencers", sequencers=sequencers)
        submodules = pulsar.submodules
        registered_names = list(submodules.keys())

        assert sequencers == registered_names

    def test_initial_setup(self):
        """Test initial setup method"""
        parameters = {"out0_offset": 1, "reference_source": "internal"}
        pulsar = Pulsar(alias="test_pulsar_with_sequencers")
        pulsar.initial_setup(params=parameters)

        assert pulsar.get("out0_offset") == 1
        assert pulsar.get("reference_source") == "internal"

    def test_instrument_repr(self):
        """Test that the instrument_repr method returns the right representation."""
        parameters = {"out0_offset": 1, "reference_source": "internal"}
        pulsar = Pulsar(alias="test_pulsar_with_sequencers")
        pulsar.initial_setup(params=parameters)

        expected_alias = "test_pulsar_with_sequencers"
        expected_minimum_params = {"out0_offset": 1, "reference_source": "internal"}
        instrument_reptr = pulsar.instrument_repr()

        assert "alias" in instrument_reptr
        assert expected_alias == instrument_reptr["alias"]
        assert "parameters" in instrument_reptr
        for key, value in expected_minimum_params.items():
            assert key in instrument_reptr["parameters"]
            assert instrument_reptr["parameters"][key] == value


class TestPulsarIntegration:
    """Integration tests for the Pulsar class. These tests use the `dummy_cfg` attribute to be able to use the
    code from qcodes (without mocking the parent class)."""

    @classmethod
    def teardown_method(cls):
        """Tear down after all tests have been run"""
        Instrument.close_all()

    def test_init_qcm_type(self):
        """Unittest for init method for a QCM pulsar."""
        pulsar = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QCM)
        sequencers_prefix = "sequencer"
        submodules = pulsar.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{PULSAR_NAME}_{sequencers_prefix}{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], SequencerQCM) for seq_idx in seq_idxs)
        assert expected_names == registered_names

    def test_init_qrm_type(self):
        """Unittest for init method for a QRM pulsar."""
        pulsar = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QRM)
        sequencers_prefix = "sequencer"
        submodules = pulsar.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{PULSAR_NAME}_{sequencers_prefix}{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], SequencerQRM) for seq_idx in seq_idxs)
        assert expected_names == registered_names

    def test_params(self):
        """Unittest to test the params property."""
        pulsar_qcm = Pulsar(alias=f"{PULSAR_NAME}1", dummy_type=PulsarType.PULSAR_QCM)
        pulsar_qrm = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QRM)

        assert pulsar_qcm.params == pulsar_qcm.parameters
        assert pulsar_qrm.params == pulsar_qrm.parameters

    def test_alias(self):
        """Unittest to test the alias property."""
        pulsar_qcm = Pulsar(alias=f"{PULSAR_NAME}1", dummy_type=PulsarType.PULSAR_QCM)
        pulsar_qrm = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QRM)

        assert pulsar_qcm.alias == pulsar_qcm.name
        assert pulsar_qrm.alias == pulsar_qrm.name
