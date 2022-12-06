""" AWG with Digital To Analog Conversion (DAC) capabilities."""
from abc import abstractmethod
from dataclasses import dataclass
from typing import List

from qililab.instruments.awg import AWG
from qililab.instruments.instrument import Instrument
from qililab.result.result import Result
from qililab.typings.enums import AcquireTriggerMode, IntegrationMode, Parameter


class AWGDigitalAnalogConverter(AWG):
    """AWG with Digital To Analog Conversion (DAC) capabilities."""

    @dataclass
    class AWGDigitalAnalogConverterSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            acquire_trigger_mode (str): Set scope acquisition trigger mode. Options are 'sequencer' or 'level'.
            scope_hardware_averaging (bool): Enable/disable hardware averaging of the data during scope mode.
            integration_length (int): Duration (in ns) of the integration.
            integration_mode (str): Integration mode. Options are 'ssb'.
            sequence_timeout (int): Time (in minutes) to wait for the sequence to finish.
            If timeout is reached a TimeoutError is raised.
            acquisition_timeout (int): Time (in minutes) to wait for the acquisition to finish.
            If timeout is reached a TimeoutError is raised.
            acquisition_name (str): Name of the acquisition saved in the sequencer.
        """

        scope_acquire_trigger_mode: List[AcquireTriggerMode]
        scope_hardware_averaging: List[bool]
        sampling_rate: List[int]  # default sampling rate for Qblox is 1.e+09
        hardware_integration: List[bool]  # integration flag
        hardware_demodulation: List[bool]  # demodulation flag
        integration_length: List[int]
        integration_mode: List[IntegrationMode]
        sequence_timeout: List[int]  # minutes
        acquisition_timeout: List[int]  # minutes
        acquisition_delay_time: int  # ns

    settings: AWGDigitalAnalogConverterSettings

    @property
    def acquisition_delay_time(self):
        """AWG 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.acquisition_delay_time

    @property
    def scope_acquire_trigger_mode(self):
        """QbloxPulsarQRM 'acquire_trigger_mode' property.

        Returns:
            AcquireTriggerMode: settings.acquire_trigger_mode.
        """
        return self.settings.scope_acquire_trigger_mode

    @property
    def scope_hardware_averaging(self):
        """QbloxPulsarQRM 'scope_hardware_averaging' property.

        Returns:
            bool: settings.scope_hardware_averaging.
        """
        return self.settings.scope_hardware_averaging

    @property
    def sampling_rate(self):
        """QbloxPulsarQRM 'sampling_rate' property.

        Returns:
            int: settings.sampling_rate.
        """
        return self.settings.sampling_rate

    @property
    def integration_length(self):
        """QbloxPulsarQRM 'integration_length' property.

        Returns:
            int: settings.integration_length.
        """
        return self.settings.integration_length

    @property
    def integration_mode(self):
        """QbloxPulsarQRM 'integration_mode' property.

        Returns:
            IntegrationMode: settings.integration_mode.
        """
        return self.settings.integration_mode

    @property
    def sequence_timeout(self):
        """QbloxPulsarQRM 'sequence_timeout' property.

        Returns:
            int: settings.sequence_timeout.
        """
        return self.settings.sequence_timeout

    @property
    def acquisition_timeout(self):
        """QbloxPulsarQRM 'acquisition_timeout' property.

        Returns:
            int: settings.acquisition_timeout.
        """
        return self.settings.acquisition_timeout

    @property
    def final_wait_time(self) -> int:
        """QbloxPulsarQRM 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return self.acquisition_delay_time

    @property
    def hardware_integration(self):
        """QbloxPulsarQRM 'integration' property.

        Returns:
            bool: Integration flag.
        """
        return self.settings.hardware_integration

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
        super().setup(parameter=parameter, value=value, channel_id=channel_id)
        if parameter == Parameter.SCOPE_HARDWARE_AVERAGING:
            self._set_scope_hardware_averaging(value=value, channel_id=channel_id)
            return
        if parameter == Parameter.HARDWARE_DEMODULATION:
            self._set_hardware_demodulation(value=value, channel_id=channel_id)
            return
        if parameter == Parameter.SCOPE_ACQUIRE_TRIGGER_MODE:
            self._set_acquisition_mode(value=value, channel_id=channel_id)
            return
        if parameter == Parameter.INTEGRATION_LENGTH:
            self._set_integration_length(value=value, channel_id=channel_id)
            return
        raise ValueError(f"Invalid Parameter: {parameter.value}")

    @abstractmethod
    def _set_device_scope_hardware_averaging(self, value: bool, channel_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """

    @abstractmethod
    def _set_device_hardware_demodulation(self, value: bool, channel_id: int):
        """set hardware demodulation

        Args:
            value (bool): value to update
            channel_id (int): sequencer to update the value
        """

    @abstractmethod
    def _set_device_acquisition_mode(self, mode: AcquireTriggerMode, channel_id: int):
        """set acquisition_mode for the specific channel

        Args:
            mode (AcquireTriggerMode): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """

    @abstractmethod
    def _set_device_integration_length(self, value: int, channel_id: int):
        """set integration_length for the specific channel

        Args:
            value (int): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """

    @Instrument.CheckParameterValueBool
    def _set_scope_hardware_averaging(self, value: float | str | bool, channel_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self.settings.scope_hardware_averaging[channel_id] = bool(value)
        self._set_device_scope_hardware_averaging(value=bool(value), channel_id=channel_id)

    @Instrument.CheckParameterValueBool
    def _set_hardware_demodulation(self, value: float | str | bool, channel_id: int):
        """set hardware demodulation

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self.settings.hardware_demodulation[channel_id] = bool(value)
        self._set_device_hardware_demodulation(value=bool(value), channel_id=channel_id)

    def _set_acquisition_mode(self, value: float | str | bool | AcquireTriggerMode, channel_id: int):
        """set acquisition_mode for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        if not isinstance(value, AcquireTriggerMode) and not isinstance(value, str):
            raise ValueError(f"value must be a string or AcquireTriggerMode. Current type: {type(value)}")
        self.settings.scope_acquire_trigger_mode[channel_id] = AcquireTriggerMode(value)
        self._set_device_acquisition_mode(mode=AcquireTriggerMode(value), channel_id=channel_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_integration_length(self, value: int | float | str | bool, channel_id: int):
        """set integration_length for the specific channel

        Args:
            value (float | str | bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.settings.integration_length[channel_id] = int(value)
        self._set_device_integration_length(value=int(value), channel_id=channel_id)
