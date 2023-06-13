"""VoltageSource class."""

from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


@dataclass
class Dac:
    """Dac class."""

    index: int
    parameters: dict


class VoltageSource(Instrument):
    """Abstract base class defining all instruments used to generate voltages."""

    dacs: list[Dac]

    def to_dict(self):
        """Return a dict representation of the VoltageSource class."""
        return dict(super().to_dict().items())
