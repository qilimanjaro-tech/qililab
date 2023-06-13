"""Qblox pulsar QRM class"""
from typing import cast

from qpysequence import Sequence as QpySequence
from qpysequence.program import Loop, Program, Register
from qpysequence.program.instructions import Acquire, AcquireWeighed, Move
from qpysequence.weights import Weights

from qililab.config import logger
from qililab.instruments.awg_analog_digital_converter import AWGAnalogDigitalConverter
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseBusSchedule
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings.enums import InstrumentName, Parameter

from .sequencer import Sequencer


@InstrumentFactory.register
class QbloxQRM(QbloxModule, AWGAnalogDigitalConverter):
    """Qblox QRM class.

    Args:
        settings (QBloxQRMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QRM
    _scoping_sequencer: int | None = None

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        self._obtain_scope_sequencer()
        for sequencer in self.sequencers:
            sequencer_id = sequencer.identifier
            # Remove all acquisition data
            self.device.delete_acquisition_data(sequencer=sequencer_id, all=True)

    def _obtain_scope_sequencer(self):
        """Checks that only one sequencer is storing the scope and saves that sequencer in `_scoping_sequencer`

        Raises:
            ValueError: The scope can only be stores in one sequencer at a time.
        """
        for sequencer in self.sequencers:
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

    @Instrument.CheckDeviceInitialized
    def get_acquisitions(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        results = []
        integration_lengths = []
        for sequencer in self.sequencers:
            if sequencer.identifier in self.sequences:
                sequencer_id = sequencer.identifier
                flags = self.device.get_sequencer_state(
                    sequencer=sequencer_id, timeout=sequencer.parameters["sequence_timeout"]
                )
                logger.info("Sequencer[%d] flags: \n%s", sequencer_id, flags)
                self.device.get_acquisition_state(
                    sequencer=sequencer_id, timeout=sequencer.parameters["acquisition_timeout"]
                )

                if sequencer.parameters["scope_store_enabled"]:
                    self.device.store_scope_acquisition(sequencer=sequencer_id, name="default")

                results.append(self.device.get_acquisitions(sequencer=sequencer.identifier)["default"]["acquisition"])
                self.device.sequencers[sequencer.identifier].sync_en(False)
                integration_lengths.append(cast(int, sequencer.parameters["used_integration_length"]))

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

    def _generate_weights(self, sequencer: Sequencer) -> Weights:  # type: ignore
        """Generate acquisition weights.

        Returns:
            Weights: Acquisition weights.
        """
        weights = Weights()
        pair = (sequencer.parameters["weights_i"], sequencer.parameters["weights_q"])
        if (sequencer.path_i, sequencer.path_q) == (1, 0):
            pair = pair[::-1]  # swap paths
        weights.add_pair(pair=pair, indices=(0, 1))
        return weights

    def integration_length(self, sequencer_id: int):
        """QbloxPulsarQRM 'integration_length' property.
        Returns:
            int: settings.integration_length.
        """
        return self.sequencers[sequencer_id].parameters["integration_length"]

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set a specific parameter to the instrument"""
        try:
            AWGAnalogDigitalConverter.setup(self, parameter=parameter, value=value, channel_id=channel_id)
        except ParameterNotFound:
            QbloxModule.setup(self, parameter=parameter, value=value, channel_id=channel_id)
