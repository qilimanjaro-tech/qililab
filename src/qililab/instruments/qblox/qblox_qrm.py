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

    def _compile(self, pulse_bus_schedule: PulseBusSchedule, sequencer: int) -> QpySequence:
        """Deletes the old acquisition data, compiles the ``PulseBusSchedule`` into an assembly program and updates
        the cache and the saved sequences.
        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            sequencer (int): index of the sequencer to generate the program
        """
        if sequencer in self.sequences:
            sequence_uploaded = self.sequences[sequencer][1]
            if sequence_uploaded:
                self.device.delete_acquisition_data(sequencer=sequencer, name="default")
        return super()._compile(pulse_bus_schedule=pulse_bus_schedule, sequencer=sequencer)

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
        scope_already_stored = False
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
                if scope_already_stored:
                    raise ValueError("The scope can only be stored in one sequencer at a time.")
                scope_already_stored = True
                self.device.store_scope_acquisition(sequencer=sequencer_id, name="default")

        results = [
            self.device.get_acquisitions(sequencer=sequencer.identifier)["default"]["acquisition"]
            for sequencer in self.awg_sequencers
        ]

        # FIXME: using the integration length of the first sequencer
        return QbloxResult(pulse_length=self.integration_length(sequencer_id=0), qblox_raw_results=results)

    def _append_acquire_instruction(self, loop: Loop, register: Register, sequencer_id: int):
        """Append an acquire instruction to the loop."""
        loop.append_component(Acquire(acq_index=0, bin_index=register, wait_time=self._MIN_WAIT_TIME))

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

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        try:
            AWGAnalogDigitalConverter.setup(self, parameter=parameter, value=value, channel_id=channel_id)
        except ParameterNotFound:
            QbloxModule.setup(self, parameter=parameter, value=value, channel_id=channel_id)
