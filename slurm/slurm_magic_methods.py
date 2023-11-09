import os

from IPython.core.magic import needs_local_scope, register_cell_magic
from submitit import AutoExecutor


@needs_local_scope
@register_cell_magic
def slurm(line: str, cell: str, local_ns: dict) -> None:
    """Magic method that queues the content of a cell as a SLURM job.

    Args:
        line (str): String containing the parameters of the cell magic. These are:
            - Name of the variables used inside the cell that are not defined in the same cell.
            - Name of the variable where we will store the output of the job.
        cell (str): String containing the code of the cell to be executed.
        local_ns (dict): Dictionary containing all the local scope of the jupyter notebook.

    Examples:

        Imagine you want to execute a cell that uses 2 external variables (Platform and Circuit) and saves the results
        of the computation in a variable called `results`. To execute this cell as a SLURM job you need to do the
        following:

        .. code-block:: python

            %%slurm -i platform circuit -o results
            print(platform.buses)

            results = []
            for i in np.arange(0, 1, step=0.001):
                print(i)
                platform.set_parameter(alias="Drag(0)", parameter=ql.Parameter.GAIN, value=i)
                result = np.random.random(size=10)
                results.append(result)

        Inside the Jupyter Notebook, `results` will correspond to the `Job` class from the `submitit` library. To
        retrieve the results of the actual execution, you need to call `results.result()`:

        >>> results.result()
        [array([0.23125418, 0.10364256, 0.24847791, 0.49476144, 0.35349929,
        0.6723665 , 0.89654103, 0.86501083, 0.05293337, 0.05119478]),
        ...
    """
    # Parse the arguments in the `line` parameter
    args = line.split()
    input_args_str = args[args.index("-i") + 1 : args.index("-o")]
    output_arg_str = args[args.index("-o") + 1 : args.index("-p")]
    partition_arg_str = args[args.index("-p") + 1]

    # Take all the import lines and add them right before the code of the cell (to make sure all the needed libraries
    # are imported inside the SLURM job)
    notebook_code = "\n".join(local_ns["In"]).split("\n")
    import_lines = [line for line in notebook_code if line.startswith(("import ", "from ")) and "slurm" not in line]
    executable_code = "\n".join(import_lines + [cell])

    # Create the executor that will be used to queue the SLURM job
    executor = AutoExecutor(folder=".slurm_job_data")
    executor.update_parameters(slurm_partition=partition_arg_str)

    # Compile the code defined above
    code = compile(executable_code, "<string>", "exec")
    # Take all the variables given by the user
    variables = {arg: local_ns[arg] for arg in input_args_str} | {output: None for output in output_arg_str}

    # Define the function that will be queued as a SLURM job
    def function():
        # Execute the code and return the output variable defined by the user
        exec(code, variables)
        return {output: variables[output] for output in output_arg_str}
    
    # Submit slurm job
    job = executor.submit(function)
    # Overrides the output variable with the obtained job
    local_ns['job'] = job
    
    #Delete info from past jobs
    folder_path = "./.slurm_job_data"  # Replace with the path to your folder

    try:
        for filename in os.listdir(folder_path):
            if str(job.job_id) not in filename:
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    except FileNotFoundError:
        print(f"Folder not found: {folder_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
