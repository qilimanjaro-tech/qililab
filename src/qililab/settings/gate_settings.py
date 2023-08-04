from dataclasses import dataclass, field

from qililab.typings.enums import Parameter
from typing import Collection

# TODO: docstrings


@dataclass
class GateEventSettings:
    """GatesSchema class."""

    @dataclass
    class GatePulseSettings:
        amplitude: float
        phase: float
        frequency: float
        duration: int
        shape: dict

    bus: str
    pulse: GatePulseSettings
    wait_time: int = 0

    def __post_init__(self):
        self.pulse = self.GatePulseSettings(**self.pulse)

    def set_parameter(self, parameter: Parameter, value: float | str | bool):
        """Change a gate parameter with the given value."""
        param = parameter.value
        if hasattr(self, param):
            setattr(self, param, value)
        elif hasattr(self.pulse, param):
            setattr(self.pulse, param, value)
        else:
            self.pulse.shape[param] = value


@dataclass
class GateSettings:
    """GatesSchema class."""

    schedule: list[GateEventSettings] | dict[str, Collection[str]]

    def __post_init__(self):
        self.schedule = [GateEventSettings(**event) for event in self.schedule]

    def set_parameter(self, parameter: Parameter, value: float | str | bool, schedule_element: int):
        """Set a parameter of a schedule element."""
        self.schedule[schedule_element].set_parameter(parameter, value)
