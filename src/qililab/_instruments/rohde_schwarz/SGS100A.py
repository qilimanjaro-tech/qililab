from typing import Any

from qcodes.instrument_drivers.rohde_schwarz import RohdeSchwarzSGS100A as QcodesSGS100A

from qililab._instruments.interfaces import LocalOscillator


class RhodeSchwarzSGS100A(QcodesSGS100A, LocalOscillator):
    """Qililab's driver for the SGS100A local oscillator

    Args:
        QcodesSGS100A: QCoDeS Rohde Schwarz driver for SGS100A
        LocalOscillator: Qililab's local oscillator interface
    """

    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name=name, address=address, **kwargs)
