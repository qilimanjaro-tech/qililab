"""Test StreamArray"""

# pylint: disable=protected-access
import datetime
from unittest.mock import MagicMock, patch

import matplotlib as mpl
import numpy as np
import pytest

from qililab.result.database import DatabaseManager, Measurement, _load_config, get_db_manager, get_engine, load_by_id

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

            dbm = DatabaseManager(
                "user", "pass", "host", "5432", "db", "/local_test/", "/shared_test/", "mesaurement_folder"
            )
            dbm._mock_session = mock_session  # Add reference for testing
            return dbm


@pytest.fixture(name="measurement")
def fixture_measurement():
    return Measurement(
        experiment_name="test_experiment",
        sample_name="sampleA",
        result_path="/test/result.h5",
        experiment_completed=False,
        start_time=datetime.datetime(2023, 1, 1, 12, 0, 0),
        cooldown="CDX",
    )


class TestMeasurement:
    """Test Measurement class"""

    @patch("qililab.result.database.datetime")
    def test_end_experiment(self, mock_datetime, measurement):
        fixed_now = datetime.datetime(2023, 1, 1, 14, 0, 0)
        mock_datetime.datetime.now.return_value = fixed_now

        mock_session_context = MagicMock()
        mock_session = MagicMock()
        mock_session_context.__enter__.return_value = mock_session
        mock_session.merge.return_value = measurement

        result = measurement.end_experiment(lambda: mock_session_context)

        assert result.end_time == fixed_now
        assert result.experiment_completed is True
        assert result.run_length == fixed_now - measurement.start_time
        mock_session.commit.assert_called_once()

    @patch("qililab.result.database.datetime")
    def test_end_experiment_raises_exception(self, mock_datetime, measurement):
        fixed_now = datetime.datetime(2023, 1, 1, 14, 0, 0)
        mock_datetime.datetime.now.return_value = fixed_now

        mock_session_context = MagicMock()
        mock_session = MagicMock()
        mock_session_context.__enter__.return_value = mock_session
        mock_session.merge.return_value = measurement
        mock_session.commit.side_effect = Exception("Measurement error")

        with pytest.raises(Exception, match="Measurement error"):
            result = measurement.end_experiment(lambda: mock_session_context)

        mock_session.rollback.assert_called_once()

    @patch("qililab.result.database.ExperimentResults")
    def test_read_experiment(self, mock_experiment_results, measurement):
        mock_instance = MagicMock()
        mock_instance.get.return_value = ("data", "dims")
        mock_experiment_results.return_value.__enter__.return_value = mock_instance

        data, dims = measurement.read_experiment()

        assert data == "data"
        assert dims == "dims"
        mock_experiment_results.assert_called_once_with(measurement.result_path)

    @patch("qililab.result.database.ExperimentResults")
    @patch("qililab.result.database.DataArray")
    def test_read_experiment_xarray(self, mock_data_array, mock_experiment_results, measurement):
        mock_results = MagicMock()
        dims_mock = [
            MagicMock(labels=["x"], values=[[0, 1]]),
            MagicMock(labels=["I/Q"], values=[[0, 1]]),
        ]
        data_mock = MagicMock()
        data_mock.take.side_effect = [np.array([[1.0]]), np.array([[2.0]])]

        mock_results.get.return_value = (data_mock, dims_mock)
        mock_experiment_results.return_value.__enter__.return_value = mock_results

        measurement.read_experiment_xarray()

        data_mock.take.assert_any_call(indices=0, axis=1)
        data_mock.take.assert_any_call(indices=1, axis=1)
        mock_data_array.assert_called_once()

    @patch("qililab.result.database.load_results")
    def test_load_old_h5(self, mock_load_results, measurement):
        measurement.load_old_h5()
        mock_load_results.assert_called_once_with(measurement.result_path)

    @patch("qililab.result.database.read_hdf")
    def test_load_df(self, mock_read_hdf, measurement):
        measurement.load_df()
        mock_read_hdf.assert_called_once_with(measurement.result_path)

    @patch("qililab.result.database.read_hdf")
    def test_load_xarray(self, mock_read_hdf, measurement):
        mock_df = MagicMock()
        mock_read_hdf.return_value = mock_df
        measurement.load_xarray()
        mock_df.to_xarray.assert_called_once()

    @patch("qililab.result.database.read_hdf")
    def test_read_numpy(self, mock_read_hdf, measurement):
        mock_da = MagicMock()
        mock_da.dims = ["batch", "x", "y"]
        mock_da.coords = {"x": MagicMock(values=np.array([1, 2])), "y": MagicMock(values=np.array([3, 4]))}
        mock_da.to_numpy.return_value = np.array([[[1, 2], [3, 4]]])

        mock_xr = MagicMock()
        mock_xr.to_dataarray.return_value = mock_da
        mock_df = MagicMock()
        mock_df.to_xarray.return_value = mock_xr

        mock_read_hdf.return_value = mock_df

        arr, labels = measurement.read_numpy()

        assert isinstance(arr, np.ndarray)
        assert "x" in labels and "y" in labels
        mock_read_hdf.assert_called_once()


class Testdatabase:
    """Test database class"""

    def test_set_sample(self, db_manager: DatabaseManager):
        mock_session = db_manager.Session()
        mock_session.query.return_value.scalar.return_value = True
        db_manager.set_sample_and_cooldown("sample1")
        assert db_manager.current_sample == "sample1"

    def test_set_sample_and_cooldown(self, db_manager: DatabaseManager):
        mock_session = db_manager.Session()
        mock_session.query.return_value.scalar.return_value = True
        db_manager.set_sample_and_cooldown("sample1", "CD1")
        assert db_manager.current_sample == "sample1"
        assert db_manager.current_cd == "CD1"

    def test_set_sample_and_cooldown_warn_inactive_cd(self, db_manager: DatabaseManager):
        mock_session = db_manager.Session()
        mock_session.__enter__.return_value = mock_session

        # Mock sample and cooldown
        mock_sample = MagicMock()
        mock_sample.scalar.return_value = True
        mock_cd_object = MagicMock(active=False)  # Mocking CD active as false
        mock_cd = MagicMock()
        mock_cd.filter.return_value.one_or_none.return_value = mock_cd_object

        mock_session.query.side_effect = [mock_sample, mock_cd]

        # Patch warnings.warn and assert correct call
        with patch("warnings.warn") as mock_warn:
            db_manager.set_sample_and_cooldown(sample="sample1", cooldown="cooldown1")
            mock_warn.assert_any_call("Cooldown 'cooldown1' is not active. Make sure you have set the right cooldown.")

    def test_set_sample_and_cooldown_invalid_sample(self, db_manager: DatabaseManager):
        # Sample does not exist
        db_manager._mock_session.query.return_value.scalar.return_value = False
        with pytest.raises(Exception, match="Sample entry 'sample1' does not exist. Add it with add_sample()"):
            db_manager.set_sample_and_cooldown("sample1")

    def test_set_sample_and_cooldown_invalid_cooldown(self, db_manager: DatabaseManager):
        # Sample exists
        db_manager._mock_session.query.return_value.scalar.return_value = True
        # Cooldown does not exist
        db_manager._mock_session.query.return_value.filter.return_value.one_or_none.return_value = None

        with pytest.raises(Exception, match="CD entry 'CD1' does not exist. Add it with add_cooldown()"):
            db_manager.set_sample_and_cooldown("sample1", "CD1")

    def test_add_cooldown(self, db_manager: DatabaseManager):
        cooldown_data = {
            "cooldown": "c1",
            "date": datetime.date.today(),
            "fridge": "f1",
        }

        db_manager.add_cooldown(**cooldown_data)

        db_manager._mock_session.add.assert_called
        db_manager._mock_session.commit.assert_called

    def test_add_cooldown_raises_exception(self, db_manager: DatabaseManager):
        cooldown_data = {
            "cooldown": "c1",
            "date": datetime.date.today(),
            "fridge": "f1",
        }

        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB error")

        db_manager.Session = MagicMock(return_value=mock_session)

        with pytest.raises(Exception, match="DB error"):
            db_manager.add_cooldown(**cooldown_data)

        mock_session.rollback.assert_called_once

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

        db_manager._mock_session.add.assert_called
        db_manager._mock_session.commit.assert_called

    def test_add_sample_raises_exception(self, db_manager: DatabaseManager):
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

        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB error")

        db_manager.Session = MagicMock(return_value=mock_session)

        with pytest.raises(Exception, match="DB error"):
            db_manager.add_sample(**sample_data)

        mock_session.rollback.assert_called_once

    def test_load_by_id(self, db_manager: DatabaseManager):
        mock_measurement = MagicMock(spec=Measurement)
        mock_measurement.result_path = "/local_test/results/file.h5"
        mock_measurement.measurement_id = 123

        db_manager._mock_session.query.return_value.where.return_value.one_or_none.return_value = mock_measurement

        with patch("os.path.isfile", return_value=False):
            result = db_manager.load_by_id(123)

        db_manager._mock_session.query.assert_called
        assert result.result_path == "/shared_test/results/file.h5"

    def test_load_by_id_path_not_found(self, db_manager: DatabaseManager):
        # Setup a mock measurement
        mock_measurement = MagicMock(spec=Measurement)
        mock_measurement.result_path = "/local_test/results/file.h5"
        db_manager._mock_session.query.return_value.where.return_value.one_or_none.return_value = mock_measurement

        # Patch os.path.isfile to return False to simulate missing file
        with patch("os.path.isfile", return_value=False):
            db_manager.load_by_id(123)

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
        result = db_manager.tail(exp_name="test", since_id=1)

        # Assertions
        mock_session.query.assert_called_with(Measurement)
        query_mock.filter.assert_called
        query_mock.order_by.assert_called
        query_mock.all.assert_called
        assert result == ["result1", "result2"]

        # Mock connection to Pandas
        conn_mock = MagicMock()
        db_manager.engine.connect.return_value.__enter__.return_value = conn_mock
        df_mock = MagicMock()
        mock_read_sql.return_value = df_mock

        # Pandas output path
        result_pandas = db_manager.tail(order_limit=None, pandas_output=True, light_read=True)

        # Assertions
        query_mock.order_by.assert_called  # same mock
        query_mock.with_entities.assert_called
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
        result = db_manager.head(exp_name="test", before_id=10)

        # Assertions
        mock_session.query.assert_called_with(Measurement)
        query_mock.filter.assert_called
        query_mock.order_by.assert_called
        query_mock.all.assert_called
        assert result == ["result1", "result2"]

        # Mock connection to Pandas
        conn_mock = MagicMock()
        db_manager.engine.connect.return_value.__enter__.return_value = conn_mock
        df_mock = MagicMock()
        mock_read_sql.return_value = df_mock

        # Pandas output path
        result_pandas = db_manager.head(order_limit=None, pandas_output=True, light_read=True)

        # Assertions
        assert query_mock.order_by.called  # same mock
        mock_read_sql.assert_called_once()
        assert result_pandas == df_mock

    def test_get_qprogram(self, db_manager: DatabaseManager):
        """Test get qprogram function from the database manager"""
        mock_session = db_manager.Session()
        mock_session.__enter__.return_value = mock_session

        with patch("os.path.isfile", return_value=False):
            qprogram = db_manager.get_qprogram(123)

        assert qprogram == mock_session.query(Measurement.qprogram).filter(Measurement.measurement_id == 123).scalar()

    def test_get_platform(self, db_manager: DatabaseManager):
        """Test get platform function from the database manager"""
        mock_session = db_manager.Session()
        mock_session.__enter__.return_value = mock_session

        with patch("os.path.isfile", return_value=False):
            platform = db_manager.get_platform(123)

        assert platform == mock_session.query(Measurement.platform).filter(Measurement.measurement_id == 123).scalar()

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
        expected_path = "/shared_test/mesaurement_folder/sampleA/cdX/2023-01-01/12_00_00/exp1.h5"
        assert measurement.result_path == expected_path
        db_manager._mock_session.add.assert_called_once
        db_manager._mock_session.commit.assert_called_once
        mock_makedirs.assert_called_once_with("/shared_test/mesaurement_folder/sampleA/cdX/2023-01-01/12_00_00")

    def test_add_measurement_raises_exception_no_sample(self, db_manager: DatabaseManager):
        # Set current_sample to None to simulate no sample set
        db_manager.current_sample = None

        with pytest.raises(Exception, match="Please set at least a sample using set_sample_and_cooldown(...)"):
            db_manager.add_measurement(experiment_name="exp1", experiment_completed=True)

    @patch("qililab.result.database.os.makedirs")
    @patch("qililab.result.database.datetime")
    def test_add_measurement_raises_exception(self, mock_datetime, mock_makedirs, db_manager: DatabaseManager):
        db_manager.current_sample = "sampleA"
        db_manager.current_cd = "cdX"

        fixed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.now.return_value = fixed_time
        mock_datetime.datetime.strftime = datetime.datetime.strftime  # fallback

        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB error")

        db_manager.Session = MagicMock(return_value=mock_session)

        with pytest.raises(Exception, match="DB error"):
            _ = db_manager.add_measurement("exp1", experiment_completed=True)

        mock_session.rollback.assert_called_once

    @patch("qililab.result.database.h5py.File")
    @patch("qililab.result.database.os.makedirs")
    @patch("qililab.result.database.os.path.isdir")
    @patch("qililab.result.database.datetime")
    def test_add_results(self, mock_datetime, mock_isdir, mock_makedirs, mock_h5py_file, db_manager: DatabaseManager):
        db_manager.current_sample = "sampleA"
        db_manager.current_cd = "cdX"

        # Simulate the directory does not exist
        mock_isdir.return_value = False

        # Simulate fixed time
        fixed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.now.return_value = fixed_time
        mock_datetime.datetime.strftime = datetime.datetime.strftime

        # Setup HDF5 mock
        file_mock = MagicMock()
        group_mock = MagicMock()
        file_mock.create_group.return_value = group_mock
        mock_h5py_file.return_value = file_mock

        # Simulated data
        results = np.array([[1, 2], [3, 4]])
        loops = {"x": np.array([0, 1])}

        # Run the method
        db_manager.add_results("exp1", results, loops)

        # Assertions
        group_mock.create_dataset.assert_called_once_with(name="x", data=loops["x"])
        file_mock.create_dataset.assert_called_once_with("results", data=results)
        db_manager._mock_session.add.assert_called_once()
        db_manager._mock_session.commit.assert_called_once()
        mock_makedirs.assert_called_once()  # make sure directory was attempted to be created

    def test_add_results_raises_exception_no_sample(self, db_manager: DatabaseManager):
        # Set current_sample to None to simulate no sample set
        db_manager.current_sample = None

        results = np.array([[1, 2], [3, 4]])
        loops = {"x": np.array([0, 1])}

        with pytest.raises(Exception, match="Please set at least a sample using set_sample_and_cooldown(...)"):
            db_manager.add_results(experiment_name="exp1", results=results, loops=loops)

    @patch("qililab.result.database.h5py.File")
    @patch("qililab.result.database.os.makedirs")
    @patch("qililab.result.database.os.path.isdir")
    @patch("qililab.result.database.datetime")
    def test_add_results_raises_exception(
        self, mock_datetime, mock_isdir, mock_makedirs, mock_h5py_file, db_manager: DatabaseManager
    ):
        db_manager.current_sample = "sampleA"
        db_manager.current_cd = "cdX"

        # Simulate the directory does not exist
        mock_isdir.return_value = False

        # Simulate fixed time
        fixed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.now.return_value = fixed_time
        mock_datetime.datetime.strftime = datetime.datetime.strftime

        # Setup HDF5 mock
        file_mock = MagicMock()
        group_mock = MagicMock()
        file_mock.create_group.return_value = group_mock
        mock_h5py_file.return_value = file_mock

        # Simulated data
        results = np.array([[1, 2], [3, 4]])
        loops = {"x": np.array([0, 1])}

        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.commit.side_effect = Exception("DB error")

        db_manager.Session = MagicMock(return_value=mock_session)

        with pytest.raises(Exception, match="DB error"):
            db_manager.add_results("exp1", results, loops)

        mock_session.rollback.assert_called_once


@patch("qililab.result.database.ConfigParser")
def test_load_config_success(mock_config_parser):
    mock_parser = MagicMock()
    mock_parser.has_section.return_value = True
    mock_parser.items.return_value = [("host", "localhost"), ("database", "testdb")]
    mock_config_parser.return_value = mock_parser

    result = _load_config(filename="fakefile.ini", section="postgresql")

    assert result == {"host": "localhost", "database": "testdb"}
    mock_parser.read.assert_called_once_with("fakefile.ini")
    mock_parser.has_section.assert_called_once_with("postgresql")


@patch("qililab.result.database.ConfigParser")
def test_load_config_missing_section(mock_config_parser):
    mock_parser = MagicMock()
    mock_parser.has_section.return_value = False
    mock_config_parser.return_value = mock_parser

    with pytest.raises(Exception, match="Section section not found in the failfile.ini file"):
        _load_config(filename="failfile.ini", section="section")


@patch("qililab.result.database._load_config")
@patch("qililab.result.database.DatabaseManager")
def test_get_db_manager(mock_db_manager, mock_load_config):
    mock_load_config.return_value = {
        "host": "localhost",
        "user": "user",
        "password": "pass",
        "port": "5432",
        "database": "testdb",
    }
    get_db_manager()
    mock_db_manager.assert_called_once_with(**mock_load_config.return_value)


@patch("qililab.result.database.create_engine")
def test_get_engine(mock_create_engine):
    user = "user"
    passwd = "password"
    host = "localhost"
    port = "5432"
    database = "mydb"
    expected_url = f"postgresql://{user}:{passwd}@{host}:{port}/{database}"

    get_engine(user, passwd, host, port, database)
    mock_create_engine.assert_called_once_with(expected_url)


@patch("qililab.result.database.get_db_manager")
def test_independent_load_by_id(mock_get_db_manager):
    mock_db = MagicMock()
    mock_get_db_manager.return_value = mock_db

    test_id = 1
    load_by_id(test_id)

    mock_get_db_manager.assert_called_once()
    mock_db.load_by_id.assert_called_once_with(test_id)
