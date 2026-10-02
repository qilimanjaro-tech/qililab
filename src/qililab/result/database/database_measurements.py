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
import warnings
from typing import TYPE_CHECKING, Any, ClassVar

from pandas import read_hdf
from sqlalchemy import (
    ARRAY,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from xarray import DataArray

from qililab.result.experiment_results import ExperimentResults
from qililab.result.result_management import load_results

if TYPE_CHECKING:
    from qililab.result.database.database_manager import DatabaseManager


class _MeasurementsBase(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {
        dict[str, Any]: JSONB,
        list[int]: ARRAY(Integer),
        list[str]: ARRAY(String),
    }


class Cooldown(_MeasurementsBase):
    """Creates and manipulates CoolDown metadata database"""

    __tablename__ = "cooldowns"

    cooldown: Mapped[str] = mapped_column(primary_key=True)
    date: Mapped[datetime.date | None]
    fridge: Mapped[str | None]
    active: Mapped[bool | None] = mapped_column(server_default=text("true"))

    def __repr__(self):
        return f"{self.cooldown} {self.date} {self.fridge} {self.active}"


class Sample(_MeasurementsBase):
    """Creates and manipulates Sample metadata database"""

    __tablename__ = "samples"

    sample_name: Mapped[str] = mapped_column(primary_key=True)
    manufacturer: Mapped[str | None]
    wafer: Mapped[str | None]
    fab_run: Mapped[str | None]
    sample: Mapped[str | None]
    device_design: Mapped[str | None]
    n_qubits_per_device: Mapped[list[int] | None]
    additional_info: Mapped[str | None]

    def __repr__(self):
        return f"{self.sample_name} {self.manufacturer} {self.additional_info}"


class SequenceRun(_MeasurementsBase):
    """Creates and manipulates a sequence of measurements run metadata database"""

    __tablename__ = "sequence_run"

    sequence_id: Mapped[int] = mapped_column(primary_key=True)
    sequence_name: Mapped[str]
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[datetime.datetime | None]
    run_length: Mapped[datetime.timedelta | None]
    sequence_tree: Mapped[dict[str, Any] | None]
    sequence_completed: Mapped[bool]
    cooldown: Mapped[str | None] = mapped_column(ForeignKey(Cooldown.cooldown), index=True)
    sample_name: Mapped[str] = mapped_column(ForeignKey(Sample.sample_name))

    def end_sequence(self, session: sessionmaker[Session], traceback: str | None = None):
        """Function to end sequence of experiments. The function sets inside the database information
        about the end of the sequence: the finishing time, completeness status and sequence length."""

        with session() as running_session:
            # Merge the detached instance into the current session
            persistent_instance = running_session.merge(self)
            persistent_instance.end_time = datetime.datetime.now()
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time
            self.end_time = persistent_instance.end_time
            self.run_length = persistent_instance.run_length
            try:
                if traceback is None:
                    persistent_instance.sequence_completed = True
                    self.sequence_completed = True
                running_session.commit()
                return persistent_instance
            except Exception as e:
                running_session.rollback()
                raise e

    def __repr__(self):
        return f"{self.sequence_id} {self.sequence_name} {self.start_time} {self.sequence_completed} {self.sample_name} {self.cooldown}"


class Measurement(_MeasurementsBase):
    """Creates and manipulates Measurement metadata database"""

    __tablename__ = "measurements"

    measurement_id: Mapped[int] = mapped_column(primary_key=True)
    experiment_name: Mapped[str]
    optional_identifier: Mapped[str | None]
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[datetime.datetime | None]
    run_length: Mapped[datetime.timedelta | None]
    experiment_completed: Mapped[bool]
    sample_name: Mapped[str] = mapped_column(ForeignKey(Sample.sample_name))
    cooldown: Mapped[str | None] = mapped_column(ForeignKey(Cooldown.cooldown), index=True)
    sequence_id: Mapped[int | None]
    dc_offsets: Mapped[dict[str, Any] | None]
    flux_offsets: Mapped[dict[str, Any] | None]
    target: Mapped[list[str] | None]
    secondary_source: Mapped[list[str] | None]
    result_path: Mapped[str] = mapped_column(unique=True)
    platform: Mapped[dict[str, Any] | None]
    experiment: Mapped[dict[str, Any] | None]
    qprogram: Mapped[dict[str, Any] | None]
    bus_mapping: Mapped[dict[str, Any] | None]
    calibration: Mapped[dict[str, Any] | None]
    parameters: Mapped[dict[str, Any] | None]
    data_shape: Mapped[list[int] | None]
    fitting_path: Mapped[str | None]
    fitting_parameters: Mapped[dict[str, Any] | None]
    debug_file: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(server_default=text("current_user"))
    # TODO: add error_report = Column("error_report", String, nullable=True)

    def end_experiment(self, session: sessionmaker[Session], traceback: str | None = None):
        """Function to end measurement of the experiment. The function sets inside the database information
        about the end of the experiment: the finishing time, completeness status and experiment length."""

        with session() as running_session:
            # Merge the detached instance into the current session
            persistent_instance = running_session.merge(self)
            persistent_instance.end_time = datetime.datetime.now()
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time
            try:
                if traceback is None:
                    persistent_instance.experiment_completed = True
                # TODO: add else: persistent_instance.error_report = traceback
                running_session.commit()
                return persistent_instance
            except Exception as e:
                running_session.rollback()
                raise e

    def read_experiment(self):
        """Reads current experiment."""

        with ExperimentResults(self.result_path) as results:
            data, dims = results.get()
        return data, dims

    def read_experiment_xarray(self):
        """Rewads current experiment in Xarray format."""

        with ExperimentResults(self.result_path) as results:
            data, dims = results.get()

        d = {}
        labels = []
        for i in range(len(dims)):
            if dims[i].values != []:
                d.update({dims[i].labels[0]: dims[i].values[0]})
            labels.append(dims[i].labels[0])

        iq_axis = labels.index("I/Q")
        labels.remove("I/Q")
        complex_data = data.take(indices=0, axis=iq_axis) + 1j * data.take(indices=1, axis=iq_axis)

        data_xr = DataArray(complex_data, coords=d, dims=labels)
        return data_xr

    def load_old_h5(self):
        """Load experiment data from h5 files.

        .. deprecated::
            Use ``load_h5`` instead.
        """
        warnings.warn(
            "`load_old_h5` is deprecated and will be removed in a future release. Use `load_h5` instead.",
            FutureWarning,
            stacklevel=2,
        )
        return self.load_h5()

    def load_h5(self):
        """Load experiment data from h5 files."""
        return load_results(self.result_path)

    def load_df(self):
        """Loads experiments data from hdf files."""
        return read_hdf(self.result_path)

    def load_xarray(self):
        """Loads experiments data from hdf files into Xarray format."""
        df = read_hdf(self.result_path)
        return df.to_xarray().to_dataarray()

    def read_numpy(self):
        """Loads experiments data from hdf files into numpy array format."""
        df = read_hdf(self.result_path)
        da = df.to_xarray().to_dataarray()
        arr = da.to_numpy()[0,]
        axis_labels = {dim: da.coords[dim].values for dim in da.dims[1:]}
        return arr, axis_labels

    def add_fitting(self, database_manager: "DatabaseManager", path: str, parameters: dict[str, Any] | None = None):
        """Add fitting_path and fitting_parameters into Measurements database table.

        Args:
            database_manager (DatabaseManager): _description_
            path (str): Fitting plots or data path.
            parameters (dict[str, Any] | None, optional): Fitting parameters in dictionary form. Defaults to None.
        """
        session = database_manager.session
        with session() as running_session:
            persistent_instance = running_session.merge(self)
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
        return f"{self.measurement_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.sample_name} {self.cooldown}"
