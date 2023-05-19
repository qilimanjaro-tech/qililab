"""CZ gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class CZ(HardwareGate):  # pylint: disable=invalid-name
    """CZ gate.

    CZ / C-Phase gate (2 qubit gate)
    Sends a Sudden Net Zero (SNZ) pulse to the target in CZ(control, target)
    """

    # TODO implementation,this is just a mock

    name = GateName.CZ
    class_type = gates.CZ

    @classmethod
    def translate(
        cls,
        gate: gates.CZ,
        master_amplitude_gate: float,  # TODO check that this actually loads the amplitude from gate settings
        master_duration_gate: int,
    ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        qubits = gate.qubits
        return cls.parameters(
            qubits=qubits,
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
