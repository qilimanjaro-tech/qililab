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

from typing import Any, Callable

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox_module import QbloxReadoutModule
from qililab.runcard.runcard_instruments import QbloxQRMRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import (
    QbloxADCSequencerSettings,
    QbloxLFInputSettings,
    QbloxLFOutputSettings,
    QbloxQRMSettings,
)
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QBLOX_QRM)
class QbloxQRM(QbloxReadoutModule[QbloxQRMSettings, QbloxLFOutputSettings, QbloxLFInputSettings]):
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
    def instrument_parameter_to_settings(cls) -> dict[Parameter, str]:
        return super().instrument_parameter_to_settings() | {
            Parameter.SCOPE_HARDWARE_AVERAGING: "scope_hardware_averaging"
        }

    @classmethod
    def _channel_parameter_to_settings(cls) -> dict[Parameter, str]:
        return super()._channel_parameter_to_settings() | {
            Parameter.HARDWARE_DEMODULATION: "hardware_demodulation",
            Parameter.INTEGRATION_LENGTH: "integration_length",
            Parameter.THRESHOLD: "threshold",
            Parameter.THRESHOLD_ROTATION: "threshold_rotation",
            Parameter.TIME_OF_FLIGHT: "time_of_flight",
        }

    @classmethod
    def _output_parameter_to_settings(cls) -> dict[Parameter, str]:
        return super()._output_parameter_to_settings() | {
            Parameter.OFFSET: "offset",
        }

    @classmethod
    def _input_parameter_to_settings(cls) -> dict[Parameter, str]:
        return super()._input_parameter_to_settings() | {Parameter.GAIN: "gain", Parameter.OFFSET: "offset"}

    def _instrument_parameter_to_device_operation(self) -> dict[Parameter, Callable[..., Any]]:
        return super()._instrument_parameter_to_device_operation() | {
            Parameter.SCOPE_HARDWARE_AVERAGING: self._on_scope_hardware_averaging_changed,
        }

    def _on_scope_hardware_averaging_changed(self, value: float):
        self.device.scope_acq_avg_mode_en_path0(value)
        self.device.scope_acq_avg_mode_en_path1(value)

    def _channel_parameter_to_device_operation(self) -> dict[Parameter, Callable]:
        return super()._channel_parameter_to_device_operation() | {
            Parameter.HARDWARE_DEMODULATION: self._on_hardware_demodulation_changed,
            Parameter.INTEGRATION_LENGTH: self._on_integration_length_changed,
            Parameter.THRESHOLD: self._on_threshold_changed,
            Parameter.THRESHOLD_ROTATION: self._on_threshold_rotation_changed,
        }

    def _on_hardware_demodulation_changed(self, value: float, channel: int):
        self.device.sequencers[channel].demod_en_acq(value)

    def _on_integration_length_changed(self, value: float, channel: int):
        self.device.sequencers[channel].integration_length_acq(value)

    def _on_threshold_changed(self, value: float, channel: int):
        integrated_value = value * self.device.sequencers[channel].integration_length_acq()
        self.device.sequencers[channel].thresholded_acq_threshold(integrated_value)

    def _on_threshold_rotation_changed(self, value: float, channel: int):
        self.device.sequencers[channel].thresholded_acq_rotation(value)

    def _output_parameter_to_device_operation(self) -> dict[Parameter, Callable[..., Any]]:
        return super()._output_parameter_to_device_operation() | {Parameter.OFFSET: self._on_output_offset_changed}

    def _on_output_offset_changed(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset,
            1: self.device.out1_offset,
            2: self.device.out2_offset,
            3: self.device.out3_offset,
        }
        operations[output](value)

    def _input_parameter_to_device_operation(self) -> dict[Parameter, Callable[..., Any]]:
        return super()._input_parameter_to_device_operation() | {
            Parameter.GAIN: self._on_input_gain_changed,
            Parameter.OFFSET: self._on_input_offset_changed,
        }

    def _on_input_gain_changed(self, value: float, input: int):
        operations = {0: self.device.in0_gain, 1: self.device.in1_gain}
        operations[input](value)

    def _on_input_offset_changed(self, value: float, input: int):
        operations = {0: self.device.in0_offset, 1: self.device.in1_offset}
        operations[input](value)
