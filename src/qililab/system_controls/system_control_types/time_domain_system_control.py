"""Time Domain SystemControl class."""
from dataclasses import dataclass
from pathlib import Path

from qililab.instruments.awg import AWG
from qililab.pulse import PulseBusSchedule
from qililab.system_controls.system_control import SystemControl
from qililab.typings import SystemControlCategory
from qililab.typings.enums import Category, Parameter


class TimeDomainSystemControl(SystemControl):
    """TimeDomainSystemControl class."""

    @dataclass
    class TimeDomainSystemControlSettings(SystemControl.SystemControlSettings):
        """Time Domain System Control settings class."""

        system_control_category = SystemControlCategory.TIME_DOMAIN
        awg: AWG

        def _supported_instrument_categories(self) -> list[str]:
            """return a list of supported instrument categories."""
            return [Category.AWG.value]

    settings: TimeDomainSystemControlSettings

    @property
    def awg(self):
        """System Control 'awg' property.
        Returns:
            AWG: settings.awg.
        """
        return self.settings.awg

    @property
    def frequency(self):
        """SystemControl 'frequency' property."""
        return self.awg.frequency

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return [Category.AWG]

    def __str__(self):
        """String representation of the TimeDomainSystemControl class."""
        return f"-|{self.awg}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        self.awg.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetitition duration
            path (Path): path to save the program to upload
        """
        return self.awg.generate_program_and_upload(
            pulse_bus_schedule=pulse_bus_schedule,
            nshots=nshots,
            repetition_duration=repetition_duration,
            path=path,
        )

    def run(self) -> None:
        """Run the uploaded program"""
        return self.awg.run()
