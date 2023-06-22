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

from qcodes_contrib_drivers.drivers.ERAInstruments import ERASynthPlus as QcdERASynthPlus

from qililab._drivers.interfaces import LocalOscillator


class ERASynthPlus(QcdERASynthPlus, LocalOscillator):
    """Qililab's driver for the ERASynthPlus local oscillator

    Args:
        QcdEraSynth: QCoDeS contributors driver for the ERASynthPlus instrument
        LocalOscillator: Qililab's local oscillator interface
    """

    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name=name, address=address, **kwargs)
