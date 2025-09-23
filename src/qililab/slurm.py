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

from __future__ import annotations

import ast
import logging
import os
import re
import shutil
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable

import cloudpickle
from IPython import get_ipython
from IPython.core.magic import needs_local_scope, register_cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from submitit import AutoExecutor

from qililab.config import logger

# Keep at job-group granularity rather than raw files (see cleanup below).
# Historically this was "files"; we interpret it as "job groups" to be robust.
max_groups_to_keep = 500

# ---------------------------
# Helpers
# ---------------------------


def _assigned_to_name(target: ast.AST, name: str) -> bool:
    """Return True if the assignment target contains a Name with given identifier."""
    if isinstance(target, ast.Name):
        return target.id == name
    if isinstance(target, (ast.Tuple, ast.List)):
        return any(_assigned_to_name(elt, name) for elt in target.elts)
    # We ignore Attribute/Subscript etc. on purpose: `x.y = ...` shouldn't count as assigning `x`.
    return False


def is_variable_assigned(code: str, variable: str) -> bool:
    """Check whether a value is assigned to `variable` inside the magic cell."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(_assigned_to_name(t, variable) for t in node.targets):
                return True
        elif isinstance(node, ast.AugAssign):
            if _assigned_to_name(node.target, variable):
                return True
        elif isinstance(node, ast.AnnAssign):
            if node.simple and isinstance(node.target, ast.Name) and node.target.id == variable:
                return True
        elif isinstance(node, ast.NamedExpr):  # walrus: x := ...
            if isinstance(node.target, ast.Name) and node.target.id == variable:
                return True
    return False


def _safe_expand_path(p: str) -> str:
    """Expand ~ and env vars, but do not resolve to avoid breaking remote mounts."""
    return os.path.expandvars(os.path.expanduser(p))


def _iter_import_lines_from_history(in_cells: Iterable[str]) -> Iterable[str]:
    """Extract simple one-line import statements from the notebook history."""
    for cell_src in in_cells:
        for line in cell_src.splitlines():
            stripped = line.strip()
            # conservative: only literal one-line imports; ignore magics and multiline constructs
            if stripped.startswith(("import ", "from ")) and not stripped.startswith(("from __future__",)):
                yield stripped


def _is_picklable(obj: Any) -> bool:
    try:
        cloudpickle.dumps(obj)
        return True
    except Exception:  # noqa: BLE001
        return False


def _collect_user_variables(local_ns: dict[str, Any], output_name: str) -> dict[str, Any]:
    """Filter local_ns to a picklable dict suitable for shipping to a Submitit job."""
    skip_keys = {"In", "Out", "exit", "quit", "open", "get_ipython"}
    vars_for_job: dict[str, Any] = {}

    for k, v in local_ns.items():
        if k.startswith("_"):
            continue
        if k in skip_keys:
            continue
        if isinstance(v, ModuleType):
            continue
        if isinstance(v, logging.Logger):
            continue
        if not _is_picklable(v):
            # It's fairly common to have unpicklables in a notebook namespace; just skip them.
            continue
        vars_for_job[k] = v

    # Ensure the expected output name exists in the namespace
    vars_for_job[output_name] = None
    return vars_for_job


def _cleanup_submitit_folder(folder: Path, max_groups_to_keep: int) -> None:
    """
    Submitit typically creates files/dirs prefixed by the numeric Slurm job id, e.g.:
      1234567_submission.pkl, 1234567_log.out, 1234567_...
    We group by the numeric prefix and keep only the newest groups.
    """
    try:
        entries = list(folder.iterdir())
    except FileNotFoundError:
        return

    # Group by numeric prefix; non-conforming files are removed as noise.
    groups: dict[int, list[Path]] = {}
    noise: list[Path] = []
    id_re = re.compile(r"^(\d+)")
    for p in entries:
        name = p.name
        m = id_re.match(name)
        if not m:
            noise.append(p)
            continue
        job_id = int(m.group(1))
        groups.setdefault(job_id, []).append(p)

    # Remove noise (non-submitit artefacts)
    for p in noise:
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            logger.warning("%s shouldn't be in %s. It has been removed!", p.name, str(folder))
        except Exception as e:  # noqa: BLE001
            logger.debug("Failed to remove stray entry %s: %s", p, e)

    if not groups:
        return

    # Keep the most recent groups (by job_id), remove the rest.
    job_ids_sorted = sorted(groups.keys())
    to_remove_ids = job_ids_sorted[:-max(1, max_groups_to_keep)]
    for jid in to_remove_ids:
        for p in groups[jid]:
            try:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    p.unlink(missing_ok=True)
            except Exception as e:  # noqa: BLE001
                logger.debug("Failed to remove %s for job %d: %s", p, jid, e)


# ---------------------------
# Magic
# ---------------------------

@magic_arguments()
@argument(
    "-o", "--output",
    required=True,
    help=("Name of the variable defined in the cell whose value you want to retrieve. "
          "After queuing, this variable becomes a `Job`. Call `variable.result()` to get the result."),
)
@argument("-p", "--partition", help="Slurm partition to run on (optional).")
@argument("-g", "--gres", default=None, help="Value for `--gres` (e.g. 'gpu:2' or 'gpu:a100:2').")
@argument("-n", "--name", default="submitit", help="Slurm job name.")
@argument("-t", "--time", type=int, default=120, help="Time limit in minutes.")
@argument(
    "-b", "--begin", default="now",
    help=("Defer the allocation until the given time, e.g. 'HH:MM:SS', 'now+1hour', "
          "'2010-01-20T12:34:00'.")
)
@argument(
    "-l", "--logs", default=".slurm_job_data",
    help=("Directory where submitit will store job artefacts and logs. "
          f"We keep the last {max_groups_to_keep} job groups."),
)
@argument(
    "-e", "--execution-environment", "--execution_environment", dest="execution_environment",
    default=None,
    help="Execution backend (e.g. 'slurm' or 'local'). Defaults to submitit's auto-detection.",
)
@argument(
    "-lp", "--low-priority", "--low_priority", dest="low_priority",
    action="store_true", default=False,
    help=("Queue with lower priority (we set a positive Slurm NICE value so Lab jobs yield to others)."),
)
@argument(
    "-c", "--chdir",
    default=None,
    help=("Working directory for the job (`sbatch --chdir`). "
          "Also applied inside the job so it works for the local backend."),
)
@needs_local_scope
@register_cell_magic
def submit_job(line: str, cell: str, local_ns: dict) -> None:
    """
    Queue the content of a cell as a Slurm job using submitit.

    WARNING: Variables whose names start with '_' are not shipped to the job.
    """
    args = parse_argstring(submit_job, line)

    output_name: str = args.output
    partition: str | None = args.partition
    gres: str | None = args.gres
    job_name: str = args.name
    time_limit: int = args.time
    begin_time: str = args.begin
    low_priority: bool = args.low_priority
    chdir_opt: str | None = args.chdir
    execution_env: str | None = args.execution_environment

    # Prepare logs folder
    folder_path = Path(_safe_expand_path(args.logs))
    folder_path.mkdir(parents=True, exist_ok=True)

    # Gather import lines from history (conservative, one-liners only)
    ip = get_ipython()
    in_cells = ip.user_ns.get("In", []) if ip is not None else []
    import_lines = list(_iter_import_lines_from_history(in_cells))

    executable_code = "\n".join([*import_lines, cell])

    # Validate that the cell assigns to the requested output variable
    if not is_variable_assigned(executable_code, output_name):
        raise ValueError(f"Output variable '{output_name}' was not assigned to any value inside the cell.")

    # Collect a safe subset of the local namespace to ship with the job
    variables = _collect_user_variables(local_ns, output_name)

    # Build executor
    extra: dict[str, Any] = {}
    if begin_time:
        extra["begin"] = begin_time
    if low_priority:
        # NICE range is typically [-10000, 10000]; positive lowers priority.
        extra["nice"] = 10000
    if gres:
        extra["gres"] = f"{gres}:1"
    if chdir_opt:
        extra["chdir"] = _safe_expand_path(chdir_opt)

    executor = AutoExecutor(folder=str(folder_path), cluster=execution_env)

    update_params: dict[str, Any] = {
        "name": job_name,
        "timeout_min": time_limit,
    }
    if partition:
        update_params["slurm_partition"] = partition
    if extra:
        update_params["slurm_additional_parameters"] = extra

    executor.update_parameters(**update_params)

    # Define the job function
    def _run(code_str: str, ns: dict[str, Any], out_name: str, chdir_path: str | None = None):
        # Apply chdir locally as well (helpful when -e local)
        if chdir_path:
            try:
                import os as _os
                _os.chdir(chdir_path)
            except Exception as e:  # noqa: BLE001
                # Don't fail the job just because chdir failed; user can inspect logs.
                print(f"[submit_job] Warning: failed to chdir to {chdir_path!r}: {e}")  # noqa: T201

        # Execute user code in the provided namespace and return the output
        exec(compile(code_str, "<submit_job>", "exec"), ns)  # noqa: S102
        return ns[out_name]

    # Submit
    job = executor.submit(_run, executable_code, variables, output_name, extra.get("chdir"))
    logger.info("Your slurm job '%s' with ID %s has been queued!", job_name, job.job_id)

    # Expose the Job object under the requested output variable name
    local_ns[output_name] = job
    if ip is not None:
        ip.user_ns[output_name] = job

    # Cleanup old artefacts (interpret num_files_to_keep as “job groups” to keep)
    try:
        _cleanup_submitit_folder(folder_path, max_groups_to_keep=max_groups_to_keep)
    except Exception as e:  # noqa: BLE001
        logger.debug("Cleanup of %s failed: %s", str(folder_path), e)
