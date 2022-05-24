"""PulsedGateFactory class."""
from typing import List, Tuple, Type

from qibo.abstractions.gates import Gate

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate


class HardwareGateFactory:
    """Contains the gates that can be directly translated into a pulse."""

    pulsed_gates: List[Type[HardwareGate]] = []

    @classmethod
    def register(cls, handler_cls: Type[HardwareGate]):
        """Register handler in the factory.

        Args:
            output_type (type): Class type to register.
        """
        cls.pulsed_gates.append(handler_cls)
        return handler_cls

    @classmethod
    def get(cls, gate: Gate) -> Tuple[float | None, float | None]:
        """Return the amplitude and phase of the specified gate.

        Args:
            gate (Gate): Qibo Gate class.

        Returns:
            Tuple[float, float]: Amplitude and phase of the translated pulse.
        """
        return next(
            (
                pulsed_gate.translate(gate=gate)
                for pulsed_gate in cls.pulsed_gates
                if isinstance(gate, pulsed_gate.class_type)
            ),
            (None, None),
        )
