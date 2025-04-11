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

from qililab.result.database import DatabaseManager

mpl.use("Agg")  # Use non-interactive backend for testing


# Dummy path for testing
EXPERIMENT_RESULTS_PATH = "dummy.hdf5"


@pytest.fixture(name="database_manager")
def fixture_database_manager():
    """Create a mock DatabaseManager class for testing"""
    user = "user"
    passwd = "passwd"
    host = "host"
    port = 0
    database = "database"
    database_manager = DatabaseManager(user=user, passwd=passwd, host=host, port=port, database=database)
    return database_manager


class Testdatabase:
    """Test database class"""

    def test_database_manager_create_and_set_sample_and_coldown(self, database_manager: DatabaseManager):
        """Test __enter__ and __exit__"""
        sample = "sample"
        cooldown = "cooldown"
        database_manager.add_cooldown(cooldown=cooldown, fridge="Mimas", date=datetime.date.today())
        database_manager.add_sample(
            sample_name=sample,
            manufacturer="manufacturer",
            wafer="wafer",
            sample="sample",
            fab_run="fab_run",
            device_design="device_design",
            n_qubits_per_device=[1, 1],
            additional_info="additional_info",
        )

        database_manager.set_sample_and_cooldown(sample, cooldown)

    def test_database_manager_create_and_set_sample(self, database_manager: DatabaseManager):
        """Test __enter__ and __exit__"""
        sample = "sample"
        cooldown = "cooldown"
        database_manager.add_cooldown(cooldown=cooldown, fridge="Mimas", date=datetime.date.today())
        database_manager.add_sample(
            sample_name=sample,
            manufacturer="manufacturer",
            wafer="wafer",
            sample="sample",
            fab_run="fab_run",
            device_design="device_design",
            n_qubits_per_device=[1, 1],
            additional_info="additional_info",
        )

        database_manager.set_sample_and_cooldown(sample)

    def test_database_manager_set_sample_error_wrong_cooldown(self, database_manager: DatabaseManager):
        """Test __enter__ and __exit__"""
        sample = "sample"
        sample_2 = "sample_2"
        cooldown = "cooldown"
        cooldown_2 = "cooldown_2"
        database_manager.add_cooldown(cooldown=cooldown, fridge="Mimas", date=datetime.date.today())
        database_manager.add_sample(
            sample_name=sample,
            manufacturer="manufacturer",
            wafer="wafer",
            sample="sample",
            fab_run="fab_run",
            device_design="device_design",
            n_qubits_per_device=[1, 1],
            additional_info="additional_info",
        )

        error_string = f"CD entry '{cooldown_2}' does not exist. Add it with add_cooldown()"
        with pytest.raises(Exception, match=re.escape(error_string)):
            database_manager.set_sample_and_cooldown(sample, cooldown_2)

        error_string = f"Sample entry '{sample_2}' does not exist. Add it with add_sample()"
        with pytest.raises(Exception, match=re.escape(error_string)):
            database_manager.set_sample_and_cooldown(sample_2)
