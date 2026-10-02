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

import datetime
from typing import TYPE_CHECKING, Any, ClassVar

from sqlalchemy import ARRAY, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from qililab.result.result_management import load_results

if TYPE_CHECKING:
    from qililab.platform.platform import Platform
    from qililab.result.database.database_manager import DatabaseManager


class _AutocalBase(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {
        dict[str, Any]: JSONB,
        list[int]: ARRAY(Integer),
        list[str]: ARRAY(String),
    }


class CalibrationRun(_AutocalBase):
    """Creates and manipulates Sample metadata database"""

    __tablename__ = "calibration_run"

    calibration_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.datetime | None]
    calibration_tree: Mapped[dict[str, Any] | None]
    calibration_completed: Mapped[bool]
    cooldown: Mapped[str | None] = mapped_column(index=True)
    sample_name: Mapped[str]

    def end_calibration(self, session: sessionmaker[Session], traceback: str | None = None):
        """Function to end measurement of the experiment. The function sets inside the database information
        about the end of the experiment: the finishing time, completeness status and experiment length."""

        with session() as running_session:
            # Merge the detached instance into the current session
            persistent_instance = running_session.merge(self)
            try:
                if traceback is None:
                    persistent_instance.calibration_completed = True
                running_session.commit()
                return persistent_instance
            except Exception as e:
                running_session.rollback()
                raise e

    def __repr__(self):
        return f"calibration_run: {self.calibration_id} {self.date}"


class AutocalMeasurement(_AutocalBase):
    """Creates and manipulates Measurement metadata database"""

    __tablename__ = "measurements"

    measurement_id: Mapped[int] = mapped_column(primary_key=True)
    experiment_name: Mapped[str]
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[datetime.datetime | None]
    run_length: Mapped[datetime.timedelta | None]
    experiment_completed: Mapped[bool]
    calibration_id: Mapped[int] = mapped_column(ForeignKey(CalibrationRun.calibration_id))
    result_path: Mapped[str] = mapped_column(unique=True)
    fitting_path: Mapped[str | None]
    fitting_parameters: Mapped[dict[str, Any] | None]
    qbit_idx: Mapped[str | None]
    platform_after: Mapped[dict[str, Any] | None]
    platform: Mapped[dict[str, Any] | None] = mapped_column("platform_before")
    qprogram: Mapped[dict[str, Any] | None]
    calibration: Mapped[dict[str, Any] | None]
    parameters: Mapped[dict[str, Any] | None]
    data_shape: Mapped[list[int] | None]

    @property
    def target(self) -> list[str] | None:
        """Measured qubit as a list, matching ``Measurement.target``. None if no qubit was stored."""
        return None if self.qbit_idx is None else [self.qbit_idx]

    def end_experiment(self, session: sessionmaker[Session], traceback: str | None = None):
        """Function to end measurement of the experiment. The function sets inside the database information
        about the end of the experiment: the finishing time, completeness status and experiment length."""

        with session() as running_session:
            # Merge the detached instance into the current session
            persistent_instance = running_session.merge(self)

            persistent_instance.end_time = datetime.datetime.now()
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time
            self.end_time = persistent_instance.end_time
            self.run_length = persistent_instance.run_length

            try:
                if traceback is None:
                    persistent_instance.experiment_completed = True
                    self.experiment_completed = True
                running_session.commit()
                return persistent_instance
            except Exception as e:
                running_session.rollback()
                raise e

    def load_h5(self):
        """Load old experiment data from h5 files."""
        return load_results(self.result_path)

    def update_platform(self, session: sessionmaker[Session], platform: "Platform"):
        """Function to update measurement platform. The function sets inside the database information
        about the platform."""

        with session() as running_session:
            # Merge the detached instance into the current session
            persistent_instance = running_session.merge(self)

            self.platform_after = platform.to_dict()
            persistent_instance.platform_after = platform.to_dict()

            try:
                running_session.commit()
                return persistent_instance
            except Exception as e:
                running_session.rollback()
                raise e

    def add_fitting(
        self, database_manager: "DatabaseManager", path: str | None = None, parameters: dict[str, Any] | None = None
    ):
        """Add fitting_path and fitting_parameters into the autocalibration Measurements database table.

        The row is re-loaded from the database by its ``measurement_id`` inside the session and only the
        fitting columns are updated, instead of merging ``self``. This avoids a stale in-memory instance
        overwriting columns that were changed elsewhere (e.g. by ``update_platform`` or ``end_experiment``).

        Args:
            database_manager (DatabaseManager): Database manager holding the session.
            path (str | None, optional): Fitting plots or data path. Defaults to None.
            parameters (dict[str, Any] | None, optional): Fitting parameters in dictionary form. Defaults to None.
        """
        session = database_manager.session
        with session() as running_session:
            persistent_instance = (
                running_session.query(AutocalMeasurement)
                .where(AutocalMeasurement.measurement_id == self.measurement_id)
                .one_or_none()
            )
            if persistent_instance is None:
                raise IndexError(f"Autocalibration measurement entry '{self.measurement_id}' does not exist.")
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

    def __repr__(self):
        return f"{self.measurement_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.calibration_id}"
