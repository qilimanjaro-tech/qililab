"""QubitControl class."""
from abc import abstractmethod
from dataclasses import dataclass, field

from qililab.instruments.instrument import Instrument
from qililab.instruments.mixer import Mixer
from qililab.pulse import PulseSequence
from qililab.result import QbloxResult


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @dataclass
    class AWGSettings(Instrument.InstrumentSettings):
        """Contains the settings of a AWG.

        Args:
            frequency (float): Intermediate frequency (IF).
            offset_i (float): I offset (unitless). amplitude + offset should be in range [0 to 1].
            offset_q (float): Q offset (unitless). amplitude + offset should be in range [0 to 1].
            epsilon (float): Amplitude added to the Q channel.
            delta (float): Dephasing.
        """

        frequency: float
        mixer_settings: Mixer.MixerSettings = field(init=False)

        @property
        def epsilon(self):
            """MixerSettings 'epsilon' property.

            Returns:
                float: mixer.epsilon.
            """
            return self.mixer_settings.epsilon

        @property
        def delta(self):
            """MixerSettings 'delta' property.

            Returns:
                float: mixer.delta.
            """
            return self.mixer_settings.delta

        @property
        def offset_i(self):
            """MixerSettings 'offset_i' property.

            Returns:
                float: mixer.offset_i.
            """
            return self.mixer_settings.offset_i

        @property
        def offset_q(self):
            """MixerSettings 'offset_q' property.

            Returns:
                float: mixer.offset_q.
            """
            return self.mixer_settings.offset_q

    settings: AWGSettings

    @abstractmethod
    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int) -> QbloxResult:
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """

    @property
    def frequency(self):
        """QbloxPulsar 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency

    def setup_mixer_settings(self, mixer: Mixer):
        """Setup mixer settings."""
        self.settings.mixer_settings = mixer.settings
