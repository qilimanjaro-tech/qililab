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
"""Reads QPrograms and calibration blocks that qililab saved as YAML before it moved to qprogram.

Importing this module registers, on qililab's YAML instance, a constructor for every tag of qililab's former QProgram
classes (``!QProgram``, ``!ForLoop``, ``!Play``, ``!IntVariable``, ...). Each one builds the qprogram node that does the
same thing, so ``deserialize`` of an old program, or of a calibration holding old blocks, returns qprogram objects.

The former operations did not say which instrument they were for: a ``play`` became a QDAC play only at compile time,
when its bus was a QDAC bus. Here an operation becomes a QDAC one when it carries an argument only the QDAC takes (a
play's ``dwell``, ``delay``, ``repetitions`` or ``stepped``, a wait for a trigger's ``port``, a trigger at each
``step``). For the others, pass the QDAC buses to `qdac_operations`.
"""

from __future__ import annotations

import warnings
from collections import deque
from typing import TYPE_CHECKING, Any, cast

import qprogram as qp
from qprogram import MeasurementHandle, Values, Variable
from qprogram.blocks import Average, Block, Parallel, Sweep
from qprogram.operations import (
    Measure,
    Operation,
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qprogram.operations.operation import MeasurementOperation
from qprogram.waveforms import IQWaveform, Waveform
from qprogram_qblox import Acquire, SetMarkers
from qprogram_qblox import SetTrigger as QbloxSetTrigger
from qprogram_qblox import WaitTrigger as QbloxWaitTrigger
from qprogram_qdac import Play as QdacPlay
from qprogram_qdac import SetOffset as QdacSetOffset
from qprogram_qdac import SetTrigger as QdacSetTrigger
from qprogram_qdac import WaitTrigger as QdacWaitTrigger

from qililab.qprogram.blocks import ForLoop, IfTrigger, InfiniteLoop
from qililab.qprogram.operations import MeasureReset, QbloxPlay
from qililab.qprogram.variable_ids import unique_variable_id
from qililab.yaml import yaml

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from ruamel.yaml.constructor import BaseConstructor
    from ruamel.yaml.nodes import MappingNode, Node, ScalarNode

    from qililab.qprogram.qprogram import QProgram

# The former variables were copied wherever they were used, one YAML mapping per use, sharing only their UUID: one
# qprogram variable per UUID and per document gives them back their identity. They are kept under this key in the
# constructor's table of the objects read from the document, which ruamel empties after each document.
_DOCUMENT_VARIABLES = object()

_QDAC_ONLY_TRIGGER_POSITIONS = ("step", "end_step")


def _mapping(constructor: BaseConstructor, node: MappingNode) -> dict[str, Any]:
    """Construct a mapping node deeply.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        dict[str, Any]: The mapping.
    """
    return constructor.construct_mapping(node, deep=True)  # type: ignore[attr-defined]


def _construct_variable(constructor: BaseConstructor, node: MappingNode) -> Variable:
    """Build the qprogram variable of a former ``!IntVariable`` or ``!FloatVariable``, one per UUID in the document.

    Former variables were told apart by UUID, so two could share a label: the id is made from the label, unique in
    the document.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        Variable: The variable.
    """
    mapping = _mapping(constructor, node)
    uuid = mapping["_uuid"].int
    variables: dict[int, Variable] = constructor.constructed_objects.setdefault(_DOCUMENT_VARIABLES, {})
    variable = variables.get(uuid)
    if variable is None:
        label = mapping.get("_label") or "variable"
        variable = Variable(unique_variable_id(label, {other.id for other in variables.values()}), label=label)
        variables[uuid] = variable
    return variable


def _construct_expression(constructor: BaseConstructor, node: MappingNode) -> qp.Expression:
    """Build the qprogram expression of a former ``!VariableExpression``: ``left + right`` or ``left - right``.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        qp.Expression: The expression.
    """
    mapping = _mapping(constructor, node)
    left, right = mapping["left"], mapping["right"]
    return left + right if mapping["operator"] == "+" else left - right


def _construct_ignored(constructor: BaseConstructor, node: Node) -> None:
    """Read a former tag whose content qprogram does not keep (``!VariableInfo``).

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (Node): The node.
    """


def _construct_domain(constructor: BaseConstructor, node: ScalarNode) -> str:
    """Read a former ``!Domain``: variables have no domain any more, so its name is kept as plain text.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (ScalarNode): The node, ``<name>-<value>``.

    Returns:
        str: The domain's name.
    """
    return str(constructor.construct_scalar(node)).split("-")[0]  # type: ignore[attr-defined]


def _construct_namespace(constructor: BaseConstructor, node: MappingNode) -> Iterator[dict[str, Any]]:
    """Read a former ``!_QbloxInterface``, ``!_QdacInterface`` or ``!_QuantumMachinesInterface`` as a mapping.

    It refers back to the QProgram holding it, so it is built in two steps.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Yields:
        dict[str, Any]: The mapping, filled once the QProgram exists.
    """
    data: dict[str, Any] = {}
    yield data
    data.update(_mapping(constructor, node))


def _measurement_handle() -> MeasurementHandle:
    """Return a placeholder handle for a former measurement; the program holding it names it.

    Returns:
        MeasurementHandle: The handle.
    """
    return MeasurementHandle("legacy_measurement")


def _warn_save_adc(mapping: dict[str, Any]) -> None:
    """Warn that a former measurement saved the scope, which is now ``qp.qblox.scope``.

    Args:
        mapping (dict[str, Any]): The former measurement.
    """
    if mapping.get("save_adc"):
        warnings.warn(
            f"The measurement on bus {mapping['bus']!r} had save_adc=True, which no longer exists: add "
            f"qp.qblox.scope({mapping['bus']!r}) to the program to record the scope trace.",
            UserWarning,
            stacklevel=2,
        )


def _construct_play(constructor: BaseConstructor, node: MappingNode) -> Play | QbloxPlay | QdacPlay:
    """Build a former ``!Play`` or ``!PlayWithCalibratedWaveform``.

    It becomes a ``qp.qblox.play`` when it had a ``wait_time``, a ``qp.qdac.play`` when it had a QDAC argument, else a
    ``play``.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        Play | QbloxPlay | QdacPlay: The play.
    """
    mapping = _mapping(constructor, node)
    bus, waveform = mapping["bus"], mapping["waveform"]
    if mapping.get("wait_time") is not None:
        return QbloxPlay(bus=bus, waveform=waveform, wait_time=mapping["wait_time"])
    qdac_arguments = {key: mapping.get(key) for key in ("dwell", "delay", "repetitions", "stepped")}
    if any(value is not None for value in qdac_arguments.values()):
        return _qdac_play(bus, waveform, qdac_arguments)
    return Play(bus=bus, waveform=waveform)


def _qdac_play(bus: str, waveform: Waveform | IQWaveform | str, arguments: dict[str, Any]) -> QdacPlay:
    """Build a ``qp.qdac.play``, leaving qprogram-qdac's defaults for the arguments that were not given.

    Args:
        bus (str): The bus.
        waveform (Waveform | IQWaveform | str): The waveform, the I waveform of an IQ one, or the name of a calibrated
            one.
        arguments (dict[str, Any]): ``dwell``, ``delay``, ``repetitions`` and ``stepped``, None when not given.

    Returns:
        QdacPlay: The play.
    """
    if isinstance(waveform, IQWaveform):
        waveform = waveform.get_I()
    # a calibrated waveform's name stays a str until the calibration resolves it
    return QdacPlay(
        bus=bus,
        waveform=cast("Waveform", waveform),
        **{key: value for key, value in arguments.items() if value is not None},
    )


def _construct_measure(constructor: BaseConstructor, node: MappingNode) -> Measure:
    """Build a former ``!Measure`` or ``!MeasureWithCalibrated...``: a ``measure`` returning the IQ field.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        Measure: The measurement.
    """
    mapping = _mapping(constructor, node)
    _warn_save_adc(mapping)
    return Measure(
        bus=mapping["bus"], waveform=mapping["waveform"], weights=mapping["weights"], handle=_measurement_handle()
    )


def _construct_acquire(constructor: BaseConstructor, node: MappingNode) -> Acquire:
    """Build a former ``!Acquire`` or ``!AcquireWithCalibratedWeights``: a ``qp.qblox.acquire`` returning the IQ field.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        Acquire: The acquisition.
    """
    mapping = _mapping(constructor, node)
    _warn_save_adc(mapping)
    return Acquire(bus=mapping["bus"], weights=mapping["weights"], handle=_measurement_handle())


def _construct_measure_reset(constructor: BaseConstructor, node: MappingNode) -> MeasureReset:
    """Build a former ``!MeasureReset`` or ``!MeasureResetCalibrated``.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        MeasureReset: The measurement and reset.
    """
    mapping = _mapping(constructor, node)
    _warn_save_adc(mapping)
    return MeasureReset(
        bus=mapping["bus"],
        waveform=mapping["waveform"],
        weights=mapping["weights"],
        control_bus=mapping["control_bus"],
        reset_pulse=mapping["reset_pulse"],
        handle=_measurement_handle(),
        trigger_address=mapping.get("trigger_address", 1),
    )


def _construct_wait_trigger(constructor: BaseConstructor, node: MappingNode) -> QbloxWaitTrigger | QdacWaitTrigger:
    """Build a former ``!WaitTrigger``: a ``qp.qdac.wait_trigger`` when it had a ``port``, else ``qp.qblox`` one.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        QbloxWaitTrigger | QdacWaitTrigger: The wait for a trigger.
    """
    mapping = _mapping(constructor, node)
    if mapping.get("port") is not None:
        return QdacWaitTrigger(bus=mapping["bus"], port=mapping["port"])
    return QbloxWaitTrigger(bus=mapping["bus"], duration=mapping["duration"])


def _construct_set_trigger(constructor: BaseConstructor, node: MappingNode) -> QbloxSetTrigger | QdacSetTrigger:
    """Build a former ``!SetTrigger``.

    It becomes a ``qp.qdac.set_trigger`` when it fired at each step (a QDAC position) or lasted under a millisecond
    (QDAC durations were in seconds, Qblox ones in ns), else a ``qp.qblox.set_trigger``.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        QbloxSetTrigger | QdacSetTrigger: The trigger.
    """
    mapping = _mapping(constructor, node)
    bus, duration, outputs, position = mapping["bus"], mapping["duration"], mapping.get("outputs"), mapping["position"]
    if position in _QDAC_ONLY_TRIGGER_POSITIONS or duration < 1e-3:
        if outputs is None:
            outputs = []
        elif not isinstance(outputs, list):
            outputs = [outputs]
        return QdacSetTrigger(bus=bus, duration=duration, position=cast("Any", position), outputs=outputs)
    return QbloxSetTrigger(bus=bus, duration=duration, outputs=outputs, position=position)


def _operation(cls: type[Operation], *attributes: str) -> Callable[[BaseConstructor, MappingNode], Operation]:
    """Return a constructor for a former operation that maps onto ``cls`` with the same attributes.

    Args:
        cls (type[Operation]): The qprogram operation class.
        *attributes (str): The attributes passed on as keyword arguments.

    Returns:
        Callable[[BaseConstructor, MappingNode], Operation]: The constructor.
    """

    def construct(constructor: BaseConstructor, node: MappingNode) -> Operation:
        mapping = _mapping(constructor, node)
        return cls(**{attribute: mapping.get(attribute) for attribute in attributes if attribute in mapping})

    return construct


def _construct_sync(constructor: BaseConstructor, node: MappingNode) -> Sync:
    """Build a former ``!Sync``, whose ``buses`` are now ``targets``.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Returns:
        Sync: The sync.
    """
    return Sync(targets=_mapping(constructor, node).get("buses") or None)


def _fill(block: Block, elements: list) -> Block:
    """Append ``elements`` to ``block`` and return it.

    Args:
        block (Block): The block.
        elements (list): Its elements.

    Returns:
        Block: The block.
    """
    for element in elements:
        block.append(element)
    return block


def _block(factory: Callable[[dict[str, Any]], Block]) -> Callable[[BaseConstructor, MappingNode], Block]:
    """Return a constructor for a former block, built by ``factory`` from its mapping.

    Args:
        factory (Callable[[dict[str, Any]], Block]): Builds the empty qprogram block from the former block's mapping.

    Returns:
        Callable[[BaseConstructor, MappingNode], Block]: The constructor.
    """

    def construct(constructor: BaseConstructor, node: MappingNode) -> Block:
        mapping = _mapping(constructor, node)
        return _fill(factory(mapping), mapping.get("elements", []))

    return construct


def _construct_qprogram(constructor: BaseConstructor, node: MappingNode) -> Iterator[QProgram]:
    """Build a former ``!QProgram`` as a qililab ``QProgram``.

    Its measurements are named ``m0``, ``m1``, ... in the order they come, as a new program names them. It refers to
    itself (through its namespaces), so it is built in two steps.

    Args:
        constructor (BaseConstructor): The YAML constructor.
        node (MappingNode): The node.

    Yields:
        QProgram: The program, filled once its content is built.
    """
    from qililab.qprogram.qprogram import QProgram

    program = QProgram()
    yield program
    mapping = _mapping(constructor, node)
    program._body = mapping["_body"]
    program._block_stack = deque([program._body])
    program._variables = list(mapping.get("_variables", {}))
    program.qblox.disable_autosync = bool(mapping.get("qblox", {}).get("disable_autosync", False))
    for index, operation in enumerate(node for node in program.body.walk() if isinstance(node, MeasurementOperation)):
        operation.handle.name = f"m{index}"


def qdac_operations(qprogram: QProgram, qdac_buses: set[str]) -> QProgram:
    """Return a copy of a QProgram read from old YAML with its operations on ``qdac_buses`` made QDAC ones.

    The former ``play``, ``set_offset``, ``wait_trigger`` and ``set_trigger`` did not say they were for the QDAC; those
    the loader could not tell apart become ``qp.qdac.play``, ``qp.qdac.set_offset``, ``qp.qdac.wait_trigger`` and
    ``qp.qdac.set_trigger`` here when their bus is a QDAC bus.

    Args:
        qprogram (QProgram): The program read from old YAML.
        qdac_buses (set[str]): The QDAC buses.

    Returns:
        QProgram: The copy, with QDAC operations on the QDAC buses.

    Raises:
        ValueError: If a ``wait_trigger`` on a QDAC bus has no port.
    """
    from copy import deepcopy

    program = deepcopy(qprogram)

    def convert(element: Block | Operation) -> Block | Operation:
        if getattr(element, "bus", None) not in qdac_buses:
            return element
        if isinstance(element, Play):
            return _qdac_play(element.bus, element.waveform, {})
        if isinstance(element, SetOffset):
            return QdacSetOffset(bus=element.bus, offset=element.offset_path0)
        if isinstance(element, QbloxWaitTrigger):
            if element.port is None:
                raise ValueError(f"The wait_trigger on QDAC bus {element.bus!r} has no port, which the QDAC requires.")
            return QdacWaitTrigger(bus=element.bus, port=element.port)
        if isinstance(element, QbloxSetTrigger):
            outputs = [] if element.outputs is None else element.outputs
            outputs = outputs if isinstance(outputs, list) else [outputs]
            return QdacSetTrigger(
                bus=element.bus, duration=element.duration, position=cast("Any", element.position), outputs=outputs
            )
        return element

    for block in (node for node in program.body.walk() if isinstance(node, Block)):
        block.elements[:] = [convert(element) for element in block.elements]
    return program


def _register() -> None:
    """Register a constructor for every tag of qililab's former QProgram classes on qililab's YAML instance."""
    add = yaml.constructor.add_constructor
    for tag in ("!IntVariable", "!FloatVariable"):
        add(tag, _construct_variable)
    add("!VariableExpression", _construct_expression)
    add("!VariableInfo", _construct_ignored)
    add("!Domain", _construct_domain)
    for tag in ("!_QbloxInterface", "!_QdacInterface", "!_QuantumMachinesInterface"):
        add(tag, _construct_namespace)
    for tag in ("!Play", "!PlayWithCalibratedWaveform"):
        add(tag, _construct_play)
    for tag in (
        "!Measure",
        "!MeasureWithCalibratedWaveform",
        "!MeasureWithCalibratedWeights",
        "!MeasureWithCalibratedWaveformWeights",
    ):
        add(tag, _construct_measure)
    for tag in ("!Acquire", "!AcquireWithCalibratedWeights"):
        add(tag, _construct_acquire)
    for tag in ("!MeasureReset", "!MeasureResetCalibrated"):
        add(tag, _construct_measure_reset)
    add("!WaitTrigger", _construct_wait_trigger)
    add("!SetTrigger", _construct_set_trigger)
    add("!Sync", _construct_sync)
    add("!Wait", _operation(Wait, "bus", "duration"))
    add("!SetFrequency", _operation(SetFrequency, "bus", "frequency"))
    add("!SetPhase", _operation(SetPhase, "bus", "phase"))
    add("!ResetPhase", _operation(ResetPhase, "bus"))
    add("!SetGain", _operation(SetGain, "bus", "gain"))
    add("!SetOffset", _operation(SetOffset, "bus", "offset_path0", "offset_path1"))
    add("!SetMarkers", _operation(SetMarkers, "bus", "mask"))
    add("!Block", _block(lambda _: Block()))
    add("!Average", _block(lambda mapping: Average(shots=mapping["shots"])))
    add("!InfiniteLoop", _block(lambda _: InfiniteLoop()))
    add(
        "!Conditional",
        _block(
            lambda mapping: IfTrigger(
                trigger_padding_ns=mapping.get("trigger_padding_ns"),
                expected_wait_time_ns=mapping.get("expected_wait_time_ns"),
            )
        ),
    )
    add(
        "!ForLoop",
        _block(
            lambda mapping: Sweep(
                mapping["variable"],
                ForLoop(mapping["variable"], mapping["start"], mapping["stop"], mapping["step"]).to_range(),
            )
        ),
    )
    add("!Loop", _block(lambda mapping: Sweep(mapping["variable"], Values(mapping["values"]))))
    add("!Parallel", _block(lambda mapping: Parallel(mapping["loops"])))
    add("!QProgram", _construct_qprogram)


_register()
