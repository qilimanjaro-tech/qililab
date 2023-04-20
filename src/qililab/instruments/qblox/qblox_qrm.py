"""Qblox pulsar QRM class"""
from dataclasses import dataclass
from typing import Sequence, cast

from qpysequence import Sequence as QpySequence
from qpysequence.program import Loop, Register
from qpysequence.program.instructions import Acquire

from qililab.config import logger
from qililab.instruments.awg_analog_digital_converter import AWGAnalogDigitalConverter
from qililab.instruments.awg_settings.awg_qblox_adc_sequencer import AWGQbloxADCSequencer
from qililab.instruments.instrument import Instrument, ParameterNotFound
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

    def compile(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int) -> list[QpySequence]:
        """Deletes the old acquisition data and compiles the ``PulseBusSchedule`` into an assembly program.

        This method skips compilation if the pulse schedule is in the cache. Otherwise, the pulse schedule is
        compiled and added into the cache.

        If the number of shots or the repetition duration changes, the cache will be cleared.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration

        Returns:
            list[QpySequence]: list of compiled assembly programs
        """
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=pulse_bus_schedule.port)
        for sequencer in sequencers:
            if sequencer in self.sequences:
                sequence_uploaded = self.sequences[sequencer][1]
                if sequence_uploaded:
                    self.device.delete_acquisition_data(
                        sequencer=sequencer, name=self.acquisition_name(sequencer_id=sequencer)
                    )
        return super().compile(
            pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration
        )

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        return self.get_acquisitions()

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
        self.device.scope_acq_sequencer_select(sequencer_id)
        self.device.scope_acq_avg_mode_en_path0(value)
        self.device.scope_acq_avg_mode_en_path1(value)

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
        for sequencer in self.awg_sequencers:
            sequencer_id = sequencer.identifier
            flags = self.device.get_sequencer_state(
                sequencer=sequencer_id, timeout=cast(AWGQbloxADCSequencer, sequencer).sequence_timeout
            )
            logger.info("Sequencer[%d] flags: \n%s", sequencer_id, flags)
            self.device.get_acquisition_state(
                sequencer=sequencer_id, timeout=cast(AWGQbloxADCSequencer, sequencer).acquisition_timeout
            )

            if sequencer.scope_store_enabled:
                self.device.store_scope_acquisition(
                    sequencer=sequencer_id, name=self.acquisition_name(sequencer_id=sequencer_id)
                )

        results = [
            self.device.get_acquisitions(sequencer=sequencer.identifier)[
                self.acquisition_name(sequencer_id=sequencer.identifier)
            ]["acquisition"]
            for sequencer in self.awg_sequencers
        ]

        # FIXME: using the integration length of the first sequencer
        return QbloxResult(pulse_length=self.integration_length(sequencer_id=0), qblox_raw_results=results)

    def _append_acquire_instruction(self, loop: Loop, register: Register, sequencer_id: int):
        """Append an acquire instruction to the loop."""
        acquisition_idx = (
            0 if cast(AWGQbloxADCSequencer, self.get_sequencer(sequencer_id)).scope_hardware_averaging else 1
        )  # use binned acquisition if averaging is false
        loop.append_component(Acquire(acq_index=acquisition_idx, bin_index=register, wait_time=self._MIN_WAIT_TIME))

    def _generate_weights(self) -> dict:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return {}

    def integration_length(self, sequencer_id: int):
        """QbloxPulsarQRM 'integration_length' property.
        Returns:
            int: settings.integration_length.
        """
        return cast(AWGQbloxADCSequencer, self.get_sequencer(sequencer_id)).integration_length

    def acquisition_name(self, sequencer_id: int) -> str:
        """QbloxPulsarQRM 'acquisition_name' property:

        Returns:
            str: Name of the acquisition. Options are "single" or "binning".
        """
        return (
            "single"
            if cast(AWGQbloxADCSequencer, self.get_sequencer(sequencer_id)).scope_hardware_averaging
            else "binning"
        )

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        try:
            AWGAnalogDigitalConverter.setup(self, parameter=parameter, value=value, channel_id=channel_id)
        except ParameterNotFound:
            QbloxModule.setup(self, parameter=parameter, value=value, channel_id=channel_id)
