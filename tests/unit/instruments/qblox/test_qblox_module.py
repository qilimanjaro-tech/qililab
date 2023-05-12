"""This file tests the the ``qblox_d5a`` class"""

from unittest.mock import MagicMock

import pytest
from qpysequence.program import Loop, Register

from qililab.constants import RUNCARD
from qililab.instruments.awg_settings.typings import AWGSequencerTypes, AWGTypes
from qililab.instruments.qblox import QbloxModule
from qililab.typings.enums import Category, InstrumentName, Parameter


class DummyAWG(QbloxModule):
    """Dummy AWG class."""

    def _generate_weights(self) -> dict:
        return {}

    def _append_acquire_instruction(self, loop: Loop, register: Register, sequencer_id: int):
        pass


@pytest.fixture(name="pulsar")
def fixture_pulsar_controller_qcm():
    """Fixture that returns an instance of a dummy QbloxD5a."""
    settings = {
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
                "output_i": 0,
                "output_q": 1,
                Parameter.NUM_BINS.value: 1,
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SYNC_ENABLED.value: True,
            }
        ],
    }
    return DummyAWG(settings=settings)


class TestQbloxD5a:
    """This class contains the unit tests for the ``qblox_d5a`` class."""

    def test_error_raises_when_no_channel_specified(self, pulsar):
        """These test makes soure that an error raises whenever a channel is not specified in chainging a parameter

        Args:
            pulsar (_type_): pulsar
        """
        pulsar.settings.num_sequencers = 2
        with pytest.raises(ValueError, match="channel not specified to update instrument"):
            pulsar.device = MagicMock()
            pulsar.setup(parameter=Parameter.GAIN, value=2, channel_id=None)
