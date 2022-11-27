"""Continuous SystemControl class."""
from dataclasses import dataclass

from qililab.instruments.system_control.system_control import SystemControl
from qililab.typings import SystemControlCategory


class ContinuousSystemControl(SystemControl):
    """Continuous System Control class."""

    @dataclass
    class ContinuousSystemControlSettings(SystemControl.SystemControlSettings):
        """Continuous System Control settings class."""

        system_control_category = SystemControlCategory.CONTINUOUS

    settings: ContinuousSystemControlSettings
