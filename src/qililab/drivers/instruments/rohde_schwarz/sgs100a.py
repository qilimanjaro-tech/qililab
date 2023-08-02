from typing import Any

from qcodes.instrument import DelegateParameter
from qcodes.instrument_drivers.rohde_schwarz import RohdeSchwarzSGS100A as QcodesSGS100A

from qililab.drivers import parameters
from qililab.drivers.instruments.instrument_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import LocalOscillator


@InstrumentDriverFactory.register
class RhodeSchwarzSGS100A(QcodesSGS100A, LocalOscillator):
    """Qililab's driver for the SGS100A local oscillator

    QcodesSGS100A: QCoDeS Rohde Schwarz driver for SGS100A
    LocalOscillator: Qililab's local oscillator interface
    """

    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name, address, **kwargs)

        # change the name for frequency
        self.add_parameter(
            parameters.lo.frequency,
            label="Delegated parameter for local oscillator frequency",
            source=self.parameters["frequency"],
            parameter_class=DelegateParameter,
        )
