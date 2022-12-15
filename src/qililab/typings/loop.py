""" Loop Typings """
from dataclasses import asdict, dataclass
from functools import partial
from typing import Callable

import numpy as np

from qililab.constants import LOOP
from qililab.typings.enums import CallbackOrder
from qililab.typings.yaml_type import yaml


@dataclass
class LoopOptions:
    """Loop Options"""

    start: float | None = None
    stop: float | None = None
    num: int | None = None
    step: float | None = None
    logarithmic: bool = False
    channel_id: int | None = None
    values: np.ndarray | None = None
    callback: Callable | None = None
    callback_order: CallbackOrder | None = None
    callback_kwargs: dict | None = None

    class CheckStartStopDefined:
        """check start and stop to be defined when values is not specified."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "LoopOptions", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                ValueError: 'start' and 'stop' must be defined when no values are specified
            """
            if not isinstance(ref, dict) and ref.values is None and (ref.start is None or ref.stop is None):
                raise ValueError("'start' and 'stop' must be defined when no values array are passed as an input.")
            return self._method(ref, *args, **kwargs)

    @CheckStartStopDefined
    def __post_init__(self):
        """Initial Loop checks."""
        if self.values is not None:
            self._build_loop_from_values()
        if self.step is not None and self.num is not None and self.values is None:
            raise ValueError("'step' and 'num' arguments cannot be used together.")
        if self.logarithmic and self.num is None:
            raise ValueError("'logarithmic' requires 'num' argument to be specified.")

    def _build_loop_from_values(self):
        """Build a loop from specified values"""
        if len(self.values) == 0:
            raise ValueError("Values should be an array of at least one element")
        self.start = self.values[0]
        self.stop = self.values[-1]
        self.num = len(self.values)

    def __str__(self):
        """Returns a string representation of the loop options."""
        return yaml.dump(asdict(self), sort_keys=False)

    def to_dict(self) -> dict:
        """Convert class to a dictionary.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            LOOP.START: self.start,
            LOOP.STOP: self.stop,
            LOOP.NUM: self.num,
            LOOP.STEP: self.step,
            LOOP.LOGARITHMIC: self.logarithmic,
            LOOP.CHANNEL_ID: self.channel_id,
            LOOP.VALUES: list(self.values) if self.values is not None else None,
        }
