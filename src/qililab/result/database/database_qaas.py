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

from sqlalchemy import Boolean, Column, DateTime, Integer, Interval, String
from sqlalchemy.ext.declarative import declarative_base

from qililab.result.experiment_results import ExperimentResults

base = declarative_base()


class QaaS_Experiment(base):  # type: ignore
    """Creates and manipulates Experiment metadata database"""

    __tablename__ = "experiments"

    experiment_id: Column = Column("experiment_id", Integer, primary_key=True)
    job_id: Column = Column("job_id", Integer)
    experiment_name: Column = Column("experiment_name", String)
    start_time: Column = Column("start_time", DateTime, nullable=False)
    end_time: Column = Column("end_time", DateTime)
    run_length: Column = Column("run_length", Interval)
    experiment_completed: Column = Column("experiment_completed", Boolean, nullable=False)
    cooldown: Column = Column("cooldown", String, index=True)
    sample_name: Column = Column("sample_name", String, nullable=False)
    result_path: Column = Column("result_path", String, unique=True, nullable=False)

    def __init__(
        self,
        job_id,
        experiment_name,
        sample_name,
        result_path,
        experiment_completed,
        start_time,
        cooldown,
    ):
        # Required fields
        self.job_id = job_id
        self.experiment_name = experiment_name
        self.sample_name = sample_name
        self.result_path = result_path
        self.experiment_completed = experiment_completed
        self.start_time = start_time
        self.cooldown = cooldown

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

    def load_experiment(self):
        """Reads current experiment."""

        with ExperimentResults(self.result_path) as results:
            data, dims = results.get()
        return data, dims

    def __repr__(self):
        return f"{self.job_id} {self.experiment_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.sample_name} {self.cooldown}"
