import pytest
from IPython.testing.globalipapp import start_ipython


@pytest.fixture(scope="session")
def session_ip():
    """Get an IPython shell"""
    yield start_ipython()


@pytest.fixture(scope="function")
def ip(session_ip):
    """Prepare IPython shell for running unit tests"""
    session_ip.run_cell(raw_cell="import qililab.slurm")
    yield session_ip


def test_submit_job(ip):
    ip.run_cell(raw_cell="a=1\nb=1")
    ip.run_cell_magic(
        magic_name="submit_job", line="-o results -d debug -l slurm_job_data_tests -n unit_test", cell="results = a+b "
    )
    assert ip.user_global_ns["results"].result() == 2
