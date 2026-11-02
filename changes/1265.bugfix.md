Fixed how `DatabaseManager` builds result paths:

- The folder now uses the `sample_name` and `cooldown` passed to `add_measurement` and `add_results`. It used to use `current_sample` / `current_cd`, so a different sample or cooldown passed as an argument was stored in the row but ignored in the path.
- A `None` cooldown no longer creates a literal `None` folder; the cooldown segment is left out instead.
- If the database config has no base path and no `result_folder` is given, a `ValueError` is raised. Previously the path started with `NoneNone/`, relative to the working directory.
- Adding a measurement whose folder already exists no longer fails, and the "Data folder did not exist" warning is only raised when the folder is actually created.
- `add_autocal_measurement` no longer stores the data folder in `fitting_path`. `fitting_path` stays None until `add_fitting` sets it, as on the `measurements` schema.
