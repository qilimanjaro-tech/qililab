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

from qpysequence import Program
from qpysequence import Sequence as QpySequence
from qpysequence import Weights
from qpysequence.program import Loop, Register
from qpysequence.program.instructions import Acquire, AcquireWeighed, Move

from qililab.config import logger
from qililab.instruments.awg_analog_digital_converter import AWGAnalogDigitalConverter
from qililab.instruments.awg_settings import AWGQbloxADCSequencer
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

    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list[QpySequence]:
        """Deletes the old acquisition data and compiles the ``PulseBusSchedule`` into an assembly program.

        This method skips compilation if the pulse schedule is in the cache. Otherwise, the pulse schedule is
        compiled and added into the cache.

        If the number of shots or the repetition duration changes, the cache will be cleared.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins

        Returns:
            list[QpySequence]: list of compiled assembly programs
        """
        # Clear cache if `nshots` or `repetition_duration` changes
        if nshots != self.nshots or repetition_duration != self.repetition_duration or num_bins != self.num_bins:
            self.nshots = nshots
            self.repetition_duration = repetition_duration
            self.num_bins = num_bins
            self.clear_cache()

        # Get all sequencers connected to port the schedule acts on
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=pulse_bus_schedule.port)
        # Separate the readout schedules by the qubit they act on
        qubit_schedules = pulse_bus_schedule.qubit_schedules()
        compiled_sequences = []
        for schedule in qubit_schedules:
            # Get the sequencer that acts on the same qubit as the schedule
            qubit_sequencers = [sequencer for sequencer in sequencers if sequencer.qubit == schedule.qubit]
            if len(qubit_sequencers) != 1:
                raise IndexError(
                    f"Expected 1 sequencer connected to port {schedule.port} and qubit {schedule.qubit}, "
                    f"got {len(qubit_sequencers)}"
                )
            sequencer = qubit_sequencers[0]
            if schedule != self._cache.get(sequencer.identifier):
                # If the schedule is not in the cache, compile it and add it to the cache
                sequence = self._compile(schedule, sequencer)
                compiled_sequences.append(sequence)
            else:
                # If the schedule is in the cache, delete the acquisition data (if uploaded) and add it to the list of
                # compiled sequences
                sequence_uploaded = self.sequences[sequencer.identifier][1]
                if sequence_uploaded:
                    self.device.delete_acquisition_data(sequencer=sequencer.identifier, name="default")
                compiled_sequences.append(self.sequences[sequencer.identifier][0])
        return compiled_sequences

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

                results.append(self.device.get_acquisitions(sequencer=sequencer.identifier)["default"]["acquisition"])
                self.device.sequencers[sequencer.identifier].sync_en(False)
                integration_lengths.append(sequencer.used_integration_length)

        return QbloxResult(integration_lengths=integration_lengths, qblox_raw_results=results)

    def _append_acquire_instruction(
        self, loop: Loop, bin_index: Register | int, sequencer_id: int, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""
        weighed_acq = self._get_sequencer_by_id(id=sequencer_id).weighed_acq_enabled

        acq_instruction = (
            AcquireWeighed(
                acq_index=0,
                bin_index=bin_index,
                weight_index_0=weight_regs[0],
                weight_index_1=weight_regs[1],
                wait_time=self._MIN_WAIT_TIME,
            )
            if weighed_acq
            else Acquire(acq_index=0, bin_index=bin_index, wait_time=self._MIN_WAIT_TIME)
        )
        loop.append_component(acq_instruction)

    def _init_weights_registers(self, registers: tuple[Register, Register], values: tuple[int, int], program: Program):
        """Initialize the weights `registers` to the `values` specified and place the required instructions in the
        setup block of the `program`."""
        move_0 = Move(0, registers[0])
        move_1 = Move(1, registers[1])
        setup_block = program.get_block(name="setup")
        setup_block.append_components([move_0, move_1], bot_position=1)

    def _generate_weights(self, sequencer: AWGQbloxADCSequencer) -> Weights:  # type: ignore
        """Generate acquisition weights.

        Returns:
            Weights: Acquisition weights.
        """
        weights = Weights()
        pair = ([float(w) for w in sequencer.weights_i], [float(w) for w in sequencer.weights_q])
        if (sequencer.path_i, sequencer.path_q) == (1, 0):
            pair = pair[::-1]  # swap paths
        weights.add_pair(pair=pair, indices=(0, 1))
        return weights

    def integration_length(self, sequencer_id: int):
        """QbloxPulsarQRM 'integration_length' property.
        Returns:
            int: settings.integration_length.
        """
        return cast(AWGQbloxADCSequencer, self.get_sequencer(sequencer_id)).integration_length

    @Instrument.CheckDeviceInitialized
    def setup(
        self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None, port_id: str | None = None
    ):
        """set a specific parameter to the instrument"""
        try:
            AWGAnalogDigitalConverter.setup(self, parameter=parameter, value=value, channel_id=channel_id)
        except ParameterNotFound:
            QbloxModule.setup(self, parameter=parameter, value=value, channel_id=channel_id, port_id=port_id)
