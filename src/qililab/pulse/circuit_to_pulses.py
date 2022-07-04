"""Class that translates a Qibo Circuit into a PulseSequence"""
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from qibo.abstractions.gates import Gate
from qibo.core.circuit import Circuit

from qililab.chip import Chip
from qililab.constants import RUNCARD
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_sequences import PulseSequences
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.settings import RuncardSchema
from qililab.utils import Factory


@dataclass
class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    settings: RuncardSchema.PlatformSettings.PulsesSettings

    def __post_init__(self):
        """Post init."""
        self._instantiate_gates_from_settings()

    def translate(self, circuits: List[Circuit], chip: Chip) -> List[PulseSequences]:
        """Translate each circuit to a PulseSequences class, which is a list of PulseSequence classes for
        each different port and pulse name (control/readout).

        Args:
            circuits (List[Circuit]): List of Qibo Circuit classes.

        Returns:
            List[PulseSequences]: List of PulseSequences classes.
        """
        pulse_sequences_list: List[PulseSequences] = []
        for circuit in circuits:
            pulse_sequences = PulseSequences()
            time: Dict[int, int] = {}  # restart time
            control_gates = list(circuit.queue)
            readout_gate = circuit.measurement_gate
            for gate in control_gates:
                pulse, port = self._control_gate_to_pulse(time=time, control_gate=gate, chip=chip)
                if pulse is not None:
                    pulse_sequences.add(pulse=pulse, port=port)
            if readout_gate is not None:
                for qubit_idx in readout_gate.target_qubits:
                    readout_pulse, port = self._readout_gate_to_pulse(
                        time=time, readout_gate=readout_gate, qubit_idx=qubit_idx, chip=chip
                    )
                    if readout_pulse is not None:
                        pulse_sequences.add(pulse=readout_pulse, port=port)

            pulse_sequences_list.append(pulse_sequences)

        return pulse_sequences_list

    def _control_gate_to_pulse(self, time: Dict[int, int], control_gate: Gate, chip: Chip) -> Tuple[Pulse | None, int]:
        """Translate a gate into a pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        gate_settings = HardwareGateFactory.gate_settings(control_gate)
        shape_settings = gate_settings.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        port = chip.get_port_from_qubit_idx(idx=control_gate.target_qubits[0], readout=False)
        old_time = self._update_time(
            time=time, port=port.id_, pulse_time=gate_settings.duration + self.settings.delay_between_pulses
        )
        return (
            Pulse(
                amplitude=float(gate_settings.amplitude),
                phase=float(gate_settings.phase),
                duration=gate_settings.duration,
                pulse_shape=pulse_shape,
                start_time=old_time,
            )
            if gate_settings.duration > 0
            else None,
            port.id_,
        )

    def _readout_gate_to_pulse(
        self, time: Dict[int, int], readout_gate: Gate, qubit_idx: int, chip: Chip
    ) -> Tuple[ReadoutPulse | None, int]:
        """Translate a gate into a pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        gate_settings = HardwareGateFactory.gate_settings(readout_gate)
        shape_settings = gate_settings.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        port = chip.get_port_from_qubit_idx(idx=qubit_idx, readout=True)
        old_time = self._update_time(
            time=time, port=port.id_, pulse_time=gate_settings.duration + self.settings.delay_before_readout
        )
        return (
            ReadoutPulse(
                amplitude=gate_settings.amplitude,
                phase=gate_settings.phase,
                duration=gate_settings.duration,
                pulse_shape=pulse_shape,
                start_time=old_time,
            )
            if gate_settings.duration > 0
            else None,
            port.id_,
        )

    def _update_time(self, time: Dict[int, int], port: int, pulse_time: int):
        """Create new timeline if not already created and update time.

        Args:
            port (int): Index of the chip port.
            pulse_time (int): Duration of the puls + wait time.
        """
        if port not in time:
            time[port] = 0
        old_time = time[port]
        time[port] += pulse_time
        return old_time

    def _instantiate_gates_from_settings(self):
        """Instantiate all gates defined in settings and add them to the factory."""
        for gate_settings in self.settings.gates:
            settings_dict = asdict(gate_settings)
            gate_class = HardwareGateFactory.get(name=settings_dict.pop(RUNCARD.NAME))
            gate_class.settings = gate_class.HardwareGateSettings(**settings_dict)
