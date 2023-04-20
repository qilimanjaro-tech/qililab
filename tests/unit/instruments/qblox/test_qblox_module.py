"""This file tests the the ``qblox_d5a`` class"""
import pytest


from qililab.constants import INSTRUMENTCONTROLLER, RUNCARD, INSTRUMENTREFERENCE

from qililab.typings.enums import Parameter, Category
from qililab.instruments.qblox import QbloxModule
from qpysequence.program import Loop, Register

from qililab.instruments.awg_settings.typings import (
    AWGChannelMappingTypes,
    AWGIQChannelTypes,
    AWGSequencerPathTypes,
    AWGSequencerTypes,
    AWGTypes)

from qililab.typings.enums import InstrumentName

from unittest.mock import MagicMock

class DummyAWG(QbloxModule):
    """Dummy AWG class."""

    def _generate_weights(self) -> dict:
        return {}

    def _append_acquire_instruction(self, loop: Loop, register: Register, sequencer_id: int):
        pass

@pytest.fixture(name="pulsar")
def fixture_pulsar_controller_qcm():
    """Fixture that returns an instance of a dummy QbloxD5a."""
    settings = settings = {
        RUNCARD.ID: 0,
        RUNCARD.ALIAS: InstrumentName.QBLOX_QCM.value,
        RUNCARD.CATEGORY: Category.AWG.value,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 1,
        AWGTypes.OUT_OFFSETS.value: [0, 0.5, 0.7, 0.8],
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
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_PATH0.value: 1,
                Parameter.GAIN_PATH1.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_PATH0.value: 0,
                Parameter.OFFSET_PATH1.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SYNC_ENABLED.value: True,
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
    return DummyAWG(settings=settings)

class TestQblox_d5a:
    """This class contains the unit tests for the ``qblox_d5a`` class."""

    def test_error_raises_when_no_channel_specified(self, pulsar):
        pulsar.settings.num_sequencers = 2
        with pytest.raises(ValueError, match="channel not specified to update instrument"):
            pulsar.device = MagicMock()
            pulsar.setup(parameter = Parameter.GAIN, value = 2, channel_id = None)