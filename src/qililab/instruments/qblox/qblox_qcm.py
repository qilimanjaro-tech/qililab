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

"""Qblox QCM class"""
from dataclasses import dataclass

from qpysequence.program import Loop, Register
from qpysequence.weights import Weights

from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils.instrument_factory import InstrumentFactory
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings.enums import InstrumentName


@InstrumentFactory.register
class QbloxQCM(QbloxModule):
    """Qblox QCM class.

    Args:
        settings (QBloxQCMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QCM

    @dataclass
    class QbloxQCMSettings(QbloxModule.QbloxModuleSettings):
        """Contains the settings of a specific pulsar."""

    settings: QbloxQCMSettings

    def _generate_weights(self, sequencer: AWGQbloxSequencer) -> Weights:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return Weights()

    def _append_acquire_instruction(
        self, loop: Loop, bin_index: Register | int, sequencer_id: int, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        raise NotImplementedError
