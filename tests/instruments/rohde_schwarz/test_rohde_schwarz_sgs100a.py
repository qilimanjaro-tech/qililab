"""Tests for the SGS100A class."""

import re
import warnings
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments import SGS100A, ParameterNotFound
from qililab.typings.enums import Parameter


@pytest.fixture(name="sdg100a")
def fixture_sdg100a() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a = SGS100A(
        {
            "alias": "sgs100a",
            "power": 10,
            "frequency": 80e6,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": True,
        }
    )
    sdg100a.device = MagicMock()
    return sdg100a


@pytest.fixture(name="sdg100a_iq")
def fixture_sdg100a_iq() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_iq = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 80e6,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": True,
            "operation_mode": "normal"
        }
    )
    sdg100a_iq.device = MagicMock()
    return sdg100a_iq


@pytest.fixture(name="sdg100a_rf_off")
def fixture_sdg100a_rf_off() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_rf_off = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 80e6,
            "rf_on": False,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": True,
        }
    )
    sdg100a_rf_off.device = MagicMock()
    return sdg100a_rf_off


@pytest.fixture(name="sdg100a_alc_off")
def fixture_sdg100a_alc_off() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_alc_off = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 80e6,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": False,
        }
    )
    sdg100a_alc_off.device = MagicMock()
    return sdg100a_alc_off


@pytest.fixture(name="sdg100a_iq_mod_off")
def fixture_sdg100a_iq_mod_off() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_iq_mod_off = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 80e6,
            "rf_on": True,
            "iq_modulation": False,
            "iq_wideband": True,
            "alc": True,
        }
    )
    sdg100a_iq_mod_off.device = MagicMock()
    return sdg100a_iq_mod_off


@pytest.fixture(name="sdg100a_wideband_off")
def fixture_sdg100a_wideband_off() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_wideband_off = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 80e6,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": False,
            "alc": True,
        }
    )
    sdg100a_wideband_off.device = MagicMock()
    return sdg100a_wideband_off


@pytest.fixture(name="sdg100a_wideband_off_large_freq")
def fixture_sdg100a_wideband_off_large_freq() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_wideband_off_large_freq = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 5e9,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": False,
            "alc": True,
        }
    )
    sdg100a_wideband_off_large_freq.device = MagicMock()
    return sdg100a_wideband_off_large_freq


@pytest.fixture(name="sdg100a_wrong_power")
def fixture_sdg100a_wrong_power() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_wrong_power = SGS100A(
        {
            "alias": "qdac",
            "power": 100,
            "frequency": 80e6,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": True,
        }
    )
    sdg100a_wrong_power.device = MagicMock()
    return sdg100a_wrong_power


@pytest.fixture(name="sdg100a_wrong_freq")
def fixture_sdg100a_wrong_freq() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_wrong_freq = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 13e9,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": True,
        }
    )
    sdg100a_wrong_freq.device = MagicMock()
    return sdg100a_wrong_freq

@pytest.fixture(name="sdg100a_bypass_mode")
def fixture_sdg100a_bypass_mode() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_wrong_op_mode = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 8e9,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": True,
            "operation_mode": "bypass"
        }
    )
    sdg100a_wrong_op_mode.device = MagicMock()
    return sdg100a_wrong_op_mode

@pytest.fixture(name="sdg100a_wrong_op_mode")
def fixture_sdg100a_wrong_op_mode() -> SGS100A:
    """Fixture that returns an instance of a dummy SGS100a."""
    sdg100a_wrong_op_mode = SGS100A(
        {
            "alias": "qdac",
            "power": 10,
            "frequency": 8e9,
            "rf_on": True,
            "iq_modulation": True,
            "iq_wideband": True,
            "alc": True,
            "operation_mode": "wrong_operation_mode"
        }
    )
    sdg100a_wrong_op_mode.device = MagicMock()
    return sdg100a_wrong_op_mode


class TestSGS100A:
    """Unit tests checking the SGS100A attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.POWER, 0.01),
            (Parameter.LO_FREQUENCY, 6.0e09),
            (Parameter.RF_ON, True),
            (Parameter.RF_ON, False),
            (Parameter.IQ_MODULATION, True),
            (Parameter.IQ_MODULATION, False),
            (Parameter.ALC, True),
            (Parameter.ALC, False),
            (Parameter.IQ_WIDEBAND, True),
            (Parameter.IQ_WIDEBAND, False),
            (Parameter.OPERATION_MODE, "normal")
        ],
    )
    def test_set_parameter_method(
        self,
        sdg100a: SGS100A,
        parameter: Parameter,
        value: float,
    ):
        """Test setup method"""
        sdg100a.set_parameter(parameter=parameter, value=value)
        if parameter == Parameter.POWER:
            assert sdg100a.settings.power == value
        if parameter == Parameter.LO_FREQUENCY:
            assert sdg100a.settings.frequency == value
        if parameter == Parameter.RF_ON:
            assert sdg100a.settings.rf_on == value
        if parameter == Parameter.IQ_MODULATION:
            assert sdg100a.settings.iq_modulation == value
        if parameter == Parameter.OPERATION_MODE:
            assert sdg100a.settings.operation_mode == value

    def test_set_parameter_method_raises_error(self, sdg100a: SGS100A):
        """Test setup method"""
        with pytest.raises(ParameterNotFound):
            sdg100a.set_parameter(parameter=Parameter.BUS_FREQUENCY, value=123)
        with pytest.raises(ParameterNotFound):
            sdg100a.set_parameter(parameter=Parameter.OPERATION_MODE, value="wrong_operation_mode")

    @pytest.mark.parametrize(
        "parameter, expected_value",
        [
            (Parameter.POWER, 10),
            (Parameter.LO_FREQUENCY, 80e6),
            (Parameter.RF_ON, True),
            (Parameter.IQ_MODULATION, True),
            (Parameter.ALC, True),
            (Parameter.IQ_WIDEBAND, True),
            (Parameter.OPERATION_MODE, "normal")
        ],
    )
    def test_get_parameter_method(
        self,
        sdg100a: SGS100A,
        parameter: Parameter,
        expected_value: float,
    ):
        """Test get_parameter method"""
        value = sdg100a.get_parameter(parameter=parameter)
        assert value == expected_value

    def test_get_parameter_method_raises_error(self, sdg100a: SGS100A):
        """Test get_parameter method"""
        with pytest.raises(ParameterNotFound):
            sdg100a.get_parameter(parameter=Parameter.BUS_FREQUENCY)

    @patch("warnings.warn")
    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_method(self, mock_get_rs_options, mock_warn, sdg100a: SGS100A):
        """Test initial setup method"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a.initial_setup()
        sdg100a.device.power.assert_called_with(sdg100a.power)
        sdg100a.device.frequency.assert_called_with(sdg100a.frequency)
        sdg100a.device.on.assert_called_once()

        sdg100a.settings.rf_on = False
        sdg100a.initial_setup()
        sdg100a.device.power.assert_called_with(sdg100a.power)
        sdg100a.device.frequency.assert_called_with(sdg100a.frequency)
        sdg100a.device.off.assert_called_once()

        mock_warn.assert_any_call(
            "LO frequency below 2.5GHz only allows for IF sweeps of ±1.60e+07 Hz", ResourceWarning
        )

    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_method_iq_mod_off(self, mock_get_rs_options, sdg100a_iq_mod_off: SGS100A):
        """Test initial method when the runcard sets rf_on as False"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a_iq_mod_off.initial_setup()
        assert sdg100a_iq_mod_off.settings.iq_modulation is False
        assert sdg100a_iq_mod_off.iq_modulation is False

    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_method_alc_off(self, mock_get_rs_options, sdg100a_alc_off: SGS100A):
        """Test initial method when the runcard sets rf_on as False"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a_alc_off.initial_setup()
        assert sdg100a_alc_off.settings.alc is False
        assert sdg100a_alc_off.alc is False
        
    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_method_bypass_operation_mode(self, mock_get_rs_options, sdg100a_bypass_mode: SGS100A):
        """Test initial method when the runcard sets rf_on as False"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a_bypass_mode.initial_setup()
        assert sdg100a_bypass_mode.settings.operation_mode == "bypass"

    @patch("qililab.instruments.rohde_schwarz.sgs100a.warnings.warn")
    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_method_wrong_bypass(self, mock_get_rs_options, mock_warn, sdg100a_wrong_op_mode: SGS100A):
        """Test initial method when the runcard sets rf_on as False"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a_wrong_op_mode.initial_setup()
        assert sdg100a_wrong_op_mode.settings.operation_mode=="normal"
        sdg100a_wrong_op_mode.device.write.assert_any_call(":SOUR:OPMode NORMal")

        mock_warn.assert_any_call(
            "Operation mode 'wrong_operation_mode' not allowed, defaulting to normal operation mode", ResourceWarning
        )

    @patch("warnings.warn")
    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_method_wideband_off(self, mock_get_rs_options, mock_warn, sdg100a_wideband_off: SGS100A):
        """Test initial method when the runcard sets rf_on as False"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a_wideband_off.initial_setup()
        assert sdg100a_wideband_off.settings.iq_wideband is False
        assert sdg100a_wideband_off.iq_wideband is False
        assert sdg100a_wideband_off.iq_modulation is True

        mock_warn.assert_any_call(
            "Deactivated wideband & LO frequency below 1GHz allows for IF sweeps of ±4.00e+06 Hz", ResourceWarning
        )

    @patch("warnings.warn")
    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_method_wideband_off_large_freq(
        self, mock_get_rs_options, mock_warn, sdg100a_wideband_off_large_freq: SGS100A
    ):
        """Test initial method when the runcard sets rf_on as False"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a_wideband_off_large_freq.initial_setup()
        assert sdg100a_wideband_off_large_freq.settings.iq_wideband is False
        assert sdg100a_wideband_off_large_freq.iq_wideband is False
        assert sdg100a_wideband_off_large_freq.iq_modulation is True

        mock_warn.assert_any_call("Deactivated wideband allows for IF sweeps of ±50e6 Hz", ResourceWarning)

    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_initial_setup_sets_correct_freq_range(self, mock_get_rs_options, sdg100a: SGS100A):
        """Test initial setup method"""
        mock_get_rs_options.return_value = "Some,other,SGS-B112"
        sdg100a.initial_setup()
        assert sdg100a.freq_top_limit == 12.75e9
        assert sdg100a.freq_bot_limit == 1e6

        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        sdg100a.initial_setup()
        assert sdg100a.freq_top_limit == 12.75e9
        assert sdg100a.freq_bot_limit == 80e6

        mock_get_rs_options.return_value = "Some,other,SGS-B106"
        sdg100a.initial_setup()
        assert sdg100a.freq_top_limit == 6e9
        assert sdg100a.freq_bot_limit == 1e6

        mock_get_rs_options.return_value = "Some,other,SGS-B106V"
        sdg100a.initial_setup()
        assert sdg100a.freq_top_limit == 6e9
        assert sdg100a.freq_bot_limit == 80e6

    def test_get_rs_options(self, sdg100a: SGS100A):
        sdg100a.get_rs_options()
        sdg100a.device.ask.assert_called_once()

    def test_turn_on_method_rf_off(self, sdg100a_rf_off: SGS100A):
        """Test initial method when the runcard sets rf_on as False"""
        sdg100a_rf_off.turn_on()
        assert sdg100a_rf_off.settings.rf_on is False
        sdg100a_rf_off.device.off.assert_called_once()

    def test_turn_on_method(self, sdg100a: SGS100A):
        """Test turn_on method"""
        sdg100a.turn_on()
        assert sdg100a.settings.rf_on is True
        sdg100a.device.on.assert_called_once()

    def test_turn_off_method(self, sdg100a: SGS100A):
        """Test turn_off method"""
        sdg100a.turn_off()
        assert sdg100a.settings.rf_on is False
        sdg100a.device.off.assert_called_once()

    def test_reset_method(self, sdg100a: SGS100A):
        """Test reset method"""
        sdg100a.reset()

    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_raise_error_power_out_of_range(self, mock_get_rs_options, sdg100a_wrong_power: SGS100A):
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        error_string = "Value set for power is outside of the allowed range [-120,25]: 100"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            sdg100a_wrong_power.initial_setup()

    @patch("qililab.instruments.rohde_schwarz.SGS100A.get_rs_options")
    def test_raise_error_freq_out_of_range(self, mock_get_rs_options, sdg100a_wrong_freq: SGS100A):
        mock_get_rs_options.return_value = "Some,other,SGS-B112V"
        error_string = "Value set for frequency is outside of the allowed range [80000000.0, 12750000000.0]: 13000000000.0"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            sdg100a_wrong_freq.initial_setup()
