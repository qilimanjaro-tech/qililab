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

from sqlalchemy import ARRAY, Boolean, Column, DateTime, ForeignKey, Integer, Interval, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from qililab.result.result_management import load_results

base = declarative_base()


class Calibration_run(base):  # type: ignore
    """Creates and manipulates Sample metadata database"""

    __tablename__ = "calibration_run"

    calibration_id: Column = Column("calibration_id", Integer, primary_key=True)
    date: Column = Column("date", DateTime)
    calibration_tree: Column = Column("calibration_tree", JSONB)
    calibration_completed: Column = Column("calibration_completed", Boolean, nullable=False)

    def __init__(
        self,
        date,
        calibration_tree,
        calibration_completed,
    ):
        self.date = date
        self.calibration_tree = calibration_tree
        self.calibration_completed = calibration_completed

    def end_calibration(self, Session, traceback=None):
        """Function to end measurement of the experiment. The function sets inside the database information
        about the end of the experiment: the finishing time, completeness status and experiment length."""

        with Session() as session:
            # Merge the detached instance into the current session
            persistent_instance = session.merge(self)
            try:
                if traceback is None:
                    persistent_instance.calibration_completed = True
                session.commit()
                return persistent_instance
            except Exception as e:
                session.rollback()
                raise e

    def __repr__(self):
        return f"calibration_run: {self.calibration_id} {self.date}"


class Autocal_Measurement(base):  # type: ignore
    """Creates and manipulates Measurement metadata database"""

    __tablename__ = "measurements"

    measurement_id: Column = Column("measurement_id", Integer, primary_key=True)
    experiment_name: Column = Column("experiment_name", String, nullable=False)
    start_time: Column = Column("start_time", DateTime, nullable=False)
    end_time: Column = Column("end_time", DateTime)
    run_length: Column = Column("run_length", Interval)
    experiment_completed: Column = Column("experiment_completed", Boolean, nullable=False)
    cooldown: Column = Column("cooldown", String, index=True)
    sample_name: Column = Column("sample_name", String, nullable=False)
    calibration_id: Column = Column("calibration_id", ForeignKey(Calibration_run.calibration_id), nullable=False)
    result_path: Column = Column("result_path", String, unique=True, nullable=False)
    fitting_path: Column = Column("fitting_path", String, unique=True, nullable=True)
    qbit_idx: Column = Column("qbit_idx", Integer)
    platform_after: Column = Column("platform_after", JSONB)
    platform_before: Column = Column("platform_before", JSONB)
    qprogram: Column = Column("qprogram", JSONB)
    calibration: Column = Column("calibration", JSONB)
    parameters: Column = Column("parameters", JSONB)
    data_shape: Column = Column("data_shape", ARRAY(Integer))

    def __init__(
        self,
        experiment_name,
        sample_name,
        calibration_id,
        result_path,
        experiment_completed,
        start_time,
        qbit_idx,
        fitting_path=None,
        cooldown=None,
        end_time=None,
        run_length=None,
        platform_after=None,
        platform_before=None,
        qprogram=None,
        calibration=None,
        parameters=None,
        data_shape=None,
    ):
        # Required fields
        self.experiment_name = experiment_name
        self.sample_name = sample_name
        self.result_path = result_path
        self.experiment_completed = experiment_completed
        self.start_time = start_time
        self.calibration_id = calibration_id
        self.qbit_idx = qbit_idx

        # Optional fields
        self.fitting_path = fitting_path
        self.cooldown = cooldown
        self.end_time = end_time
        self.run_length = run_length
        self.platform_after = platform_after
        self.platform_before = platform_before
        self.qprogram = qprogram
        self.calibration = calibration
        self.parameters = parameters
        self.data_shape = data_shape

        # self.result_array = result_array

    def end_experiment(self, Session, traceback=None):
        """Function to end measurement of the experiment. The function sets inside the database information
        about the end of the experiment: the finishing time, completeness status and experiment length."""

        with Session() as session:
            # Merge the detached instance into the current session
            persistent_instance = session.merge(self)

            persistent_instance.end_time = datetime.datetime.now()
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time
            try:
                if traceback is None:
                    persistent_instance.experiment_completed = True
                session.commit()
                return persistent_instance
            except Exception as e:
                session.rollback()
                raise e

    def load_h5(self):
        """Load old experiment data from h5 files."""
        return load_results(self.result_path)

    def update_platform(self, Session, platform_before):
        """Function to update measurement platform. The function sets inside the database information
        about the platform_before."""

        with Session() as session:
            # Merge the detached instance into the current session
            persistent_instance = session.merge(self)

            self.platform_before = platform_before
            persistent_instance.platform_before = platform_before

            try:
                session.commit()
                return persistent_instance
            except Exception as e:
                session.rollback()
                raise e

    def __repr__(self):
        return f"{self.measurement_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.sample_name} {self.cooldown} {self.calibration_id}"
