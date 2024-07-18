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

from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.variable import Variable
from qililab.waveforms import IQPair, Waveform
from qililab.yaml import yaml


@yaml.register_class
@dataclass
class Play(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    waveform: Waveform | IQPair
    wait_time: int | None = None  # TODO: remove this in clean fix

    def get_waveforms(self) -> tuple[Waveform, Waveform | None]:
        """Get the waveforms.

        Returns:
            tuple[Waveform, Waveform | None]: The waveforms as tuple. The second waveform can be None.
        """
        wf_I: Waveform = self.waveform.I if isinstance(self.waveform, IQPair) else self.waveform
        wf_Q: Waveform | None = self.waveform.Q if isinstance(self.waveform, IQPair) else None
        return wf_I, wf_Q

    def get_waveform_I_variables(self) -> set[Variable]:
        wf_I, _ = self.get_waveforms()
        return wf_I.get_variables()

    def get_waveform_Q_variables(self) -> set[Variable]:
        _, wf_Q = self.get_waveforms()
        return wf_Q.get_variables() if wf_Q else set()

    def get_waveform_variables(self) -> set[Variable]:
        """Get a set of the variables used in the waveforms, if any.

        Returns:
            set[Variable]: The set of variables used in the waveforms.
        """
        return self.get_waveform_I_variables() | self.get_waveform_Q_variables()

    def replace_variables(self, variables: dict[Variable, int | float]) -> "Play":
        """Replace variables in the waveform with their values from the provided variable_map.

        Args:
            variable_map (dict[Variable, Union[int, float]]): Mapping of variables to their values.

        Returns:
            Waveform: A new waveform with variables replaced.
        """
        wf_I, wf_Q = self.get_waveforms()
        wf_I.replace_variables(variables=variables)
        if wf_Q is not None:
            wf_Q.replace_variables(variables=variables)

        return super().replace_variables(variables=variables)  # type: ignore[return-value]


@yaml.register_class
@dataclass
class PlayWithCalibratedWaveform(Operation):  # pylint: disable=missing-class-docstring
    bus: str
    waveform: str
    wait_time: int | None = None
