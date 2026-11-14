"""Opt-in integration checks against a disposable local PostgreSQL server.

Set QILILAB_TEST_POSTGRES_PORT to opt in. The local server must provide a
qililab_test role (password test) with CREATEDB permission. Every case creates
and drops its own uniquely named database, never reusing an existing database.
"""

import os
from uuid import uuid4

import h5py
import numpy as np
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from qililab.qprogram import Calibration
from qililab.result.database.database_autocal import AutocalMeasurement
from qililab.result.database.database_manager import get_db_manager, get_engine
from qililab.result.database.database_measurements import Measurement

pytestmark = pytest.mark.skipif(
    not os.environ.get("QILILAB_TEST_POSTGRES_PORT"),
    reason="set QILILAB_TEST_POSTGRES_PORT for disposable local PostgreSQL integration tests",
)


@pytest.fixture(params=["measurements", "autocal"])
def postgres_manager(request, tmp_path):
    schema = request.param
    port = os.environ["QILILAB_TEST_POSTGRES_PORT"]
    database = f"qililab_test_{uuid4().hex}"
    admin = get_engine("qililab_test", "test", "127.0.0.1", port, "postgres")
    admin = admin.execution_options(isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database}"'))
    manager = None
    try:
        config = tmp_path / "database.ini"
        config.write_text(
            "[postgresql]\nuser=qililab_test\npasswd=test\nhost=127.0.0.1\n"
            f"port={port}\ndatabase={database}\ndatabase_schema={schema}\n",
            encoding="utf-8",
        )
        manager = get_db_manager(str(config))
        model = Measurement if schema == "measurements" else AutocalMeasurement
        model.metadata.create_all(manager.engine)
        yield manager, model
    finally:
        if manager is not None:
            manager.engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{database}" WITH (FORCE)'))
        admin.dispose()


def test_postgresql_measurement_and_fitting_round_trip(postgres_manager, tmp_path):
    manager, _ = postgres_manager
    if manager.database_schema == "measurements":
        manager.add_sample("sample", "synthetic", "wafer", "sample", "run", "design", [2])
        manager.set_sample_and_cooldown("sample")
        entry = manager.add_results(
            "integration",
            np.array([[1.0, 2.0], [3.0, 4.0]]),
            {"frequency": np.array([10.0, 20.0])},
            parameters=["amplitude"],
            result_folder=str(tmp_path),
        )
        with h5py.File(entry.result_path) as result:
            np.testing.assert_array_equal(result["results"][:], [[1.0, 2.0], [3.0, 4.0]])
            assert result["results"].dtype == np.dtype("float64")
            np.testing.assert_array_equal(result["loops/frequency"][:], [10.0, 20.0])
        for read in (manager.head, manager.tail):
            for light in (False, True):
                assert read(light_read=light)[0].measurement_id == entry.measurement_id
                frame = read(light_read=light, pandas_output=True)
                assert frame["measurement_id"].tolist() == [entry.measurement_id]
                assert frame["experiment_name"].tolist() == ["integration"]
    else:
        manager.add_calibration_run({"node": "integration"}, "sample", "cooldown")
        calibration = Calibration()
        calibration.parameters = {"amplitude": 0.25}
        entry = manager.add_autocal_measurement(
            "integration", 0, calibration, data_shape=[2, 2], result_folder=str(tmp_path)
        )
        assert entry.qbit_idx == "0"
        assert "amplitude: 0.25" in entry.calibration

    loaded = manager.load_entry_by_id(entry.measurement_id)
    assert loaded.experiment_name == "integration"
    assert loaded.data_shape == [2, 2]
    assert loaded.result_path == entry.result_path
    fitted = manager.add_fitting(entry.measurement_id, parameters={"frequency_hz": 10.0})
    assert fitted.fitting_parameters == {"frequency_hz": 10.0}
    assert manager.load_entry_by_id(entry.measurement_id).fitting_parameters == {"frequency_hz": 10.0}
    assert manager.add_fitting(entry.measurement_id, parameters={}).fitting_parameters == {"frequency_hz": 10.0}
    with pytest.raises(IndexError, match="does not exist"):
        manager.add_fitting(entry.measurement_id + 1, parameters={"frequency_hz": 20.0})


def test_postgresql_failed_transaction_can_be_rolled_back(postgres_manager):
    manager, model = postgres_manager
    with manager.session() as session:
        session.add(model(measurement_id=1))  # Required measurement fields are deliberately missing.
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.execute(select(model.measurement_id)).scalars().all() == []
        assert session.execute(text("SELECT 42")).scalar_one() == 42


def test_postgresql_missing_database_reports_connection_failure(postgres_manager):
    manager, _ = postgres_manager
    engine = get_engine("qililab_test", "test", "127.0.0.1", manager.engine.url.port, f"missing_{uuid4().hex}")
    try:
        with pytest.raises(OperationalError, match="does not exist"):
            engine.connect()
    finally:
        engine.dispose()
