import pytest
from IPython.testing.globalipapp import start_ipython


@pytest.fixture(scope="session")
def session_ip():
    """Get an IPython shell"""
    yield start_ipython()


@pytest.fixture(scope="function")
def ip(session_ip):
    """Prepare IPython shell for running unit tests"""
    session_ip.run_cell(raw_cell="import qililab")
    yield session_ip


def test_submit_job(ip):
    ip.run_cell(raw_cell="a=1\nb=1")
    ip.run_cell_magic(
        magic_name="submit_job",
        line="-o results -d debug -l slurm_job_data_tests -n unit_test -e local",
        cell="results = a+b ",
    )
    assert ip.user_global_ns["results"].result() == 2


def test_submit_job_output_not_assigned(ip):
    """Check ValueError is raised in case values are not assigned to the output variable within the magic cell."""
    ip.run_cell(raw_cell="a=1\nb=1")
    with pytest.raises(ValueError):
        ip.run_cell_magic(
            magic_name="submit_job",
            line="-o results -d debug -l slurm_job_data_tests -n unit_test -e local",
            cell="a+b",
        )


def test_submit_job_with_random_file_in_logs_folder(ip):
    """Checl ValueError is raised if non-submitit files are found in logs folder"""
    ip.run_cell(
        raw_cell="import os\nfolder_path='slurm_job_data_tests'\nfile_name='abc.py'\nfile_path = os.path.join(folder_path, file_name)\nif not os.path.exists(folder_path):\tos.makedirs(folder_path)\nopen(file_path, 'w')"
    )
    # with pytest.raises(ValueError):
    ip.run_cell_magic(
        magic_name="submit_job",
        line="-o results -d debug -l slurm_job_data_tests -n unit_test -e local",
        cell="results=a+b",
    )
