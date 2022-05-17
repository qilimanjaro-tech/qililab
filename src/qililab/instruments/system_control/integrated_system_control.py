"""IntegratedSystemControl class."""
from qililab.instruments.instrument import Instrument
from qililab.instruments.system_control.system_control import SystemControl
from qililab.typings import BusElementName


class IntegratedSystemControl(SystemControl, Instrument):
    """IntegratedSystemControl class."""

    class IntegratedSystemControlSettings(SystemControl.SystemControlSettings, Instrument.InstrumentSettings):
        """IntegratedSystemControlSettings class."""

    settings: IntegratedSystemControlSettings

    name = BusElementName.INTEGRATED_SYSTEM_CONTROL
