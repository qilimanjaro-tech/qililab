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
"""Turn the raw acquisitions of a Qblox QRM into qprogram measurement results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import xarray as xr
from qprogram.blocks import Parallel, Sweep
from qprogram.operations.operation import MeasurementField

if TYPE_CHECKING:
    from qililab.qprogram.compilers.qblox_compiler import AcquisitionData

MeasurementFields = dict[str, xr.DataArray]
"""The arrays of one measurement, keyed by field name (``iq``, ``state``, ``raw``)."""


def _dimension(loop: Sweep | Parallel, wait_points: dict[str, np.ndarray]) -> tuple[str, dict[str, Any]]:
    """Return the dimension a loop gives a measurement, named as qprogram names it, with its coordinates.

    A sweep gives a dimension named after its variable; a parallel gives one dimension, ``"a|b"``, carrying the
    coordinates of each of its variables. A loop over a wait is labelled with the whole ns it runs.

    Args:
        loop (Sweep | Parallel): The loop.
        wait_points (dict[str, np.ndarray]): The points the variable of each loop over a wait runs, by variable id.

    Returns:
        tuple[str, dict[str, Any]]: The dimension's name, and its coordinates as xarray takes them.
    """
    sweeps = loop.loops if isinstance(loop, Parallel) else [loop]
    name = "|".join(sweep.variable.id for sweep in sweeps)
    coordinates = {
        sweep.variable.id: xr.Variable(
            name,
            wait_points.get(sweep.variable.id, sweep.source.values()),
            attrs={
                key: value
                for key, value in (("long_name", sweep.variable.label), ("units", sweep.variable.units))
                if value is not None
            },
        )
        for sweep in sweeps
    }
    return name, coordinates


def measurement_fields(raw: dict, acquisition: AcquisitionData) -> list[tuple[str, MeasurementFields]]:
    """Split the bins of one Qblox acquisition into the arrays of the measurements writing into it.

    The measurements take the bins in turn, so measurement ``k`` of ``N`` reads bins ``k``, ``k + N``, ... Each gets
    the fields it asked for: ``iq``, dims ``(*sweeps, "IQ")``, from the integration bins, and ``state``, dims
    ``(*sweeps)``, from the thresholded bins (the excited-state population when averaged).

    Args:
        raw (dict): The acquisition as the QRM returns it: ``{"bins": {"integration": {"path0", "path1"},
            "threshold", "avg_cnt"}, "scope": ...}``.
        acquisition (AcquisitionData): What the compiler recorded about the acquisition.

    Returns:
        list[tuple[str, MeasurementFields]]: The name and the arrays of each measurement, in bin order.
    """
    dimensions = [_dimension(loop, acquisition.wait_points) for loop in acquisition.loops]
    dims = tuple(name for name, _ in dimensions)
    coords = {key: value for _, coordinates in dimensions for key, value in coordinates.items()}
    bins = raw["bins"]
    path0 = np.asarray(bins["integration"]["path0"], dtype=float)
    path1 = np.asarray(bins["integration"]["path1"], dtype=float)
    threshold = np.asarray(bins["threshold"], dtype=float)
    step = acquisition.intertwined
    records = []
    for index, (name, fields) in enumerate(zip(acquisition.measurements, acquisition.fields)):
        arrays: MeasurementFields = {}
        if MeasurementField.IQ in fields:
            iq = np.stack([path0[index::step], path1[index::step]], axis=-1).reshape(*acquisition.shape, 2)
            arrays[MeasurementField.IQ.value] = xr.DataArray(
                iq, dims=(*dims, "IQ"), coords={**coords, "IQ": ["I", "Q"]}
            )
        if MeasurementField.STATE in fields:
            state = threshold[index::step].reshape(acquisition.shape)
            arrays[MeasurementField.STATE.value] = xr.DataArray(state, dims=dims, coords=coords)
        records.append((name, arrays))
    return records


def scope_trace(raw: dict) -> xr.DataArray:
    """Return the scope trace stored in an acquisition, dims ``("time", "IQ")``: the QRM's two inputs, in ns.

    Args:
        raw (dict): The acquisition the scope was stored in, as the QRM returns it.

    Returns:
        xr.DataArray: The trace, not demodulated.
    """
    scope = raw["scope"]
    trace = np.stack(
        [np.asarray(scope["path0"]["data"], dtype=float), np.asarray(scope["path1"]["data"], dtype=float)], axis=-1
    )
    return xr.DataArray(trace, dims=("time", "IQ"), coords={"time": np.arange(len(trace)), "IQ": ["I", "Q"]})
