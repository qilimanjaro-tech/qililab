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

"""Qblox pulsar QRM class"""

from dataclasses import dataclass
from typing import Sequence, cast

from qililab.config import logger
from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.qblox.qblox_adc_sequencer import QbloxADCSequencer
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils import InstrumentFactory
from qililab.qprogram.qblox_compiler import AcquisitionData
from qililab.result.qblox_results import QbloxResult
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.typings import (
    AcquireTriggerMode,
    ChannelID,
    InstrumentName,
    IntegrationMode,
    OutputID,
    Parameter,
    ParameterValue,
)


@InstrumentFactory.register
class QbloxQRM(QbloxModule):
    """Qblox QRM class.

    Args:
        settings (QBloxQRMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QRM
    _scoping_sequencer: int | None = None

    @dataclass
    class QbloxQRMSettings(QbloxModule.QbloxModuleSettings):
        """Contains the settings of a specific QRM."""

        awg_sequencers: Sequence[QbloxADCSequencer]
        # filters: Sequence[QbloxFilter] = field(
        #     init=False,
        #     default_factory=list,  # QCM-RF module doesn't have filters
        # )

        def __post_init__(self):
            """build AWGQbloxADCSequencer"""
            if len(self.awg_sequencers) > QbloxModule._NUM_MAX_SEQUENCERS:
                raise ValueError(
                    f"The number of sequencers must be greater than 0 and less or equal than {QbloxModule._NUM_MAX_SEQUENCERS}. Received: {len(self.awg_sequencers)}"
                )

            self.awg_sequencers = [
                QbloxADCSequencer(**sequencer) if isinstance(sequencer, dict) else sequencer
                for sequencer in self.awg_sequencers
            ]

            super().__post_init__()

    settings: QbloxQRMSettings

    def is_awg(self) -> bool:
        """Returns True if instrument is an AWG."""
        return True

    def is_adc(self) -> bool:
        """Returns True if instrument is an ADC."""
        return True

    @check_device_initialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        self._obtain_scope_sequencer()
        for sequencer in self.awg_sequencers:
            sequencer_id = sequencer.identifier
            # Remove all acquisition data
            self.device.delete_acquisition_data(sequencer=sequencer_id, all=True)
            self._set_integration_length(
                value=cast("QbloxADCSequencer", sequencer).integration_length, sequencer_id=sequencer_id
            )
            self._set_acquisition_mode(
                value=cast("QbloxADCSequencer", sequencer).scope_acquire_trigger_mode, sequencer_id=sequencer_id
            )
            self._set_scope_hardware_averaging(
                value=cast("QbloxADCSequencer", sequencer).scope_hardware_averaging, sequencer_id=sequencer_id
            )
            self._set_hardware_demodulation(
                value=cast("QbloxADCSequencer", sequencer).hardware_demodulation, sequencer_id=sequencer_id
            )
            self._set_threshold(value=cast("QbloxADCSequencer", sequencer).threshold, sequencer_id=sequencer_id)
            self._set_threshold_rotation(
                value=cast("QbloxADCSequencer", sequencer).threshold_rotation, sequencer_id=sequencer_id
            )

    def _map_connections(self):
        """Disable all connections and map sequencer paths with output/input channels."""
        # Disable all connections
        self.device.disconnect_outputs()
        self.device.disconnect_inputs()

        for sequencer_dataclass in self.awg_sequencers:
            sequencer = self.device.sequencers[sequencer_dataclass.identifier]
            for path, output in zip(["I", "Q"], sequencer_dataclass.outputs):
                getattr(sequencer, f"connect_out{output}")(path)

            sequencer.connect_acq_I("in0")
            sequencer.connect_acq_Q("in1")

    def _obtain_scope_sequencer(self):
        """Checks that only one sequencer is storing the scope and saves that sequencer in `_scoping_sequencer`

        Raises:
            ValueError: The scope can only be stores in one sequencer at a time.
        """
        for sequencer in self.awg_sequencers:
            if sequencer.scope_store_enabled:
                if self._scoping_sequencer in (None, sequencer.identifier):
                    self._scoping_sequencer = sequencer.identifier
                    return
                raise ValueError("The scope can only be stored in one sequencer at a time.")
            if self._scoping_sequencer == sequencer.identifier:
                self._scoping_sequencer = None

    @check_device_initialized
    def acquire_result(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        results = []
        integration_lengths = []
        for sequencer in self.awg_sequencers:
            if sequencer.identifier in self.sequences:
                sequencer_id = sequencer.identifier
                flags = self.device.get_sequencer_status(
                    sequencer=sequencer_id, timeout=cast("QbloxADCSequencer", sequencer).sequence_timeout
                )
                logger.info("Sequencer[%d] flags: \n%s", sequencer_id, flags)
                self.device.get_acquisition_status(
                    sequencer=sequencer_id, timeout=cast("QbloxADCSequencer", sequencer).acquisition_timeout
                )

                if sequencer.scope_store_enabled:
                    self.device.store_scope_acquisition(sequencer=sequencer_id, name="default")

                for key, data in self.device.get_acquisitions(sequencer=sequencer.identifier).items():
                    acquisitions = data["acquisition"]
                    # parse acquisition index
                    _, qubit, measure = key.split("_")
                    qubit = int(qubit[1:])
                    measurement = int(measure)
                    acquisitions["qubit"] = qubit
                    acquisitions["measurement"] = measurement
                    results.append(acquisitions)
                    integration_lengths.append(sequencer.integration_length)
                self.device.sequencers[sequencer.identifier].sync_en(False)
                integration_lengths.append(sequencer.integration_length)
                self.device.delete_acquisition_data(sequencer=sequencer_id, all=True)

        return QbloxResult(integration_lengths=integration_lengths, qblox_raw_results=results)

    @check_device_initialized
    def acquire_qprogram_results(
        self, acquisitions: dict[str, AcquisitionData], channel_id: ChannelID
    ) -> list[QbloxMeasurementResult]:
        """Read the result from the AWG instrument

        Args:
            acquisitions (list[str]): A list of acquisitions names.

        Returns:
            list[QbloxQProgramMeasurementResult]: Acquired Qblox results in chronological order.
        """
        results = []
        for acquisition, acquisition_data in acquisitions.items():
            sequencer = next(
                (sequencer for sequencer in self.awg_sequencers if sequencer.identifier == channel_id), None
            )
            if sequencer is not None and sequencer.identifier in self.sequences:
                self.device.get_acquisition_status(
                    sequencer=sequencer.identifier,
                    timeout=cast("QbloxADCSequencer", sequencer).acquisition_timeout,
                )
                if acquisition_data.save_adc:
                    self.device.store_scope_acquisition(sequencer=sequencer.identifier, name=acquisition)
                raw_measurement_data = self.device.get_acquisitions(sequencer=sequencer.identifier)[acquisition][
                    "acquisition"
                ]
                measurement_result = QbloxMeasurementResult(
                    bus=acquisitions[acquisition].bus,
                    raw_measurement_data=raw_measurement_data,
                    shape=acquisition_data.shape,
                )
                results.append(measurement_result)

                # always deleting acquisitions without checking save_adc flag
                self.device.delete_acquisition_data(sequencer=sequencer.identifier, name=acquisition)
        return results

    def _set_device_hardware_demodulation(self, value: bool, sequencer_id: int):
        """set hardware demodulation

        Args:
            value (bool): value to update
            sequencer_id (int): sequencer to update the value
        """
        self.device.sequencers[sequencer_id].demod_en_acq(value)

    def _set_device_acquisition_mode(self, mode: AcquireTriggerMode, sequencer_id: int):
        """set acquisition_mode for the specific channel

        Args:
            mode (AcquireTriggerMode): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        if sequencer_id != self._scoping_sequencer:
            return
        self.device.scope_acq_sequencer_select(sequencer_id)
        self.device.scope_acq_trigger_mode_path0(mode.value)
        self.device.scope_acq_trigger_mode_path1(mode.value)

    def _set_device_integration_length(self, value: int, sequencer_id: int):
        """set integration_length for the specific channel

        Args:
            value (int): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.device.sequencers[sequencer_id].integration_length_acq(value)

    def _set_device_scope_hardware_averaging(self, value: bool, sequencer_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if sequencer_id != self._scoping_sequencer:
            return
        self.device.scope_acq_sequencer_select(sequencer_id)
        self.device.scope_acq_avg_mode_en_path0(value)
        self.device.scope_acq_avg_mode_en_path1(value)

    def _set_device_threshold(self, value: float, sequencer_id: int):
        """Sets the threshold for classification at the specific channel.

        Args:
            value (float): integrated value of the threshold
            sequencer_id (int): sequencer to update the value
        """
        integrated_value = value * self.device.sequencers[sequencer_id].integration_length_acq()
        self.device.sequencers[sequencer_id].thresholded_acq_threshold(integrated_value)

    def _set_device_threshold_rotation(self, value: float, sequencer_id: int):
        """Sets the threshold rotation for classification at the specific channel.

        Args:
            value (float): threshold rotation value in degrees (0.0 to 360.0).
            sequencer_id (int): sequencer to update the value
        """
        self.device.sequencers[sequencer_id].thresholded_acq_rotation(value)

    def _set_nco(self, sequencer_id: int):
        """Enable modulation/demodulation of pulses and setup NCO frequency."""
        super()._set_nco(sequencer_id=sequencer_id)
        if cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).hardware_demodulation:
            self._set_hardware_demodulation(
                value=self.get_sequencer(sequencer_id).hardware_modulation, sequencer_id=sequencer_id
            )

    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None, output_id: OutputID | None = None):
        """set a specific parameter to the instrument"""
        if output_id is not None:
            super().set_parameter(parameter=parameter, value=value, channel_id=channel_id, output_id=output_id)
            return

        if channel_id is None:
            raise ValueError("channel not specified to update instrument")

        channel_id = int(channel_id)
        if parameter == Parameter.SCOPE_HARDWARE_AVERAGING:
            self._set_scope_hardware_averaging(value=float(value), sequencer_id=channel_id)
            return
        if parameter == Parameter.HARDWARE_DEMODULATION:
            self._set_hardware_demodulation(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.SCOPE_ACQUIRE_TRIGGER_MODE:
            self._set_acquisition_mode(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.INTEGRATION_LENGTH:
            self._set_integration_length(value=int(value), sequencer_id=channel_id)
            return
        if parameter == Parameter.SAMPLING_RATE:
            self._set_sampling_rate(value=float(value), sequencer_id=channel_id)
            return
        if parameter == Parameter.INTEGRATION_MODE:
            self._set_integration_mode(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.SEQUENCE_TIMEOUT:
            self._set_sequence_timeout(value=int(value), sequencer_id=channel_id)
            return
        if parameter == Parameter.ACQUISITION_TIMEOUT:
            self._set_acquisition_timeout(value=int(value), sequencer_id=channel_id)
            return
        if parameter == Parameter.SCOPE_STORE_ENABLED:
            self._set_scope_store_enabled(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.THRESHOLD:
            self._set_threshold(value=float(value), sequencer_id=channel_id)
            return
        if parameter == Parameter.THRESHOLD_ROTATION:
            self._set_threshold_rotation(value=float(value), sequencer_id=channel_id)
            return
        if parameter == Parameter.TIME_OF_FLIGHT:
            self._set_time_of_flight(value=int(value), sequencer_id=channel_id)
            return
        super().set_parameter(parameter=parameter, value=value, channel_id=channel_id, output_id=output_id)

    def _set_scope_hardware_averaging(self, value: float | str | bool, sequencer_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).scope_hardware_averaging = bool(value)

        if self.is_device_active():
            self._set_device_scope_hardware_averaging(value=bool(value), sequencer_id=sequencer_id)

    def _set_threshold(self, value: float | str | bool, sequencer_id: int):
        """Set threshold value for the specific channel.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).threshold = float(value)

        if self.is_device_active():
            self._set_device_threshold(value=float(value), sequencer_id=sequencer_id)

    def _set_threshold_rotation(self, value: float | str | bool, sequencer_id: int):
        """Set threshold rotation value for the specific channel.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).threshold_rotation = float(value)
        if self.is_device_active():
            self._set_device_threshold_rotation(value=float(value), sequencer_id=sequencer_id)

    def _set_hardware_demodulation(self, value: float | str | bool, sequencer_id: int):
        """set hardware demodulation

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).hardware_demodulation = bool(value)
        if self.is_device_active():
            self._set_device_hardware_demodulation(value=bool(value), sequencer_id=sequencer_id)

    def _set_acquisition_mode(self, value: float | str | bool | AcquireTriggerMode, sequencer_id: int):
        """set acquisition_mode for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).scope_acquire_trigger_mode = AcquireTriggerMode(
            value
        )
        if self.is_device_active():
            self._set_device_acquisition_mode(mode=AcquireTriggerMode(value), sequencer_id=sequencer_id)

    def _set_integration_length(self, value: int | float | str | bool, sequencer_id: int):
        """set integration_length for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).integration_length = int(value)
        if self.is_device_active():
            self._set_device_integration_length(value=int(value), sequencer_id=sequencer_id)

    def _set_sampling_rate(self, value: int | float | str | bool, sequencer_id: int):
        """set sampling_rate for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).sampling_rate = float(value)

    def _set_integration_mode(self, value: float | str | bool | IntegrationMode, sequencer_id: int):
        """set integration_mode for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).integration_mode = IntegrationMode(value)

    def _set_sequence_timeout(self, value: int | float | str | bool, sequencer_id: int):
        """set sequence_timeout for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float or int
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).sequence_timeout = int(value)

    def _set_acquisition_timeout(self, value: int | float | str | bool, sequencer_id: int):
        """set acquisition_timeout for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float or int
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).acquisition_timeout = int(value)

    def _set_scope_store_enabled(self, value: float | str | bool, sequencer_id: int):
        """set scope_store_enable

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).scope_store_enabled = bool(value)

        self._obtain_scope_sequencer()
        sequencer = self.get_sequencer(sequencer_id)
        self._set_acquisition_mode(
            value=cast("QbloxADCSequencer", sequencer).scope_acquire_trigger_mode, sequencer_id=sequencer_id
        )
        self._set_scope_hardware_averaging(
            value=cast("QbloxADCSequencer", sequencer).scope_hardware_averaging, sequencer_id=sequencer_id
        )

    def _set_time_of_flight(self, value: int | float | str | bool, sequencer_id: int):
        """set time_of_flight

        Args:
            value (int | float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast("QbloxADCSequencer", self.get_sequencer(sequencer_id)).time_of_flight = int(value)
