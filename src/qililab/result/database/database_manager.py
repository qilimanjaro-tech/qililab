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
from pandas import read_sql
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import Session, sessionmaker

from qililab.result.database.database_autocal import AutocalMeasurement, CalibrationRun
from qililab.result.database.database_measurements import Cooldown, Measurement, Sample, SequenceRun
from qililab.result.database.database_qaas import QaaS_Experiment
from qililab.utils.serialization import serialize

if TYPE_CHECKING:
    from qililab.platform.platform import Platform
    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.experiment import Experiment
    from qililab.qprogram.qprogram import QProgram


class DatabaseManager:
    """Database manager for measurements results and metadata"""

    calibration_measurement: AutocalMeasurement

    def __init__(self, filename: str, database_name: str):
        """
        Args:
            filename (str): location of the database `.ini`.
            database_name (str): Name of the config section inside the `.ini`.
        """
        config = _load_config(filename, database_name)
        self.engine = get_engine(config["user"], config["passwd"], config["host"], config["port"], config["database"])
        self.session: sessionmaker[Session] = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.current_cd: str | None = None
        self.current_sample: str | None = None
        self.current_sequence: int | None = None

        self.base_path_local: str | None = None
        self.base_path_share: str | None = None
        self.folder_path: str | None = None

        if "base_path_local" in config:
            self.base_path_local = config["base_path_local"]
            self.base_path_share = config["base_path_shared"]
            self.folder_path = config["data_write_folder"]

    def set_sample_and_cooldown(self, sample: str, cooldown: str | None = None):
        """Set sample and cooldown of the database

        Args:
            sample (str): Sample name, mandatory parameter as allways needed unlike cooldown
            cooldown (str | None, optional): Cooldown name, contains multiple sample instances. Defaults to None.
        """
        with self.session() as running_session:
            sample_exists = running_session.query(exists().where(Sample.sample_name == sample)).scalar()
            if sample_exists:
                self.current_sample = sample
            else:
                raise Exception(f"Sample entry '{sample}' does not exist. Add it with add_sample()")

            # Setting CD is optional, if you are doing a measurement which is not tied to a CD
            if cooldown:
                cd_object = running_session.query(Cooldown).filter(Cooldown.cooldown == cooldown).one_or_none()
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
        with self.session() as running_session:
            running_session.add(cooldown_obj)
            try:
                running_session.commit()
            except Exception as e:
                running_session.rollback()
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
        with self.session() as running_session:
            running_session.add(sample_obj)
            try:
                running_session.commit()
            except Exception as e:
                running_session.rollback()
                raise e

    def add_sequence_run(self, sequence_tree: dict, sample_name: str, cooldown: str | None = None) -> SequenceRun:
        """Add sequence of experiments metadata.

        Args:
            sequence_tree (dict): Full experiment sequence tree of the run.
        """
        sequence_obj = SequenceRun(
            date=datetime.datetime.now(),
            sequence_tree=sequence_tree,
            sequence_completed=False,
            sample_name=sample_name,
            cooldown=cooldown,
        )
        with self.session() as running_session:
            running_session.add(sequence_obj)
            try:
                running_session.commit()
                self.current_sequence = sequence_obj.sequence_id  # type: ignore[assignment]
                return sequence_obj

            except Exception as e:
                running_session.rollback()
                raise e

    def add_calibration_run(self, calibration_tree: dict, sample_name: str, cooldown: str) -> CalibrationRun:
        """Add autocalibration metadata.

        Args:
            calibration_tree (dict): Full calibration tree of the run.
        """
        calibration_obj = CalibrationRun(
            date=datetime.datetime.now(),
            calibration_tree=calibration_tree,
            calibration_completed=False,
            sample_name=sample_name,
            cooldown=cooldown,
        )
        with self.session() as running_session:
            running_session.add(calibration_obj)
            try:
                running_session.commit()
                return calibration_obj

            except Exception as e:
                running_session.rollback()
                raise e

    def load_by_id(self, id: int) -> Measurement | None:
        """Load measurement by its measurement_id.

        Args:
            id (int): measurement_id value given by the database.
        """
        with self.session() as running_session:
            measurement_by_id = running_session.query(Measurement).where(Measurement.measurement_id == id).one_or_none()

            if measurement_by_id is not None:
                path = measurement_by_id.result_path
                if not os.path.isfile(path):
                    new_path = path.replace(self.base_path_local, self.base_path_share)
                    measurement_by_id.result_path = new_path

            return measurement_by_id

    def load_calibration_by_id(self, id: int) -> AutocalMeasurement | None:
        """Load autocalibration measurement by its measurement_id.

        Args:
            id (int): measurement_id value given by the database.
        """
        with self.session() as running_session:
            measurement_by_id = (
                running_session.query(AutocalMeasurement).where(AutocalMeasurement.measurement_id == id).one_or_none()
            )

            return measurement_by_id

    def load_experiment_by_id(self, id: int) -> QaaS_Experiment | None:
        """Load QaaS measurement by its measurement_id.

        Args:
            id (int): measurement_id value given by the database.
        """
        with self.session() as running_session:
            experiment_by_id = (
                running_session.query(QaaS_Experiment).where(QaaS_Experiment.experiment_id == id).one_or_none()
            )

            if experiment_by_id is not None:
                path = experiment_by_id.result_path
                if not os.path.isfile(path):
                    new_path = path.replace(self.base_path_local, self.base_path_share)
                    experiment_by_id.result_path = new_path

            return experiment_by_id

    def tail(
        self,
        exp_name: str | None = None,
        current_sample: bool = True,
        order_limit: int | None = 5,
        pandas_output: bool = False,
        light_read: bool = False,
        since_id: int | None = None,
    ):
        """Add an index at the end of the database.

        Args:
            exp_name (str | None, optional): Experiment name. Defaults to None.
            current_sample (bool, optional): Conditional to define if the sample is currently on use. Defaults to True.
            order_limit (int | None, optional): Limit of the order by query. Defaults to 5.
            pandas_output (bool, optional): If True, read database table into a DataFrame. Defaults to False.
            light_read (bool, optional): If True, load only a subset of the columns. Replace heavy columns Platform and Qprogram by True or False. Defaults to False.
            since_id (int | None, optional): If provided, only load measurements with measurement_id greater than since_id. Defaults to None.
        """
        with self.engine.connect() as con:
            query = self.session().query(Measurement)

            if current_sample and self.current_sample:
                query = query.filter(Measurement.sample_name == self.current_sample)
            if since_id:
                query = query.filter(Measurement.measurement_id > since_id)

            if exp_name is not None:
                query = query.filter(Measurement.experiment_name == exp_name)

            if order_limit is not None:
                query = query.order_by(Measurement.measurement_id.desc()).limit(order_limit)
            else:
                query = query.order_by(Measurement.measurement_id.desc())

            Measurement.platform.isnot
            if light_read:
                query = query.with_entities(  # Note that some columns are missing that currently are not being used
                    Measurement.measurement_id,
                    Measurement.experiment_name,
                    Measurement.optional_identifier,
                    Measurement.start_time,
                    Measurement.end_time,
                    Measurement.run_length,
                    Measurement.experiment_completed,
                    Measurement.cooldown,
                    Measurement.sample_name,
                    Measurement.result_path,
                    Measurement.created_by,
                    (Measurement.qprogram != "null").label("has_qprogram"),
                    (Measurement.platform != "null").label("has_platform"),
                    (Measurement.calibration != "null").label("has_calibration"),
                    (Measurement.debug_file != "null").label("has_debug"),
                )

            if pandas_output:
                return read_sql(query.statement, con=con)
            return query.all()

    def head(
        self,
        exp_name: str | None = None,
        current_sample: bool = True,
        order_limit: int | None = 5,
        pandas_output: bool = False,
        light_read: bool = False,
        before_id: int | None = None,
    ):
        """Add an index at the beginning of the database.

        Args:
            exp_name (str | None, optional): Experiment name. Defaults to None.
            current_sample (bool, optional): Conditional to define if the sample is currently on use. Defaults to True.
            order_limit (int | None, optional): Limit of the order by query. Defaults to 5.
            pandas_output (bool, optional): If True, read database table into a DataFrame. Defaults to False.
            light_read (bool, optional): If True, load only a subset of the columns. Replace heavy columns Platform and Qprogram by True or False. Defaults to False.
            before_id (int | None, optional): If provided, only load measurements with measurement_id lower than since_id. Defaults to None.
        """
        with self.engine.connect() as con:
            query = self.session().query(Measurement)

            if current_sample and self.current_sample:
                query = query.filter(Measurement.sample_name == self.current_sample)

            if before_id:
                query = query.filter(Measurement.measurement_id < before_id)

            if exp_name is not None:
                query = query.filter(Measurement.experiment_name == exp_name)

            if order_limit is not None:
                query = query.order_by(Measurement.measurement_id).limit(order_limit)
            else:
                query = query.order_by(Measurement.measurement_id)

            if light_read:
                query = query.with_entities(  # Note that some columns are missing that currently are not being used
                    Measurement.measurement_id,
                    Measurement.experiment_name,
                    Measurement.optional_identifier,
                    Measurement.start_time,
                    Measurement.end_time,
                    Measurement.run_length,
                    Measurement.experiment_completed,
                    Measurement.cooldown,
                    Measurement.sample_name,
                    Measurement.result_path,
                    Measurement.created_by,
                    (Measurement.qprogram != "null").label("has_qprogram"),
                    (Measurement.platform != "null").label("has_platform"),
                    (Measurement.calibration != "null").label("has_calibration"),
                    (Measurement.debug_file != "null").label("has_debug"),
                )

            if pandas_output:
                return read_sql(query.statement, con=con)
            return query.all()

    def get_qprogram(self, measurement_id: int) -> str:
        """Get QProgram of a measurement by its measurement_id.
        To be used when you have light loaded measurements

        Args:
            measurement_id (int): measurement_id value given by the database.
        """
        with self.session() as running_session:
            return (
                running_session.query(Measurement.qprogram)
                .filter(Measurement.measurement_id == measurement_id)
                .scalar()
            )

    def get_calibration(self, measurement_id: int) -> str:
        """Get Calibration of a measurement by its measurement_id.
        To be used when you have light loaded measurements

        Args:
            measurement_id (int): measurement_id value given by the database.
        """
        with self.session() as running_session:
            return (
                running_session.query(Measurement.calibration)
                .filter(Measurement.measurement_id == measurement_id)
                .scalar()
            )

    def get_platform(self, measurement_id: int) -> dict:
        """Get Platform of a measurement by its measurement_id.
        To be used when you have light loaded measurements

        Args:
            measurement_id (int): measurement_id value given by the database.
        """
        with self.session() as running_session:
            return (
                running_session.query(Measurement.platform)
                .filter(Measurement.measurement_id == measurement_id)
                .scalar()
            )

    def get_debug(self, measurement_id: int) -> str:
        """Get Debug of a measurement by its measurement_id.
        To be used when you have light loaded measurements

        Args:
            measurement_id (int): measurement_id value given by the database.
        """
        with self.session() as running_session:
            return (
                running_session.query(Measurement.debug_file)
                .filter(Measurement.measurement_id == measurement_id)
                .scalar()
            )

    def add_autocal_measurement(
        self,
        experiment_name: str,
        qubit_idx: int,
        calibration: "Calibration",  # type: ignore
        platform: "Platform" = None,  # type: ignore
        qprogram: "QProgram" = None,  # type: ignore
        parameters: list[str] | None = None,
        data_shape: np.ndarray | None = None,
    ):
        """Add autocalibration measurement metadata and data path

        Args:
            experiment_name (str): Experiment name.
            qubit_idx (int): Number of qubit index.
            calibration (Calibration): Experiment calibration parameters.
            platform (Platform, optional): Platform used on the experiment. Defaults to None.
            qprogram (QProgram | None, optional): Qprogram used on the experiment. Defaults to None.
            parameters (list[str] | None, optional): Parameters used on the experiment. Defaults to None.
            data_shape (np.ndarray | None, optional): Shape of the results array. Defaults to None.
        """

        start_time = datetime.datetime.now()

        with self.session() as running_session:
            calibration_id = (
                running_session.query(CalibrationRun)  # type: ignore[union-attr]
                .order_by(CalibrationRun.calibration_id.desc())
                .first()
                .calibration_id
            )

        base_path = calibration.parameters["base_path"]

        result_path = os.path.join(base_path, f"{experiment_name}.h5")

        if not os.path.isdir(base_path):
            os.makedirs(base_path)
            warnings.warn(f"Data folder did not exist. Created one at {base_path}")

        self.calibration_measurement = AutocalMeasurement(
            experiment_name=experiment_name,
            calibration_id=calibration_id,
            qbit_idx=qubit_idx,
            result_path=result_path,
            fitting_path=base_path,
            experiment_completed=False,
            start_time=start_time,
            platform_before=platform,
            qprogram=qprogram,
            calibration=serialize(calibration),
            parameters=serialize(parameters),
            data_shape=data_shape,
        )
        with self.session() as running_session:
            running_session.add(self.calibration_measurement)
            try:
                running_session.commit()
                return self.calibration_measurement
            except Exception as e:
                running_session.rollback()
                raise e

    def update_platform(self, platform: "Platform"):
        """Update calibration platform after fitting

        Args:
            platform (Platform): New platform to be set at platform_before column from `AutocalMeasurement`.
        """
        self.calibration_measurement.update_platform(self.session, platform)

    def add_experiment(
        self,
        job_id: int,
        experiment_name: str,
        result_path: str,
        sample_name: str,
        cooldown: str,
    ):
        """Add queued experiment metadata and data path

        Args:
            job_id (int): Queue job ID.
            experiment_name (str): Experiment name.
            result_path (str): Result path for data location.
            cooldown (str): Cooldown id.
            sample_name (str): Sample id.
        """

        start_time = datetime.datetime.now()

        measurement = QaaS_Experiment(
            job_id=job_id,
            experiment_name=experiment_name,
            sample_name=sample_name,
            result_path=result_path,
            experiment_completed=False,
            start_time=start_time,
            cooldown=cooldown,
        )
        with self.session() as running_session:
            running_session.add(measurement)
            try:
                running_session.commit()
                return measurement
            except Exception as e:
                running_session.rollback()
                raise e

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
        debug_file: str | None = None,
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
            sequence_id=self.current_sequence,
            optional_identifier=optional_identifier,
            end_time=end_time,
            run_length=run_length,
            platform=platform,
            experiment=experiment,
            qprogram=qprogram,
            calibration=calibration,
            debug_file=debug_file,
            parameters=parameters,
            data_shape=data_shape,
        )
        with self.session() as running_session:
            running_session.add(measurement)
            try:
                running_session.commit()
                return measurement
            except Exception as e:
                running_session.rollback()
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
        with self.session() as running_session:
            running_session.add(measurement)
            try:
                running_session.commit()
                return measurement
            except Exception as e:
                running_session.rollback()
                raise e


def _load_config(filename, section):
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


def get_db_manager(path: str = "~/database.ini", database_name: str = "postgresql") -> DatabaseManager:
    """Automatic DatabaseManager generator based on default load_config"""
    filename = os.path.expanduser(path)
    return DatabaseManager(filename, database_name)


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


def load_by_id(id: int, path: str = "~/database.ini") -> Measurement | None:
    """Function to get the database ID without loading the Database Manager"""

    db = get_db_manager(path)
    measurement_by_id = db.load_by_id(id)
    return measurement_by_id
