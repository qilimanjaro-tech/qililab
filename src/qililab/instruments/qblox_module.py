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
from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, ClassVar, TypeVar

from qililab.config import logger
from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument import InstrumentWithChannels
from qililab.result.qblox_results import QbloxResult
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.settings.instruments.qblox_base_settings import (
    QbloxADCSequencerSettings,
    QbloxControlModuleSettings,
    QbloxInputSettings,
    QbloxModuleSettings,
    QbloxOutputSettings,
    QbloxReadoutModuleSettings,
    QbloxSequencerSettings,
)
from qililab.typings.enums import Parameter
from qililab.typings.instruments import QbloxModuleDevice

if TYPE_CHECKING:
    from qpysequence import Sequence as QpySequence

    from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
    from qililab.qprogram.qblox_compiler import AcquisitionData
    from qililab.settings.instruments.input_settings import InputSettings

TSettings = TypeVar("TSettings", bound=QbloxModuleSettings)
TSequencerSettings = TypeVar("TSequencerSettings", bound=QbloxSequencerSettings)
TOutputSettings = TypeVar("TOutputSettings", bound=QbloxOutputSettings)
TInputSettings = TypeVar("TInputSettings", bound=QbloxInputSettings | None)


class QbloxModule(
    InstrumentWithChannels[QbloxModuleDevice, TSettings, TSequencerSettings, int], ABC
):
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
        for sequencer in self.settings.channels:
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
        for sequencer in self.settings.channels:
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
        return any(sequencer.id == sequencer_id for sequencer in self.settings.channels)

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


TControlModuleSettings = TypeVar("TControlModuleSettings", bound=QbloxControlModuleSettings)


class QbloxControlModule(QbloxModule[TControlModuleSettings, QbloxSequencerSettings], ABC):
    pass


TReadoutModuleSettings = TypeVar("TReadoutModuleSettings", bound=QbloxReadoutModuleSettings)


class QbloxReadoutModule(
    QbloxModule[TReadoutModuleSettings, QbloxADCSequencerSettings], ABC
):

    @check_device_initialized
    def acquire_result(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        results = []
        integration_lengths = []
        for sequencer in self.settings.channels:
            if sequencer.id in self.sequences:
                flags = self.device.get_sequencer_state(sequencer=sequencer.id, timeout=self.settings.timeout)
                logger.info("Sequencer[%d] flags: \n%s", sequencer.id, flags)
                self.device.get_acquisition_state(sequencer=sequencer.id, timeout=self.settings.timeout)

                # if sequencer.scope_store_enabled:
                #     self.device.store_scope_acquisition(sequencer=sequencer.id, name="default")

                for key, data in self.device.get_acquisitions(sequencer=sequencer.id).items():
                    acquisitions = data["acquisition"]
                    # parse acquisition index
                    _, qubit, measure = key.split("_")
                    qubit = int(qubit[1:])
                    measurement = int(measure)
                    acquisitions["qubit"] = qubit
                    acquisitions["measurement"] = measurement
                    results.append(acquisitions)
                    integration_lengths.append(sequencer.integration_length)
                self.device.sequencers[sequencer.id].sync_en(False)
                integration_lengths.append(sequencer.integration_length)
                self.device.delete_acquisition_data(sequencer=sequencer.id, all=True)

        return QbloxResult(integration_lengths=integration_lengths, qblox_raw_results=results)

    @check_device_initialized
    def acquire_qprogram_results(
        self, acquisitions: dict[str, AcquisitionData], sequencer_id: int
    ) -> list[QbloxMeasurementResult]:
        """Read the result from the AWG instrument

        Args:
            acquisitions (list[str]): A list of acquisitions names.

        Returns:
            list[QbloxQProgramMeasurementResult]: Acquired Qblox results in chronological order.
        """
        results = []
        for acquisition, acquistion_data in acquisitions.items():
            if self._is_sequencer_valid(sequencer_id) and sequencer_id in self.sequences:
                self.device.get_acquisition_state(sequencer=sequencer_id, timeout=self.settings.timeout)
                if acquistion_data.save_adc:
                    self.device.store_scope_acquisition(sequencer=sequencer_id, name=acquisition)
                raw_measurement_data = self.device.get_acquisitions(sequencer=sequencer_id)[acquisition]["acquisition"]
                measurement_result = QbloxMeasurementResult(
                    bus=acquisitions[acquisition].bus, raw_measurement_data=raw_measurement_data
                )
                results.append(measurement_result)

                # always deleting acquisitions without checking save_adc flag
                self.device.delete_acquisition_data(sequencer=sequencer_id, name=acquisition)
        return results
