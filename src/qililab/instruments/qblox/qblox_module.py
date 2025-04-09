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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from qililab.config import logger
from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument import InstrumentWithChannels
from qililab.result.qblox_results import QbloxResult
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.settings.instruments.qblox_base_settings import (
    QbloxADCSequencerSettings,
    QbloxControlModuleSettings,
    QbloxModuleSettings,
    QbloxReadoutModuleSettings,
    QbloxSequencerSettings,
)
from qililab.typings.instruments import QbloxModuleDevice

if TYPE_CHECKING:
    from qpysequence import Sequence as QpySequence

    from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
    from qililab.qprogram.qblox_compiler import AcquisitionData

TSettings = TypeVar("TSettings", bound=QbloxModuleSettings)
TSequencerSettings = TypeVar("TSequencerSettings", bound=QbloxSequencerSettings)


class QbloxModule(
    InstrumentWithChannels[QbloxModuleDevice, TSettings, TSequencerSettings, int], ABC
):
    qpysequences: dict[int, QpySequence]
    cache: dict[int, PulseBusSchedule]

    def __init__(self, settings: TSettings | None = None):
        super().__init__(settings=settings)
        self.qpysequences: dict[int, QpySequence] = {}
        self.cache: dict[int, PulseBusSchedule] = {}

        self.add_parameter(
            name="timeout",
            settings_field="timeout"
        )

        for channel in self.settings.channels:
            self.add_channel_parameter(
                channel_id=channel.id,
                name="gain_i",
                settings_field="gain_i",
                get_device_value=self._get_gain_i,
                set_device_value=self._set_gain_i,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="gain_q",
                settings_field="gain_q",
                get_device_value=self._get_gain_q,
                set_device_value=self._set_gain_q,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="offset_i",
                settings_field="offset_i",
                get_device_value=self._get_offset_i,
                set_device_value=self._set_offset_i,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="offset_q",
                settings_field="offset_q",
                get_device_value=self._get_offset_q,
                set_device_value=self._set_offset_q,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="hardware_modulation",
                settings_field="hardware_modulation",
                get_device_value=self._get_hardware_modulation,
                set_device_value=self._set_hardware_modulation,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="intermediate_frequency",
                settings_field="intermediate_frequency",
                get_device_value=self._get_intermediate_frequency,
                set_device_value=self._set_intermediate_frequency,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="gain_imbalance",
                settings_field="gain_imbalance",
                get_device_value=self._get_gain_imbalance,
                set_device_value=self._set_gain_imbalance,
            )
            self.add_channel_parameter(
                channel_id=channel.id,
                name="phase_imbalance",
                settings_field="phase_imbalance",
                get_device_value=self._get_phase_imbalance,
                set_device_value=self._set_phase_imbalance,
            )

    @check_device_initialized
    def initial_setup(self):
        self._map_output_connections()
        self.clear_cache()
        for channel in self.settings.channels:
            self.device.sequencers[channel.id].sync_en(False)
            self.device.sequencers[channel.id].marker_ovr_en(False)
            self._set_gain_i(value=channel.gain_i, channel=channel.id)
            self._set_gain_q(value=channel.gain_q, channel=channel.id)
            self._set_offset_i(value=channel.offset_i, channel=channel.id)
            self._set_offset_q(value=channel.offset_q, channel=channel.id)
            self._set_intermediate_frequency(value=channel.intermediate_frequency, channel=channel.id)
            self._set_hardware_modulation(value=channel.hardware_modulation, channel=channel.id)
            self._set_gain_imbalance(value=channel.gain_imbalance, channel=channel.id)
            self._set_phase_imbalance(value=channel.phase_imbalance, channel=channel.id)

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

    @abstractmethod
    def _map_output_connections(self):
        """Disable all connections and map sequencer paths with output channels."""

    def _is_channel_valid(self, channel_id: int):
        return any(channel.id == channel_id for channel in self.settings.channels)

    def _get_gain_i(self, channel: int):
        self.device.sequencers[channel].gain_awg_path0()

    def _set_gain_i(self, value: float, channel: int):
        self.device.sequencers[channel].gain_awg_path0(value)

    def _get_gain_q(self, channel: int):
        self.device.sequencers[channel].gain_awg_path1()

    def _set_gain_q(self, value: float, channel: int):
        self.device.sequencers[channel].gain_awg_path1(value)

    def _get_offset_i(self, channel: int):
        self.device.sequencers[channel].offset_awg_path0()

    def _set_offset_i(self, value: float, channel: int):
        self.device.sequencers[channel].offset_awg_path0(value)

    def _get_offset_q(self, channel: int):
        self.device.sequencers[channel].offset_awg_path1()

    def _set_offset_q(self, value: float, channel: int):
        self.device.sequencers[channel].offset_awg_path1(value)

    def _get_hardware_modulation(self, channel: int):
        self.device.sequencers[channel].mod_en_awg()

    def _set_hardware_modulation(self, value: bool, channel: int):
        self.device.sequencers[channel].mod_en_awg(value)

    def _get_intermediate_frequency(self, channel: int):
        self.device.sequencers[channel].nco_freq()

    def _set_intermediate_frequency(self, value: float, channel: int):
        self.device.sequencers[channel].nco_freq(value)

    def _get_gain_imbalance(self, channel: int):
        self.device.sequencers[channel].mixer_corr_gain_ratio()

    def _set_gain_imbalance(self, value: float, channel: int):
        self.device.sequencers[channel].mixer_corr_gain_ratio(value)

    def _get_phase_imbalance(self, channel: int):
        self.device.sequencers[channel].mixer_corr_phase_offset_degree()

    def _set_phase_imbalance(self, value: float, channel: int):
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
        self.qpysequences = {}

    def upload_qpysequence(self, qpysequence: QpySequence, channel_id: int):
        """Upload the qpysequence to its corresponding sequencer.

        Args:
            qpysequence (QpySequence): The qpysequence to upload.
            port (str): The port of the sequencer to upload to.
        """
        if self._is_channel_valid(channel_id):
            logger.info("Sequence program: \n %s", repr(qpysequence._program))
            self.device.sequencers[channel_id].sequence(qpysequence.todict())
            self.qpysequences[channel_id] = qpysequence

    def upload(self, sequencer_id: int):
        """Upload all the previously compiled programs to its corresponding sequencers.

        This method must be called after the method ``compile`` in the compiler
        Args:
            port (str): The port of the sequencer to upload to.
        """
        if self._is_channel_valid(sequencer_id) and sequencer_id in self.qpysequences:
            sequence = self.qpysequences[sequencer_id]
            logger.info("Uploaded sequence program: \n %s", repr(sequence._program))  # pylint: disable=protected-access
            self.device.sequencers[sequencer_id].sequence(sequence.todict())
            self.device.sequencers[sequencer_id].sync_en(True)

    def run(self, sequencer_id: int):
        """Run the uploaded program"""
        if self._is_channel_valid(sequencer_id) and sequencer_id in self.qpysequences:
            self.device.arm_sequencer(sequencer_id)
            self.device.start_sequencer(sequencer_id)


TControlModuleSettings = TypeVar("TControlModuleSettings", bound=QbloxControlModuleSettings)


class QbloxControlModule(QbloxModule[TControlModuleSettings, QbloxSequencerSettings], ABC):
    pass


TReadoutModuleSettings = TypeVar("TReadoutModuleSettings", bound=QbloxReadoutModuleSettings)


class QbloxReadoutModule(
    QbloxModule[TReadoutModuleSettings, QbloxADCSequencerSettings], ABC
):
    def __init__(self, settings: TReadoutModuleSettings | None = None):
        super().__init__(settings=settings)

        self.add_parameter(
            name="scope_hardware_averaging",
            settings_field="scope_hardware_averaging",
            get_device_value=self._get_scope_hardware_averaging,
            set_device_value=self._set_scope_hardware_averaging,
        )

        for channel in self.settings.channels:
            self.add_channel_parameter(
                    channel_id=channel.id,
                    name="hardware_demodulation",
                    settings_field="hardware_demodulation",
                    get_device_value=self._get_hardware_demodulation,
                    set_device_value=self._set_hardware_demodulation,
                )
            self.add_channel_parameter(
                    channel_id=channel.id,
                    name="integration_length",
                    settings_field="integration_length",
                    get_device_value=self._get_integration_length,
                    set_device_value=self._set_integration_length,
                )
            self.add_channel_parameter(
                    channel_id=channel.id,
                    name="threshold",
                    settings_field="threshold",
                    get_device_value=self._get_threshold,
                    set_device_value=self._set_threshold,
                )
            self.add_channel_parameter(
                    channel_id=channel.id,
                    name="threshold_rotation",
                    settings_field="threshold_rotation",
                    get_device_value=self._get_threshold_rotation,
                    set_device_value=self._set_threshold_rotation,
                )

    @check_device_initialized
    def initial_setup(self):
        super().initial_setup()

        self._map_input_connections()
        self._set_scope_hardware_averaging(self.settings.scope_hardware_averaging)
        for channel in self.settings.channels:
            self.device.delete_acquisition_data(sequencer=channel.id, all=True)
            self._set_hardware_demodulation(value=channel.hardware_demodulation, channel=channel.id)
            self._set_integration_length(value=channel.integration_length, channel=channel.id)
            self._set_threshold(value=channel.threshold, channel=channel.id)
            self._set_threshold_rotation(value=channel.threshold_rotation, channel=channel.id)

    @abstractmethod
    def _map_input_connections(self):
        """Disable all connections and map sequencer paths with inputs."""

    def _get_scope_hardware_averaging(self):
        return self.device.scope_acq_avg_mode_en_path0()

    def _set_scope_hardware_averaging(self, value: bool):
        self.device.scope_acq_avg_mode_en_path0(value)
        self.device.scope_acq_avg_mode_en_path1(value)

    def _get_hardware_demodulation(self, channel: int):
        self.device.sequencers[channel].demod_en_acq()

    def _set_hardware_demodulation(self, value: float, channel: int):
        self.device.sequencers[channel].demod_en_acq(value)

    def _get_integration_length(self, channel: int):
        self.device.sequencers[channel].integration_length_acq()

    def _set_integration_length(self, value: float, channel: int):
        self.device.sequencers[channel].integration_length_acq(value)

    def _get_threshold(self, channel: int):
        integrated_value = self.device.sequencers[channel].integration_length_acq()
        return integrated_value / self.device.sequencers[channel].thresholded_acq_threshold()

    def _set_threshold(self, value: float, channel: int):
        integrated_value = value * self.device.sequencers[channel].integration_length_acq()
        self.device.sequencers[channel].thresholded_acq_threshold(integrated_value)

    def _get_threshold_rotation(self, channel: int):
        self.device.sequencers[channel].thresholded_acq_rotation()

    def _set_threshold_rotation(self, value: float, channel: int):
        self.device.sequencers[channel].thresholded_acq_rotation(value)

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
            if sequencer.id in self.qpysequences:
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
        self, acquisitions: dict[str, AcquisitionData], channel_id: int
    ) -> list[QbloxMeasurementResult]:
        """Read the result from the AWG instrument

        Args:
            acquisitions (list[str]): A list of acquisitions names.

        Returns:
            list[QbloxQProgramMeasurementResult]: Acquired Qblox results in chronological order.
        """
        results = []
        for acquisition, acquistion_data in acquisitions.items():
            if self._is_channel_valid(channel_id) and channel_id in self.qpysequences:
                self.device.get_acquisition_state(sequencer=channel_id, timeout=self.settings.timeout)
                if acquistion_data.save_adc:
                    self.device.store_scope_acquisition(sequencer=channel_id, name=acquisition)
                raw_measurement_data = self.device.get_acquisitions(sequencer=channel_id)[acquisition]["acquisition"]
                measurement_result = QbloxMeasurementResult(
                    bus=acquisitions[acquisition].bus, raw_measurement_data=raw_measurement_data
                )
                results.append(measurement_result)

                # always deleting acquisitions without checking save_adc flag
                self.device.delete_acquisition_data(sequencer=channel_id, name=acquisition)
        return results
