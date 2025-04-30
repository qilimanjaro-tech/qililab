"""Test StreamArray"""

# pylint: disable=protected-access
import datetime
import os
import re
from types import MethodType
from unittest.mock import MagicMock, create_autospec, patch

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from pandas import DataFrame

from qililab.result.database import DatabaseManager, Measurement

mpl.use("Agg")  # Use non-interactive backend for testing


# Dummy path for testing
EXPERIMENT_RESULTS_PATH = "dummy.hdf5"


@pytest.fixture(name="db_manager")
def fixture_db_manager():
    with patch("qililab.result.database.get_engine") as mock_engine:
        mock_engine.return_value = MagicMock()

        with patch("qililab.result.database.sessionmaker") as mock_sessionmaker:
            mock_session = MagicMock()
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_session
            mock_sessionmaker.return_value = lambda: mock_context_manager

            dbm = DatabaseManager("user", "pass", "host", "5432", "db")
            dbm._mock_session = mock_session  # Add reference for testing
            return dbm


class Testdatabase:
    """Test database class"""

    def test_set_sample_and_cooldown_valid_sample_only(self, db_manager: DatabaseManager):
        mock_session = db_manager.Session()
        mock_session.query.return_value.scalar.return_value = True
        db_manager.set_sample_and_cooldown("sample1")
        assert db_manager.current_sample == "sample1"

    def test_set_sample_and_cooldown_invalid_sample(self, db_manager: DatabaseManager):
        db_manager._mock_session.query.return_value.scalar.return_value = False
        with pytest.raises(Exception, match="Sample entry 'sample1' does not exist. Add it with add_sample()"):
            db_manager.set_sample_and_cooldown("sample1")

    def test_add_cooldown(self, db_manager: DatabaseManager):
        cooldown_data = {
            "cooldown": "c1",
            "date": datetime.date.today(),
            "fridge": "f1",
        }

        db_manager.add_cooldown(**cooldown_data)

        assert db_manager._mock_session.add.called
        assert db_manager._mock_session.commit.called

    def test_add_sample(self, db_manager: DatabaseManager):
        sample_data = {
            "sample_name": "s1",
            "manufacturer": "mfg",
            "wafer": "w1",
            "sample": "sam1",
            "fab_run": "run42",
            "device_design": "designX",
            "n_qubits_per_device": [5, 5],
            "additional_info": "test info",
        }

        db_manager.add_sample(**sample_data)

        assert db_manager._mock_session.add.called
        assert db_manager._mock_session.commit.called

    def test_load_by_id(self, db_manager: DatabaseManager):
        db_manager.load_by_id(123)
        assert db_manager.Session().query.called

    # def test_tail(self, db_manager: DatabaseManager):
    #     db_manager.tail(exp_name="exp_name", current_sample=True, order_limit=5, pandas_output=True)
    #     assert db_manager.Session().query(Measurement).filter.called
    #     # assert db_manager.Session().query(Measurement).order_by.called
    #     assert db_manager.Session().query(Measurement).all.called

    #     tail_output = db_manager.tail(exp_name="exp_name", current_sample=True, order_limit=None, pandas_output=False)
    #     assert db_manager.Session().query(Measurement).order_by.called
    #     # assert isinstance(tail_output, DataFrame)
    @patch("qililab.result.database.read_sql")
    def test_tail(self, mock_read_sql, db_manager: DatabaseManager):
        db_manager.current_sample = "sampleA"

        # Capture the mocked session
        mock_session = db_manager.Session()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = ["result1", "result2"]
        mock_session.query.return_value = query_mock

        # Call the method
        result = db_manager.tail()

        # Assertions
        mock_session.query.assert_called_with(Measurement)
        assert query_mock.filter.called
        assert query_mock.order_by.called
        assert query_mock.all.called
        assert result == ["result1", "result2"]

        # Mock connection to Pandas
        conn_mock = MagicMock()
        db_manager.engine.connect.return_value.__enter__.return_value = conn_mock
        df_mock = MagicMock()
        mock_read_sql.return_value = df_mock

        # Pandas output path
        result_pandas = db_manager.tail(order_limit=None, pandas_output=True)

        # Assertions
        assert query_mock.order_by.called  # same mock
        mock_read_sql.assert_called_once()
        assert result_pandas == df_mock

    @patch("qililab.result.database.read_sql")
    def test_head(self, mock_read_sql, db_manager: DatabaseManager):
        db_manager.current_sample = "sampleA"

        # Capture the mocked session
        mock_session = db_manager.Session()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = ["result1", "result2"]
        mock_session.query.return_value = query_mock

        # Call the method
        result = db_manager.head()

        # Assertions
        mock_session.query.assert_called_with(Measurement)
        assert query_mock.filter.called
        assert query_mock.order_by.called
        assert query_mock.all.called
        assert result == ["result1", "result2"]

        # Mock connection to Pandas
        conn_mock = MagicMock()
        db_manager.engine.connect.return_value.__enter__.return_value = conn_mock
        df_mock = MagicMock()
        mock_read_sql.return_value = df_mock

        # Pandas output path
        result_pandas = db_manager.head(order_limit=None, pandas_output=True)

        # Assertions
        assert query_mock.order_by.called  # same mock
        mock_read_sql.assert_called_once()
        assert result_pandas == df_mock

    @patch("qililab.result.database.os.makedirs")
    @patch("qililab.result.database.datetime")
    def test_add_measurement(self, mock_datetime, mock_makedirs, db_manager: DatabaseManager):
        # Setup
        db_manager.current_sample = "sampleA"
        db_manager.current_cd = "cdX"

        fixed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.now.return_value = fixed_time
        mock_datetime.datetime.strftime = datetime.datetime.strftime  # fallback

        # Act
        measurement = db_manager.add_measurement("exp1", experiment_completed=True)

        # Assert
        expected_path = "/home/jupytershared/data/sampleA/cdX/2023-01-01/12_00_00/exp1.h5"
        assert measurement.result_path == expected_path
        assert db_manager._mock_session.add.called_once
        assert db_manager._mock_session.commit.called_once
        assert mock_makedirs.called_once_with("/home/jupytershared/data/sampleA/cdX/2023-01-01/12_00_00")

    @patch("qililab.result.database.h5py.File")
    @patch("qililab.result.database.datetime")
    def test_add_results(self, mock_datetime, mock_h5py_file, db_manager: DatabaseManager):
        db_manager.current_sample = "sampleA"
        db_manager.current_cd = "cdX"

        fixed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.now.return_value = fixed_time
        mock_datetime.datetime.strftime = datetime.datetime.strftime

        # Fake HDF5 structure
        file_mock = MagicMock()
        group_mock = MagicMock()
        file_mock.create_group.return_value = group_mock
        mock_h5py_file.return_value = file_mock

        # Simulated data
        results = np.array([[1, 2], [3, 4]])
        loops = {"x": np.array([0, 1])}

        mock_session = db_manager.Session()
        mock_session.commit = MagicMock()

        db_manager.add_results("exp1", results, loops)

        assert file_mock.create_group.called_once_with(name="loops")
        assert group_mock.create_dataset.called_once_with(name="x", data=loops["x"])
        assert file_mock.create_dataset.called_with("results", data=results)
        assert db_manager._mock_session.add.called_once()
        assert db_manager._mock_session.commit.called_once()
