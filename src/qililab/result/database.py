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
from configparser import ConfigParser

import pandas as pd

# from sqlalchemy_utils import database_exists, create_database
import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from qililab import load_results

base = declarative_base()


class Cooldown(base):
    __tablename__ = "cooldowns"

    cooldown = Column("cooldown", String, primary_key=True)
    date = Column("date", sa.Date)
    fridge = Column("fridge", String)

    def __init__(self, cooldown, date, fridge):
        self.cooldown = cooldown
        self.date = date
        self.fridge = fridge

    def __repr__(self):
        return f"{self.cooldown} {self.date} {self.fridge}"


class Sample(base):  # should it be wafer instead?
    __tablename__ = "samples"

    sample_name = Column("sample_name", String, primary_key=True)
    manufacturer = Column("manufacturer", String)

    def __init__(self, sample_name, manufacturer):
        self.sample_name = sample_name
        self.manufacturer = manufacturer

    def __repr__(self):
        return f"{self.sample_name} {self.manufacturer}"


class Measurement(base):
    __tablename__ = "measurements"

    measurement_id = Column("measurement_id", Integer, primary_key=True)
    # exp_id = Column("exp_id", Integer) # intended to count individually based on sample and exp_type
    experiment_name = Column("experiment_name", String, nullable=False)
    optional_identifier = Column("optional_identifier", String)  # add max length?
    start_time = Column("start_time", sa.DateTime, nullable=False)
    end_time = Column("end_time", sa.DateTime)
    run_length = Column("run_length", sa.Interval)
    experiment_completed = Column("experiment_completed", sa.Boolean, nullable=False)
    # temperature = Column("temperature", sa.ARRAY(Integer))
    cooldown = Column("cooldown", ForeignKey(Cooldown.cooldown))
    sample_name = Column("sample_name", ForeignKey(Sample.sample_name), nullable=False)
    result_path = Column("result_path", String, unique=True, nullable=False)
    platform = Column("platform", JSONB)
    experiment = Column("experiment", JSONB)
    qprogram = Column("qprogram", JSONB)
    calibration = Column("calibration", JSONB)
    parameters = Column("parameters", JSONB)
    data_shape = Column("data_shape", sa.ARRAY(Integer))

    def _end_experiment(self, Session):
        with Session() as session:
            # Merge the detached instance into the current session
            persistent_instance = session.merge(self)
            persistent_instance.end_time = datetime.datetime.now()
            persistent_instance.experiment_completed = True
            persistent_instance.run_length = persistent_instance.end_time - persistent_instance.start_time
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)

    def load_old_h5(self):
        return load_results(self.result_path)

    def load_df(self):
        return pd.read_hdf(self.result_path)

    def load_xarray(self):
        df = pd.read_hdf(self.result_path)
        return df.to_xarray().to_dataarray()

    def load_numpy(self):
        df = pd.read_hdf(self.result_path)
        da = df.to_xarray().to_dataarray()
        arr = da.to_numpy()[0,]
        axis_labels = {dim: da.coords[dim].values for dim in da.dims[1:]}
        return arr, axis_labels

    def __init__(  # We create a custon __init__ method to make sure that the required fields are filled
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

        # self.result_array = result_array

    def __repr__(self):
        return f"{self.measurement_id} {self.experiment_name} {self.start_time} {self.end_time} {self.run_length} {self.sample_name} {self.cooldown}"


def get_engine(user, passwd, host, port, db):
    url = f"postgresql://{user}:{passwd}@{host}:{port}/{db}"
    return create_engine(url)


class DatabaseManager:
    def __init__(self, user, passwd, host, port, db):
        self.engine = get_engine(user, passwd, host, port, db)
        # Base.metadata.drop_all(bind=self.engine)  # For quick development, remove in production
        # Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.current_cd = None
        self.current_sample = None

    def set_sample_and_cooldown(self, sample, cooldown=None):
        # You always need to set sample
        with self.Session() as session:
            sample_exists = session.query(sa.exists().where(Sample.sample_name == sample)).scalar()
            if sample_exists:
                self.current_sample = sample
            else:
                raise Exception(f"Sample entry '{sample}' does not exist. Add it with add_sample()")

            # Setting CD is optional, if you are doing a measurement which is not tied to a CD
            if cooldown:
                cd_exists = session.query(sa.exists().where(Cooldown.cooldown == cooldown)).scalar()
                if cd_exists:
                    self.current_cd = cooldown
                else:
                    raise Exception(f"CD entry '{cooldown}' does not exist. Add it with add_cooldown()")
                print(f"Set current sample to {sample} and cooldown to {cooldown}")
                return None

            print(f"Set current sample to {sample}")
            return None

    def add_cooldown(self, cooldown: str, fridge: str, date: datetime.date = datetime.date.today()):
        cooldown_obj = Cooldown(cooldown=cooldown, date=date, fridge=fridge)
        with self.Session() as session:
            session.add(cooldown_obj)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)

    def add_sample(self, sample_name: str, manufacturer: str):
        sample_obj = Sample(sample_name=sample_name, manufacturer=manufacturer)
        with self.Session() as session:
            session.add(sample_obj)
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)

    def load_by_id(self, id):
        return self.Session().query(Measurement).where(Measurement.measurement_id == id).one_or_none()

    def tail(self, exp_name=None, current_sample=True, n=5, pandas_output=False):
        with self.engine.connect() as con:
            query = self.Session().query(Measurement)

            if current_sample and self.current_sample:
                query = query.filter(Measurement.sample_name == self.current_sample)

            if exp_name is not None:
                query = query.filter(Measurement.experiment_name == exp_name)

            if n is not None:
                query = query.order_by(Measurement.measurement_id).desc().limit(n)
            else:
                query = query.order_by(Measurement.measurement_id).desc()

            if pandas_output:
                return pd.read_sql(query.statement, con=con)
            else:
                return query.all()

    def head(self, n=5, exp_name=None, current_sample=True, pandas_output=False):
        with self.engine.connect() as con:
            query = self.Session().query(Measurement)

            if current_sample and self.current_sample:
                query = query.filter(Measurement.sample_name == self.current_sample)

            if exp_name is not None:
                query = query.filter(Measurement.experiment_name == exp_name)

            if n is not None:
                query = query.order_by(Measurement.measurement_id).limit(n)
            else:
                query = query.order_by(Measurement.measurement_id)

            if pandas_output:
                return pd.read_sql(query.statement, con=con)
            else:
                return query.all()

    def add_measurement(
        self,
        experiment_name,
        result_path,
        experiment_completed,
        start_time=datetime.datetime.now(),
        cooldown=None,
        sample_name=None,
        optional_identifier=None,
        end_time=None,
        run_length=None,
        platform=None,
        experiment=None,
        qprogram=None,
        calibration=None,
        parameters=None,
        data_shape=None,
    ):
        if sample_name is None:
            if self.current_sample:
                sample_name = self.current_sample
            else:
                raise Exception("Please set a sample using set_sample()")
        if cooldown is None:
            cooldown = self.current_cd

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
                print(e)
                return None


def load_config(filename="database.ini", section="postgresql"):
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception("Section {0} not found in the {1} file".format(section, filename))
    return config


def get_db_manager():
    return DatabaseManager(**load_config())
