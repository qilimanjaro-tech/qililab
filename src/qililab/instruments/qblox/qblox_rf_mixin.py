# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Mixer calibration shared by the Qblox RF modules."""

from typing import TYPE_CHECKING, Any, Sequence

from qililab.typings import ChannelID, MixerCalibrationType

if TYPE_CHECKING:
    from .qblox_sequencer import QbloxSequencer


class QbloxRFMixin:
    """Mixer calibration shared by the QCM-RF and QRM-RF.

    Each module only says how its LO is calibrated (``_calibrate_lo``) and which sequencers share an output
    (``_sequencers_on_output``); the rest of the calibration is the same for both.
    """

    if TYPE_CHECKING:
        # Provided by `QbloxModule`.
        device: Any

        @property
        def awg_sequencers(self) -> Sequence[QbloxSequencer]: ...

        def get_sequencer(self, sequencer_id: int) -> QbloxSequencer: ...

    def calibrate_mixers(self, cal_type: MixerCalibrationType | str, channel_id: ChannelID) -> None:
        """Calibrate the mixer of the output the given sequencer is connected to.

        The LO is calibrated through the driver's public per-output method, picked from the sequencer's output.
        With ``"lo and sidebands"``, the sidebands are then calibrated on every sequencer connected to that output,
        as the driver does when the calibration is set in the runcard.

        The LO calibration applies to the whole output, so it affects every bus whose sequencer is on that output
        (e.g. two drive buses on the same QCM-RF output, or every readout bus of a QRM-RF, whose out0 and in0 share
        one LO). A calibration also stops the module's other sequencers: they need to be armed and started again
        before they are used.

        Args:
            cal_type (MixerCalibrationType | str): ``"off"``, ``"lo only"`` or ``"lo and sidebands"``. The
                ``"lo"`` and ``"lo_and_sidebands"`` spellings are deprecated.
            channel_id (ChannelID): id of a sequencer of the module, used to pick the output to calibrate.

        Raises:
            ValueError: if ``cal_type`` is not a recognised calibration type.
            IndexError: if the module has no sequencer with id ``channel_id``.
        """
        cal_type = MixerCalibrationType.parse(cal_type, stacklevel=2)
        sequencer = self.get_sequencer(sequencer_id=int(channel_id))
        if cal_type == MixerCalibrationType.OFF:
            return

        output = sequencer.outputs[0]
        self._calibrate_lo(output)
        if cal_type == MixerCalibrationType.LO_AND_SIDEBANDS:
            for connected_sequencer in self._sequencers_on_output(output):
                self.device.sequencers[connected_sequencer.identifier].sideband_cal()

    def _calibrate_lo(self, output: int) -> None:
        """Calibrate the LO leakage of the given output with the driver's public method."""
        raise NotImplementedError

    def _sequencers_on_output(self, output: int) -> list["QbloxSequencer"]:
        """Return the sequencers connected to the given output."""
        return [sequencer for sequencer in self.awg_sequencers if sequencer.outputs[0] == output]
