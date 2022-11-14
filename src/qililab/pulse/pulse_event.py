"""PulseEvent class."""
from dataclasses import dataclass, field

from qililab.constants import PULSEEVENT, RUNCARD
from qililab.pulse.pulse import Pulse
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.typings.enums import PulseName
from qililab.utils.waveforms import Waveforms


@dataclass(order=True)
class PulseEvent:
    """Describes a single pulse with a start time."""
    sort_index: int = field(init=False, repr=False)
    
    pulse: Pulse
    start_time: int
    end_time: int = field(init=False, repr=False)
    duration: int = field(init=False, repr=False)

    def __post_init__(self):
        self.sort_index = self.start_time
        self.duration = self.pulse.duration
        self.end_time = self.start_time + self.duration

    def modulated_waveforms(self, frequency: float, resolution: float = 1.0) -> Waveforms:
        return self.pulse.modulated_waveforms(frequency=frequency, resolution=resolution, start_time=self.start_time)

    @property
    def start(self):
        """Pulse 'start' property.

        Raises:
            ValueError: Is start time is not defined.

        Returns:
            int: Start time of the pulse.
        """
        return self.start_time

    def to_dict(self):
        """Return dictionary of pulse.

        Returns:
            dict: Dictionary describing the pulse.
        """
        return {PULSEEVENT.PULSE: self.pulse.to_dict(), PULSEEVENT.START_TIME: self.start_time}

    @classmethod
    def from_dict(cls, dictionary: dict):
        """Load PulseEvent object from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the PulseEvent object.

        Returns:
            PulseEvent: Loaded class.
        """
        pulse_settings = dictionary[PULSEEVENT.PULSE]
        pulse = (
            Pulse(**pulse_settings)
            if Pulse.name == PulseName(pulse_settings.pop(RUNCARD.NAME))
            else ReadoutPulse(**pulse_settings)
        )
        start_time = dictionary[PULSEEVENT.START_TIME]
        return PulseEvent(pulse=pulse, start_time=start_time)
