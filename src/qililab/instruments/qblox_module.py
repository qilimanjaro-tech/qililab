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

from abc import ABC
from typing import Callable, ClassVar, TypeVar

from qpysequence import Sequence as QpySequence

from qililab.config import logger
from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument2 import Instrument2
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.settings.instruments.qblox_qcm_settings import QbloxModuleSettings, QbloxSequencerSettings
from qililab.typings.enums import Parameter
from qililab.typings.instruments import QbloxModuleDevice

TSettings = TypeVar("TSettings", bound=QbloxModuleSettings)
TSequencerSettings = TypeVar("TSequencerSettings", bound=QbloxSequencerSettings)


class QbloxModule(Instrument2[QbloxModuleDevice, TSettings, TSequencerSettings, int], ABC):
    cache: ClassVar[dict[int, PulseBusSchedule]] = {}

    def __init__(self, settings: TSettings | None = None):
        super().__init__(settings=settings)
        self.sequences: dict[int, QpySequence] = {}

    @check_device_initialized
    def turn_on(self):
        pass

    @check_device_initialized
    def turn_off(self):
        self.device.stop_sequencer()

    @check_device_initialized
    def reset(self):
        self.clear_cache()
        self.device.reset()

    @check_device_initialized
    def initial_setup(self):
        self._map_output_connections()
        self.clear_cache()
        for sequencer in self.settings.sequencers:
            self.device.sequencers[sequencer.id].sync_en(False)
            self.device.sequencers[sequencer.id].marker_ovr_en(False)
            self._on_gain_i_changed(value=sequencer.gain_i, channel=sequencer.id)
            self._on_gain_q_changed(value=sequencer.gain_q, channel=sequencer.id)
            self._on_offset_i_changed(value=sequencer.offset_i, channel=sequencer.id)
            self._on_offset_q_changed(value=sequencer.offset_q, channel=sequencer.id)
            self._on_intermediate_frequency_changed(value=sequencer.intermediate_frequency, channel=sequencer.id)
            self._on_hardware_modulation_changed(value=sequencer.hardware_modulation, channel=sequencer.id)
            self._on_gain_imbalance_changed(value=sequencer.gain_imbalance, channel=sequencer.id)
            self._on_phase_imbalance_changed(value=sequencer.phase_imbalance, channel=sequencer.id)

        for idx, offset in enumerate(self.settings.output_offsets):
            operations = {
                0: self._on_offset_out0_changed,
                1: self._on_offset_out1_changed,
                2: self._on_offset_out2_changed,
                3: self._on_offset_out3_changed,
            }
            operations[idx](offset)

    @classmethod
    def parameter_to_instrument_settings(cls) -> dict[Parameter, str]:
        return {
            Parameter.TIMEOUT: "timeout",
            Parameter.OFFSET_OUT0: "output_offsets[0]",
            Parameter.OFFSET_OUT1: "output_offsets[1]",
            Parameter.OFFSET_OUT2: "output_offsets[2]",
            Parameter.OFFSET_OUT3: "output_offsets[3]",
        }

    @classmethod
    def parameter_to_channel_settings(cls) -> dict[Parameter, str]:
        return {
            Parameter.GAIN: "gain_i,gain_q",
            Parameter.GAIN_I: "gain_i",
            Parameter.GAIN_Q: "gain_q",
            Parameter.OFFSET_I: "offset_i",
            Parameter.OFFSET_Q: "offset_q",
            Parameter.HARDWARE_MODULATION: "hardware_modulation",
            Parameter.IF: "intermediate_frequency",
            Parameter.GAIN_IMBALANCE: "gain_imbalance",
            Parameter.PHASE_IMBALANCE: "phase_imbalance",
        }

    def get_channel_settings(self, channel: int) -> TSequencerSettings:
        for channel_settings in self.settings.sequencers:
            if channel_settings.id == channel:
                return channel_settings
        raise ValueError(f"Channel {channel} not found.")

    def parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return {
            Parameter.OFFSET_OUT0: self._on_offset_out0_changed,
            Parameter.OFFSET_OUT1: self._on_offset_out1_changed,
            Parameter.OFFSET_OUT2: self._on_offset_out2_changed,
            Parameter.OFFSET_OUT3: self._on_offset_out3_changed,
            Parameter.GAIN_I: self._on_gain_i_changed,
            Parameter.GAIN_Q: self._on_gain_q_changed,
            Parameter.OFFSET_I: self._on_offset_i_changed,
            Parameter.OFFSET_Q: self._on_offset_q_changed,
            Parameter.HARDWARE_MODULATION: self._on_hardware_modulation_changed,
            Parameter.IF: self._on_intermediate_frequency_changed,
            Parameter.GAIN_IMBALANCE: self._on_gain_imbalance_changed,
            Parameter.PHASE_IMBALANCE: self._on_phase_imbalance_changed,
        }

    def _on_offset_out0_changed(self, value: float):
        self.device.out0_offset(value)

    def _on_offset_out1_changed(self, value: float):
        self.device.out1_offset(value)

    def _on_offset_out2_changed(self, value: float):
        self.device.out2_offset(value)

    def _on_offset_out3_changed(self, value: float):
        self.device.out3_offset(value)

    def _on_gain_i_changed(self, value: float, channel: int):
        self.device.sequencers[channel].gain_awg_path0(value)

    def _on_gain_q_changed(self, value: float, channel: int):
        self.device.sequencers[channel].gain_awg_path1(value)

    def _on_offset_i_changed(self, value: float, channel: int):
        self.device.sequencers[channel].offset_awg_path0(value)

    def _on_offset_q_changed(self, value: float, channel: int):
        self.device.sequencers[channel].offset_awg_path1(value)

    def _on_hardware_modulation_changed(self, value: bool, channel: int):
        self.device.sequencers[channel].mod_en_awg(value)

    def _on_intermediate_frequency_changed(self, value: float, channel: int):
        self.device.sequencers[channel].nco_freq(value)

    def _on_gain_imbalance_changed(self, value: float, channel: int):
        self.device.sequencers[channel].mixer_corr_gain_ratio(value)

    def _on_phase_imbalance_changed(self, value: float, channel: int):
        self.device.sequencers[channel].mixer_corr_phase_offset_degree(value)

    def sync_sequencer(self, sequencer_id: int) -> None:
        """Syncs all sequencers."""
        self.device.sequencers[sequencer_id].sync_en(True)

    def desync_sequencer(self, sequencer_id: int) -> None:
        """Syncs all sequencers."""
        self.device.sequencers[sequencer_id].sync_en(False)

    def desync_sequencers(self) -> None:
        """Desyncs all sequencers."""
        for sequencer in self.settings.sequencers:
            self.device.sequencers[sequencer.identifier].sync_en(False)

    def clear_cache(self):
        """Empty cache."""
        self.cache = {}
        self.sequences = {}

    def _map_output_connections(self):
        """Disable all connections and map sequencer paths with output channels."""
        self.device.disconnect_outputs()

        for sequencer in self.settings.sequencers:
            operations = {
                0: self.device.sequencers[sequencer.id].connect_out0,
                1: self.device.sequencers[sequencer.id].connect_out1,
                2: self.device.sequencers[sequencer.id].connect_out2,
                3: self.device.sequencers[sequencer.id].connect_out3,
            }
            for path, output in zip(sequencer.outputs, ["I", "Q"]):
                operations[output](path)

    def _is_sequencer_valid(self, sequencer_id: int):
        return any(sequencer.id == sequencer_id for sequencer in self.settings.sequencers)

    def upload_qpysequence(self, qpysequence: QpySequence, sequencer_id: int):
        """Upload the qpysequence to its corresponding sequencer.

        Args:
            qpysequence (QpySequence): The qpysequence to upload.
            port (str): The port of the sequencer to upload to.
        """
        if self._is_sequencer_valid(sequencer_id):
            logger.info("Sequence program: \n %s", repr(qpysequence._program))
            self.device.sequencers[sequencer_id].sequence(qpysequence.todict())
            self.sequences[sequencer_id] = qpysequence

    def upload(self, sequencer_id: int):
        """Upload all the previously compiled programs to its corresponding sequencers.

        This method must be called after the method ``compile`` in the compiler
        Args:
            port (str): The port of the sequencer to upload to.
        """
        if self._is_sequencer_valid(sequencer_id) and sequencer_id in self.sequences:
            sequence = self.sequences[sequencer_id]
            logger.info("Uploaded sequence program: \n %s", repr(sequence._program))  # pylint: disable=protected-access
            self.device.sequencers[sequencer_id].sequence(sequence.todict())
            self.device.sequencers[sequencer_id].sync_en(True)

    def run(self, sequencer_id: int):
        """Run the uploaded program"""
        if self._is_sequencer_valid(sequencer_id) and sequencer_id in self.sequences:
            self.device.arm_sequencer(sequencer_id)
            self.device.start_sequencer(sequencer_id)
