"""PulsedGateFactory class."""
from qibo.gates import Gate

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate


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

    @classmethod
    def gate_settings(cls, gate: Gate) -> HardwareGate.HardwareGateSettings:
        """Return the settings of the specified gate.

        Args:
            gate (Gate): Qibo Gate class.

        Returns:
            tuple[float, float]: Amplitude and phase of the translated pulse.
        """
        for pulsed_gate in cls.pulsed_gates.values():
            if isinstance(gate, pulsed_gate.class_type):
                return pulsed_gate.translate(gate=gate)

        raise NotImplementedError(f"Qililab has not defined a gate {gate.__class__.__name__}")
