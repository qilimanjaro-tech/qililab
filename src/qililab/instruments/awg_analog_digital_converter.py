""" AWG with Digital To Analog Conversion (DAC) capabilities."""
from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence

from qililab.instruments.awg import AWG
from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.instrument import Instrument
from qililab.result.result import Result
from qililab.typings.enums import AcquireTriggerMode, IntegrationMode, Parameter


class AWGAnalogDigitalConverter(AWG):
    """AWG with Digital To Analog Conversion (ADC) capabilities."""

    @dataclass
    class AWGAnalogDigitalConverterSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:

        """

        awg_sequencers: Sequence[AWGADCSequencer]

    settings: AWGAnalogDigitalConverterSettings

    @abstractmethod
    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        if channel_id is None:
            raise ValueError("channel not specified to update instrument")
        if parameter == Parameter.ACQUISITION_DELAY_TIME:
            self._set_acquisition_delay_time(value=value, sequencer_id=channel_id)
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

        raise ValueError(f"Invalid Parameter: {parameter.value}")

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
        self.awg_sequencers[sequencer_id].scope_hardware_averaging = bool(value)
        self._set_device_scope_hardware_averaging(value=bool(value), sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueBool
    def _set_hardware_demodulation(self, value: float | str | bool, sequencer_id: int):
        """set hardware demodulation

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self.awg_sequencers[sequencer_id].hardware_demodulation = bool(value)
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
        self.awg_sequencers[sequencer_id].scope_acquire_trigger_mode = AcquireTriggerMode(value)
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
        self.awg_sequencers[sequencer_id].integration_length = int(value)
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
        self.awg_sequencers[sequencer_id].sampling_rate = float(value)

    def _set_integration_mode(self, value: float | str | bool | IntegrationMode, sequencer_id: int):
        """set integration_mode for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        if isinstance(value, (IntegrationMode, str)):
            self.awg_sequencers[sequencer_id].integration_mode = IntegrationMode(value)
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
        self.awg_sequencers[sequencer_id].sequence_timeout = int(value)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_acquisition_timeout(self, value: int | float | str | bool, sequencer_id: int):
        """set acquisition_timeout for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float or int
        """
        self.awg_sequencers[sequencer_id].acquisition_timeout = int(value)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_acquisition_delay_time(self, value: int | float | str | bool, sequencer_id: int):
        """set acquisition_delaty_time for the specific channel

        Args:
            value (float | str | bool): value to update

        Raises:
            ValueError: when value type is not float or int
        """
        self.awg_sequencers[sequencer_id].acquisition_delay_time = int(value)

    @Instrument.CheckParameterValueBool
    def _set_scope_store_enabled(self, value: float | str | bool, sequencer_id: int):
        """set scope_store_enable

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self.awg_sequencers[sequencer_id].scope_store_enabled = bool(value)
