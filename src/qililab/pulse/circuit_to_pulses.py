"""Class that translates a Qibo Circuit into a PulseSequence"""
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

import numpy as np
from qibo.gates import Gate, M
from qibo.models.circuit import Circuit

from qililab.chip import Chip, Node
from qililab.constants import RUNCARD
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.pulse.readout_event import ReadoutEvent
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.settings import RuncardSchema
from qililab.typings.enums import PulseShapeName
from qililab.utils import Factory, qibo_gates


@dataclass
class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    settings: RuncardSchema.PlatformSettings

    def __post_init__(self):
        """Post init."""
        self._instantiate_gates_from_settings()

    def translate(self, circuits: List[Circuit], chip: Chip) -> List[PulseSchedule]:
        """Translate each circuit to a PulseSequences class, which is a list of PulseSequence classes for
        each different port and pulse name (control/readout).

        Args:
            circuits (List[Circuit]): List of Qibo Circuit classes.

        Returns:
            List[PulseSequences]: List of PulseSequences classes.
        """
        pulse_schedule_list: List[PulseSchedule] = []
        for circuit in circuits:
            pulse_schedule = PulseSchedule()
            time: Dict[int, int] = {}  # restart time
            readout_gates = circuit.gates_of_type(M)
            control_gates = [
                gate for (i, gate) in enumerate(circuit.queue) if i not in [idx for (idx, _) in readout_gates]
            ]
            _, readout_gate = readout_gates[0] if len(readout_gates) > 0 else (None, None)
            wait_of_next_pulse_event = 0
            for gate in control_gates:
                if isinstance(gate, qibo_gates.Wait):
                    wait_of_next_pulse_event = gate.parameters[0]
                    continue
                pulse_event, port = self._control_gate_to_pulse_event(
                    time=time, control_gate=gate, chip=chip, wait_time=wait_of_next_pulse_event
                )
                if pulse_event is not None:
                    pulse_schedule.add_event(pulse_event=pulse_event, port=port)
                wait_of_next_pulse_event = 0
            if readout_gate is not None:
                for qubit_idx in readout_gate.target_qubits:
                    readout_pulse_event, port = self._readout_gate_to_pulse_event(
                        time=time,
                        readout_gate=readout_gate,
                        qubit_idx=qubit_idx,
                        chip=chip,
                        wait_time=wait_of_next_pulse_event,
                    )
                    if readout_pulse_event is not None:
                        pulse_schedule.add_event(pulse_event=readout_pulse_event, port=port)

            pulse_schedule_list.append(pulse_schedule)

        return pulse_schedule_list

    def _build_pulse_shape_from_gate_settings(self, gate_settings: HardwareGate.HardwareGateSettings):
        """Build Pulse Shape from Gate seetings"""
        shape_settings = gate_settings.shape.copy()
        return Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)

    def _control_gate_to_pulse_event(
        self, time: Dict[int, int], control_gate: Gate, chip: Chip, wait_time: int
    ) -> Tuple[PulseEvent | None, int]:
        """Translate a gate into a pulse event.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            PulseEvent: PulseEvent object.
        """
        gate_settings = self._get_gate_settings_with_master_values(gate=control_gate)
        pulse_shape = self._build_pulse_shape_from_gate_settings(gate_settings=gate_settings)
        # TODO: Adapt this code to translate two-qubit gates.
        port = chip.get_port_from_qubit_idx(idx=control_gate.target_qubits[0], readout=False)
        old_time = self._update_time(
            time=time,
            chip=chip,
            node=port,
            pulse_time=gate_settings.duration + self.settings.delay_between_pulses,
            wait_time=wait_time,
        )
        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=float(gate_settings.amplitude),
                    phase=float(gate_settings.phase),
                    duration=gate_settings.duration,
                    pulse_shape=pulse_shape,
                ),
                start_time=old_time,
            )
            if gate_settings.duration > 0
            else None,
            port.id_,
        )

    def _get_gate_settings_with_master_values(self, gate: Gate):
        """get gate settings with master values"""
        gate_settings = HardwareGateFactory.gate_settings(
            gate=gate,
            master_amplitude_gate=self.settings.master_amplitude_gate,
            master_duration_gate=self.settings.master_duration_gate,
        )
        if (
            not isinstance(gate_settings.amplitude, float)
            and not isinstance(gate_settings.amplitude, int)
            and not isinstance(gate_settings.amplitude, np.number)
        ):
            raise ValueError(
                f"Value amplitude: {gate_settings.amplitude} MUST be a float or an integer. "
                f"Current type is {type(gate_settings.amplitude)}."
            )

        if (
            not isinstance(gate_settings.duration, float)
            and not isinstance(gate_settings.duration, int)
            and not isinstance(gate_settings.duration, np.number)
        ):
            raise ValueError(
                f"Value duration: {gate_settings.duration} MUST be an integer. "
                f"Current type is {type(gate_settings.duration)}."
            )
        if isinstance(gate_settings.duration, float):
            gate_settings.duration = int(gate_settings.duration)
        return gate_settings

    def _readout_gate_to_pulse_event(
        self, time: Dict[int, int], readout_gate: Gate, qubit_idx: int, chip: Chip, wait_time: int
    ) -> Tuple[ReadoutEvent | None, int]:
        """Translate a gate into a pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        gate_settings = self._get_gate_settings_with_master_values(gate=readout_gate)
        shape_settings = gate_settings.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        port = chip.get_port_from_qubit_idx(idx=qubit_idx, readout=True)
        old_time = self._update_time(
            time=time,
            chip=chip,
            node=port,
            pulse_time=gate_settings.duration + self.settings.delay_before_readout,
            wait_time=wait_time,
        )

        return (
            ReadoutEvent(
                pulse=ReadoutPulse(
                    amplitude=gate_settings.amplitude,
                    phase=gate_settings.phase,
                    duration=gate_settings.duration,
                    pulse_shape=pulse_shape,
                ),
                start_time=old_time + self.settings.delay_before_readout,
            )
            if gate_settings.duration > 0
            else None,
            port.id_,
        )

    def _update_time(self, time: Dict[int, int], chip: Chip, node: Node, pulse_time: int, wait_time: int):
        """Create new timeline if not already created and update time.

        Args:
            port (int): Index of the chip port.
            pulse_time (int): Duration of the puls + wait time.
        """
        qubit_idx = chip.get_qubit_idx_from_node(node=node)
        if qubit_idx not in time:
            time[qubit_idx] = 0
        old_time = wait_time + time[qubit_idx]
        time[qubit_idx] += wait_time + pulse_time
        return old_time

    def _instantiate_gates_from_settings(self):
        """Instantiate all gates defined in settings and add them to the factory."""
        for gate_settings in self.settings.gates:
            settings_dict = asdict(gate_settings)
            gate_class = HardwareGateFactory.get(name=settings_dict.pop(RUNCARD.NAME))
            gate_class.settings = gate_class.HardwareGateSettings(**settings_dict)
