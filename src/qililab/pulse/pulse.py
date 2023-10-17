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

"""Pulse class."""
from dataclasses import dataclass

from qililab.constants import PULSE, RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.utils import Factory


@dataclass(frozen=True, eq=True)
class Pulse:
    """Describes a single pulse to be added to waveform array, which will be send through the lab buses to the chips.

    This class contains information about the pulse envelope shape, amplitude, phase, duration and frequency.

    Args:
        amplitude (float): Pulse's amplitude. Value normalized between 0 and 1.
        phase (float): Pulse's phase. Value in radians.
        duration (int): Pulse's duration. Value in ns.
        frequency (float): Pulse's frequency. Value in hertzs.
        pulse_shape (PulseShape): Pulse's envelope shape. Can be any of the different types of pulse shapes supported.
    """

    amplitude: float
    phase: float
    duration: int
    frequency: float
    pulse_shape: PulseShape

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0):
        """Pulse 'envelope' property.

        Args:
            amplitude (float, optional): Pulse's amplitude. Value normalized between 0 and 1. Defaults to None
            resolution (float): Pulse's resolution. Value normalized between 0 and 1.

        Returns:
            list[float]: Amplitudes of the envelope of the pulse. Max amplitude is fixed to 1.
        """
        if amplitude is None:
            amplitude = self.amplitude
        return self.pulse_shape.envelope(duration=self.duration, amplitude=amplitude, resolution=resolution)

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Pulse":
        """Loads Pulse object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Pulse object.

        Returns:
            Pulse: Loaded class.
        """
        local_dictionary = dictionary.copy()
        pulse_shape_dict = local_dictionary[PULSE.PULSE_SHAPE]
        local_dictionary[PULSE.PULSE_SHAPE] = Factory.get(name=pulse_shape_dict[RUNCARD.NAME]).from_dict(
            pulse_shape_dict
        )

        return cls(**local_dictionary)

    def to_dict(self):
        """Returns dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {
            PULSE.AMPLITUDE: self.amplitude,
            PULSE.FREQUENCY: self.frequency,
            PULSE.PHASE: self.phase,
            PULSE.DURATION: self.duration,
            PULSE.PULSE_SHAPE: self.pulse_shape.to_dict(),
        }

    def label(self) -> str:
        """Returns short string representation of the Pulse object.

        Returns:
            str: String representation of the Pulse object.
        """
        return f"{str(self.pulse_shape)} - {self.duration}ns"
