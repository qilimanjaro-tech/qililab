from unittest.mock import MagicMock, call

import pytest

from qililab.exceptions import ParameterNotFound
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.typings.enums import Parameter


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
            "dacs": [10, 11],
            "low_pass_filter": ["dc", "dc"],
            "firmware": "0.7.0",
        }
    )
    qdac.device = MagicMock()
    return qdac


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
    def test_setup_method(self, qdac: QDevilQDac2, parameter: Parameter, value):
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
    def test_setup_method_raises_exception(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test the setup method raises an exception with wrong parameters"""
        for channel_id in qdac.dacs:
            with pytest.raises(ParameterNotFound):
                qdac.setup(parameter, value, channel_id)

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.GAIN, 0.0005)])
    def test_get_method_raises_exception(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test the get method raises an exception with wrong parameters"""
        for channel_id in qdac.dacs:
            with pytest.raises(ParameterNotFound):
                qdac.get(parameter, channel_id)

    @pytest.mark.parametrize("channel_id", [0, 25, -1, None])
    def test_validate_channel_method_raises_exception(self, qdac: QDevilQDac2, channel_id):
        """Test the _validate_channel method raises an exception with wrong parameters"""
        with pytest.raises(ValueError):
            qdac._validate_channel(channel_id)
