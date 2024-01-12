import os
import shutil
import time
from unittest.mock import MagicMock, patch

import pytest
from IPython.testing.globalipapp import start_ipython

import qililab as ql

# pylint: disable=redefined-outer-name
slurm_job_data_test = "slurm_job_data_test"


@pytest.fixture(scope="session")
def session_ip():
    """Get an IPython shell"""
    yield start_ipython()


@pytest.fixture(scope="function")
def ip(session_ip):
    """Prepare IPython shell for running unit tests"""
    session_ip.run_cell(raw_cell="import qililab.slurm")
    yield session_ip


class TestSubmitJob:
    def teardown_method(self):
        """Teardown method to make sure all files are deleted."""
        if os.path.exists(slurm_job_data_test):
            shutil.rmtree(slurm_job_data_test)

    def test_submit_job(self, ip):
        ip.run_cell(raw_cell="a=1\nb=1")
        ip.run_cell_magic(
            magic_name="submit_job",
            line=f"-o results -p debug -l {slurm_job_data_test} -n unit_test -e local",
            cell="results = a+b ",
        )
        time.sleep(4)
        assert ip.user_global_ns["results"].result() == 2

    def test_submit_job_output_not_assigned(self, ip):
        """Check ValueError is raised in case values are not assigned to the output variable within the magic cell."""
        ip.run_cell(raw_cell="a=1\nb=1")
        with pytest.raises(
            ValueError, match="Output variable 'results' was not assigned to any value inside the cell!"
        ):
            ip.run_cell_magic(
                magic_name="submit_job",
                line=f"-o results -p debug -l {slurm_job_data_test} -n unit_test -e local",
                cell="a+b",
            )

    def test_submit_job_with_random_file_in_logs_folder(self, ip):
        """Check non-submitit files are deleted if found in logs folder"""
        ip.run_cell(
            raw_cell=f"import os\nfolder_path='{slurm_job_data_test}'\nfile_name='abc.py'\nfile_path = os.path.join(folder_path, file_name)\nif not os.path.exists(folder_path):\tos.makedirs(folder_path)\nopen(file_path, 'w')\na=1\nb=1"
        )
        ip.run_cell_magic(
            magic_name="submit_job",
            line=f"-o results -p debug -l {slurm_job_data_test} -n unit_test -e local",
            cell="results=a+b",
        )
        time.sleep(4)  # give time to ensure processes are finished
        assert os.path.isfile(os.path.join(slurm_job_data_test, "abc.py")) is False

    def test_submit_job_delete_info_from_past_jobs(self, ip):
        """Check only a certain amount files are kept in the logs folder"""
        ql.slurm.num_files_to_keep = 8
        ip.run_cell(raw_cell="a=1\nb=1")
        for _ in range(int(ql.slurm.num_files_to_keep / 4)):
            ip.run_cell_magic(
                magic_name="submit_job",
                line=f"-o results -p debug -l {slurm_job_data_test} -n unit_test -e local",
                cell="results=a+b",
            )
            time.sleep(2)  # give time submitit to create the files

        assert (
            len([f for f in os.listdir(slurm_job_data_test) if os.path.isfile(os.path.join(slurm_job_data_test, f))])
            == ql.slurm.num_files_to_keep
        )
        ip.run_cell_magic(
            magic_name="submit_job",
            line=f"-o results -p debug -l {slurm_job_data_test} -n unit_test -e local",
            cell="results=a+b",
        )
        time.sleep(2)
        assert (
            len([f for f in os.listdir(slurm_job_data_test) if os.path.isfile(os.path.join(slurm_job_data_test, f))])
            == ql.slurm.num_files_to_keep
        )
        assert ip.user_global_ns["results"].result() == 2

    def test_setting_parameters(self, ip):
        """Test that the parameters of the magic method work properly."""
        ip.run_cell(raw_cell="a=1\nb=1")
        with patch("qililab.slurm.AutoExecutor") as executor:
            executor_instance = MagicMock()
            executor.return_value = executor_instance
            with patch("qililab.slurm.os"):
                ip.run_cell_magic(
                    magic_name="submit_job",
                    line=f"-o results -p debug -l {slurm_job_data_test} -n unit_test -e local -t 5 --begin now+1hour -lp true",
                    cell="results=a+b",
                )
        executor.assert_called_once_with(folder=slurm_job_data_test, cluster="local")
        executor_instance.update_parameters.assert_called_once_with(
            slurm_partition="debug",
            name="unit_test",
            timeout_min=5,
            slurm_additional_parameters={"begin": "now+1hour", "nice": 1000000},
        )
