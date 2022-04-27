"""Pulse class."""
from dataclasses import dataclass, field

from qililab.instruments.pulse.utils.pulse_shape_hashtable import PulseShapeHashTable
from qililab.typings import PulseShapeOptions


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
        """

        start: float
        duration: float
        amplitude: float
        frequency: float
        phase: float
        shape: PulseShapeOptions
        offset_i: float
        offset_q: float
        index: int = field(init=False)  # FIXME: This index is only for Qblox, find where to put it

        def __post_init__(self):
            """Cast 'shape' attribute to its corresponding Enum class."""
            self.shape = PulseShapeOptions(self.shape)

    settings: PulseSettings

    def __init__(self, settings: dict):
        self.settings = self.PulseSettings(**settings)

    @property
    def envelope(self):
        """Pulse 'envelope' property.

        Returns:
            List[float]: Amplitudes of the envelope of the pulse.
        """
        pulse_shape = PulseShapeHashTable.get(name=self.shape)
        return pulse_shape.envelope

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
    def shape(self):
        """Pulse 'shape' property.

        Returns:
            PulseShapeOptions: settings.shape.
        """
        return self.settings.shape

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
