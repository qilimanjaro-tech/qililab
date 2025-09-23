import os
import shutil
import logging
import ast
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import qililab as ql
from IPython.testing.globalipapp import start_ipython

slurm_job_data_test = "slurm_job_data_test"

class _Unpicklable:
    def __reduce__(self):
        raise RuntimeError("nope")

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

        ql.slurm.max_job_groups_to_keep = 3
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
        expected_top_n = sorted(candidate_ids)[-ql.slurm.max_job_groups_to_keep:]
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

    @pytest.mark.parametrize(
        "code, expected",
        [
            ("results = 1", True),                      # Assign
            ("results += 1", True),                     # AugAssign
            ("results: int = 1", True),                 # AnnAssign
            ("(results, other) = (1, 2)", True),        # Tuple destructuring
            ("x = (results := 5)", True),               # NamedExpr (walrus)
            ("x = 1\ny = 2", False),                    # Not assigned
        ],
    )
    def test_is_variable_assigned_variants(self, code, expected):
        assert ql.slurm.is_variable_assigned(code, "results") is expected


    def test_is_variable_assigned_syntax_error_returns_false(self):
        # Invalid Python -> SyntaxError branch covered
        code = "def = 1"
        assert ql.slurm.is_variable_assigned(code, "results") is False

    def test_safe_expand_path_expands_tilde_and_env(self, monkeypatch):
        monkeypatch.setenv("SLURM_TEST_ENVPATH", "foo")
        raw = "~/${SLURM_TEST_ENVPATH}"
        expanded = ql.slurm._safe_expand_path(raw)
        assert os.path.expanduser("~") in expanded
        assert expanded.endswith(os.sep + "foo")

    def test_iter_import_lines_from_history_filters_future_and_keeps_simple_imports(self):
        cells = [
            "import os\nx = 1",
            "from sys import path\nprint('ok')",
            "from __future__ import annotations\nprint('ignored')",
            "%%bash\necho hi",
            "y = 3",
        ]
        lines = list(ql.slurm._iter_import_lines_from_history(cells))
        # Should include the first import lines only (one-liners)
        assert "import os" in lines
        assert "from sys import path" in lines
        # Should exclude __future__ and non-import cells
        assert not any("__future__" in l for l in lines)
        assert not any("%%bash" in l for l in lines)

    def test_is_picklable_true_and_false(self, tmp_path):
        assert ql.slurm._is_picklable({"a": 1}) is True
        assert ql.slurm._is_picklable(_Unpicklable()) is False

    def test_collect_user_variables_filters_unwanted(self, monkeypatch, tmp_path):
        fpath = tmp_path / "f.txt"
        fpath.write_text("x")
        f = open(fpath, "r")  # unpicklable

        try:
            ns = {
                "_private": 1,
                "In": [],
                "Out": {},
                "exit": object(),
                "quit": object(),
                "open": open,
                "get_ipython": lambda: None,
                "mod": logging,                         # ModuleType
                "log": logging.getLogger("t"),          # Logger
                "ok": 42,                               # picklable
                "unpick": f,                            # not picklable
            }
            collected = ql.slurm._collect_user_variables(ns, "results")
            assert "ok" in collected
            assert "results" in collected
            # All others filtered
            for k in ["_private", "In", "Out", "exit", "quit", "open", "get_ipython", "mod", "log"]:
                assert k not in collected
        finally:
            f.close()

    def test_run_function_chdir_failure_prints_and_executes(self, ip, capsys, tmp_path):
        """
        Patch AutoExecutor to capture the submitted function, then invoke it with a
        non-existent workdir to cover the try/except path that prints a warning.
        """
        workdir = tmp_path / "does-not-exist"  # we do NOT create it

        with patch("qililab.slurm.AutoExecutor") as executor:
            executor_instance = MagicMock()
            fake_job = MagicMock()
            fake_job.job_id = "777000"
            executor_instance.submit.return_value = fake_job
            executor.return_value = executor_instance

            ip.run_cell(raw_cell="a=1\nb=1")
            ip.run_cell_magic(
                magic_name="submit_job",
                line=f"-o results -l {tmp_path} -n unit_test -e local -c {workdir}",
                cell="results = a+b",
            )

            # Extract submitted function and args
            (run_fn, code_str, ns, out_name, chdir_arg), _ = executor_instance.submit.call_args

        # Call the submitted function ourselves to hit the chdir exception path
        ret = run_fn(code_str, ns, out_name, str(workdir))
        out = capsys.readouterr().out
        assert "failed to chdir" in out.lower()
        assert ret == 2


    def test_cleanup_missing_folder_no_crash(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        # Should simply return without throwing
        ql.slurm._cleanup_submitit_folder(missing, max_groups_to_keep=3)


    def test_cleanup_removes_noise_files_and_dirs(self, tmp_path, caplog):
        caplog.set_level(logging.WARNING)
        base = tmp_path / "logs"
        base.mkdir()

        # Noise: file and directory not starting with digits
        (base / "abc.py").write_text("x")
        (base / "miscdir").mkdir()
        (base / "miscdir" / "note.txt").write_text("y")

        # Valid job groups: 1001 and 1002
        (base / "1001_log.out").write_text("l1")
        (base / "1001_submission.pkl").write_text("p1")
        (base / "1002_log.out").write_text("l2")
        (base / "1002_submission.pkl").write_text("p2")

        ql.slurm._cleanup_submitit_folder(base, max_groups_to_keep=2)

        # Noise removed; valid files remain
        assert not (base / "abc.py").exists()
        assert not (base / "miscdir").exists()
        assert (base / "1001_log.out").exists()
        assert (base / "1002_log.out").exists()
        # Warning message logged for noise removal
        assert any("has been removed" in rec.message for rec in caplog.records)


    def test_cleanup_exception_handling_in_remove(self, monkeypatch, tmp_path, caplog):
        base = tmp_path / "logs"
        base.mkdir()

        # Create noise and valid groups
        (base / "junkfile").write_text("x")
        (base / "1001_a").write_text("x")
        (base / "1002_a").write_text("x")

        # Force deletion to fail
        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(ql.slurm.shutil, "rmtree", boom)
        monkeypatch.setattr(Path, "unlink", lambda self, missing_ok=True: (_ for _ in ()).throw(RuntimeError("boom")))

        # Should not raise, even though deletions fail
        ql.slurm._cleanup_submitit_folder(base, max_groups_to_keep=1)

        # Entries still exist because deletion failed
        assert (base / "junkfile").exists()
        # One of the job groups should still exist (since removal failed)
        assert any((base / f).exists() for f in ("1001_a", "1002_a"))

    def test_cleanup_removes_old_directory_group_triggers_rmtree(self, tmp_path, monkeypatch):
        base = tmp_path / "logs"
        base.mkdir()

        # Old group (to be removed): include a directory so p.is_dir() is True
        old_dir = base / "1001_dir"
        old_dir.mkdir()
        (old_dir / "payload.txt").write_text("x")
        # Add another file in same old group
        (base / "1001_file").write_text("x")

        # Newer group (to be kept)
        (base / "1002_keep").write_text("y")

        # Spy on shutil.rmtree to prove the directory branch executes
        orig_rmtree = ql.slurm.shutil.rmtree
        calls = {"count": 0}

        def spy_rmtree(path, *, ignore_errors=True):
            calls["count"] += 1
            # perform real removal so filesystem reflects expected state
            return orig_rmtree(path, ignore_errors=ignore_errors)

        monkeypatch.setattr(ql.slurm.shutil, "rmtree", spy_rmtree)

        # Keep only the newest group (1002) -> 1001 group must be removed
        ql.slurm._cleanup_submitit_folder(base, max_groups_to_keep=1)

        # rmtree branch was executed
        assert calls["count"] >= 1
        # Old group directory removed, newer file remains
        assert not old_dir.exists()
        assert (base / "1002_keep").exists()

    def test_assigned_to_name_returns_false_for_attribute_and_subscript(self):
        # Attribute target: x.y = 1  -> should not count as assigning 'x'
        attr_target = ast.parse("x.y = 1", mode="exec").body[0].targets[0]
        # Subscript target: x[0] = 1  -> should not count as assigning 'x'
        sub_target = ast.parse("x[0] = 1", mode="exec").body[0].targets[0]

        assert ql.slurm._assigned_to_name(attr_target, "x") is False
        assert ql.slurm._assigned_to_name(sub_target, "x") is False

    def test_submit_job_cleanup_exception_is_caught_and_logged(self, ip, monkeypatch, tmp_path, caplog):
        # Capture debug records from the slurm module's logger
        caplog.set_level(logging.DEBUG, logger=ql.slurm.logger.name)

        # Force the internal cleanup call to raise so the outer try/except runs
        def boom(*_args, **_kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(ql.slurm, "_cleanup_submitit_folder", boom)

        # Submit a trivial local job; cleanup will raise but be caught and logged
        ip.run_cell(raw_cell="a=1\nb=1")
        ip.run_cell_magic(
            magic_name="submit_job",
            line=f"-o results -l {tmp_path} -n unit_test -e local",
            cell="results=a+b",
        )

        # Job still works
        assert ip.user_global_ns["results"].result() == 2

        # The except body executed (debug log emitted)
        assert any("Cleanup of" in rec.getMessage() for rec in caplog.records)