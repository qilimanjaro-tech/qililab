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


from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.variable import Variable
from qililab.waveforms import IQPair, Waveform
from qililab.yaml import yaml


@yaml.register_class
class Play(Operation):
    def __init__(
        self,
        bus: str,
        waveform: Waveform | IQPair,
        wait_time: int | None = None,
        dwell: int | None = None,
        delay: int | None = None,
        repetitions: int | None = None,
        crosstalk: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: Waveform | IQPair = waveform
        self.wait_time: int | None = wait_time
        self.dwell: int | None = dwell
        self.delay: int | None = delay
        self.repetitions: int | None = repetitions
        self.crosstalk: bool = crosstalk

    def get_waveforms(self) -> tuple[Waveform, Waveform | None]:
        """Get the waveforms.

        Returns:
            tuple[Waveform, Waveform | None]: The waveforms as tuple. The second waveform can be None.
        """
        wf_I: Waveform = self.waveform.I if isinstance(self.waveform, IQPair) else self.waveform
        wf_Q: Waveform | None = self.waveform.Q if isinstance(self.waveform, IQPair) else None
        return wf_I, wf_Q

    def get_waveform_variables(self) -> set[Variable]:
        """Get a set of the variables used in the waveforms, if any.

        Returns:
            set[Variable]: The set of variables used in the waveforms.
        """
        wf_I, wf_Q = self.get_waveforms()
        variables_I = [attribute for attribute in wf_I.__dict__.values() if isinstance(attribute, Variable)]
        variables_Q = (
            [attribute for attribute in wf_Q.__dict__.values() if isinstance(attribute, Variable)] if wf_Q else []
        )
        return set(variables_I + variables_Q)

    def get_variables(self) -> set[Variable]:
        """Get a set of the variables used in operation, if any.

        Returns:
            set[Variable]: The set of variables used in operation.
        """
        return super().get_variables() | self.get_waveform_variables()


@yaml.register_class
class PlayWithCalibratedWaveform(Operation):
    def __init__(
        self,
        bus: str,
        waveform: str,
        wait_time: int | None = None,
        dwell: int | None = None,
        delay: int | None = None,
        repetitions: int | None = None,
        crosstalk: bool = True,
    ) -> None:
        super().__init__()
        self.bus: str = bus
        self.waveform: str = waveform
        self.wait_time: int | None = wait_time
        self.dwell: int | None = dwell
        self.delay: int | None = delay
        self.repetitions: int | None = repetitions
        self.crosstalk: bool = crosstalk
