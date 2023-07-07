"""Basic operations that the qprogram can perform"""

from dataclasses import dataclass

from qililab.waveforms.waveform import Waveform

from .operation import Operation


@dataclass
class Acquire(Operation):
    bus: str  # TODO: should bus be a str or a bus?
    weights: list | None


@dataclass
class Play(Operation):
    bus: str
    waveform: Waveform


@dataclass
class Sync(Operation):
    buses: list[str]


@dataclass
class Wait(Operation):
    bus: str
    time: int
