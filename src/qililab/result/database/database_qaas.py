# Copyright 2025 Qilimanjaro Quantum Tech
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

from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from qililab.result.experiment_results import ExperimentResults


class _QaasBase(DeclarativeBase):
    pass


class QaaS_Experiment(_QaasBase):
    """Creates and manipulates Experiment metadata database"""

    __tablename__ = "executions"

    experiment_id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int | None]
    experiment_name: Mapped[str | None]
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[datetime.datetime | None]
    run_length: Mapped[datetime.timedelta | None]
    experiment_completed: Mapped[bool]
    cooldown: Mapped[str | None] = mapped_column(index=True)
    sample_name: Mapped[str]
    result_path: Mapped[str] = mapped_column(unique=True)

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
                running_session.commit()
                return persistent_instance
            except Exception as e:
                running_session.rollback()
                raise e

    def load_experiment(self):
        """Reads current experiment."""

        with ExperimentResults(self.result_path) as results:
            data, dims = results.get()
        return data, dims

    def __repr__(self):
        return f"{self.job_id} {self.experiment_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.sample_name} {self.cooldown}"
