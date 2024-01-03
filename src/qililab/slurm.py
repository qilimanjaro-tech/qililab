import ast
import os
from types import ModuleType

from IPython.core.magic import needs_local_scope, register_cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from submitit import AutoExecutor

from qililab.config import logger

num_files_to_keep = 500  # needs to be a multiple of 4 and 5


# pylint: disable=too-many-locals


def is_variable_used(code, variable):
    """Check whether any values are assigned to the output variable inside the magic cell."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return True
    return False


@magic_arguments()
@argument(
    "-o",
    "--output",
    help="Output of the SLURM job. This name should correspond to a variable defined in the cell that we want to"
    " retrieve after execution. After queuing a cell, this variable will be converted to a `Job` class. To retrieve"
    " the results of the job, you need to call `variable.result()`.",
)
@argument("-p", "--partition", help="Name of the partition where you want to execute the SLURM job.")
@argument("-n", "--name", default="submitit", help="Name of the slurm job.")
@argument("-t", "--time", default=120, help="Time limit (in minutes) of the job.")
@argument(
    "-b",
    "--begin",
    default="now",
    help="Submit the batch script to the Slurm controller immediately, like normal, "
    "but tell the controller to defer the allocation of the job until the specified time. The time format can be"
    " either `HH:MM:SS`, `now+1hour`, `now+60minutes`, `now+60` (seconds by default), `2010-01-20T12:34:00`.",
)
@argument(
    "-l",
    "--logs",
    default=".slurm_job_data",
    help=(f"Path where you want slurm to write the logs for the last {num_files_to_keep} jobs."),
)
@argument(
    "-e",
    "--execution_environment",
    default=None,
    help="Select execution environment. Targets slurm by default but if '-e local' the job is run locally.",
)
@argument(
    "-lp",
    "--low_priority",
    default=None,
    help="By default lab jobs have higher priority than QaaS jobs. However, if '--lp True' or '--lp true' they will be queued with same priority as QaaS jobs, hence other Lab jobs will be executed first.",
)
@needs_local_scope
@register_cell_magic
def submit_job(line: str, cell: str, local_ns: dict) -> None:
    """Magic method that queues the content of a cell as a SLURM job.

    WARNING: Variables that start with an underscore (`_`) won't be recognized in the queued job.
    """
    # This method does NOT have a standard documentation because it corresponds to an Ipython magic method.

    args = parse_argstring(submit_job, line)
    output = args.output
    partition = args.partition
    job_name = args.name
    time_limit = int(args.time)
    folder_path = args.logs
    execution_env = args.execution_environment
    begin_time = args.begin
    low_priority = args.low_priority

    nice_factor = 0
    if low_priority in ["True", "true"]:
        nice_factor = 1000000  # this ensures Lab jobs have 0 priority, same as QaaS jobs

    # Take all the import lines and add them right before the code of the cell (to make sure all the needed libraries
    # are imported inside the SLURM job)
    notebook_code = "\n".join(local_ns["In"]).split("\n")
    import_lines = [line for line in notebook_code if line.startswith(("import ", "from ")) and "slurm" not in line]
    executable_code = "\n".join(import_lines + [cell])

    # Create the executor that will be used to queue the SLURM job
    executor = AutoExecutor(folder=folder_path, cluster=execution_env)
    executor.update_parameters(
        slurm_partition=partition,
        name=job_name,
        timeout_min=time_limit,
        slurm_additional_parameters={"begin": begin_time, "nice": nice_factor},
    )

    # Compile the code defined above
    code = compile(executable_code, "<string>", "exec")
    # Take all the variables defined by the user in the Jupyter Notebook and the output variable
    variables = {
        k: v
        for k, v in local_ns.items()
        if not (
            isinstance(v, ModuleType) or k.startswith("_") or k in {"In", "Out", "exit", "quit", "open", "get_ipython"}
        )
    } | {output: None}

    # Define the function that will be queued as a SLURM job
    def function(code, variables):
        # Execute the code and return the output variable defined by the user
        exec(code, variables)  # pylint: disable=exec-used # nosec
        return variables[output]

    # Check if output variables are defined or used in the magic cell
    if not is_variable_used(executable_code, output):
        raise ValueError(f"Output variable '{output}' was not assigned to any value inside the cell!")
    # Submit slurm job
    job = executor.submit(function, code, variables)
    logger.info("Your slurm job '%s' with ID %s has been queued!", job_name, job.job_id)
    # Overrides the output variable with the obtained job
    local_ns[output] = job

    # Delete info from past jobs
    job_ids = []
    file_paths = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path)]
    for file_path in file_paths:
        try:
            job_ids.append(int(file_path.split("/")[1].split("_")[0]))

        # remove non-submitit files, not starting with an id
        except ValueError:
            logger.warning("%s shouldn't be in %s. It has been removed!", file_path.split("/")[1], folder_path)
            os.remove(file_path)

    for file_path in file_paths:
        if len(file_paths) >= num_files_to_keep and str(min(job_ids)) in file_path:
            os.remove(file_path)
