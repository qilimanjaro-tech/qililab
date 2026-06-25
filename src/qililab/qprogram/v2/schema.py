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

"""Build a :class:`qprogram.buses.BusSchema` from a qililab platform's runcard buses.

The new ``qprogram`` package routes capabilities per ``(element, bus_kind)`` slot and validates
programs against a :class:`~qprogram.buses.BusSchema`. qililab's runcard, however, describes buses
as flat aliases (``"drive"``, ``"resonator"``, ``"qdac_bus_1"``) with no qubit/element/kind
structure — the *vendor* of a bus is implied by the instrument attached to it (a
:class:`~qililab.instruments.qblox.QbloxModule` vs a :class:`~qililab.instruments.qdevil.QDevilQDac2`).

This module bridges the two: it builds a **flat** schema where each runcard bus alias becomes its
own element and the produced :class:`~qprogram.buses.BusRef` has its string value equal to the alias
(via the ``"{element}"`` naming pattern). That keeps the addressing identical to legacy qililab — a
program references a bus by its runcard alias — while still giving the validator a schema-backed
``BusRef`` it can route per ``(element, kind)``. The kind is derived from the bus role
(``readout`` if it has an ADC, ``flux`` for a QDAC, else ``drive``); since the element is unique per
alias, the ``(element, kind)`` pair is unique and maps cleanly to a vendor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qprogram.buses import BusNaming, BusRef, BusSchema

if TYPE_CHECKING:
    from collections.abc import Iterable

    from qililab.platform.components.bus import Bus

#: Vendor tag used as the ``bus_specs`` value and to pick the capability profile per bus.
Vendor = str  # "qblox" | "qdac"


def _vendor_of(bus: Bus) -> Vendor | None:
    """Return the vendor backing ``bus`` (``"qblox"`` / ``"qdac"``), or ``None`` if unrecognised."""
    from qililab.instruments.qblox import QbloxModule
    from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2

    if any(isinstance(instrument, QbloxModule) for instrument in bus.instruments):
        return "qblox"
    if any(isinstance(instrument, QDevilQDac2) for instrument in bus.instruments):
        return "qdac"
    return None


def _channel_of(bus: Bus, vendor: Vendor) -> str:
    """Return ``"IQ"`` or ``"single"`` for ``bus``.

    QDAC buses are single-path DC sources. Qblox QCM-RF / QRM-RF modules are IQ; for baseband
    modules the channel kind follows the sequencer output count (one output → single, else IQ),
    mirroring how :meth:`Platform.compile_qprogram` builds its ``single_channel`` list.
    """
    if vendor == "qdac":
        return "single"

    from qililab.instruments.qblox import QbloxModule
    from qililab.typings import InstrumentName

    for instrument, channel in zip(bus.instruments, bus.channels):
        if isinstance(instrument, QbloxModule):
            if instrument.name in (InstrumentName.QCMRF, InstrumentName.QRMRF):
                return "IQ"
            try:
                sequencer = instrument.get_sequencer(sequencer_id=channel)
            except Exception:  # noqa: BLE001 - defensive: fall back to IQ if introspection fails
                return "IQ"
            return "single" if len(sequencer.outputs) == 1 else "IQ"
    return "IQ"


def _kind_of(vendor: Vendor, *, acquires: bool) -> str:
    """Derive a bus *kind* from its role (used as the schema element's single bus kind)."""
    if vendor == "qdac":
        return "flux"
    return "readout" if acquires else "drive"


class RuncardBusSchema:
    """A flat :class:`~qprogram.buses.BusSchema` built from a platform's runcard buses.

    Attributes:
        schema: The :class:`~qprogram.buses.BusSchema` (naming pattern ``"{element}"`` so each
            ``BusRef``'s string value equals the runcard alias).
        bus_specs: Mapping ``(element, kind) -> vendor`` consumed by
            :func:`~qililab.qprogram.v2.capabilities.qililab_capabilities`.
        refs: Mapping ``alias -> BusRef`` — the schema-backed reference for each bus.
    """

    def __init__(self, schema: BusSchema, bus_specs: dict[tuple[str, str], Vendor], refs: dict[str, BusRef]) -> None:
        self.schema = schema
        self.bus_specs = bus_specs
        self.refs = refs

    def ref(self, alias: str) -> BusRef:
        """Return the schema-backed :class:`~qprogram.buses.BusRef` for a runcard bus ``alias``."""
        if alias not in self.refs:
            raise KeyError(f"Bus alias {alias!r} is not a recognised qblox/qdac bus on this platform.")
        return self.refs[alias]


def build_runcard_bus_schema(buses: Iterable[Bus]) -> RuncardBusSchema:
    """Build a :class:`RuncardBusSchema` from the platform's buses.

    Only buses backed by a recognised vendor (Qblox or QDAC) are included; others are skipped.

    Args:
        buses: The platform's :class:`~qililab.platform.components.bus.Bus` objects.

    Returns:
        A :class:`RuncardBusSchema` bundling the schema, the ``(element, kind) -> vendor`` specs, and
        the per-alias ``BusRef`` map.
    """
    schema = BusSchema(naming=BusNaming("{element}"))
    bus_specs: dict[tuple[str, str], Vendor] = {}
    refs: dict[str, BusRef] = {}

    for bus in buses:
        vendor = _vendor_of(bus)
        if vendor is None:
            continue
        alias = bus.alias
        acquires = bool(bus.has_adc())
        channel = _channel_of(bus, vendor)
        kind = _kind_of(vendor, acquires=acquires)

        schema.add_element(alias, {kind: (channel, acquires)})
        bus_specs[(alias, kind)] = vendor
        # Build the schema-backed BusRef; with the "{element}" naming pattern its value == alias.
        accessor = getattr(schema, alias)[0]
        refs[alias] = getattr(accessor, kind)

    return RuncardBusSchema(schema=schema, bus_specs=bus_specs, refs=refs)
