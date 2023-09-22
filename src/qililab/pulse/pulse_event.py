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

"""PulseEvent class."""
from dataclasses import dataclass, field

import numpy as np

from qililab.constants import PULSEEVENT
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_distortion import PulseDistortion
from qililab.utils import Waveforms
from qililab.utils.signal_processing import modulate


@dataclass
class PulseEvent:
    """Object representing a :class:`Pulse` starting at a certain time, and with its corresponding :class:`PulseDistortion`'s.

    This class will receive a :class:`Pulse` object, a start time for it, a list of the :class:`PulseDistortion`'s that such
    pulse will get applied and a qubit alias to where such pulse will be sent.
    It provides functionality for instrument to generate the waveforms and modulation of pulses.

    Args:
        pulse (Pulse): :class:`Pulse` contained in the PulseEvent.
        start_time (int): Start time of the pulse. Value in ns.
        pulse_distortion (list[PulseDistortion]: List of :class:`PulseDistortion` applied to the pulse.
        qubit (int, optional): the qubit alias. Defaults to None.
    """

    pulse: Pulse
    start_time: int
    pulse_distortions: list[PulseDistortion] = field(default_factory=list)
    qubit: int | None = None

    @property
    def duration(self) -> int:
        """Duration of the pulse in ns."""
        return self.pulse.duration

    @property
    def end_time(self) -> int:
        """End time of the pulse in ns."""
        return self.start_time + self.duration

    @property
    def frequency(self) -> float:
        """Frequency of the pulse in Hz."""
        return self.pulse.frequency

    @property
    def phase(self) -> float:
        """Phase of the pulse."""
        return self.pulse.phase

    def modulated_waveforms(self, resolution: float = 1.0) -> Waveforms:
        """Applies digital quadrature amplitude modulation (QAM) to the envelope.

        Args:
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.

        Returns:
            Waveforms: I and Q modulated waveforms.
        """
        envelope = self.envelope(resolution=resolution)
        i = np.real(envelope)
        q = np.imag(envelope)

        # Convert pulse relative phase to absolute phase by adding the absolute phase at t=start_time.
        phase_offset = self.phase + 2 * np.pi * self.frequency * self.start_time * 1e-9
        imod, qmod = modulate(i=i, q=q, frequency=self.frequency, phase_offset=phase_offset)

        return Waveforms(i=imod.tolist(), q=qmod.tolist())

    def envelope(self, amplitude: float | None = None, resolution: float = 1.0) -> np.ndarray:
        """Returns the pulse envelope with the corresponding distortions applied.

        Args:
            amplitude (float, optional): Amplitude of the envelope. Defaults to None.
            resolution (float, optional): The resolution of the pulse in ns. Defaults to 1.0.

        Returns:
            np.ndarray: Distorted envelope of the pulse.
        """
        envelope = self.pulse.envelope(amplitude=amplitude, resolution=resolution)

        for distortion in self.pulse_distortions:
            envelope = distortion.apply(envelope)

        return envelope

    @classmethod
    def from_dict(cls, dictionary: dict) -> "PulseEvent":
        """Loads PulseEvent object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseEvent object.

        Returns:
            PulseEvent: PulseEvent Loaded class.
        """
        local_dictionary = dictionary.copy()
        pulse_settings = local_dictionary[PULSEEVENT.PULSE]
        local_dictionary[PULSEEVENT.PULSE] = Pulse.from_dict(pulse_settings)

        pulse_distortions_list: list[PulseDistortion] = []

        if PULSEEVENT.PULSE_DISTORTIONS in local_dictionary:
            pulse_distortions_list.extend(
                PulseDistortion.from_dict(pulse_distortion_dict)
                for pulse_distortion_dict in local_dictionary[PULSEEVENT.PULSE_DISTORTIONS]
            )

        local_dictionary[PULSEEVENT.PULSE_DISTORTIONS] = pulse_distortions_list

        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse event.
        """
        return {
            PULSEEVENT.PULSE: self.pulse.to_dict(),
            PULSEEVENT.START_TIME: self.start_time,
            PULSEEVENT.PULSE_DISTORTIONS: [distortion.to_dict() for distortion in self.pulse_distortions],
            "qubit": self.qubit,
        }

    def __lt__(self, other: "PulseEvent") -> bool:
        """Returns True if and only if self.start_time is less than other.start_time

        Args:
            other (PulseEvent): PulseEvent to compare.

        Returns:
            bool: Comparison evaluation.
        """
        return self.start_time < other.start_time
