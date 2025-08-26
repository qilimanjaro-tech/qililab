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
import os
import warnings
from configparser import ConfigParser
from typing import TYPE_CHECKING

import h5py
import numpy as np
from pandas import read_hdf, read_sql
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
    create_engine,
    exists,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from xarray import DataArray

from qililab.result.experiment_results import ExperimentResults
from qililab.result.result_management import load_results

if TYPE_CHECKING:
    from qililab.platform.platform import Platform
    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.experiment import Experiment
    from qililab.qprogram.qprogram import QProgram

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
    # TODO: add temperature = Column("temperature", ARRAY(Integer)) when available
    cooldown: Column = Column("cooldown", ForeignKey(Cooldown.cooldown), index=True)
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

    def end_experiment(self, Session):
        """Function to end measurement of the experiment. The function sets inside the database information
        about the end of the experiment: the finishing time, completeness status and experiment length."""

        with Session() as session:
            # Merge the detached instance into the current session
            persistent_instance = session.merge(self)
            persistent_instance.end_time = datetime.datetime.now()
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time
            try:
                session.commit()
                persistent_instance.experiment_completed = True
                return persistent_instance
            except Exception as e:
                session.rollback()
                # TODO: add persistent_instance.error_report = e.__str__()
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

        IQ_axis = labels.index("I/Q")
        labels.remove("I/Q")
        complex_data = data.take(indices=0, axis=IQ_axis) + 1j * data.take(indices=1, axis=IQ_axis)

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

        # self.result_array = result_array

    def __repr__(self):
        return f"{self.measurement_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.sample_name} {self.cooldown}"


class DatabaseManager:
    """Database manager for measurements results and metadata"""

    def __init__(
        self,
        user: str,
        passwd: str,
        host: str,
        port: str,
        database: str,
        base_path_local: str,
        base_path_shared: str,
        data_write_folder: str,
    ):
        """
        Args:
            user (str): SQLalchemy user.
            passwd (str): Personal password.
            host (str): Host name.
            port (str): Host port.
            database (str): Database name.
            base_path_local (str): Local base path.
            base_path_shared  (str): Shared base path.
            data_write_folder (str): Folder name for data path.
        """
        self.engine = get_engine(user, passwd, host, port, database)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.current_cd: str | None = None
        self.current_sample: str | None = None

        self.base_path_local = base_path_local
        self.base_path_share = base_path_shared
        self.folder_path = data_write_folder

    def set_sample_and_cooldown(self, sample: str, cooldown: str | None = None):
        """Set sample and cooldown of the database

        Args:
            sample (str): Sample name, mandatory parameter as allways needed unlike cooldown
            cooldown (str | None, optional): Cooldown name, contains multiple sample instances. Defaults to None.
        """
        with self.Session() as session:
            sample_exists = session.query(exists().where(Sample.sample_name == sample)).scalar()
            if sample_exists:
                self.current_sample = sample
            else:
                raise Exception(f"Sample entry '{sample}' does not exist. Add it with add_sample()")

            # Setting CD is optional, if you are doing a measurement which is not tied to a CD
            if cooldown:
                cd_object = session.query(Cooldown).filter(Cooldown.cooldown == cooldown).one_or_none()
                if cd_object:
                    self.current_cd = cooldown
                    if not cd_object.active:
                        warnings.warn(
                            f"Cooldown '{cooldown}' is not active. Make sure you have set the right cooldown."
                        )
                        # TODO: limit data addition to active cooldowns
                else:
                    raise Exception(f"CD entry '{cooldown}' does not exist. Add it with add_cooldown()")
                warnings.warn(f"Set current sample to {sample} and cooldown to {cooldown}")
                return
            warnings.warn(f"Set current sample to {sample}")

    def add_cooldown(self, cooldown: str, fridge: str, date: datetime.date = datetime.date.today()):
        """Add cooldown to metadata

        Args:
            cooldown (str): Cooldown reference.
            fridge (str): Cooldown fridge.
            date (datetime.date, optional): Date of cooldown. Defaults to datetime.date.today().
        """
        cooldown_obj = Cooldown(cooldown=cooldown, date=date, fridge=fridge)
        with self.Session() as session:
            session.add(cooldown_obj)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def add_sample(
        self,
        sample_name: str,
        manufacturer: str,
        wafer: str,
        sample: str,
        fab_run: str,
        device_design: str,
        n_qubits_per_device: list[int],
        additional_info: str | None = None,
    ):
        """Add sample metadata

        Args:
            sample_name (str): Sample id.
            manufacturer (str): Sample manufacturer.
            wafer (str): Wafer id.
            sample (str): Sample id.
            fab_run (str): Fabrication information.
            device_design (str): Design information.
            n_qubits_per_device (list[int]): Number of Qbits inside the sample.
            additional_info (str | None, optional): Optional additional information. Defaults to None.
        """
        sample_obj = Sample(
            sample_name=sample_name,
            manufacturer=manufacturer,
            wafer=wafer,
            sample=sample,
            fab_run=fab_run,
            device_design=device_design,
            n_qubits_per_device=n_qubits_per_device,
            additional_info=additional_info,
        )
        with self.Session() as session:
            session.add(sample_obj)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def load_by_id(self, id):
        """Load measurement by its measurement_id."""

        measurement_by_id = self.Session().query(Measurement).where(Measurement.measurement_id == id).one_or_none()

        path = measurement_by_id.result_path
        if not os.path.isfile(path):
            new_path = path.replace(self.base_path_local, self.base_path_share)
            measurement_by_id.result_path = new_path

        return measurement_by_id

    def tail(
        self,
        exp_name: str | None = None,
        current_sample: bool = True,
        order_limit: int | None = 5,
        pandas_output: bool = False,
    ):
        """Add an index at the end of the database.

        Args:
            exp_name (str | None, optional): Experiment name. Defaults to None.
            current_sample (bool, optional): Conditional to define if the sample is currently on use. Defaults to True.
            order_limit (int | None, optional): Limit of the order by query. Defaults to 5.
            pandas_output (bool, optional): If True, read database table into a DataFrame. Defaults to False.
        """
        with self.engine.connect() as con:
            query = self.Session().query(Measurement)

            if current_sample and self.current_sample:
                query = query.filter(Measurement.sample_name == self.current_sample)

            if exp_name is not None:
                query = query.filter(Measurement.experiment_name == exp_name)

            if order_limit is not None:
                query = query.order_by(Measurement.measurement_id.desc()).limit(order_limit)
            else:
                query = query.order_by(Measurement.measurement_id.desc())

            if pandas_output:
                return read_sql(query.statement, con=con)
            return query.all()

    def head(
        self,
        exp_name: str | None = None,
        current_sample: bool = True,
        order_limit: int | None = 5,
        pandas_output: bool = False,
    ):
        """Add an index at the beginning of the database.

        Args:
            exp_name (str | None, optional): Experiment name. Defaults to None.
            current_sample (bool, optional): Conditional to define if the sample is currently on use. Defaults to True.
            order_limit (int | None, optional): Limit of the order by query. Defaults to 5.
            pandas_output (bool, optional): If True, read database table into a DataFrame. Defaults to False.
        """
        with self.engine.connect() as con:
            query = self.Session().query(Measurement)

            if current_sample and self.current_sample:
                query = query.filter(Measurement.sample_name == self.current_sample)

            if exp_name is not None:
                query = query.filter(Measurement.experiment_name == exp_name)

            if order_limit is not None:
                query = query.order_by(Measurement.measurement_id).limit(order_limit)
            else:
                query = query.order_by(Measurement.measurement_id)

            if pandas_output:
                return read_sql(query.statement, con=con)
            return query.all()

    def add_measurement(
        self,
        experiment_name: str,
        experiment_completed: bool,
        cooldown: str | None = None,
        sample_name: str | None = None,
        optional_identifier: str | None = None,
        end_time: datetime.datetime | None = None,
        run_length: float | None = None,
        platform: "Platform" = None,  # type: ignore
        experiment: "Experiment" = None,  # type: ignore
        qprogram: "QProgram" = None,  # type: ignore
        calibration: "Calibration" = None,  # type: ignore
        parameters: list[str] | None = None,
        data_shape: np.ndarray | None = None,
    ):
        """Add measurement metadata and data path

        Args:
            experiment_name (str): Experiment name.
            experiment_completed (bool): Status of the experiment.
            base_path (str): Base path for data location.
            cooldown (str | None, optional): Cooldown id. Defaults to None.
            sample_name (str | None, optional): Sample id. Defaults to None.
            optional_identifier (str | None, optional): Optional additional information. Defaults to None.
            end_time (datetime.datetime | None, optional): Finishing time of the experiment. Defaults to None.
            run_length (float | None, optional): Time length of the experiment. Defaults to None.
            platform (Platform, optional): Platform used on the experiment. Defaults to None.
            experiment (Experiment | None, optional): Experiment class used on the experiment. Defaults to None.
            qprogram (QProgram | None, optional): Qprogram used on the experiment. Defaults to None.
            calibration (Calibration | None, optional): Calibration used on the experiment. Defaults to None.
            parameters (list[str] | None, optional): Parameters used on the experiment. Defaults to None.
            data_shape (np.ndarray | None, optional): Shape of the results array. Defaults to None.
        """
        if sample_name is None:
            if self.current_sample:
                sample_name = self.current_sample
            else:
                raise Exception("Please set at least a sample using set_sample_and_cooldown(...)")
        if cooldown is None:
            cooldown = self.current_cd

        start_time = datetime.datetime.now()
        formatted_time = start_time.strftime("%Y-%m-%d/%H_%M_%S")

        base_path = f"{self.base_path_local}{self.folder_path}"
        if not os.path.isdir(base_path):
            base_path = f"{self.base_path_share}{self.folder_path}"
        dir_path = (
            f"{base_path}{self.current_sample}/{self.current_cd}/{formatted_time}"
            if base_path[-1] == "/"
            else f"{base_path}/{self.current_sample}/{self.current_cd}/{formatted_time}"
        )
        result_path = f"{dir_path}/{experiment_name}.h5"

        folder = dir_path
        if not os.path.isfile(folder):
            os.makedirs(folder)
            warnings.warn(f"Data folder did not exist. Created one at {folder}")

        measurement = Measurement(
            experiment_name=experiment_name,
            sample_name=sample_name,
            result_path=result_path,
            experiment_completed=experiment_completed,
            start_time=start_time,
            cooldown=cooldown,
            optional_identifier=optional_identifier,
            end_time=end_time,
            run_length=run_length,
            platform=platform,
            experiment=experiment,
            qprogram=qprogram,
            calibration=calibration,
            parameters=parameters,
            data_shape=data_shape,
        )
        with self.Session() as session:
            session.add(measurement)
            try:
                session.commit()
                return measurement
            except Exception as e:
                session.rollback()
                raise e

    def add_results(
        self,
        experiment_name: str,
        results: np.ndarray,
        loops: dict[str, np.ndarray],
        cooldown: str | None = None,
        sample_name: str | None = None,
        optional_identifier: str | None = None,
        platform: "Platform" = None,  # type: ignore
        experiment: "Experiment" = None,  # type: ignore
        qprogram: "QProgram" = None,  # type: ignore
        calibration: "Calibration" = None,  # type: ignore
        parameters: list[str] | None = None,
    ):
        """Add measurement metadata, data path and results from a finished experiment.

        Args:
            experiment_name (str): Experiment name.
            results (np.ndarray): Results array of a completed measurement.
            loops (dict[str, np.ndarray]): Dictionary of loops used in the experiment.
            cooldown (str | None, optional): Cooldown id. Defaults to None.
            sample_name (str | None, optional): Sample id. Defaults to None.
            optional_identifier (str | None, optional): Optional additional information. Defaults to None.
            platform (Platform, optional): Platform used on the experiment. Defaults to None.
            experiment (Experiment | None, optional): Experiment class used on the experiment. Defaults to None.
            qprogram (QProgram | None, optional): Qprogram used on the experiment. Defaults to None.
            calibration (Calibration | None, optional): Calibration used on the experiment. Defaults to None.
            parameters (list[str] | None, optional): Parameters used on the experiment. Defaults to None.
        """
        if sample_name is None:
            if self.current_sample:
                sample_name = self.current_sample
            else:
                raise Exception("Please set at least a sample using set_sample_and_cooldown(...)")
        if cooldown is None:
            cooldown = self.current_cd

        start_time = datetime.datetime.now()

        base_path = f"{self.base_path_local}{self.folder_path}"
        if not os.path.isdir(base_path):
            base_path = f"{self.base_path_share}{self.folder_path}"
        formatted_time = start_time.strftime("%Y-%m-%d/%H_%M_%S")
        dir_path = f"{base_path}/{self.current_sample}/{self.current_cd}/{formatted_time}"
        result_path = f"{dir_path}/{experiment_name}.h5"

        folder = dir_path
        if not os.path.isfile(folder):
            os.makedirs(folder)
            warnings.warn(f"Data folder did not exist. Created one at {folder}")

        # Save results
        _file = h5py.File(name=result_path, mode="w")
        g = _file.create_group(name="loops")
        for loop_name, array in loops.items():
            g.create_dataset(name=loop_name, data=array)

        _file.create_dataset("results", data=results)
        _file.__exit__()

        measurement = Measurement(
            experiment_name=experiment_name,
            sample_name=sample_name,
            result_path=result_path,
            experiment_completed=True,
            start_time=start_time,
            cooldown=cooldown,
            optional_identifier=optional_identifier,
            end_time=datetime.datetime.now(),
            platform=platform,
            experiment=experiment,
            qprogram=qprogram,
            calibration=calibration,
            parameters=parameters,
            data_shape=results.shape,
        )
        with self.Session() as session:
            session.add(measurement)
            try:
                session.commit()
                return measurement
            except Exception as e:
                session.rollback()
                raise e


def _load_config(filename, section="postgresql"):
    """Load database configuration based on postrgreSQL"""
    parser = ConfigParser()
    parser.read(filename)

    # Get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
        return config
    raise ReferenceError("Section {0} not found in the {1} file".format(section, filename))


def get_db_manager(path: str = "~/database.ini"):
    """Automatic DatabaseManager generator based on default load_config"""
    filename = os.path.expanduser(path)
    return DatabaseManager(**_load_config(filename))


def get_engine(user: str, passwd: str, host: str, port: str, database: str):
    """Returns SQLalchemy engine based on user information

    Args:
        user (str): SQLalchemy user
        passwd (str): Personal password
        host (str): Host name
        port (str): Host port
        database (str): Database name
    """
    url = f"postgresql://{user}:{passwd}@{host}:{port}/{database}"
    return create_engine(url)
