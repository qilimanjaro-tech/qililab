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

""" AWG with Digital To Analog Conversion (DAC) capabilities."""
from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence, cast

from qililab.instruments.awg import AWG
from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.result.result import Result
from qililab.typings.enums import AcquireTriggerMode, IntegrationMode, Parameter


class AWGAnalogDigitalConverter(AWG):
    """AWG with Digital To Analog Conversion (ADC) capabilities."""

    @dataclass
    class AWGAnalogDigitalConverterSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            acquisition_delay_time (str): Time specified before starting the acquisition
            awg_sequencers (Sequence[AWGADCSequencer]): Properties of each AWG ADC sequencer
        """

        acquisition_delay_time: int  # ns
        awg_sequencers: Sequence[AWGADCSequencer]

    settings: AWGAnalogDigitalConverterSettings

    @abstractmethod
    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """

    def setup(  # pylint: disable=too-many-return-statements, too-many-branches
        self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None
    ):
        """set a specific parameter to the instrument"""
        if channel_id is None:
            if self.num_sequencers == 1:
                channel_id = 0
            else:
                raise ValueError("channel not specified to update instrument")
        if parameter == Parameter.ACQUISITION_DELAY_TIME:
            self._set_acquisition_delay_time(value=value)
            return
        if parameter == Parameter.SCOPE_HARDWARE_AVERAGING:
            self._set_scope_hardware_averaging(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.HARDWARE_DEMODULATION:
            self._set_hardware_demodulation(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.SCOPE_ACQUIRE_TRIGGER_MODE:
            self._set_acquisition_mode(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.INTEGRATION_LENGTH:
            self._set_integration_length(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.SAMPLING_RATE:
            self._set_sampling_rate(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.INTEGRATION_MODE:
            self._set_integration_mode(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.SEQUENCE_TIMEOUT:
            self._set_sequence_timeout(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.ACQUISITION_TIMEOUT:
            self._set_acquisition_timeout(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.SCOPE_STORE_ENABLED:
            self._set_scope_store_enabled(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.THRESHOLD:
            self._set_threshold(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.THRESHOLD_ROTATION:
            self._set_threshold_rotation(value=value, sequencer_id=channel_id)
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @abstractmethod
    def _set_device_scope_hardware_averaging(self, value: bool, sequencer_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """

    @abstractmethod
    def _set_device_threshold(self, value: float, sequencer_id: int):
        """Set threshold value for the specific channel.

        Args:
            value (float): the threshold value
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float"""

    @abstractmethod
    def _set_device_threshold_rotation(self, value: float, sequencer_id: int):
        """Set threshold rotation value for the specific channel.

        Args:
            value (float): the threshold rotation value
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float"""

    @abstractmethod
    def _set_device_hardware_demodulation(self, value: bool, sequencer_id: int):
        """set hardware demodulation

        Args:
            value (bool): value to update
            sequencer_id (int): sequencer to update the value
        """

    @abstractmethod
    def _set_device_acquisition_mode(self, mode: AcquireTriggerMode, sequencer_id: int):
        """set acquisition_mode for the specific channel

        Args:
            mode (AcquireTriggerMode): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """

    @abstractmethod
    def _set_device_integration_length(self, value: int, sequencer_id: int):
        """set integration_length for the specific channel

        Args:
            value (int): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """

    @Instrument.CheckParameterValueBool
    def _set_scope_hardware_averaging(self, value: float | str | bool, sequencer_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).scope_hardware_averaging = bool(value)

        if self.is_device_active():
            self._set_device_scope_hardware_averaging(value=bool(value), sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_threshold(self, value: float | str | bool, sequencer_id: int):
        """Set threshold value for the specific channel.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).threshold = float(value)

        if self.is_device_active():
            self._set_device_threshold(value=float(value), sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_threshold_rotation(self, value: float | str | bool, sequencer_id: int):
        """Set threshold rotation value for the specific channel.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).threshold_rotation = float(value)
        if self.is_device_active():
            self._set_device_threshold_rotation(value=float(value), sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueBool
    def _set_hardware_demodulation(self, value: float | str | bool, sequencer_id: int):
        """set hardware demodulation

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).hardware_demodulation = bool(value)
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
        if not isinstance(value, AcquireTriggerMode) and not isinstance(value, str):
            raise ValueError(f"value must be a string or AcquireTriggerMode. Current type: {type(value)}")
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).scope_acquire_trigger_mode = AcquireTriggerMode(value)
        if self.is_device_active():
            self._set_device_acquisition_mode(mode=AcquireTriggerMode(value), sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_integration_length(self, value: int | float | str | bool, sequencer_id: int):
        """set integration_length for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).integration_length = int(value)
        if self.is_device_active():
            self._set_device_integration_length(value=int(value), sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_sampling_rate(self, value: int | float | str | bool, sequencer_id: int):
        """set sampling_rate for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).sampling_rate = float(value)

    def _set_integration_mode(self, value: float | str | bool | IntegrationMode, sequencer_id: int):
        """set integration_mode for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        if isinstance(value, (IntegrationMode, str)):
            cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).integration_mode = IntegrationMode(value)
        else:
            raise ValueError(f"value must be a string or IntegrationMode. Current type: {type(value)}")

    @Instrument.CheckParameterValueFloatOrInt
    def _set_sequence_timeout(self, value: int | float | str | bool, sequencer_id: int):
        """set sequence_timeout for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float or int
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).sequence_timeout = int(value)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_acquisition_timeout(self, value: int | float | str | bool, sequencer_id: int):
        """set acquisition_timeout for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float or int
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).acquisition_timeout = int(value)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_acquisition_delay_time(self, value: int | float | str | bool):
        """set acquisition_delaty_time for the specific channel

        Args:
            value (float | str | bool): value to update

        Raises:
            ValueError: when value type is not float or int
        """
        self.settings.acquisition_delay_time = int(value)

    @Instrument.CheckParameterValueBool
    def _set_scope_store_enabled(self, value: float | str | bool, sequencer_id: int):
        """set scope_store_enable

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast(AWGADCSequencer, self.get_sequencer(sequencer_id)).scope_store_enabled = bool(value)

    @property
    def acquisition_delay_time(self):
        """AWG 'delay_before_readout' property.
        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.acquisition_delay_time
