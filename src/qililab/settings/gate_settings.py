from dataclasses import dataclass, field

from qililab.typings.enums import Parameter

# TODO: docstrings


@dataclass
class CircuitPulseSettings:
    """GatesSchema class."""

    bus: str
    amplitude: float
    phase: float
    frequency: float
    duration: int
    shape: dict
    wait_time: int = 0

    def set_parameter(self, parameter: Parameter, value: float | str | bool):
        """Change a gate parameter with the given value."""
        param = parameter.value
        if not hasattr(self, param):
            self.shape[param] = value
        else:
            setattr(self, param, value)


@dataclass
class GateSettings:
    """GatesSchema class."""

    name: str
    schedule: list[CircuitPulseSettings]

    # TODO: do we want this?
    def set_parameter(self, parameter: Parameter, value: float | str | bool, schedule_element: int):
        """Set a parameter of a schedule element."""
        self.schedule[schedule_element].set_parameter(parameter, value)
