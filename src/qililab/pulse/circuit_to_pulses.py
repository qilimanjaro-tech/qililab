"""Class that translates a Qibo Circuit into a PulseSequence"""
import platform
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

import numpy as np
from qibo.gates import Gate, M
from qibo.models.circuit import Circuit

from qililab.chip import Chip
from qililab.constants import RUNCARD
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.settings import RuncardSchema
from qililab.utils import Factory


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
            for gate in control_gates:
                pulse_event, port = self._control_gate_to_pulse_event(time=time, control_gate=gate, chip=chip)
                if pulse_event is not None:
                    pulse_schedule.add_event(pulse_event=pulse_event, port=port)
            for _, readout_gate in readout_gates:
                for qubit_idx in readout_gate.target_qubits:
                    readout_pulse_event, port = self._readout_gate_to_pulse_event(
                        time=time, readout_gate=readout_gate, qubit_idx=qubit_idx, chip=chip
                    )
                    if readout_pulse_event is not None:
                        pulse_schedule.add_event(pulse_event=readout_pulse_event, port=port)

            pulse_schedule_list.append(pulse_schedule)

        return pulse_schedule_list

    def _build_pulse_shape_from_gate_settings(self, gate_settings: HardwareGate.HardwareGateSettings):
        """Build Pulse Shape from Gate settings"""
        shape_settings = gate_settings.shape.copy()
        return Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)

    def _control_gate_to_pulse_event(
        self, time: Dict[int, int], control_gate: Gate, chip: Chip
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
        qubit_idx = control_gate.target_qubits[0]
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=False)
        port = chip.get_port(node)
        old_time = self._update_time(
            time=time,
            qubit_idx=qubit_idx,
            pulse_time=gate_settings.duration + self.settings.delay_between_pulses,
        )
        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=float(gate_settings.amplitude),
                    phase=float(gate_settings.phase),
                    duration=gate_settings.duration,
                    pulse_shape=pulse_shape,
                    frequency=node.frequency,
                ),
                start_time=old_time,
            )
            if gate_settings.duration > 0
            else None,
            port,
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
        self, time: Dict[int, int], readout_gate: Gate, qubit_idx: int, chip: Chip
    ) -> Tuple[PulseEvent | None, int]:
        """Translate a gate into a pulse.

        Args:
            time: Dict[int, int]: time.
            readout_gate (Gate): Qibo Gate.
            qubit_id (int): qubit number.
            chip (Chip): chip object.

        Returns:
            Tuple[PulseEvent | None, int]: (PulseEvent or None, port_id).
        """
        gate_settings = self._get_gate_settings_with_master_values(gate=readout_gate)
        shape_settings = gate_settings.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=True)
        port = chip.get_port(node)
        old_time = self._update_time(
            time=time,
            qubit_idx=qubit_idx,
            pulse_time=gate_settings.duration + self.settings.delay_before_readout,
        )

        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=gate_settings.amplitude,
                    phase=gate_settings.phase,
                    duration=gate_settings.duration,
                    frequency=node.frequency,
                    pulse_shape=pulse_shape,
                ),
                start_time=old_time + self.settings.delay_before_readout,
            )
            if gate_settings.duration > 0
            else None,
            port,
        )

    def _update_time(self, time: Dict[int, int], qubit_idx: int, pulse_time: int):
        """Create new timeline if not already created and update time.

        Args:
            time (Dict[int, int]): Dictionary with the time of each qubit.
            qubit_idx (int): Index of the qubit.
            pulse_time (int): Duration of the puls + wait time.
        """
        if qubit_idx not in time:
            time[qubit_idx] = 0
        old_time = time[qubit_idx]
        residue = pulse_time % self.settings.minimum_clock_time
        if residue != 0:
            pulse_time += self.settings.minimum_clock_time - residue
        time[qubit_idx] += pulse_time
        return old_time

    def _instantiate_gates_from_settings(self):
        """Instantiate all gates defined in settings and add them to the factory."""
        for gate_settings in self.settings.gates:
            settings_dict = asdict(gate_settings)
            gate_class = HardwareGateFactory.get(name=settings_dict.pop(RUNCARD.NAME))
            gate_class.settings = gate_class.HardwareGateSettings(**settings_dict)
