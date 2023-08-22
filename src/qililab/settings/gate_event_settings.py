from dataclasses import dataclass

from qililab.typings.enums import Parameter


@dataclass
class GateEventSettings:
    """Settings for a single gate event. A gate event is an element of a gate schedule, which is the
    sequence of gate events that define what a gate does (the pulse events it consists of).

    A gate event is made up of GatePulseSettings, which contains pulse specific information, and extra arguments
    (bus and wait_time) which are related to the context in which the specific pulse in GatePulseSettings is applied

    Attributes:
        bus (str): bus through which the pulse is to be sent. The string has to match that of the bus alias in the runcard
        pulse (GatePulseSettings): settings of the bus to be launched
        wait_time (int): time to wait w.r.t gate start time (taken as 0) before launching the pulse
    """

    @dataclass
    class GatePulseSettings:
        """Single pulse settings

        Attributes:
            amplitude (float): amplitude of the pulse
            phase (float): phase of the pulse
            duration (int): pulse duration
            shape (dict): pulse envelope
        """

        amplitude: float
        phase: float
        duration: int
        shape: dict

    bus: str
    pulse: GatePulseSettings
    wait_time: int = 0

    def __post_init__(self):
        """post init method to initialize pulse settings from runcard yaml file"""
        self.pulse = self.GatePulseSettings(**self.pulse)  # pylint: disable=E1134

    def set_parameter(self, parameter: Parameter, value: float | str | bool):
        """Change a given parameter from settings. Will look up into subclasses.

        Args:
            parameter (Parameter): parameter to be set
            value (float | str | bool): value of the parameter
        """
        param = parameter.value
        if hasattr(self, param):
            setattr(self, param, value)
        elif hasattr(self.pulse, param):
            setattr(self.pulse, param, value)
        else:
            self.pulse.shape[param] = value
