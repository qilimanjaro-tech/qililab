"""X gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class X(HardwareGate):  # pylint: disable=invalid-name
    """X gate."""

    name = GateName.X
    class_type = gates.X

    @classmethod
    def translate(
        cls,
        gate: gates.X,
        master_amplitude_gate: float,
        master_duration_gate: int,
    ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        qubit = gate.target_qubits[0]
        return cls.parameters(
            qubits=qubit,
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
