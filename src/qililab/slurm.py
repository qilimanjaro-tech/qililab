import os
from types import ModuleType

from IPython.core.magic import needs_local_scope, register_cell_magic
from submitit import AutoExecutor


@needs_local_scope
@register_cell_magic
def queue(line: str, cell: str, local_ns: dict) -> None:
    """Magic method that queues the content of a cell as a SLURM job.

    Args:
        line (str): String containing the parameters of the cell magic. These are:
            - o: Name of the variable where we will store the output of the job.
            - p: Name of the partition we want to access.
        cell (str): String containing the code of the cell to be executed.
        local_ns (dict): Dictionary containing all the local scope of the jupyter notebook.

    .. warning::

        Variables that start with an underscore won't be recognized in the queued job.

    Examples:

        Imagine you want to execute a cell that does a computation and saves the results in a variable called `results`.
        To execute this cell as a SLURM job in a partition called `galadriel` you need to do the following:

        .. code-block:: python

            %%slurm -o results -p galadriel
            print(platform.buses)

            results = []
            for i in np.arange(0, 1, step=0.001):
                print(i)
                platform.set_parameter(alias="Drag(0)", parameter=ql.Parameter.GAIN, value=i)
                result = np.random.random(size=10)
                results.append(result)

        Inside the Jupyter Notebook, the `results` will be overriden by the `Job` class from the `submitit` library.

        To retrieve the results of the actual execution, you need to call `results.result()`:

        >>> results.result()
        [array([0.23125418, 0.10364256, 0.24847791, 0.49476144, 0.35349929,
        0.6723665 , 0.89654103, 0.86501083, 0.05293337, 0.05119478]),
        ...
    """
    # Parse the arguments in the `line` parameter
    args = line.split()
    outputs = args[args.index("-o") + 1 : args.index("-p")]

    if len(outputs) > 1:
        raise ValueError(
            "Only one output is supported. If multiple values are computed in the cell, unify them in a single variable"
        )
    output = outputs[0]
    partition = args[args.index("-p") + 1]

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
