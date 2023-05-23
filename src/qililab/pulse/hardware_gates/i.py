"""Identity gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class I(HardwareGate):  # pylint: disable=invalid-name # noqa: E742
    """Identity gate."""

    name = GateName.I
    class_type = gates.I

    @classmethod
    def translate(cls, gate: gates.I) -> HardwareGate.HardwareGateSettings:  # noqa: E741
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        qubit = gate.target_qubits[0]
        return cls.settings[qubit]
