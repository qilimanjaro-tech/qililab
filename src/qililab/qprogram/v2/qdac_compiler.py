# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""QDAC compiler for the new ``qprogram`` AST (v2).

A port of :class:`qililab.qprogram.qdac_compiler.QdacCompiler` to the new decoupled ``qprogram``
package. Like the legacy compiler, this is a *control* compiler rather than a code generator: it
walks the QProgram and **programs the QDAC-II instruments as a side effect** (sets DC voltages,
uploads voltage lists, arms trigger markers). The returned :class:`QdacCompilationOutput` only
carries the instruments and the trigger position; the device state lives on the instrument objects.

The supported operations are the QDAC **vendor** ops (``qprogram_qdac.operations``): ``SetOffset``
(static DC voltage), ``Play`` (voltage-list / staircase / ramp), ``SetTrigger`` and ``WaitTrigger``
(trigger-network plumbing), plus the control-flow blocks (``ForLoop`` / ``Loop`` / ``Average`` /
``Parallel`` / ``Block``) which multiply the voltage-list repetition count. RF / timing / readout
operations on a QDAC bus are rejected — the QDAC is a slow DC source with no NCO, mixer, time-grid
sequencer or ADC.

Integration model — flux buses are software-only (``hw=None``), so QDAC ops classify ``{sw}`` and
live in the software region. ``QProgramExecutor`` should compile the program's QDAC ops **once, up
front** (a single :meth:`QdacCompilerV2.compile` pass over the whole program before driving the
software loops) so the device DC lists / triggers are armed, then coordinate the QDAC ``start()``
with the Qblox hardware-frontier run via :attr:`QdacCompilationOutput.trigger_position` (``"front"``
→ start QDAC after Qblox ``run``; ``"back"`` → start QDAC before Qblox ``run``; ``None`` → no
external triggering). This mirrors the legacy ``Platform._execute_qblox_compilation_output`` QDAC
coordination. See the module-level report for the exact wiring.
"""

from __future__ import annotations

import math
from collections import deque
from typing import TYPE_CHECKING, Any

import numpy as np
from qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qprogram.waveforms import Arbitrary
from qprogram_qdac.operations import Play as QdacPlay
from qprogram_qdac.operations import SetOffset as QdacSetOffset
from qprogram_qdac.operations import SetTrigger as QdacSetTrigger
from qprogram_qdac.operations import WaitTrigger as QdacWaitTrigger

from qililab.config import logger
from qililab.instruments.qdevil import QDevilQDac2
from qililab.qprogram.qdac_compiler import QdacCompilationOutput  # reuse the legacy output dataclass
from qililab.typings.enums import Parameter

if TYPE_CHECKING:
    from collections.abc import Callable

    from qprogram.operations.operation import Operation
    from qprogram.qprogram import QProgram

    from qililab.platform.components.bus import Bus


class QdacBusCompilationInfo:
    """Per-bus bookkeeping the compiler keeps while walking the QProgram."""

    def __init__(self) -> None:
        self.qprogram_block_stack: deque[Block] = deque()
        self.loop_counter = 0
        self.dc_set: bool = False


class QdacCompilerV2:
    """Compile a new-AST :class:`~qprogram.QProgram` onto QDAC-II instruments."""

    def __init__(self) -> None:
        self._handlers: dict[type, Callable] = {
            Parallel: self._handle_parallel,
            Average: self._handle_average,
            ForLoop: self._handle_for_loop,
            Loop: self._handle_loop,
            QdacSetOffset: self._handle_set_offset,
            QdacPlay: self._handle_play,
            QdacWaitTrigger: self._handle_wait_trigger,
            QdacSetTrigger: self._handle_set_trigger,
            Block: self._handle_block,
        }

        self._qprogram: QProgram
        self._buses: dict[str, QdacBusCompilationInfo]
        self._qdac_buses: list[Bus]
        self._qdac_buses_by_alias: dict[str, Bus]
        self._qdac_buses_alias: list[str]
        self._qdac_buses_offset: dict[str, float]
        self._channels: dict[str, int]
        self._qdacs: list[QDevilQDac2]
        self._out_instrument: QDevilQDac2 | None

        self._dc_dwell: int = 2
        self._dc_delay: int = 0
        self._dc_stepped: bool = False
        self._loop_repetitions: dict[str, int] = {}
        self._play_params: dict[str, Any] = {}

        self._trigger_hashes: dict[str, str] = {}
        self._trigger_position: str | None = None
        # Buses introduced on the fly (e.g. a trigger bus that had no DC list). Tracked separately
        # because the new QProgram.buses is a computed property and cannot be mutated like the legacy set.
        self._extra_buses: set[str] = set()

    # ------------------------------------------------------------------ entry point

    def compile(
        self,
        qprogram: QProgram,
        qdacs: list[QDevilQDac2],
        qdac_buses: list[Bus],
        qdac_offsets: list[float],
        out_instrument: QDevilQDac2 | None = None,
    ) -> QdacCompilationOutput:
        """Walk ``qprogram`` and program the QDAC instruments.

        Args:
            qprogram: The program to compile (its QDAC-bus operations are realised on the devices).
            qdacs: The QDAC-II instruments in play.
            qdac_buses: The platform buses backed by a QDAC channel.
            qdac_offsets: The resting offset voltage of each ``qdac_buses`` entry (same order).
            out_instrument: When more than one QDAC is used, the instrument that drives the shared
                output trigger.

        Returns:
            A :class:`QdacCompilationOutput` carrying the (programmed) instruments and the trigger
            position used to coordinate the QDAC ``start()`` with the Qblox run.
        """

        def traverse(block: Block) -> None:
            for bus in self._qdac_buses_alias:
                self._buses[bus].qprogram_block_stack.append(block)
            for element in block.elements:
                handler = self._handlers.get(type(element))
                if handler is None:
                    self._handle_unknown(element)
                else:
                    handler(element)
                if isinstance(element, Block):
                    traverse(element)
            for bus in self._qdac_buses_alias:
                self._buses[bus].qprogram_block_stack.pop()

        self._qprogram = qprogram
        self._qdacs = qdacs
        self._out_instrument = out_instrument
        self._qdac_buses = qdac_buses
        self._qdac_buses_by_alias = {bus.alias: bus for bus in qdac_buses}
        self._qdac_buses_alias = [bus.alias for bus in qdac_buses]
        self._qdac_buses_offset = dict(zip(self._qdac_buses_alias, qdac_offsets))

        self._populate_qdac_buses()
        traverse(qprogram.body)

        if len(self._qdacs) > 1:
            self._handle_simultaneous_qdacs()

        return QdacCompilationOutput(qprogram=qprogram, qdacs=self._qdacs, trigger_position=self._trigger_position)

    def _populate_qdac_buses(self) -> None:
        self._buses = {bus: QdacBusCompilationInfo() for bus in self._qdac_buses_alias}
        self._loop_repetitions.update(dict.fromkeys(self._qdac_buses_alias, 1))
        self._channels = {bus.alias: bus.channels[0] for bus in self._qdac_buses}

    # ------------------------------------------------------------------ control flow

    def _handle_parallel(self, element: Parallel) -> bool:
        if not element.loops:
            raise NotImplementedError("Parallel block should contain loops.")
        iterations = []
        for loop in element.loops:
            if isinstance(loop, ForLoop):
                iterations.append(QdacCompilerV2._convert_for_loop_values(loop))
            else:
                iterations.append(int(loop.values.shape[0]))
        for alias in self._qdac_buses_alias:
            self._loop_repetitions[alias] *= min(iterations) + 1
        for bus in self._buses:
            self._buses[bus].loop_counter += 1
        return True

    def _handle_average(self, element: Average) -> bool:
        for alias in self._qdac_buses_alias:
            self._loop_repetitions[alias] *= element.shots + 1
        for bus in self._buses:
            self._buses[bus].loop_counter += 1
        return True

    def _handle_for_loop(self, element: ForLoop) -> bool:
        iterations = QdacCompilerV2._convert_for_loop_values(element)
        for alias in self._qdac_buses_alias:
            self._loop_repetitions[alias] *= iterations + 1
        for bus in self._buses:
            self._buses[bus].loop_counter += 1
        return True

    def _handle_loop(self, element: Loop) -> bool:
        for alias in self._qdac_buses_alias:
            self._loop_repetitions[alias] *= int(element.values.shape[0]) + 1
        for bus in self._buses:
            self._buses[bus].loop_counter += 1
        return True

    def _handle_block(self, element: Block) -> None:
        pass

    # ------------------------------------------------------------------ operations

    def _handle_set_offset(self, element: QdacSetOffset) -> None:
        if element.bus not in self._qdac_buses_alias:
            return
        instrument = self._qdac_instrument(element.bus)
        instrument.set_parameter(
            parameter=Parameter.VOLTAGE, value=element.offset, channel_id=self._channels[element.bus]
        )
        self._buses[element.bus].dc_set = True

    def _handle_play(self, element: QdacPlay) -> None:
        if element.bus not in self._qdac_buses_alias:
            return
        if element.variables():
            logger.error("Variables in waveforms are not supported in QDAC.")
            return
        instrument = self._qdac_instrument(element.bus)

        dwell = element.dwell if element.dwell else self._dc_dwell
        delay = element.delay if element.delay else self._dc_delay
        stepped = element.stepped if element.stepped else self._dc_stepped
        # A default (1) repetitions means "let the enclosing loops decide"; an explicit >1 wins.
        repetitions = (
            element.repetitions
            if element.repetitions and element.repetitions != 1
            else (self._loop_repetitions[element.bus])
        )

        self._play_params = {
            "waveform": element.waveform.envelope(),
            "dwell": dwell,
            "delay": delay,
            "stepped": stepped,
            "repetitions": repetitions,
        }

        instrument.upload_voltage_list(
            waveform=element.waveform,
            channel_id=self._channels[element.bus],
            dwell_us=dwell,
            sync_delay_s=delay,
            repetitions=repetitions,
            stepped=stepped,
        )
        self._loop_repetitions[element.bus] = 1

    def _handle_wait_trigger(self, element: QdacWaitTrigger) -> None:
        if element.bus not in self._qdac_buses_alias:
            return
        instrument = self._qdac_instrument(element.bus)
        if element.port:
            instrument.set_in_external_trigger(channel_id=self._channels[element.bus], in_port=element.port)
            if not self._trigger_position:
                self._trigger_position = "back"
        else:
            instrument.set_in_internal_trigger(
                channel_id=self._channels[element.bus],
                trigger=next(trigger for _, trigger in self._trigger_hashes.items()),
            )

    def _handle_set_trigger(self, element: QdacSetTrigger) -> None:
        if element.bus not in self._qdac_buses_alias:
            return
        if element.position not in {"end", "start", "step", "end_step"}:
            raise NotImplementedError(
                f"position must be 'end', 'start', 'step' or 'end_step'. {element.position} is not recognized"
            )

        trigger_buses = [
            bus.alias
            for bus in self._qdac_buses
            if any(instrument.trigger_sync for instrument in bus.instruments if isinstance(instrument, QDevilQDac2))
        ]
        if not trigger_buses:
            raise ValueError(
                "Cannot set Trigger without an instrument set as trigger_sync = True. "
                "Modify the runcard and add trigger_sync to a QDAC-II instrument."
            )
        instrument = self._qdac_instrument(trigger_buses[0])

        if element.bus not in trigger_buses:
            trigger_bus = next(
                (
                    bus
                    for bus in trigger_buses
                    if f"{instrument.device.name}_{self._channels[bus]}" in instrument._cache_dc
                ),
                None,
            )
            if trigger_bus is None:
                if not self._play_params:
                    raise ValueError("No DC list with the given channel ID; first create a DC list using qdac.play.")
                trigger_bus = trigger_buses[0]
                voltage = instrument.settings.voltage[self._channels[trigger_bus]]
                self._handle_play(
                    QdacPlay(
                        bus=trigger_bus,
                        waveform=Arbitrary(np.ones(self._play_params["waveform"].shape) * voltage),
                        dwell=self._play_params["dwell"],
                        delay=self._play_params["delay"],
                        repetitions=self._play_params["repetitions"],
                        stepped=self._play_params["stepped"],
                    )
                )
                self._extra_buses.add(trigger_bus)
        else:
            trigger_bus = element.bus

        if element.outputs:
            for output in element.outputs:
                trigger = self._hash_trigger(element, output)
                channel = self._channels[trigger_bus]
                if element.position == "end":
                    instrument.set_end_marker_external_trigger(
                        channel_id=channel, out_port=output, trigger=trigger, width_s=element.duration
                    )
                elif element.position == "start":
                    instrument.set_start_marker_external_trigger(
                        channel_id=channel, out_port=output, trigger=trigger, width_s=element.duration
                    )
                elif element.position == "step":
                    instrument.set_start_marker_external_trigger(
                        channel_id=channel, out_port=output, trigger=trigger, width_s=element.duration, step=True
                    )
                elif element.position == "end_step":
                    instrument.set_end_marker_external_trigger(
                        channel_id=channel, out_port=output, trigger=trigger, width_s=element.duration, step=True
                    )
            if not self._trigger_position:
                self._trigger_position = "front"
        else:
            trigger = self._hash_trigger(element, None)
            channel = self._channels[trigger_bus]
            if element.position == "end":
                instrument.set_end_marker_internal_trigger(channel_id=channel, trigger=trigger)
            elif element.position == "start":
                instrument.set_start_marker_internal_trigger(channel_id=channel, trigger=trigger)
            elif element.position == "step":
                instrument.set_start_marker_internal_trigger(channel_id=channel, trigger=trigger, step=True)
            elif element.position == "end_step":
                instrument.set_end_marker_internal_trigger(channel_id=channel, trigger=trigger, step=True)

    def _handle_unknown(self, element: Operation) -> None:
        """Reject RF / timing / readout operations that touch a QDAC bus (no NCO / sequencer / ADC)."""
        from qprogram.operations import (
            Measure,
            ResetPhase,
            SetFrequency,
            SetGain,
            SetPhase,
            Sync,
            Wait,
        )

        unsupported: tuple[type, ...] = (SetFrequency, SetPhase, ResetPhase, SetGain, Wait, Measure)
        try:
            from qprogram_qblox.operations import Acquire, SetMarkers

            unsupported = (*unsupported, Acquire, SetMarkers)
        except ImportError:  # pragma: no cover - qblox extension not installed
            pass

        if isinstance(element, unsupported) and getattr(element, "bus", None) in self._qdac_buses_alias:
            raise NotImplementedError(f"{type(element).__name__} is not supported on a QDAC-II bus.")
        if (
            isinstance(element, Sync)
            and element.targets
            and any(bus in self._qdac_buses_alias for bus in element.targets)
        ):
            raise NotImplementedError("Sync is not supported on a QDAC-II bus.")

    # ------------------------------------------------------------------ helpers

    def _qdac_instrument(self, alias: str) -> QDevilQDac2:
        return next(
            instrument
            for instrument in self._qdac_buses_by_alias[alias].instruments
            if isinstance(instrument, QDevilQDac2)
        )

    def _hash_trigger(self, element: QdacSetTrigger, output: int | None) -> str:
        trigger_hash = f"trigger_{element.bus}_{output}_{element.position}"
        self._trigger_hashes[element.bus] = trigger_hash
        return trigger_hash

    def _handle_simultaneous_qdacs(self) -> None:
        program_buses = set(self._qprogram.buses) | self._extra_buses
        out_bus = next(
            (
                bus.alias
                for bus in self._qdac_buses
                if self._out_instrument in bus.instruments and bus.alias in program_buses
            ),
            None,
        )
        self._out_instrument.set_out_external_trigger(
            channel_id=self._channels[out_bus],
            out_port=self._out_instrument.out_trigger,
            trigger="qdac_external_trigger",
        )
        for in_instrument in self._qdacs:
            if in_instrument is not self._out_instrument:
                for bus in (bus.alias for bus in self._qdac_buses if in_instrument in bus.instruments):
                    if f"{in_instrument.device.name}_{self._channels[bus]}" in in_instrument._cache_dc:
                        in_instrument.set_in_external_trigger(
                            channel_id=self._channels[bus], in_port=in_instrument.in_trigger
                        )
        self._qdacs = [qdac for qdac in self._qdacs if qdac is not self._out_instrument] + [self._out_instrument]

    @staticmethod
    def _calculate_iterations(start: float, stop: float, step: float) -> int:
        if step == 0:
            raise ValueError("Step value cannot be zero")
        raw_iterations = (stop - start + step) / step
        if abs(raw_iterations - round(raw_iterations)) < 1e-9:
            return round(raw_iterations)
        return math.floor(raw_iterations) if step > 0 else math.ceil(raw_iterations)

    @staticmethod
    def _convert_for_loop_values(for_loop: ForLoop) -> int:
        return QdacCompilerV2._calculate_iterations(start=for_loop.start, stop=for_loop.stop, step=for_loop.step)
