
from typing import Literal
from dataclasses import dataclass, field
import numpy as np

from qililab.waveforms.waveform import Waveform
from qililab.yaml import yaml


@yaml.register_class
class ComposedWaveform(Waveform):

    @dataclass
    class WaveformContext:
        waveform: Waveform
        move: int = field(default=0)

        def _get_time_lim(self, order):
            if order == "left":
                return (
                    self.move + self.waveform.get_duration(),
                    self.move
                )
            if order == "right":
                return (
                    self.move,
                    self.move - self.waveform.get_duration()
                )
            if order == "centered":
                return (
                    self.move + self.waveform.get_duration() / 2,
                    self.move - self.waveform.get_duration() / 2
                )

    def __init__(self, *wf: tuple[Waveform], order: Literal["centered", "left", "right"] = "left", duration: int | None = None):
        self.order = order
        self.duration = duration
        self.waveforms: list[ComposedWaveform.WaveformContext] = []
        for waveform in wf:
            self.add_waveform(waveform=waveform)

        self._added: float = 0.0
        self._scaled: float = 1.0

    def add_waveform(self, waveform: Waveform, move: int = 0):
        self.waveforms.append(self.WaveformContext(waveform=waveform, move=move))

    def get_duration(self):
        if not self.duration:
            lims = self._time_lims()
            self.duration = lims[0] - lims[1]
        return self.duration
    
    def _time_lims(self):
        min_max_times = np.array([wf_context._get_time_lim for wf_context in self.waveforms])
        return np.max(min_max_times[:, 0]), np.min(min_max_times[:, 1])

    def envelope(self, resolution = 1):
        duration = self.get_duration()
        array = np.ones(duration // resolution) * self._added
        _, lim_min = self._time_lims

        def _idx_from_time_lims(max_time, min_time):
            return slice((min_time - lim_min) // resolution, (max_time - lim_min) // resolution)

        for wf_context in self.waveforms:
            array[_idx_from_time_lims] += wf_context.waveform.envelope(resolution=resolution)
        
        array *= self._scaled
        return array

    def __sum__(self, other):
        self._added += other
        
    
    def __sub__(self, other):
        self._added -= other

    def __mul__(self, other):
        self._scaled