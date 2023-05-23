"""Class that translates a Qibo Circuit into a PulseSequence"""
from dataclasses import asdict, dataclass

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
from qililab.typings.enums import Line
from qililab.utils import Factory


@dataclass
class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    settings: RuncardSchema.PlatformSettings

    def __post_init__(self):
        """Post init."""
        self._instantiate_gates_from_settings()

    def translate(self, circuits: list[Circuit], chip: Chip) -> list[PulseSchedule]:
        """Translate each circuit to a PulseSequences class, which is a list of PulseSequence classes for
        each different port and pulse name (control/readout).

        Args:
            circuits (List[Circuit]): List of Qibo Circuit classes.
            chip (Chip): Chip representation as a graph.

        Returns:
            list[PulseSequences]: List of PulseSequences classes.
        """
        pulse_schedule_list: list[PulseSchedule] = []
        for circuit in circuits:
            pulse_schedule = PulseSchedule()
            time: dict[int, int] = {}  # restart time
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
        """Build Pulse Shape from Gate settings

        Args:
            gate_settings (HardwareGateSettings): gate settings loaded from the runcard

        Returns:
            shape_settings (dict): shape settings for the gate's pulse
        """
        shape_settings = gate_settings.shape.copy()
        return Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)

    def _control_gate_to_pulse_event(
        self, time: dict[int, int], control_gate: Gate, chip: Chip
    ) -> tuple[PulseEvent | None, int]:
        """Translate a gate into a pulse event.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            control_gate (Gate): non-measurement gate from circuit
            chip (Chip): chip representation as a graph.

        Returns:
            PulseEvent: PulseEvent object.
        """
        gate_settings = self._get_gate_settings(gate=control_gate)
        pulse_shape = self._build_pulse_shape_from_gate_settings(gate_settings=gate_settings)
        # TODO: Add CPhase gate
        qubit_idx = control_gate.target_qubits[0]
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=False)
        port = chip.get_port_from_qubit_idx(idx=qubit_idx, line=Line.DRIVE)
        old_time = self._update_time(
            time=time,
            qubit_idx=qubit_idx,
            pulse_time=gate_settings.duration + self.settings.delay_between_pulses,
        )
        amplitude = float(gate_settings.amplitude)
        phase = float(gate_settings.phase)

        return (
            PulseEvent(
                pulse=Pulse(
                    amplitude=amplitude,
                    phase=phase,
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

    def _get_gate_settings(self, gate: Gate):
        """get gate settings with master values

        Args:
            gate (Gate): qibo / native gate

        Returns:
            gate_settings ()
        """
        gate_settings = HardwareGateFactory.gate_settings(gate=gate)

        # check if duration is an integer value (admit floats with null decimal part)
        gate_duration = gate_settings.duration
        if not isinstance(gate_duration, int):  # this handles floats but also settings reading int as np.int64
            if gate_duration % 1 != 0:  # check decimals
                raise ValueError(
                    f"The settings of the gate {gate.name} have a non-integer duration ({gate_duration}ns). "
                    "The gate duration must be an integer or a float with 0 decimal part"
                )
            else:
                gate_duration = int(gate_duration)

        return gate_settings

    def _readout_gate_to_pulse_event(
        self, time: dict[int, int], readout_gate: Gate, qubit_idx: int, chip: Chip
    ) -> tuple[PulseEvent | None, int]:
        """Translate a gate into a pulse.

        Args:
            time (dict[int, int]): dictionary containing qubit indices as keys and current time (ns) as values
            readout_gate (Gate): measurement gate
            qubit_id (int): qubit number (note that the first qubit is the 0th).
            chip (Chip): chip representation as a graph.

        Returns:
            tuple[PulseEvent | None, int]: (PulseEvent or None, port_id).
        """
        gate_settings = self._get_gate_settings(gate=readout_gate)
        shape_settings = gate_settings.shape.copy()
        pulse_shape = Factory.get(shape_settings.pop(RUNCARD.NAME))(**shape_settings)
        node = chip.get_node_from_qubit_idx(idx=qubit_idx, readout=True)
        port = chip.get_port_from_qubit_idx(idx=qubit_idx, line=Line.FEEDLINE_INPUT)
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
                qubit=qubit_idx,
            )
            if gate_settings.duration > 0
            else None,
            port,
        )

    def _update_time(self, time: dict[int, int], qubit_idx: int, pulse_time: int):
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
        for qubit, gate_settings_list in self.settings.gates.items():
            for gate_settings in gate_settings_list:
                settings_dict = asdict(gate_settings)
                gate_class = HardwareGateFactory.get(name=settings_dict.pop(RUNCARD.NAME))
                if not hasattr(gate_class, "settings"):
                    gate_class.settings = {}
                gate_class.settings[qubit] = gate_class.HardwareGateSettings(**settings_dict)
