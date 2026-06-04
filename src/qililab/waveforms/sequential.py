from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from scipy.special import erf

from qililab.waveforms.waveform import Waveform
from qililab.yaml import yaml


@yaml.register_class
class SequentialWaveform(Waveform):
    """Waveform built by chaining sub-waveforms or scalar segment targets with configurable transitions."""

    @dataclass
    class WaveformContext:
        waveform: Waveform
        separation: int = field(default=0)
        connection_type: Literal["zeros", "line", "curved"] = field(default="line")

    @dataclass
    class SegmentContext:
        value: float
        separation: int = field(default=0)
        connection_type: Literal["line", "constant", "curved"] = field(default="line")

    def __init__(self):
        self.segments = []
        self._connection_handlers = {
            "constant": self._handle_constant,
            "zeros": self._handle_zeros,
            "line": self._handle_line,
            "curved": self._handle_curved,
        }

    def add_waveform(self, waveform: Waveform, separation: int = 0, connection_type: Literal["zeros", "line", "curved"] = "line"):
        self.segments.append(self.WaveformContext(waveform, separation, connection_type))

    def add_segment(self, value: float, separation: int = 0, connection_type: Literal["line", "constant", "curved"] = "line"):
        self.segments.append(self.SegmentContext(value, separation, connection_type))

    def __getitem__(self, key):
        return self.segments[key]

    def pop(self, key=-1):
        return self.segments.pop(key)

    def get_duration(self):
        return sum(
            ct.waveform.get_duration() + ct.separation
            if isinstance(ct, self.WaveformContext)
            else ct.separation + 1
            for ct in self.segments
        )

    def envelope(self, resolution=1):
        last_point = 0
        wf_arrays = np.array([])
        for segment in self.segments:
            if isinstance(segment, self.WaveformContext):
                curr_arr = self._get_waveform_wf(segment, last_point)
            elif isinstance(segment, self.SegmentContext):
                curr_arr = self._get_segment_wf(segment, last_point)
            last_point = curr_arr[-1]
            wf_arrays = np.concatenate((wf_arrays, curr_arr))
        return wf_arrays[::resolution]

    def _get_segment_wf(self, seg_ct: SegmentContext, last_point_prev: float):
        conn_arr = self._connection_handlers[seg_ct.connection_type](
            last_point_prev,
            seg_ct.value,
            seg_ct.separation,
        )
        return np.concatenate((conn_arr, np.array([seg_ct.value])))

    def _get_waveform_wf(self, wf_ct: WaveformContext, last_point_prev: float):
        wf_arr = wf_ct.waveform.envelope()
        if not wf_ct.separation:
            return wf_arr
        conn_arr = self._connection_handlers[wf_ct.connection_type](
            last_point_prev,
            wf_arr[0],
            wf_ct.separation,
        )
        return np.concatenate((conn_arr, wf_arr))

    @staticmethod
    def _handle_line(last_point_prev, first_point_curr, separation):
        return (first_point_curr - last_point_prev) * np.arange(0, 1, 1 / (separation + 1))[1:] + last_point_prev

    @staticmethod
    def _handle_zeros(_, __, separation):
        return np.zeros(separation)

    @staticmethod
    def _handle_constant(last_point_prev, _, separation):
        return np.ones(separation) * last_point_prev

    @staticmethod
    def _handle_curved(last_point_prev, first_point_curr, separation):
        if separation == 0:
            return np.array([])
        t = np.linspace(-3, 3, separation + 2)[1:-1]
        fraction = 0.5 * (erf(t) + 1)
        return last_point_prev + (first_point_curr - last_point_prev) * fraction
