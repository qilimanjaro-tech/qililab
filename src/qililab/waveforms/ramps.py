from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.special import erf

from qililab.yaml import yaml

from .waveform import Waveform


@yaml.register_class
class Ramps(Waveform):
    """Piecewise scalar waveform for point-to-point transitions.

    Each call to :meth:`add` appends a segment of ``duration`` total samples.
    The first ``sigma`` of those samples are the transition (linear ramp or
    erf S-curve); the remaining ``duration - sigma`` samples hold flat at the
    target value.  If ``duration <= sigma`` the entire segment is a transition.

    ``connection`` and ``sigma`` are set once at construction and apply to
    every segment uniformly.

    Args:
        start (float): Initial value of the waveform. Defaults to 0.
        connection (str): ``"linear"`` or ``"curved"`` (erf S-curve).
        sigma (int | None): Transition duration in samples.  ``None`` (default)
            means use the full segment duration — i.e. the whole segment is a
            transition with no flat hold.

    Examples:
        .. code-block:: python

            import qililab as ql

            # Flux pulse: 20-sample erf rise → 100-sample hold → 20-sample erf fall
            wf = ql.Ramps(start=0.0, connection="curved", sigma=20)
            wf.add(to=1.0, duration=20)
            wf.add(to=1.0, duration=100)
            wf.add(to=0.0, duration=20)

            # Same, built from arrays:
            wf = ql.Ramps.from_arrays(
                values=[0.0, 1.0, 1.0, 0.0],
                durations=[20, 100, 20],
                connection="curved",
                sigma=20,
            )
    """

    @dataclass
    class Segment:
        to: float
        duration: int

    def __init__(
        self,
        start: float = 0.0,
        connection: Literal["linear", "curved"] = "linear",
        sigma: int | None = None,
    ):
        self.start = start
        self.connection = connection
        self.sigma = sigma
        self.segments: list[Ramps.Segment] = []

    @classmethod
    def from_arrays(
        cls,
        values: list[float],
        durations: list[int],
        connection: Literal["linear", "curved"] = "linear",
        sigma: int | None = None,
    ) -> "Ramps":
        """Build a :class:`Ramps` from parallel keypoint and duration arrays.

        Args:
            values (list[float]): N+1 keypoint values — the first is the start,
                each subsequent value is the target of the matching segment.
            durations (list[int]): N segment durations (total samples per segment).
            connection (str): ``"linear"`` or ``"curved"``.
            sigma (int | None): Transition duration in samples (``None`` = full segment).

        Returns:
            Ramps: Configured instance.
        """
        ramps = cls(start=values[0], connection=connection, sigma=sigma)
        for to, dur in zip(values[1:], durations):
            ramps.add(to=to, duration=dur)
        return ramps

    def add(self, to: float, duration: int) -> "Ramps":
        """Append a segment ending at ``to`` with the given total ``duration``.

        Args:
            to (float): Target value at the end of this segment.
            duration (int): Total number of samples in this segment.

        Returns:
            Ramps: self, for chaining.
        """
        self.segments.append(self.Segment(to=to, duration=duration))
        return self

    def get_duration(self) -> int:
        return sum(s.duration for s in self.segments)

    def envelope(self, resolution: int = 1) -> np.ndarray:
        arrays = []
        current = self.start
        for seg in self.segments:
            n = seg.duration // resolution
            if self.sigma is None:
                sigma_n = n  # full segment is transition, no hold
            else:
                sigma_n = min(self.sigma // resolution, n)
            hold_n = n - sigma_n

            trans = self._transition(current, seg.to, sigma_n, self.connection)
            hold = np.full(hold_n, seg.to)
            arrays.append(np.concatenate([trans, hold]))
            current = seg.to

        return np.concatenate(arrays) if arrays else np.array([])

    @staticmethod
    def _transition(a: float, b: float, n: int, connection: str) -> np.ndarray:
        """Return ``n`` samples transitioning from ``a`` (exclusive) to ``b`` (inclusive)."""
        if n == 0:
            return np.array([])
        if connection == "linear":
            return np.linspace(a, b, n + 1)[1:]
        # "curved": symmetric erf S-curve.
        # Use n+2 points and drop both endpoints so the interior points are
        # symmetric around t=0 — the inflection point falls exactly in the
        # middle, giving equal flat regions at both ends of the S.
        t = np.linspace(-3, 3, n + 2)[1:-1]
        fraction = 0.5 * (erf(t) + 1)
        arr = a + (b - a) * fraction
        arr[-1] = b  # ensure the last sample is exactly the target
        return arr
