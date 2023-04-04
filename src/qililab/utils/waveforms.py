"""Waveform class."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np


@dataclass
class Waveforms:
    """Waveform class that containg the I and Q modulated waveforms."""

    i: np.ndarray = field(default_factory=lambda: np.array([]))
    q: np.ndarray = field(default_factory=lambda: np.array([]))  # pylint: disable=invalid-name

    def add(self, imod: np.ndarray, qmod: np.ndarray):
        """Add i and q arrays to the waveforms.

        Args:
            imod (np.ndarray): I modulated waveform to add.
            qmod (np.ndarray): Q modulated waveform to add.
        """
        self.i = np.append(self.i, imod)
        self.q = np.append(self.q, qmod)

    @property
    def values(self):
        """Return the waveform i and q values.

        Returns:
            np.ndarray: Array containing the i and q waveform values.
        """
        return np.array([self.i, self.q])

    def __add__(self, other):
        """Add two Waveform objects."""
        if not isinstance(other, Waveforms):
            raise NotImplementedError
        self.i = np.append(self.i, other.i)
        self.q = np.append(self.q, other.q)
        return self

    def __len__(self):
        """Length of the object."""
        if len(self.i) != len(self.q):
            raise ValueError("Both I and Q waveforms must have the same length.")
        return len(self.i)

    @classmethod
    def from_composition(cls, waveforms_list: List[Waveforms]) -> Waveforms:
        """Creates a new Waveforms objects by superposing the Waveforms in a list of waveforms.

        Args:
            waveforms_list (List[Waveforms]): List with the waveforms to create the composition.

        Returns:
            Waveforms: Waveforms object containing the composition of the waveforms in the list.
        """
        i = sum(waveforms.i for waveforms in waveforms_list) / len(waveforms_list)
        q = sum(waveforms.q for waveforms in waveforms_list) / len(waveforms_list)
        return cls(np.array(i), np.array(q))
