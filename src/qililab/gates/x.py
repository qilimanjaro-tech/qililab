from dataclasses import dataclass

from qililab.gates.hardware_gate import HardwareGate


@dataclass
class X(HardwareGate):
    """X gate

    Args:
        q (int): Index of the qubit to which the gate is applied.
    """

    q: int

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise NotImplementedError
