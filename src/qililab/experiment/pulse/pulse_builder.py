"""PulseBuilder class"""
from qililab.experiment.pulse.pulse_sequence import PulseSequence
from qililab.utils import Singleton


class PulseBuilder(metaclass=Singleton):
    """Builder of PulseSequence objects."""

    def build(self) -> PulseSequence:
        """Build PulseSequence with its corresponding Pulse objects.

        Returns:
            PulseSequence: PulseSequence object.
        """
        return PulseSequence()
