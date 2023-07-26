"""PulsedGateFactory class."""
from qibo.gates import Gate

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.settings.gate_settings import GateSettings


class HardwareGateFactory:
    """Contains the gates that can be directly translated into a pulse."""

    pulsed_gates: dict[str, type[HardwareGate]] = {}

    @classmethod
    def register(cls, handler_cls: type[HardwareGate]):
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.pulsed_gates[handler_cls.name.value] = handler_cls
        return handler_cls

    @classmethod
    def get(cls, name: str):
        """Return class attribute."""
        return cls.pulsed_gates[name]
