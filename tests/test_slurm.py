import os
import shutil
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import qililab as ql
from IPython.testing.globalipapp import start_ipython

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
            line=f"-o results -g aQPU1 -l {slurm_job_data_test} -n unit_test -e local",
            cell="results = a+b",
        )
        # give local executor time to finish
        time.sleep(3)
        assert ip.user_global_ns["results"].result() == 2

    def test_submit_job_output_not_assigned(self, ip):
        """Check ValueError is raised if the output variable is not assigned inside the cell."""
        ip.run_cell(raw_cell="a=1\nb=1")
        with pytest.raises(ValueError, match=r"assigned to any value inside the cell"):
            ip.run_cell_magic(
                magic_name="submit_job",
                line=f"-o results -g aQPU1 -l {slurm_job_data_test} -n unit_test -e local",
                cell="a+b",
            )

    def test_submit_job_no_gres_provided(self, ip):
        """Check no Error is raised when GRES is not provided."""
        ip.run_cell(raw_cell="a=1\nb=1")
        ip.run_cell_magic(
            magic_name="submit_job",
            line=f"-o results -l {slurm_job_data_test} -n unit_test -e local",
            cell="results = a+b",
        )
        # If we got here without an exception, it's OK.

    def test_submit_job_with_random_file_in_logs_folder(self, ip):
        """Check non-submitit files are deleted if found in logs folder"""
        ip.run_cell(
            raw_cell=(
                f"import os\n"
                f"folder_path='{slurm_job_data_test}'\n"
                f"file_name='abc.py'\n"
                f"file_path = os.path.join(folder_path, file_name)\n"
                f"if not os.path.exists(folder_path):\n\tos.makedirs(folder_path)\n"
                f"open(file_path, 'w')\n"
                f"a=1\nb=1"
            )
        )
        ip.run_cell_magic(
            magic_name="submit_job",
            line=f"-o results -g aQPU1 -l {slurm_job_data_test} -n unit_test -e local",
            cell="results=a+b",
        )
        time.sleep(3)  # give time to ensure processes/cleanup are finished
        assert not os.path.isfile(os.path.join(slurm_job_data_test, "abc.py"))

    def test_cleanup_keeps_only_last_n_job_groups(self, ip):
        """
        Create synthetic numeric job-id groups in the logs folder and verify
        the cleanup keeps only the newest groups by id, taking into account
        the real job submitted to trigger the cleanup.
        """
        import re
        from pathlib import Path

        ql.slurm.max_groups_to_keep = 3
        base = Path(slurm_job_data_test)
        base.mkdir(parents=True, exist_ok=True)

        # Create 5 groups with numeric prefixes: 1001..1005
        for jid in range(1001, 1006):
            (base / f"{jid}_submission.pkl").write_text("x")
            (base / f"{jid}_log.out").write_text("y")

        # Submit a job to trigger the cleanup routine
        ip.run_cell(raw_cell="a=1\nb=1")
        ip.run_cell_magic(
            magic_name="submit_job",
            line=f"-o results -l {slurm_job_data_test} -n unit_test -e local",
            cell="results=a+b",
        )
        time.sleep(1)

        # Numeric prefixes present after cleanup
        existing = {
            p.name.split("_")[0]
            for p in base.glob("*")
            if p.name and p.name[0].isdigit()
        }

        # Build the set of candidate IDs = synthetic IDs + (numeric part of) the real job id
        job = ip.user_global_ns["results"]
        m = re.match(r"^(\d+)", str(getattr(job, "job_id", "")))
        candidate_ids = {1001, 1002, 1003, 1004, 1005}
        if m:
            candidate_ids.add(int(m.group(1)))

        # Keep the largest N (by numeric order)
        expected_top_n = sorted(candidate_ids)[-ql.slurm.max_groups_to_keep:]
        expected = {str(x) for x in expected_top_n}

        # The cleanup should leave exactly those groups
        assert existing == expected

        # And the job still ran correctly
        assert ip.user_global_ns["results"].result() == 2


    def test_setting_parameters(self, ip):
        """Test that the parameters of the magic method are forwarded properly, including --chdir and low priority flag."""
        ip.run_cell(raw_cell="a=1\nb=1")

        workdir = os.path.join(slurm_job_data_test, "workdir")
        os.makedirs(workdir, exist_ok=True)

        with patch("qililab.slurm.AutoExecutor") as executor:
            # Prepare the fake executor/job
            executor_instance = MagicMock()
            fake_job = MagicMock()
            fake_job.job_id = "123456"
            executor_instance.submit.return_value = fake_job
            executor.return_value = executor_instance

            ip.run_cell_magic(
                magic_name="submit_job",
                line=(
                    f"-o results -p debug -l {slurm_job_data_test} -n unit_test "
                    f"-e local -t 5 --begin now+1hour -lp -g aQPU1 -c {workdir}"
                ),
                cell="results=a+b",
            )

        # AutoExecutor created with expected args
        executor.assert_called_once_with(folder=slurm_job_data_test, cluster="local")

        # update_parameters carries partition/name/timeout and slurm_additional_parameters
        executor_instance.update_parameters.assert_called_once()
        kwargs = executor_instance.update_parameters.call_args.kwargs
        assert kwargs["slurm_partition"] == "debug"
        assert kwargs["name"] == "unit_test"
        assert kwargs["timeout_min"] == 5

        extras = kwargs["slurm_additional_parameters"]
        # new semantics: nice=10000 (not 1000000), gres passed as-is, plus chdir
        assert extras["begin"] == "now+1hour"
        assert extras["nice"] == 10000
        assert extras["gres"] == "aQPU1:1"
        assert extras["chdir"] == workdir

        # submit receives chdir as the 5th positional arg
        # submit(_run, code, variables, output_name, chdir)
        submit_args, _ = executor_instance.submit.call_args
        assert submit_args[4] == workdir
