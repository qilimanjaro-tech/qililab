"""This file tests the the ``AWGAnalogDigitalConverter`` class"""
import pytest
import copy


from qililab.instruments import AWG
from qililab.constants import INSTRUMENTCONTROLLER, RUNCARD, INSTRUMENTREFERENCE
from qililab.typings.enums import Category, Parameter

from tests.data import Galadriel
from qililab.platform import Platform
from qililab.instruments import AWGAnalogDigitalConverter
from qililab.typings.enums import AcquireTriggerMode

from qililab.instruments.awg_settings.typings import (
    AWGChannelMappingTypes,
    AWGIQChannelTypes,
    AWGSequencerPathTypes,
    AWGSequencerTypes,
    AWGTypes)

from qililab.typings.enums import InstrumentName
from unittest.mock import MagicMock

class DummyAWG(AWGAnalogDigitalConverter):
    """Dummy AWG class."""

    def compile(self):
            return []
    
    def run(self):
         pass

    def acquire_result(self):
        return []

    def _set_device_scope_hardware_averaging(self, value: bool, sequencer_id: int):
        pass

    def _set_device_hardware_demodulation(self, value: bool, sequencer_id: int):
        pass

    def _set_device_acquisition_mode(self, mode: AcquireTriggerMode, sequencer_id: int):
        pass

    def _set_device_integration_length(self, value: int, sequencer_id: int):
        pass


@pytest.fixture(name="awg")
def fixture_awg():
    """Fixture that returns an instance of a dummy AWG."""
    settings = {
        RUNCARD.ID: 0,
        RUNCARD.ALIAS: InstrumentName.QBLOX_QCM.value,
        RUNCARD.CATEGORY: Category.AWG.value,
        'acquisition_delay_time' : 100,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 1,
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                AWGSequencerTypes.IDENTIFIER.value: 0,
                AWGSequencerTypes.CHIP_PORT_ID.value: 0,
                AWGSequencerTypes.PATH0.value: {
                    AWGSequencerPathTypes.OUTPUT_CHANNEL.value: 0,
                },
                AWGSequencerTypes.PATH1.value: {
                    AWGSequencerPathTypes.OUTPUT_CHANNEL.value: 1,
                },
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_PATH0.value: 1,
                Parameter.GAIN_PATH1.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_PATH0.value: 0,
                Parameter.OFFSET_PATH1.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
            }
        ],
        AWGTypes.AWG_IQ_CHANNELS.value: [
            {
                AWGIQChannelTypes.IDENTIFIER.value: 0,
                AWGIQChannelTypes.I_CHANNEL.value: {
                    AWGChannelMappingTypes.AWG_SEQUENCER_IDENTIFIER.value: 0,
                    AWGChannelMappingTypes.AWG_SEQUENCER_PATH_IDENTIFIER.value: 0,
                },
                AWGIQChannelTypes.Q_CHANNEL.value: {
                    AWGChannelMappingTypes.AWG_SEQUENCER_IDENTIFIER.value: 0,
                    AWGChannelMappingTypes.AWG_SEQUENCER_PATH_IDENTIFIER.value: 1,
                },
            },
        ],
    }
    return DummyAWG(settings=settings)  # pylint: disable=abstract-class-instantiated

class TestAWGAnalogDigitalConverter:
    """This class contains the unit tests for the ``AWGAnalogDigitalConverte`` class."""
    
    def test_error_raises_when_no_channel_specified(self, awg: AWG):
        awg.settings.num_sequencers = 2
        with pytest.raises(ValueError, match="channel not specified to update instrument"):
            awg.device = MagicMock()
            awg.setup(parameter = Parameter.ACQUISITION_DELAY_TIME, value = 2, channel_id = None)