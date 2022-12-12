"""Qblox pulsar QRM class"""
from dataclasses import dataclass
from pathlib import Path

from qpysequence.program import Loop, Register
from qpysequence.program.instructions import Acquire

from qililab.config import logger
from qililab.instruments.analog_digital_converter import AWGAnalogDigitalConverter
from qililab.instruments.instrument import Instrument
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseBusSchedule
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings.enums import AcquireTriggerMode, InstrumentName, Parameter


@InstrumentFactory.register
class QbloxQRM(QbloxModule, AWGAnalogDigitalConverter):
    """Qblox QRM class.

    Args:
        settings (QBloxQRMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QRM
    _NUM_SEQUENCERS: int = 1

    @dataclass
    class QbloxQRMSettings(
        QbloxModule.QbloxModuleSettings, AWGAnalogDigitalConverter.AWGAnalogDigitalConverterSettings
    ):
        """Contains the settings of a specific QRM."""

    settings: QbloxQRMSettings

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        for channel_id in range(self.num_sequencers):
            self._set_integration_length(value=self.settings.integration_length[channel_id], channel_id=channel_id)
            self._set_acquisition_mode(
                value=self.settings.scope_acquire_trigger_mode[channel_id], channel_id=channel_id
            )
            self._set_scope_hardware_averaging(
                value=self.settings.scope_hardware_averaging[channel_id], channel_id=channel_id
            )
            self._set_hardware_demodulation(
                value=self.settings.hardware_demodulation[channel_id], channel_id=channel_id
            )

    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetitition duration
            path (Path): path to save the program to upload
        """
        if (pulse_bus_schedule, nshots, repetition_duration) == self._cache:
            # TODO: Right now the only way of deleting the acquisition data is to re-upload the acquisition dictionary.
            for seq_idx in range(self.num_sequencers):
                self.device._delete_acquisition(  # pylint: disable=protected-access
                    sequencer=seq_idx, name=self.acquisition_name(sequencer=seq_idx)
                )
                acquisition = self._generate_acquisitions(sequencer=seq_idx)
                self.device._add_acquisitions(  # pylint: disable=protected-access
                    sequencer=seq_idx, acquisitions=acquisition.to_dict()
                )
        super().generate_program_and_upload(
            pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, path=path
        )

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        return self.get_acquisitions()

    def _set_device_hardware_demodulation(self, value: bool, channel_id: int):
        """set hardware demodulation

        Args:
            value (bool): value to update
            channel_id (int): sequencer to update the value
        """
        self.device.sequencers[channel_id].demod_en_acq(value)

    def _set_device_acquisition_mode(self, mode: AcquireTriggerMode, channel_id: int):
        """set acquisition_mode for the specific channel

        Args:
            mode (AcquireTriggerMode): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not string
        """
        self.device.scope_acq_sequencer_select(channel_id)
        self.device.scope_acq_trigger_mode_path0(mode.value)
        self.device.scope_acq_trigger_mode_path1(mode.value)

    def _set_device_integration_length(self, value: int, channel_id: int):
        """set integration_length for the specific channel

        Args:
            value (int): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.device.sequencers[channel_id].integration_length_acq(value)

    def _set_device_scope_hardware_averaging(self, value: bool, channel_id: int):
        """set scope_hardware_averaging for the specific channel

        Args:
            value (bool): value to update
            channel_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self.device.scope_acq_sequencer_select(channel_id)
        self.device.scope_acq_avg_mode_en_path0(value)
        self.device.scope_acq_avg_mode_en_path1(value)

    def _set_nco(self, channel_id: int):
        """Enable modulation/demodulation of pulses and setup NCO frequency."""
        super()._set_nco(channel_id=channel_id)
        if self.settings.hardware_demodulation[channel_id]:
            self._set_hardware_demodulation(value=self.settings.hardware_modulation[channel_id], channel_id=channel_id)

    @Instrument.CheckDeviceInitialized
    def get_acquisitions(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        for seq_idx in range(self.num_sequencers):
            flags = self.device.get_sequencer_state(sequencer=seq_idx, timeout=self.sequence_timeout[seq_idx])
            logger.info("Sequencer flags: %s", flags)
            self.device.get_acquisition_state(sequencer=seq_idx, timeout=self.acquisition_timeout[seq_idx])

            if self.scope_store_enabled[seq_idx]:
                self.device.store_scope_acquisition(sequencer=0, name=self.acquisition_name(sequencer=seq_idx))

        results = [
            self.device.get_acquisitions(sequencer=seq_idx)[self.acquisition_name(sequencer=seq_idx)]["acquisition"]
            for seq_idx in range(self.num_sequencers)
        ]

        return QbloxResult(pulse_length=self.integration_length, qblox_raw_results=results)

    def _append_acquire_instruction(self, loop: Loop, register: Register):
        """Append an acquire instruction to the loop."""
        # FIXME: scope_hardware_averaging it is a list now, it should return the desired channel
        acquisition_idx = 0 if self.scope_hardware_averaging[0] else 1  # use binned acquisition if averaging is false
        loop.append_component(Acquire(acq_index=acquisition_idx, bin_index=register, wait_time=self._MIN_WAIT_TIME))

    def _generate_weights(self) -> dict:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return {}

    @property
    def scope_store_enabled(self):
        """QbloxPulsarQRM 'scope_store_enabled' property.


        Returns:
            bool: settings.scope_store_enabled."""
        return self.settings.scope_store_enabled

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
    def final_wait_time(self):
        """QbloxPulsarQRM 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return self.acquisition_delay_time

    @property
    def integration(self):
        """QbloxPulsarQRM 'integration' property.

        Returns:
            bool: Integration flag.
        """
        return self.settings.hardware_integration

    def acquisition_name(self, sequencer: int) -> str:
        """QbloxPulsarQRM 'acquisition_name' property:

        Returns:
            str: Name of the acquisition. Options are "single" or "binning".
        """
        return "single" if self.scope_hardware_averaging[sequencer] else "binning"

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        try:
            AWGAnalogDigitalConverter.setup(self, parameter=parameter, value=value, channel_id=channel_id)
        except ValueError:
            QbloxModule.setup(self, parameter=parameter, value=value, channel_id=channel_id)
