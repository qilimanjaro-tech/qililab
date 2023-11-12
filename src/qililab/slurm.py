import logging
import os
from types import ModuleType

from IPython.core.magic import needs_local_scope, register_cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from submitit import AutoExecutor  # pylint: disable=import-error

logger = logging.getLogger()
num_jobs_to_keep = 10


@magic_arguments()
@argument("-o", "--output", help=("Name of the variables that will be returned from the SLURM job."))
@argument("-d", "--device", help=("Name of the device where you want to execute the SLURM job."))
@argument(
    "-l",
    "--logs",
    default="./slurm_job_data",
    help=(f"Path where you want slurm to write the logs for the last {num_jobs_to_keep} jobs"),
)
@argument("-n", "--name", default="submitit", help=("Name of the slurm job"))
@needs_local_scope
@register_cell_magic
def submit_job(line: str, cell: str, local_ns: dict) -> None:
    """Magic method that queues the content of a cell as a SLURM job.

    WARNING: Variables that start with an underscore (`_`) won't be recognized in the queued job.
    """
    # This method does NOT have a standard documentation because it corresponds to an Ipython magic method.

    args = parse_argstring(submit_job, line)
    output = args.output
    partition = args.device
    folder_path = args.logs
    job_name = args.name

    # Take all the import lines and add them right before the code of the cell (to make sure all the needed libraries
    # are imported inside the SLURM job)
    notebook_code = "\n".join(local_ns["In"]).split("\n")
    import_lines = [line for line in notebook_code if line.startswith(("import ", "from ")) and "slurm" not in line]
    executable_code = "\n".join(import_lines + [cell])

    # Create the executor that will be used to queue the SLURM job
    executor = AutoExecutor(folder=folder_path)
    executor.update_parameters(slurm_partition=partition, name=job_name)

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
        exec(code, variables)
        return variables[output]

    # Submit slurm job
    job = executor.submit(function, code, variables)
    logger.info(print(f"Your slurm job '{job_name}' with ID {job.job_id} was sent to {partition}!"))
    # Overrides the output variable with the obtained job
    local_ns[output] = job

    job_ids_to_keep = list(range(int(job.job_id) - num_jobs_to_keep, int(job.job_id) + 1))
    # Delete info from past jobs
    for filename in os.listdir(folder_path):
        if int(filename.split("_")[0]) not in job_ids_to_keep:
            file_path = os.path.join(folder_path, filename)
            os.remove(file_path)
