import os
from types import ModuleType

from IPython.core.magic import needs_local_scope, register_cell_magic
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from submitit import AutoExecutor


@magic_arguments()
@argument("-o", "--output", help=("Name of the variables that will be returned from the SLURM job."))
@argument("-d", "--device", help=("Name of the device where you want to execute the SLURM job."))
@needs_local_scope
@register_cell_magic
def queue(line: str, cell: str, local_ns: dict) -> None:
    """Magic method that queues the content of a cell as a SLURM job.

    WARNING: Variables that start with an underscore (`_`) won't be recognized in the queued job.
    """
    # This method does NOT have a standard documentation because it corresponds to an Ipython magic method.
    args = parse_argstring(queue, line)
    output = args.output
    partition = args.device

    # Take all the import lines and add them right before the code of the cell (to make sure all the needed libraries
    # are imported inside the SLURM job)
    notebook_code = "\n".join(local_ns["In"]).split("\n")
    import_lines = [line for line in notebook_code if line.startswith(("import ", "from ")) and "slurm" not in line]
    executable_code = "\n".join(import_lines + [cell])

    # Create the executor that will be used to queue the SLURM job
    folder_path = ".slurm_job_data"
    executor = AutoExecutor(folder=folder_path)
    executor.update_parameters(slurm_partition=partition)

    # Compile the code defined above
    code = compile(executable_code, "<string>", "exec")
    # Take all the variables from the Jupyter Notebook plus the output variable
    variables = {
        k: v
        for k, v in local_ns.items()
        if not (
            isinstance(v, ModuleType) or k.startswith("_") or k in {"In", "Out", "exit", "quit", "open", "get_ipython"}
        )
    } | {output: None}

    # Define the function that will be queued as a SLURM job
    def function():
        # Execute the code and return the output variable defined by the user
        exec(code, variables)
        return variables[output]

    # Submit slurm job
    job = executor.submit(function)
    # Overrides the output variable with the obtained job
    local_ns[output] = job

    # Delete info from past jobs
    for filename in os.listdir(folder_path):
        if str(job.job_id) not in filename:
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
