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

from pandas import read_hdf
from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Interval,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from xarray import DataArray

from qililab.result.experiment_results import ExperimentResults
from qililab.result.result_management import load_results

base = declarative_base()


class Cooldown(base):  # type: ignore
    """Creates and manipulates CoolDown metadata database"""

    __tablename__ = "cooldowns"

    cooldown: Column = Column("cooldown", String, primary_key=True)
    date: Column = Column("date", Date)
    fridge: Column = Column("fridge", String)
    active: Column = Column("active", Boolean, server_default=text("true"))

    def __init__(self, cooldown, date, fridge):
        self.cooldown = cooldown
        self.date = date
        self.fridge = fridge

    def __repr__(self):
        return f"{self.cooldown} {self.date} {self.fridge} {self.active}"


class Sample(base):  # type: ignore
    """Creates and manipulates Sample metadata database"""

    __tablename__ = "samples"

    sample_name: Column = Column("sample_name", String, primary_key=True)
    manufacturer: Column = Column("manufacturer", String)
    wafer: Column = Column("wafer", String)
    fab_run: Column = Column("fab_run", String)
    sample: Column = Column("sample", String)
    device_design: Column = Column("device_design", String)
    n_qubits_per_device: Column = Column("n_qubits_per_device", ARRAY(Integer))
    additional_info: Column = Column("additional_info", String)

    def __init__(
        self,
        sample_name,
        fab_run,
        wafer,
        sample,
        device_design,
        n_qubits_per_device,
        additional_info,
        manufacturer,
    ):
        self.sample_name = sample_name
        self.fab_run = fab_run
        self.wafer = wafer
        self.sample = sample
        self.device_design = device_design
        self.n_qubits_per_device = n_qubits_per_device
        self.additional_info = additional_info
        self.manufacturer = manufacturer

    def __repr__(self):
        return f"{self.sample_name} {self.manufacturer} {self.additional_info}"


class SequenceRun(base):  # type: ignore
    """Creates and manipulates a sequence of measurements run metadata database"""

    __tablename__ = "sequence_run"

    sequence_id: Column = Column("sequence_id", Integer, primary_key=True)
    start_time: Column = Column("start_time", DateTime, nullable=False)
    end_time: Column = Column("end_time", DateTime)
    run_length: Column = Column("run_length", Interval)
    sequence_tree: Column = Column("sequence_tree", JSONB)
    sequence_completed: Column = Column("sequence_completed", Boolean, nullable=False)
    cooldown: Column = Column("cooldown", ForeignKey(Cooldown.cooldown), index=True)
    sample_name: Column = Column("sample_name", ForeignKey(Sample.sample_name), nullable=False)

    def __init__(
        self, start_time, sequence_tree, sequence_completed, sample_name, end_time=None, run_length=None, cooldown=None
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.run_length = run_length
        self.sequence_tree = sequence_tree
        self.sequence_completed = sequence_completed
        self.sample_name = sample_name
        self.cooldown = cooldown

    def end_sequence(self, session: sessionmaker[Session], traceback: str | None = None):
        """Function to end sequence of experiments. The function sets inside the database information
        about the end of the sequence: the finishing time, completeness status and sequence length."""

        with session() as running_session:
            # Merge the detached instance into the current session
            persistent_instance = running_session.merge(self)
            persistent_instance.end_time = datetime.datetime.now()  # type: ignore[assignment]
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time  # type: ignore[assignment]
            self.end_time = persistent_instance.end_time
            self.run_length = persistent_instance.run_length
            try:
                if traceback is None:
                    persistent_instance.sequence_completed = True  # type: ignore[assignment]
                    self.sequence_completed = True  # type: ignore[assignment]
                running_session.commit()
                return persistent_instance
            except Exception as e:
                running_session.rollback()
                raise e

    def __repr__(self):
        return f"{self.sequence_id} {self.date} {self.sequence_completed} {self.sample_name} {self.cooldown}"


class Measurement(base):  # type: ignore
    """Creates and manipulates Measurement metadata database"""

    __tablename__ = "measurements"

    measurement_id: Column = Column("measurement_id", Integer, primary_key=True)
    experiment_name: Column = Column("experiment_name", String, nullable=False)
    optional_identifier: Column = Column("optional_identifier", String)
    start_time: Column = Column("start_time", DateTime, nullable=False)
    end_time: Column = Column("end_time", DateTime)
    run_length: Column = Column("run_length", Interval)
    experiment_completed: Column = Column("experiment_completed", Boolean, nullable=False)
    cooldown: Column = Column("cooldown", ForeignKey(Cooldown.cooldown), index=True)
    sequence_id: Column = Column("sequence_id", Integer)
    sample_name: Column = Column("sample_name", ForeignKey(Sample.sample_name), nullable=False)
    result_path: Column = Column("result_path", String, unique=True, nullable=False)
    platform: Column = Column("platform", JSONB)
    experiment: Column = Column("experiment", JSONB)
    qprogram: Column = Column("qprogram", JSONB)
    calibration: Column = Column("calibration", JSONB)
    parameters: Column = Column("parameters", JSONB)
    data_shape: Column = Column("data_shape", ARRAY(Integer))
    debug_file = Column("debug_file", Text)
    created_by = Column("created_by", String, server_default=text("current_user"))
    # TODO: add error_report = Column("error_report", String, nullable=True)

    def end_experiment(self, session: sessionmaker[Session], traceback: str | None = None):
        """Function to end measurement of the experiment. The function sets inside the database information
        about the end of the experiment: the finishing time, completeness status and experiment length."""

        with session() as running_session:
            # Merge the detached instance into the current session
            persistent_instance = running_session.merge(self)
            persistent_instance.end_time = datetime.datetime.now()  # type: ignore[assignment]
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time  # type: ignore[assignment]
            try:
                if traceback is None:
                    persistent_instance.experiment_completed = True  # type: ignore[assignment]
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
        """Load old experiment data from h5 files."""
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

    def __init__(
        self,
        experiment_name,
        sample_name,
        result_path,
        experiment_completed,
        start_time,
        cooldown=None,
        sequence_id=None,
        optional_identifier=None,
        end_time=None,
        run_length=None,
        platform=None,
        experiment=None,
        qprogram=None,
        calibration=None,
        parameters=None,
        data_shape=None,
        debug_file=None,
    ):
        # Required fields
        self.experiment_name = experiment_name
        self.sample_name = sample_name
        self.result_path = result_path
        self.experiment_completed = experiment_completed
        self.start_time = start_time

        # Optional fields
        self.cooldown = cooldown
        self.sequence_id = sequence_id
        self.optional_identifier = optional_identifier
        self.end_time = end_time
        self.run_length = run_length
        self.platform = platform
        self.experiment = experiment
        self.qprogram = qprogram
        self.calibration = calibration
        self.parameters = parameters
        self.data_shape = data_shape
        self.debug_file = debug_file

    def __repr__(self):
        return f"{self.measurement_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.sample_name} {self.cooldown}"
