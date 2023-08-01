from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation
from qililab.qprogram.variable import Variable
from qililab.waveforms import IQPair, Waveform


@dataclass(frozen=True)
class Play(Operation):
    bus: str
    waveform: Waveform | IQPair

    def get_waveforms(self) -> tuple[Waveform, Waveform | None]:
        wf_I: Waveform = self.waveform.I if isinstance(self.waveform, IQPair) else self.waveform
        wf_Q: Waveform | None = self.waveform.Q if isinstance(self.waveform, IQPair) else None
        return wf_I, wf_Q

    def get_variables(self) -> set[Variable]:
        wf_I, wf_Q = self.get_waveforms()
        variables_I = [attribute for attribute in wf_I.__dict__.values() if isinstance(attribute, Variable)]
        variables_Q = (
            [attribute for attribute in wf_Q.__dict__.values() if isinstance(attribute, Variable)] if wf_Q else []
        )
        return set(variables_I + variables_Q)
