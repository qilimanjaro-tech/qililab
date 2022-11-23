"""IntegratedSystemControl class."""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from qililab.instruments.instrument import Instrument
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseBusSchedule
from qililab.result import Result
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter
from qililab.utils.factory import Factory


@Factory.register
class IntegratedSystemControl(SystemControl):
    """IntegratedSystemControl class."""

    name = InstrumentName.INTEGRATED_SYSTEM_CONTROL

    @dataclass
    class IntegratedSystemControlSettings(SystemControl.SystemControlSettings):
        """IntegratedSystemControlSettings class."""

    settings: IntegratedSystemControlSettings

    def run(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path
    ) -> List[Result] | None:
        """Run the given pulse sequence."""

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
