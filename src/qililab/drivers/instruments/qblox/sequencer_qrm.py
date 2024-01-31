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

"""This file contains the code of the sequencer of the Qblox QRM."""
from qcodes import Instrument
from qcodes import validators as vals
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Loop, Program, Register
from qpysequence.program.instructions import Acquire, AcquireWeighed, Move
from qpysequence.weights import Weights

from qililab.config import logger
from qililab.drivers.instruments.instrument_driver_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import Digitiser
from qililab.result.qblox_results.qblox_result import QbloxResult

from .sequencer_qcm import SequencerQCM


@InstrumentDriverFactory.register
class SequencerQRM(SequencerQCM, Digitiser):
    """Qililab's driver for QBlox-instruments digitiser Sequencer

    Args:
        parent (Instrument): Parent for the sequencer instance.
        name (str): Sequencer name
        seq_idx (int): sequencer identifier index
        sequence_timeout (int): timeout to retrieve sequencer state in minutes
        acquisition_timeout (int): timeout to retrieve acquisition state in minutes
    """

    def __init__(self, parent: Instrument, name: str, seq_idx: int):
        super().__init__(parent=parent, name=name, seq_idx=seq_idx)
        self.add_parameter(name="sequence_timeout", vals=vals.Ints(), set_cmd=None, initial_value=1)
        self.add_parameter(name="acquisition_timeout", vals=vals.Ints(), set_cmd=None, initial_value=1)
        self.add_parameter(name="weights_i", vals=vals.Lists(), set_cmd=None, initial_value=[])
        self.add_parameter(name="weights_q", vals=vals.Lists(), set_cmd=None, initial_value=[])
        self.add_parameter(name="weighed_acq_enabled", vals=vals.Bool(), set_cmd=None, initial_value=False)

    def get_results(self) -> QbloxResult:
        """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        flags = self.parent.get_sequencer_state(sequencer=self.seq_idx, timeout=self.get("sequence_timeout"))
        logger.info("Sequencer[%d] flags: \n%s", self.seq_idx, flags)
        self.parent.get_acquisition_state(sequencer=self.seq_idx, timeout=self.get("acquisition_timeout"))
        if self.parent.get("scope_acq_sequencer_select") == self.seq_idx:
            self.parent.store_scope_acquisition(sequencer=self.seq_idx, name="default")
        result = self.parent.get_acquisitions(sequencer=self.seq_idx)["default"]["acquisition"]

        integration_length = (
            len(self.get("weights_i")) if self.get("weighed_acq_enabled") else self.get("integration_length_acq")
        )

        self.set("sync_en", False)
        return QbloxResult(integration_lengths=[integration_length], qblox_raw_results=[result])

    def _init_weights_registers(self, registers: tuple[Register, Register], values: tuple[int, int], program: Program):
        """Initialize the weights `registers` to the `values` specified and place the required instructions in the
        setup block of the `program`."""
        move_0 = Move(values[0], registers[0])
        move_1 = Move(values[1], registers[1])
        setup_block = program.get_block(name="setup")
        setup_block.append_components([move_0, move_1], bot_position=1)

    def _generate_acquisitions(self, num_bins: int) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "default" with
        index = 0.

        Args:
            num_bins (int): number of bins

        Returns:
            Acquisitions: Acquisitions object.
        """
        acquisitions = Acquisitions()
        acquisitions.add(name="default", num_bins=num_bins, index=0)

        return acquisitions

    def _generate_weights(self) -> Weights:
        """Generate acquisition weights.

        Returns:
            Weights: Acquisition weights.
        """
        weights = Weights()
        if len(self.get("weights_i")) > 0 and len(self.get("weights_q")) > 0:
            pair = (self.get("weights_i"), self.get("weights_q"))
            weights.add_pair(pair=pair, indices=(0, 1))
        return weights

    def _append_acquire_instruction(
        self, loop: Loop, bin_index: Register | int, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""
        weighed_acq = self.get("weighed_acq_enabled")

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
