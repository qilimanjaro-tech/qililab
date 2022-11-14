"""IntegratedSystemControl class."""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qililab.instruments.instrument import Instrument
from qililab.instruments.system_control.system_control import SystemControl
from qililab.instruments.utils import InstrumentFactory
from qililab.pulse import PulseSequence
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter


@InstrumentFactory.register
class IntegratedSystemControl(SystemControl, Instrument):
    """IntegratedSystemControl class."""

    name = InstrumentName.INTEGRATED_SYSTEM_CONTROL

    @dataclass
    class IntegratedSystemControlSettings(SystemControl.SystemControlSettings, Instrument.InstrumentSettings):
        """IntegratedSystemControlSettings class."""

    settings: IntegratedSystemControlSettings

    def start(self):
        """Start instrument."""

    def initial_setup(self):
        """Set initial instrument settings."""

    def setup(self, frequencies: List[float]):  # type: ignore
        """Setup instruments."""

    def reset(self):
        """Reset instrument settings."""

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run the given pulse sequence."""

    def stop(self):
        """Stop an instrument."""

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

    @property
    def awg_frequency(self) -> float:
        """SystemControl 'awg_frequency' property."""

    @property
    def frequency(self) -> float:
        """SystemControl 'frequency' property."""

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set parameter for an instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
