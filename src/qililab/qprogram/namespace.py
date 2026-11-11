# Copyright 2026 Qilimanjaro Quantum Tech
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
"""``qp.qblox``: qprogram-qblox's namespace plus the Qblox operations and options qililab adds."""

from collections.abc import Iterable

from qprogram import MeasurementHandle
from qprogram.operations import Measure, Play
from qprogram.operations.operation import MeasurementField
from qprogram.waveforms import IQWaveform, Waveform
from qprogram_qblox import Acquire, QbloxNamespace

from qililab.qprogram.blocks.for_loop import to_scalar
from qililab.qprogram.operations.disable_autosync import DisableAutosync
from qililab.qprogram.operations.measure_reset import MeasureReset
from qililab.qprogram.operations.play import QbloxPlay


class QililabQbloxNamespace(QbloxNamespace):
    """The ``qp.qblox`` namespace of a qililab ``QProgram``.

    Adds to qprogram-qblox's operations (``acquire``, ``scope``, ``set_markers``, ``set_trigger``, ``wait_trigger``)
    the ones qililab owns, ``play`` with a ``wait_time`` and ``measure_reset``, and the Qblox compiler option
    ``disable_autosync``.
    """

    @property
    def disable_autosync(self) -> bool:
        """Whether the Qblox compiler leaves out its sync of every bus at the end of each loop and average.

        Defaults to False. Setting it to True adds a ``DisableAutosync`` operation at the top of the program's body, so
        that the setting is part of the program: copies and ``.qp`` files keep it.
        """
        return any(isinstance(element, DisableAutosync) for element in self._program.body.elements)

    @disable_autosync.setter
    def disable_autosync(self, value: bool) -> None:
        elements = self._program.body.elements
        elements[:] = [element for element in elements if not isinstance(element, DisableAutosync)]
        if value:
            elements.insert(0, DisableAutosync())

    @property
    def weight_duration(self) -> dict[str, list[int | str]]:
        """Weight durations per bus, in acquisition order: an int in ns, or the name of calibrated weights.

        Read from the program's measurements, so it always matches the program, including after a bus mapping.
        """
        durations: dict[str, list[int | str]] = {}
        for node in self._program.body.walk():
            if isinstance(node, (Measure, Acquire, MeasureReset)):
                weights = node.weights
                durations.setdefault(node.bus, []).append(
                    weights.get_duration() if isinstance(weights, IQWaveform) else weights
                )
        return durations

    def set_markers(self, bus: str, mask: str) -> None:
        """Set the markers based on a 4-bit binary mask.

        Args:
            bus (str): Unique identifier of the bus.
            mask (str): A 4-bit mask, where 0 means that the associated marker is open (no signal), and 1 means that the
                marker is closed (signal).

        Raises:
            AttributeError: If ``mask`` is not 4 characters of ``0`` and ``1``.
        """
        if len(mask) != 4 or not set(mask).issubset({"0", "1"}):
            raise AttributeError("Marker should be a 4-bit binary string.")
        super().set_markers(bus, mask)

    # qprogram-qblox stores numpy numbers as they are, so a program no longer compares equal once saved and
    # reloaded: set_trigger and wait_trigger convert them to Python numbers first. Remove once qprogram does it
    # itself (QHC-1873).

    def set_trigger(
        self, bus: str, duration: int, outputs: list[int] | int | None = None, position: str = "start"
    ) -> None:
        """Fire Qblox trigger outputs for ``duration`` ns.

        Args:
            bus (str): Unique identifier of the bus.
            duration (int): Duration of the trigger pulse, in ns (minimum 4 ns).
            outputs (list[int] | int | None, optional): Trigger output or outputs. Defaults to None.
            position (str, optional): Point at which the trigger fires, ``"start"`` or ``"end"``. Defaults to
                ``"start"``.
        """
        super().set_trigger(bus, to_scalar(duration), outputs, position)  # type: ignore[arg-type]

    def wait_trigger(self, bus: str, duration: int, port: int | None = None) -> None:
        """Wait for the cluster's external trigger, then ``duration`` ns.

        Args:
            bus (str): Unique identifier of the bus.
            duration (int): Duration of the wait after the trigger, in ns (minimum 4 ns).
            port (int | None, optional): Ignored on Qblox buses, which always wait on the cluster's external trigger
                address. Defaults to None.
        """
        super().wait_trigger(bus, to_scalar(duration), port)  # type: ignore[arg-type]

    def play(self, bus: str, waveform: Waveform | IQWaveform | str, wait_time: int | None) -> None:
        """Play a waveform, where the Q1ASM ``play`` instruction waits ``wait_time`` ns instead of the waveform's duration.

        Args:
            bus (str): Unique identifier of the bus.
            waveform (Waveform | IQWaveform | str): The waveform, or the name of a calibrated one.
            wait_time (int | None): Overwrite the value of Q1ASM play instruction's wait_time parameter. None plays the
                waveform like ``play``.
        """
        if wait_time is None:
            self._append(Play(bus=bus, waveform=waveform))
            return
        self._append(QbloxPlay(bus=bus, waveform=waveform, wait_time=wait_time))

    def measure_reset(
        self,
        bus: str,
        waveform: IQWaveform | str,
        weights: IQWaveform | str,
        control_bus: str,
        reset_pulse: IQWaveform | str,
        trigger_address: int = 1,
        fields: Iterable[MeasurementField] = (MeasurementField.IQ,),
        *,
        name: str | None = None,
    ) -> MeasurementHandle:
        """Play a measurement and conditionally apply a reset pulse based on the result: active reset for transmons.

        If the thresholded measurement result is 1, a corrective pulse is applied on the control_bus.
        If the result is 0, the control_bus waits instead.

        Args:
            bus (str): Identifier of the measurement bus.
            waveform (IQWaveform | str): Waveform played during measurement.
            weights (IQWaveform | str): Weights used for demodulation/integration.
            control_bus (str): Identifier of the control/reset bus.
            reset_pulse (IQWaveform | str): Pulse used for active reset.
            trigger_address (int, optional): Trigger address for synchronization. Defaults to 1.
            fields (Iterable[MeasurementField], optional): The measurement fields to return. Defaults to ``(IQ,)``.
            name (str | None, optional): Name of the measurement. Allocated like any measurement's when omitted.

        Returns:
            MeasurementHandle: The handle the results are stored under.

        Raises:
            NotImplementedError: If the waveform, weights and reset pulse are not all calibrated names or all
                waveforms.
        """
        calibrated = [isinstance(component, str) for component in (waveform, weights, reset_pulse)]
        if any(calibrated) and not all(calibrated):
            raise NotImplementedError(
                "For the waveform, weight, and reset pulse, you must either use the calibration file for all three "
                "or not use it at all."
            )
        return self._append_measurement(
            MeasureReset,
            bus=bus,
            name=name,
            waveform=waveform,
            weights=weights,
            control_bus=control_bus,
            reset_pulse=reset_pulse,
            trigger_address=trigger_address,
            fields=fields,
        )
