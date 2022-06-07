"""TranslationSettings class."""
from qililab.utils import nested_dataclass


@nested_dataclass
class TranslationSettings:
    """Settings used for the translation of a circuit into pulses."""

    readout_duration: int
    readout_amplitude: float
    readout_phase: float
    delay_between_pulses: int
    delay_before_readout: int
    gate_duration: int
    num_sigmas: float
    drag_coefficient: float
