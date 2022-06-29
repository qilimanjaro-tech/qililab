"""IntegratedSystemControl class."""
from dataclasses import dataclass
from pathlib import Path

from qililab.instruments.instrument import Instrument
from qililab.instruments.system_control.system_control import SystemControl
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseSequence
from qililab.typings import InstrumentName


@InstrumentFactory.register
class IntegratedSystemControl(SystemControl, Instrument):
    """IntegratedSystemControl class."""

    name = InstrumentName.INTEGRATED_SYSTEM_CONTROL

    @dataclass
    class IntegratedSystemControlSettings(SystemControl.SystemControlSettings, Instrument.InstrumentSettings):
        """IntegratedSystemControlSettings class."""

    settings: IntegratedSystemControlSettings

    def turn_on(self):
        """Start instrument."""

    def setup(self):
        """Setup instruments."""

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run the given pulse sequence."""

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    @property
    def awg_frequency(self) -> float:
        """SystemControl 'frequency' property."""

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property. Delay (in ns) between the readout pulse and the acquisition."""
