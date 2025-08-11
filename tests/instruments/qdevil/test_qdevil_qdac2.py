import re
from unittest.mock import MagicMock, call

import pytest

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.typings.enums import Parameter
from qililab.waveforms import Square


@pytest.fixture(name="qdac")
def fixture_qdac() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""
    qdac = QDevilQDac2(
        {
            "alias": "qdac",
            "voltage": [0.5, 0.5],
            "span": ["low", "low"],
            "ramping_enabled": [True, False],
            "ramp_rate": [0.01, 0.01],
            "dacs": [2, 4, 10, 11],
            "low_pass_filter": ["dc", "dc"],
        }
    )
    qdac.device = MagicMock()
    return qdac


@pytest.fixture(name="qdac_out_range")
def range_input() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""

    qdac_out_range = QDevilQDac2(
        {
            "alias": "qdac_out_range",
            "voltage": [0.5],
            "span": ["low"],
            "ramping_enabled": [True],
            "ramp_rate": [0.001],
            "dacs": [10],
            "low_pass_filter": ["dc"],
        }
    )
    mock_device = MagicMock()
    qdac_out_range.device = mock_device
    return qdac_out_range


@pytest.fixture(name="waveform")
def get_square_waveform() -> Square:
    return Square(0.1, 4)


class TestQDevilQDac2:
    def test_initial_setup(self, qdac: QDevilQDac2):
        """Test initial_setup method"""
        qdac.initial_setup()

        channel_calls = []
        for channel_id in qdac.dacs:
            index = qdac.dacs.index(channel_id)
            channel_calls.append(call(channel_id))
            channel_calls.append(call().dc_mode("fixed"))
            channel_calls.append(call().output_range(qdac.span[index]))
            channel_calls.append(call().output_filter(qdac.low_pass_filter[index]))
            if qdac.ramping_enabled[index]:
                channel_calls.append(call().dc_slew_rate_V_per_s(qdac.ramp_rate[index]))
            else:
                channel_calls.append(call().dc_slew_rate_V_per_s(2e7))
            channel_calls.append(call().dc_constant_V(0.0))

        qdac.device.channel.assert_has_calls(channel_calls)

    def test_turn_on(self, qdac: QDevilQDac2):
        """Test turn_on method"""
        qdac.turn_on()

        channel_calls = []
        for channel_id in qdac.dacs:
            index = qdac.dacs.index(channel_id)
            channel_calls.append(call(channel_id))
            channel_calls.append(call().dc_constant_V(qdac.voltage[index]))

        qdac.device.channel.assert_has_calls(channel_calls)

    def test_turn_off(self, qdac: QDevilQDac2):
        """Test turn_off method"""
        qdac.turn_off()

        channel_calls = []
        for channel_id in qdac.dacs:
            channel_calls.append(call(channel_id))
            channel_calls.append(call().dc_constant_V(0.0))

        qdac.device.channel.assert_has_calls(channel_calls)

    def test_reset(self, qdac: QDevilQDac2):
        """Test reset method"""
        qdac.reset()

        qdac.device.reset.assert_called_once()

    def test_get_dac(self, qdac: QDevilQDac2):
        """Test get_dac method"""
        channel_calls = []
        for channel_id in qdac.dacs:
            qdac.get_dac(channel_id)
            channel_calls.append(call(channel_id))
        qdac.device.channel.assert_has_calls(channel_calls)

    def test_upload_awg_waveform(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        qdac.upload_awg_waveform(waveform, channel_id)
        qdac.device.allocate_trace.assert_called_once_with(channel_id, len(waveform.envelope()))
        assert qdac._cache_awg == {4: True}

    def test_upload_awg_waveform_fails_overwrite_cache(self, qdac: QDevilQDac2, waveform: Square):
        """Test that upload waveform raises an error when trying to allocate a waveform to an already allocated channel id"""
        channel_id = 2
        qdac._cache_awg = {channel_id: True}
        error_string = re.escape(
            f"Device {qdac.name} already has a waveform allocated to channel {channel_id}. Clear the cache before allocating a new waveform"
        )
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)

    def test_upload_awg_waveform_fails_odd_value(self, qdac: QDevilQDac2, waveform: Square):
        """Test that upload waveform raises an error when uploading a waveform with odd number of entries"""
        channel_id = 2
        waveform = Square(0.1, 3)
        error_string = "Waveform entries must be even."
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)

    def test_upload_awg_waveform_fails_amp_range(self, qdac: QDevilQDac2, waveform: Square):
        """Test that upload waveform raises an error when uploading a waveform with outside the allowed amplitude range"""
        channel_id = 2
        waveform = Square(1, 4)
        error_string = re.escape("Waveform amplitudes must be within [-1,1] range.")
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)
        qdac.clear_cache()
        channel_id = 2
        waveform = Square(-1.1, 4)
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)

    def test_play(self, qdac: QDevilQDac2):
        """Test play method"""
        channel_id = 4
        channel_calls = [call(10), call(11), call(4), call().start]
        qdac._cache_awg = {channel_id: True}
        qdac.play_awg(clear_after=False)
        # cache not erased if default clear_after
        assert qdac._cache_awg == {channel_id: True}
        qdac.play_awg(channel_id)
        qdac.get_dac(4).arbitrary_wave.assert_has_calls(channel_calls)
        # check that cache is erased
        assert qdac._cache_awg == {}

    def test_clear_cache(self, qdac: QDevilQDac2):
        """Test clear_cache method"""
        qdac._cache_awg = {2: True}
        qdac.clear_cache()
        assert qdac._cache_awg == {}
        qdac.device.remove_traces.assert_called_once()

    def test_input_range_runcard(self, qdac_out_range: QDevilQDac2):
        # Test that an error is raised when the input value on the runcard for the qdac are out of bound
        channel_id = 10
        error_string = re.escape(
            f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
        )
        with pytest.raises(ValueError, match=error_string):
            qdac_out_range.initial_setup()

    def test_input_range_set_parameter(self, qdac: QDevilQDac2):
        # Test that an error is raised when the input value on set_parameter RAMPING_RATE for the qdac are out of bound
        channel_id = 10
        error_string = re.escape(
            f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
        )
        with pytest.raises(ValueError, match=error_string):
            qdac.set_parameter(parameter=Parameter.RAMPING_RATE, value=0.0001, channel_id=channel_id)

    def test_input_range_set_parameter_enabled(self, qdac_out_range: QDevilQDac2):
        # Test that an error is raised when the input value on set_parameter RAMPING_ENABLED for the qdac are out of bound
        channel_id = 10
        error_string = re.escape(
            f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
        )
        with pytest.raises(ValueError, match=error_string):
            qdac_out_range.set_parameter(parameter=Parameter.RAMPING_ENABLED, value=True, channel_id=channel_id)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.VOLTAGE, -0.001),
            (Parameter.RAMPING_ENABLED, False),
            (Parameter.RAMPING_ENABLED, True),
            (Parameter.RAMPING_RATE, 0.05),
            (Parameter.SPAN, "high"),
            (Parameter.LOW_PASS_FILTER, "low"),
        ],
    )
    def test_set_parameter_method(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test setup method"""
        for index, channel_id in enumerate(qdac.dacs):
            qdac.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

            channel_calls = []
            channel_calls.append(call(channel_id))
            if parameter == Parameter.VOLTAGE:
                channel_calls.append(call().dc_constant_V(value))
            if parameter == Parameter.SPAN:
                channel_calls.append(call().output_range(value))
            if parameter == Parameter.LOW_PASS_FILTER:
                channel_calls.append(call().output_filter(value))
            if parameter == Parameter.RAMPING_ENABLED:
                if value:
                    channel_calls.append(call().dc_slew_rate_V_per_s(qdac.ramp_rate[index]))
                else:
                    channel_calls.append(call().dc_slew_rate_V_per_s(2e7))
            if parameter == Parameter.RAMPING_RATE:
                if qdac.ramping_enabled[index]:
                    channel_calls.append(call().dc_slew_rate_V_per_s(qdac.ramp_rate[index]))

            qdac.device.channel.assert_has_calls(channel_calls)
            assert qdac.get_parameter(parameter=parameter, channel_id=channel_id) == value

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.GAIN, 0.0005)])
    def test_set_parameter_method_raises_exception(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test the setup method raises an exception with wrong parameters"""
        for channel_id in qdac.dacs:
            with pytest.raises(ParameterNotFound):
                qdac.set_parameter(parameter, value, channel_id)

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.GAIN, 0.0005)])
    def test_get_parameter_method_raises_exception(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test the get method raises an exception with wrong parameters"""
        for channel_id in qdac.dacs:
            with pytest.raises(ParameterNotFound):
                qdac.get_parameter(parameter, channel_id)

    @pytest.mark.parametrize("channel_id", [0, 25, -1, None])
    def test_validate_channel_method_raises_exception(self, qdac: QDevilQDac2, channel_id):
        """Test the _validate_channel method raises an exception with wrong parameters"""
        with pytest.raises(ValueError):
            qdac._validate_channel(channel_id)
