from dataclasses import dataclass, field

from qililab.waveforms.waveform import Waveform

from .operation import Operation


# TODO: dummy parameter class, remove this once we have a new parameter class
class Parameter:
    pass


@dataclass
class SetNCOFreqeuncy(Operation):
    bus: str  # TODO: are buses str?
    frequency: int


@dataclass
class SetGain(Operation):
    bus: str
    gain: float


# TODO: decide between the above and this one:
@dataclass
class Set(Operation):
    bus: str
    parameter: Parameter
    value: int | float | bool


# I think the later is better because the set method for the instruments is generally
# instrument.set(parameter, value) so it's straightforward to access it in future methods
# eg:
# from qililab.parameters.drivers import lo
# instrument = LocalOscillator(...)
# set_cmd = Set("bus", lo.frequency, 4e9)
# bus.instrument.set(set_cmd.parameter, set_cm.value)
