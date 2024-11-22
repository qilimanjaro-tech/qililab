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

from typing import Callable

from qililab.config import logger
from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox_module import QbloxModule
from qililab.qprogram.qblox_compiler import AcquisitionData
from qililab.result.qblox_results import QbloxResult
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.runcard.runcard_instruments import QbloxQRMRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxADCSequencerSettings, QbloxQRMSettings
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QBLOX_QRM)
class QbloxQRM(QbloxModule[QbloxQRMSettings, QbloxADCSequencerSettings]):
    @classmethod
    def get_default_settings(cls) -> QbloxQRMSettings:
        return QbloxQRMSettings(alias="qrm", sequencers=[QbloxADCSequencerSettings(id=index) for index in range(6)])

    @check_device_initialized
    def initial_setup(self):
        super().initial_setup()
        self._map_input_connections()
        self._on_scope_hardware_averaging_changed(self.settings.scope_hardware_averaging)
        for sequencer in self.settings.sequencers:
            self.device.delete_acquisition_data(sequencer=sequencer.id, all=True)
            self._on_hardware_demodulation_changed(value=sequencer.hardware_demodulation, channel=sequencer.id)
            self._on_integration_length_changed(value=sequencer.integration_length, channel=sequencer.id)
            self._on_threshold_changed(value=sequencer.threshold, channel=sequencer.id)
            self._on_threshold_rotation_changed(value=sequencer.threshold_rotation, channel=sequencer.id)

    def _map_input_connections(self):
        """Disable all connections and map sequencer paths with output channels."""
        self.device.disconnect_inputs()

        for sequencer in self.settings.sequencers:
            self.device.sequencers[sequencer.id].connect_acq_I("in0")
            self.device.sequencers[sequencer.id].connect_acq_Q("in1")

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQRMRuncardInstrument(settings=self.settings)

    @classmethod
    def parameter_to_instrument_settings(cls) -> dict[Parameter, str]:
        return super().parameter_to_instrument_settings() | {
            Parameter.SCOPE_HARDWARE_AVERAGING: "scope_hardware_averaging"
        }

    @classmethod
    def parameter_to_channel_settings(cls) -> dict[Parameter, str]:
        return super().parameter_to_channel_settings() | {
            Parameter.HARDWARE_DEMODULATION: "hardware_demodulation",
            Parameter.INTEGRATION_LENGTH: "integration_length",
            Parameter.THRESHOLD: "threshold",
            Parameter.THRESHOLD_ROTATION: "threshold_rotation",
            Parameter.TIME_OF_FLIGHT: "time_of_flight",
        }

    def parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return super().parameter_to_device_operation() | {
            Parameter.SCOPE_HARDWARE_AVERAGING: self._on_scope_hardware_averaging_changed,
            Parameter.HARDWARE_DEMODULATION: self._on_hardware_demodulation_changed,
            Parameter.INTEGRATION_LENGTH: self._on_integration_length_changed,
            Parameter.THRESHOLD: self._on_threshold_changed,
            Parameter.THRESHOLD_ROTATION: self._on_threshold_rotation_changed,
        }

    def _on_scope_hardware_averaging_changed(self, value: float):
        self.device.scope_acq_avg_mode_en_path0(value)
        self.device.scope_acq_avg_mode_en_path1(value)

    def _on_hardware_demodulation_changed(self, value: float, channel: int):
        self.device.sequencers[channel].demod_en_acq(value)

    def _on_integration_length_changed(self, value: float, channel: int):
        self.device.sequencers[channel].integration_length_acq(value)

    def _on_threshold_changed(self, value: float, channel: int):
        integrated_value = value * self.device.sequencers[channel].integration_length_acq()
        self.device.sequencers[channel].thresholded_acq_threshold(integrated_value)

    def _on_threshold_rotation_changed(self, value: float, channel: int):
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
        for sequencer in self.settings.sequencers:
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
