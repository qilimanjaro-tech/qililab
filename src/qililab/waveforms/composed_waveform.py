from __future__ import annotations

import warnings
from copy import copy
from dataclasses import dataclass
from typing import Literal, Optional, cast

import numpy as np

from qililab.waveforms.waveform import Waveform
from qililab.yaml import yaml


@yaml.register_class
class ComposedWaveform(Waveform):
    """Waveform composed by summing sub-waveforms placed at specific sample offsets.

    Args:
        duration (int | None): Output length in samples. When None, inferred from placed waveforms.
        snap (str | None): How the duration window anchors to the rendered content when ``duration`` is set.
            ``None`` (default) behaves like ``"beginning"``. Has no effect when ``duration`` is not set —
            a warning is raised if a non-None value is given without ``duration``.

            - ``"beginning"`` / ``None``: window starts at the first waveform's start, extends forward.
            - ``"termination"``: window ends at the last waveform's end, extends backward.
            - ``"start"`` / ``"center"`` / ``"end"``: window anchors to the at=0 reference point,
              mirroring the ``align`` semantics of :meth:`add`.

    Examples:
        .. code-block:: python

            import qililab as ql

            cw = ql.ComposedWaveform()
            cw.add(ql.Gaussian(amplitude=1.0, duration=100, num_sigmas=4), at=0)
            cw.add(ql.Square(amplitude=0.5, duration=50), at=100)
    """

    @dataclass
    class WaveformContext:
        waveform: Waveform
        at: int = 0
        align: Literal["start", "center", "end"] = "start"

        def start_sample(self) -> int:
            dur = self.waveform.get_duration()
            if self.align == "center":
                return self.at - dur // 2
            if self.align == "end":
                return self.at - dur
            return self.at  # "start"

    def __init__(
        self,
        duration: int | None = None,
        snap: Optional[Literal["beginning", "start", "center", "end", "termination"]] = None,
        default_aligment: Literal["start", "center", "end"] = "start"
    ):
        if snap is not None and duration is None:
            warnings.warn(
                f"snap={snap!r} has no effect when duration is not set.",
                UserWarning,
                stacklevel=2,
            )
        self.duration = duration
        self.snap = snap
        self.waveforms: list[ComposedWaveform.WaveformContext] = []
        self.default_aligment = default_aligment
        self._added: float = 0.0
        self._scaled: float = 1.0

    def add(self, waveform: Waveform, at: int = 0, align: Optional[Literal["start", "center", "end"]] = None) -> "ComposedWaveform":
        """Place a sub-waveform at sample offset ``at``.

        Args:
            waveform (Waveform): The waveform to place.
            at (int): Sample offset reference point.
            align (str): How ``at`` aligns with the waveform — ``"start"``, ``"center"``, or ``"end"``.

        Returns:
            ComposedWaveform: self, for chaining.
        """
        wf_aligment = align or self.default_aligment
        self.waveforms.append(self.WaveformContext(waveform=waveform, at=at, align=wf_aligment))
        return self

    def _start_offset(self) -> int:
        """Negative shift to align the earliest waveform's start to sample 0."""
        if not self.waveforms:
            return 0
        return min(0, min(w_context.start_sample() for w_context in self.waveforms))

    def get_duration(self) -> int:
        if self.duration is not None:
            return self.duration
        if not self.waveforms:
            return 0
        offset = self._start_offset()
        return max(w_context.start_sample() + w_context.waveform.get_duration() for w_context in self.waveforms) - offset

    def _full_envelope(self) -> np.ndarray:
        """Render all sub-waveforms into one array without any duration cropping."""
        offset = self._start_offset()
        n = max(
            w_context.start_sample() + w_context.waveform.get_duration()
            for w_context in self.waveforms
        ) - offset
        array = np.zeros(n)
        for w_context in self.waveforms:
            start = w_context.start_sample() - offset
            wf_env = w_context.waveform.envelope()
            array[start: start + len(wf_env)] += wf_env
        return array

    def _handle_duration(self, envelope: np.ndarray, reference_idx: int) -> np.ndarray:
        """Crop or zero-pad ``envelope`` to ``self.duration`` samples using ``self.snap``.

        Args:
            envelope (np.ndarray): Full rendered envelope (no duration constraint).
            reference_idx (int): Position of the at=0 reference point within ``envelope``.
                Used only for ``"start"``, ``"center"``, and ``"end"`` snap modes.

        Returns:
            np.ndarray: Array of exactly ``self.duration`` samples.
        """
        dur = cast("int", self.duration)
        n = len(envelope)

        if self.snap in (None, "beginning"):
            start, end = 0, dur
        elif self.snap == "termination":
            start, end = n - dur, n
        elif self.snap == "start":
            start, end = reference_idx, reference_idx + dur
        elif self.snap == "center":
            start, end = reference_idx - dur // 2, reference_idx - dur // 2 + dur
        else:  # "end"
            start, end = reference_idx - dur, reference_idx

        result = np.zeros(dur)
        src_start = max(0, start)
        src_end = min(n, end)
        if src_end > src_start:
            dst_start = src_start - start
            result[dst_start: dst_start + (src_end - src_start)] = envelope[src_start:src_end]
        return result

    def envelope(self, resolution: int = 1) -> np.ndarray:
        if not self.waveforms:
            return np.zeros((self.duration or 0) // resolution)

        offset = self._start_offset()
        result = self._full_envelope()

        if self.duration is not None:
            result = self._handle_duration(result, reference_idx=-offset)

        return result[::resolution] * self._scaled + self._added

    def sum(self, other: float | int | np.floating | Waveform, return_copy = False):
        obj = copy(self) if return_copy else self
        if isinstance(other, ComposedWaveform): #TODO: warn context disapearence
            obj.waveforms += [*obj.waveforms, *other.waveforms]
        elif isinstance(other, Waveform):
            obj.add(other)
        elif isinstance(other, float | int | np.floating):
            obj._added += other
        else:
            raise NotImplementedError(f"+, - operators not supported for `ComposedWaveform` and `{other.__class__.__name__}`")
        return obj

    def mult(self, other: float | int | np.floating, return_copy = False):
        obj = copy(self) if return_copy else self
        if isinstance(other, float | int | np.floating):
            obj._scaled *= other
            obj._added += other
        else:
            raise NotImplementedError(f"*, / operators not supported for `ComposedWaveform` and `{other.__class__.__name__}`")
        return obj
