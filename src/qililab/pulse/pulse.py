"""Pulse class."""
from dataclasses import InitVar, dataclass, field

import numpy as np
import numpy.typing as npt

from qililab.constants import YAML
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.pulse.pulse_shape.utils.pulse_shape_hashtable import PulseShapeHashTable


@dataclass
class Pulse:
    """Describes a single pulse to be added to waveform array."""

    @dataclass
    class PulseSettings:
        """Contains the settings of a Pulse.

        Args:
            start (float): Start time of the pulse (ns).
            duration (float): Pulse duration (ns).
            amplitude (float): Pulse digital amplitude (unitless) [0 to 1].
            frequency (float): Pulse intermediate frequency (Hz) [10e6 to 300e6].
            phase (float): Pulse phase.
            shape: (str): Pulse shape.
            offset_i (float): Optional pulse I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (float): Optional pulse Q offset (unitless). amplitude + offset should be in range [0 to 1].
            qubit_id (int): ID of the qubit.
        """

        readout: bool
        start: float
        duration: float
        amplitude: float
        frequency: float
        phase: float
        pulse_shape: PulseShape = field(init=False)
        shape: InitVar[dict]
        offset_i: float
        offset_q: float
        qubit_id: int
        index: int = field(
            init=False
        )  # FIXME: This index is only for Qblox (it points to the specific waveform in the used dictionary), find where to put it

        def __post_init__(self, shape: dict):
            """Cast pulse_shape attribute to its corresponding class."""
            self.pulse_shape = PulseShapeHashTable.get(name=shape[YAML.NAME])(**shape)

    settings: PulseSettings

    def __init__(self, settings: dict):
        self.settings = self.PulseSettings(**settings)

    def modulated_waveforms(self, resolution: float = 1.0) -> np.ndarray:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            NDArray: I and Q modulated waveforms.
        """
        envelope = self.envelope(resolution=resolution)
        envelopes = [np.real(envelope), np.imag(envelope)]
        time = np.arange(self.duration / resolution) * 1e-9 * resolution
        cosalpha = np.cos(2 * np.pi * self.frequency * time + self.phase)
        sinalpha = np.sin(2 * np.pi * self.frequency * time + self.phase)
        mod_matrix = np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
        return np.transpose(np.einsum("abt,bt->ta", mod_matrix, envelopes))

    def envelope(self, resolution: float):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse.
        """
        return self.pulse_shape.envelope(duration=self.duration, amplitude=self.amplitude, resolution=resolution)

    @property
    def start(self):
        """Pulse 'start' property.

        Returns:
            float: settings.start.
        """
        return self.settings.start

    @property
    def duration(self):
        """Pulse 'duration' property.

        Returns:
            float: settings.duration.
        """
        return self.settings.duration

    @property
    def amplitude(self):
        """Pulse 'amplitude' property.

        Returns:
            float: settings.amplitude.
        """
        return self.settings.amplitude

    @property
    def frequency(self):
        """Pulse 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency

    @property
    def phase(self):
        """Pulse 'phase' property.

        Returns:
            float: settings.phase.
        """
        return self.settings.phase

    @property
    def pulse_shape(self):
        """Pulse 'pulse_shape' property.

        Returns:
            PulseShape: settings.shape.
        """
        return self.settings.pulse_shape

    @property
    def offset_i(self):
        """Pulse 'offset_i' property.

        Returns:
            float: settings.offset_i
        """
        return self.settings.offset_i

    @property
    def offset_q(self):
        """Pulse 'offset_q' property.

        Returns:
            float: settings.offset_q.
        """
        return self.settings.offset_q

    @property
    def index(self):
        """Pulse 'index' property.

        Returns:
            int: settings.index.
        """
        return self.settings.index

    @index.setter
    def index(self, value: int):
        """Pulse 'index' property setter.

        Args:
            value (int): Value of the index.
        """
        self.settings.index = value

    @property
    def qubit_id(self):
        """Pulse 'qubit_id' property.

        Returns:
            int: settings.qubit_id.
        """
        return self.settings.qubit_id

    @property
    def readout(self):
        """Pulse 'readout' property.

        Returns:
            bool: settings.readout.
        """
        return self.settings.readout

    def __repr__(self):
        """Return string representation of the Pulse object."""
        return f"""P(s={self.start}, d={self.duration}, a={self.amplitude}, f={self.frequency}, p={self.phase}, {self.pulse_shape.name})"""

    def __eq__(self, other: object) -> bool:
        """Compare Pulse with another object.

        Args:
            other (object): Pulse object.
        """
        return (
            (
                self.amplitude == other.amplitude
                and self.duration == other.duration
                and self.frequency == other.frequency
                and self.offset_i == other.offset_i
                and self.offset_q == other.offset_q
                and self.phase == other.phase
                and self.pulse_shape == other.pulse_shape
            )
            if isinstance(other, Pulse)
            else NotImplementedError
        )
