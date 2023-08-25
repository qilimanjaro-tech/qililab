"""
Drivers for
- :class:`qcodes_contrib_drivers.drivers.ERAInstruments.ERASynth <qcodes_contrib_drivers.drivers.ERAInstruments.erasynth.ERASynth>`,
- :class:`qcodes_contrib_drivers.drivers.ERAInstruments.ERASynthPlus <qcodes_contrib_drivers.drivers.ERAInstruments.erasynth.ERASynthPlus>`, and
- :class:`qcodes_contrib_drivers.drivers.ERAInstruments.ERASynthPlusPlus <qcodes_contrib_drivers.drivers.ERAInstruments.erasynth.ERASynthPlusPlus>`
from
https://github.com/QCoDeS/Qcodes_contrib_drivers/blob/main/qcodes_contrib_drivers/drivers/ERAInstruments/erasynth.py

All 3 classes are the same but kept separated for clarity at higher layers of the code
We only have the ERASynthPlus in the lab so for the time being we don't need to define the others.
"""
from typing import Any

from qcodes.instrument import DelegateParameter
from qcodes_contrib_drivers.drivers.ERAInstruments import ERASynthPlus as QcdERASynthPlus

from qililab.drivers import parameters
from qililab.drivers.instruments.instrument_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import LocalOscillator


@InstrumentDriverFactory.register
class ERASynthPlus(QcdERASynthPlus, LocalOscillator):
    """Qililab's driver for the ERASynthPlus local oscillator

    QcdEraSynth: QCoDeS contributors driver for the ERASynthPlus instrument
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

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name
