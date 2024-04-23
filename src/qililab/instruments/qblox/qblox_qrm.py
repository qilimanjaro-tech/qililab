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
from qililab.instruments.awg_analog_digital_converter import AWGAnalogDigitalConverter
from qililab.instruments.awg_settings import AWGQbloxADCSequencer
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils import InstrumentFactory
from qililab.result.qblox_results import QbloxResult
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.typings.enums import AcquireTriggerMode, InstrumentName, Parameter


@InstrumentFactory.register
class QbloxQRM(QbloxModule, AWGAnalogDigitalConverter):
    """Qblox QRM class.

    Args:
        settings (QBloxQRMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QRM
    _scoping_sequencer: int | None = None

    @dataclass
    class QbloxQRMSettings(
        QbloxModule.QbloxModuleSettings, AWGAnalogDigitalConverter.AWGAnalogDigitalConverterSettings
    ):
        """Contains the settings of a specific QRM."""

        awg_sequencers: Sequence[AWGQbloxADCSequencer]

        def __post_init__(self):
            """build AWGQbloxADCSequencer"""
            if (
                self.num_sequencers <= 0
                or self.num_sequencers > QbloxModule._NUM_MAX_SEQUENCERS  # pylint: disable=protected-access
            ):
                raise ValueError(
                    "The number of sequencers must be greater than 0 and less or equal than "
                    + f"{QbloxModule._NUM_MAX_SEQUENCERS}. Received: {self.num_sequencers}"  # pylint: disable=protected-access
                )
            if len(self.awg_sequencers) != self.num_sequencers:
                raise ValueError(
                    f"The number of sequencers: {self.num_sequencers} does not match"
                    + f" the number of AWG Sequencers settings specified: {len(self.awg_sequencers)}"
                )

            self.awg_sequencers = [
                AWGQbloxADCSequencer(**sequencer)
                if isinstance(sequencer, dict)
                else sequencer  # pylint: disable=not-a-mapping
                for sequencer in self.awg_sequencers
            ]
            super().__post_init__()

    settings: QbloxQRMSettings

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        self._obtain_scope_sequencer()
        for sequencer in self.awg_sequencers:
            sequencer_id = sequencer.identifier
            # Remove all acquisition data
            self.device.delete_acquisition_data(sequencer=sequencer_id, all=True)
            self._set_integration_length(
                value=cast(AWGQbloxADCSequencer, sequencer).integration_length, sequencer_id=sequencer_id
            )
            self._set_acquisition_mode(
                value=cast(AWGQbloxADCSequencer, sequencer).scope_acquire_trigger_mode, sequencer_id=sequencer_id
            )
            self._set_scope_hardware_averaging(
                value=cast(AWGQbloxADCSequencer, sequencer).scope_hardware_averaging, sequencer_id=sequencer_id
            )
            self._set_hardware_demodulation(
                value=cast(AWGQbloxADCSequencer, sequencer).hardware_demodulation, sequencer_id=sequencer_id
            )
            self._set_threshold(value=cast(AWGQbloxADCSequencer, sequencer).threshold, sequencer_id=sequencer_id)
            self._set_threshold_rotation(
                value=cast(AWGQbloxADCSequencer, sequencer).threshold_rotation, sequencer_id=sequencer_id
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
                if self._scoping_sequencer is None:
                    self._scoping_sequencer = sequencer.identifier
                else:
                    raise ValueError("The scope can only be stored in one sequencer at a time.")

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        return self.get_acquisitions()

    def acquire_qprogram_results(self, acquisitions: list[str], port: str) -> list[QbloxMeasurementResult]:  # type: ignore
        """Read the result from the AWG instrument

        Args:
            acquisitions (list[str]): A list of acquisitions names.

        Returns:
            list[QbloxQProgramMeasurementResult]: Acquired Qblox results in chronological order.
        """
        return self._get_qprogram_acquisitions(acquisitions=acquisitions, port=port)

    @Instrument.CheckDeviceInitialized
    def _get_qprogram_acquisitions(self, acquisitions: list[str], port: str) -> list[QbloxMeasurementResult]:
        results = []
        for acquisition in acquisitions:
            sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
            for sequencer in sequencers:
                if sequencer.identifier in self.sequences:
                    self.device.get_acquisition_state(
                        sequencer=sequencer.identifier,
                        timeout=cast(AWGQbloxADCSequencer, sequencer).acquisition_timeout,
                    )
                    self.device.store_scope_acquisition(sequencer=sequencer.identifier, name=acquisition)
                    raw_measurement_data = self.device.get_acquisitions(sequencer=sequencer.identifier)[acquisition][
                        "acquisition"
                    ]
                    measurement_result = QbloxMeasurementResult(raw_measurement_data=raw_measurement_data)
                    results.append(measurement_result)

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
        integrated_value = value * self._get_sequencer_by_id(id=sequencer_id).used_integration_length
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
        if cast(AWGQbloxADCSequencer, self.get_sequencer(sequencer_id)).hardware_demodulation:
            self._set_hardware_demodulation(
                value=self.get_sequencer(sequencer_id).hardware_modulation, sequencer_id=sequencer_id
            )

    @Instrument.CheckDeviceInitialized
    def get_acquisitions(self) -> QbloxResult:
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
                flags = self.device.get_sequencer_state(
                    sequencer=sequencer_id, timeout=cast(AWGQbloxADCSequencer, sequencer).sequence_timeout
                )
                logger.info("Sequencer[%d] flags: \n%s", sequencer_id, flags)
                self.device.get_acquisition_state(
                    sequencer=sequencer_id, timeout=cast(AWGQbloxADCSequencer, sequencer).acquisition_timeout
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
                    integration_lengths.append(sequencer.used_integration_length)
                self.device.sequencers[sequencer.identifier].sync_en(False)
                integration_lengths.append(sequencer.used_integration_length)
                self.device.delete_acquisition_data(sequencer=sequencer_id, all=True)

        return QbloxResult(integration_lengths=integration_lengths, qblox_raw_results=results)

    def integration_length(self, sequencer_id: int):
        """QbloxPulsarQRM 'integration_length' property.
        Returns:
            int: settings.integration_length.
        """
        return cast(AWGQbloxADCSequencer, self.get_sequencer(sequencer_id)).integration_length

    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        try:
            AWGAnalogDigitalConverter.setup(self, parameter=parameter, value=value, channel_id=channel_id)
        except ParameterNotFound:
            QbloxModule.setup(self, parameter=parameter, value=value, channel_id=channel_id)
