from qcodes import Instrument
from qcodes import validators as vals
from qpysequence.program import Loop, Program, Register
from qpysequence.program.instructions import Acquire, AcquireWeighed, Move
from qpysequence.weights import Weights

from qililab.config import logger
from qililab.drivers.interfaces import Digitiser
from qililab.result.qblox_results.qblox_result import QbloxResult

from .sequencer_qcm import SequencerQCM


class SequencerQRM(SequencerQCM, Digitiser):
    """Qililab's driver for QBlox-instruments digitiser Sequencer"""

    def __init__(
        self, parent: Instrument, name: str, seq_idx: int, sequence_timeout: int = 1, acquisition_timeout: int = 1
    ):
        """Initialise the instrument.
        Args:
            parent (Instrument): Parent for the sequencer instance.
            name (str): Sequencer name
            seq_idx (int): sequencer identifier index
            sequence_timeout (int): timeout to retrieve sequencer state in minutes
            acquisition_timeout (int): timeout to retrieve acquisition state in minutes
        """
        super().__init__(parent=parent, name=name, seq_idx=seq_idx)
        self.sequence_timeout = sequence_timeout
        self.acquisition_timeout = acquisition_timeout
        self.add_parameter(name="weights_i", vals=vals.Lists(), set_cmd=None, initial_value=[])
        self.add_parameter(name="weights_q", vals=vals.Lists(), set_cmd=None, initial_value=[])
        self.add_parameter(name="weighed_acq_enabled", vals=vals.Bool(), set_cmd=None, initial_value=False)

    def get_results(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        flags = self.device.get_sequencer_state(sequencer=self.seq_idx, timeout=self.sequence_timeout)
        logger.info("Sequencer[%d] flags: \n%s", self.seq_idx, flags)
        self.device.get_acquisition_state(sequencer=self.seq_idx, timeout=self.acquisition_timeout)
        if self.scope_store_enabled:
            self.device.store_scope_acquisition(sequencer=self.seq_idx, name="default")
        results = [self.device.get_acquisitions(sequencer=self.seq_idx)["default"]["acquisition"]]
        self.sync_en(False)
        integration_lengths = [self.used_integration_length]

        return QbloxResult(integration_lengths=integration_lengths, qblox_raw_results=results)

    def _init_weights_registers(self, registers: tuple[Register, Register], values: tuple[int, int], program: Program):
        """Initialize the weights `registers` to the `values` specified and place the required instructions in the
        setup block of the `program`."""
        move_0 = Move(values[0], registers[0])
        move_1 = Move(values[1], registers[1])
        setup_block = program.get_block(name="setup")
        setup_block.append_components([move_0, move_1], bot_position=1)

    def _generate_weights(self) -> Weights:  # type: ignore
        """Generate acquisition weights.

        Returns:
            Weights: Acquisition weights.
        """
        weights = Weights()
        pair = (self.weights_i, self.weights_q)
        if self.get("swap_paths"):
            pair = pair[::-1]  # swap paths
        weights.add_pair(pair=pair, indices=(0, 1))
        return weights

    def _append_acquire_instruction(
        self, loop: Loop, bin_index: Register | int, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""
        weighed_acq = self.weighed_acq_enabled

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
