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

"""QDAC pre-pass: prepares a QProgram for the QDAC compiler, after the shared pre-pass."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qililab.qprogram.prepass.utils_prepass import keep_instrument_operations

if TYPE_CHECKING:
    import numpy as np

    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
    from qililab.qprogram.qprogram import QProgram


def prepare_qdac(
    qprogram: QProgram,
    *,
    qdac_buses: list[str],
    qdac_buses_offset: dict[str, float],
    calibration: Calibration | None = None,
    crosstalk: CrosstalkMatrix | None = None,
    target_fluxes: dict[str, float | list[float] | np.ndarray] | None = None,
) -> QProgram:
    """Prepare a QProgram, already through the shared pre-pass, for the QDAC compiler.

    Applies the crosstalk compensation (the given matrix, else the calibration's DC matrix), then keeps only the
    operations on QDAC buses.

    Args:
        qprogram (QProgram): The QProgram returned by the shared pre-pass. It is not modified.
        qdac_buses (list[str]): The QDAC buses.
        qdac_buses_offset (dict[str, float]): Bias voltage per QDAC bus, from which the crosstalk compensation recovers
            the flux of buses without a target flux.
        calibration (Calibration, optional): Calibration holding the DC crosstalk matrix. Defaults to None.
        crosstalk (CrosstalkMatrix, optional): Crosstalk matrix, used instead of the calibration's. Defaults to None.
        target_fluxes (dict[str, float | list[float] | np.ndarray], optional): Known target flux per bus, to seed the
            crosstalk compensation. Defaults to None.

    Returns:
        QProgram: A copy of the transformed QProgram with only the operations on QDAC buses.
    """
    if calibration is not None and calibration.crosstalk_matrix and crosstalk is None:
        crosstalk = calibration.crosstalk_matrix
    if crosstalk is not None:
        qprogram = qprogram.with_crosstalk_qdac(
            crosstalk=crosstalk, target_fluxes=target_fluxes, qdac_buses_offset=qdac_buses_offset
        )
    return keep_instrument_operations(qprogram, set(qdac_buses))
