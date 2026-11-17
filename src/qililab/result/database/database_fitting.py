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

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from qililab.result.database.database_autocal import AutocalMeasurement
    from qililab.result.database.database_manager import DatabaseManager
    from qililab.result.database.database_measurements import Measurement

_FittingEntry = TypeVar("_FittingEntry", "Measurement", "AutocalMeasurement")


def add_fitting_by_id(
    model: type[_FittingEntry],
    database_manager: "DatabaseManager",
    measurement_id: int,
    path: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> _FittingEntry:
    """Store fitting information in the row of ``model`` with the given ``measurement_id``.

    The row is re-loaded from the database inside the session and only the fitting columns are updated, so a stale
    in-memory instance cannot overwrite columns that were changed elsewhere.

    Args:
        model (type[Measurement] | type[AutocalMeasurement]): Table to update.
        database_manager (DatabaseManager): Database manager holding the session.
        measurement_id (int): measurement_id of the row to update.
        path (str | None, optional): Fitting plots or data path. If empty or None, the stored value is kept.
            Defaults to None.
        parameters (dict[str, Any] | None, optional): Fitting parameters in dictionary form. If empty or None, the
            stored value is kept. Defaults to None.

    Returns:
        Measurement | AutocalMeasurement: the updated row.

    Raises:
        IndexError: if no row with ``measurement_id`` exists.
    """
    with database_manager.session() as running_session:
        persistent_instance = running_session.query(model).where(model.measurement_id == measurement_id).one_or_none()
        if persistent_instance is None:
            raise IndexError(f"{model.__name__} entry '{measurement_id}' does not exist.")
        if path:
            persistent_instance.fitting_path = path
        if parameters:
            persistent_instance.fitting_parameters = parameters
        try:
            running_session.commit()
            return persistent_instance
        except Exception as e:
            running_session.rollback()
            raise e
