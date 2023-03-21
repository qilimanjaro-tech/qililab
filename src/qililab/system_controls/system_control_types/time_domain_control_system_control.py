"""Time Domain Control SystemControl class."""
from dataclasses import dataclass
from pathlib import Path

from qililab.instruments.signal_generator import SignalGenerator
from qililab.pulse import PulseBusSchedule
from qililab.system_controls.system_control_types.time_domain_system_control import TimeDomainSystemControl
from qililab.typings import SystemControlSubCategory
from qililab.typings.enums import Category, Parameter, SystemControlName
from qililab.utils import Factory


@Factory.register
class ControlSystemControl(TimeDomainSystemControl):
    """Control SystemControl class."""

    name = SystemControlName.TIME_DOMAIN_CONTROL_SYSTEM_CONTROL

    @dataclass
    class ControlSystemControlSettings(TimeDomainSystemControl.TimeDomainSystemControlSettings):
        """Time Domain Control System Control settings class."""

        system_control_subcategory = SystemControlSubCategory.CONTROL
        signal_generator: SignalGenerator

        def _supported_instrument_categories(self) -> list[str]:
            """return a list of supported instrument categories."""
            return super()._supported_instrument_categories() + [Category.SIGNAL_GENERATOR.value]

    settings: ControlSystemControlSettings

    @property
    def signal_generator(self):
        """System Control 'signal_generator' property.
        Returns:
            SignalGenerator: settings.signal_generator.
        """
        return self.settings.signal_generator

    def frequency(self, port_id: int):
        """SystemControl 'frequency' property."""
        return self.signal_generator.frequency + self.awg.frequency(port_id=port_id)

    def __str__(self):
        """String representation of the ControlSystemControl class."""
        return f"{super().__str__()}-|{self.signal_generator}|-"

    def _update_bus_frequency(
        self, frequency: float | str | bool, channel_id: int | None = None, port_id: int | None = None
    ):
        """update frequency to the signal generator and AWG

        Args:
            frequency (float): the bus final frequency (AWG + Signal Generator)
            channel_id (int | None, optional): AWG Channel. Defaults to None.
        """
        if not isinstance(frequency, float):
            raise ValueError(f"value must be a float. Current type: {type(frequency)}")

        signal_generator_frequency = frequency - self.awg.frequency(channel_id=channel_id, port_id=port_id)
        self.signal_generator.set_parameter(parameter=Parameter.LO_FREQUENCY, value=signal_generator_frequency)

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter == Parameter.BUS_FREQUENCY:
            self._update_bus_frequency(frequency=value, channel_id=channel_id)
            return
        if parameter == Parameter.LO_FREQUENCY:
            self.signal_generator.set_parameter(parameter=Parameter.LO_FREQUENCY, value=value)
            return
        if parameter == Parameter.POWER:
            self.signal_generator.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            return

        # the rest of parameters are assigned to the TimeDomainSystemControl
        super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return super()._get_supported_instrument_categories() + [Category.SIGNAL_GENERATOR]

    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
        """
        if pulse_bus_schedule.frequency is not None and pulse_bus_schedule.frequency != self.frequency(
            port_id=pulse_bus_schedule.port
        ):
            self._update_bus_frequency(frequency=pulse_bus_schedule.frequency, port_id=pulse_bus_schedule.port)

        return super().generate_program_and_upload(
            pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration
        )
