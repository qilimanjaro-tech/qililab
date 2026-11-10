Deprecations
=================

Pending deprecations
---------------------
- `IQPair.DRAG` is deprecated in favor of the dedicated `IQDrag` class.
    - Deprecated in v0.32.0
    - No removal version set yet

- The runcard's `integration_length` field (on `QbloxADCSequencer`) is deprecated; the integration length is now derived from the QProgram's weight duration instead.
    - Deprecated in an upcoming release (`#1151 <https://github.com/qilimanjaro-tech/qililab/pull/1151>`_)
    - No removal version set yet

- The runcard's `sequence_timeout` field (on `QbloxADCSequencer`) is deprecated; it has no effect on the instrument's behavior.
    - Deprecated in an upcoming release (`#1193 <https://github.com/qilimanjaro-tech/qililab/pull/1193>`_)
    - No removal version set yet

- `add_calibration_fitting` method (on `DatabaseManager`) is deprecated; please use `add_fitting` and set the field `database_schema="autocal"` to do the same operation.
    - Deprecated in an upcoming release (`#1223 <https://github.com/qilimanjaro-tech/qililab/pull/1223>`_)
    - No removal version set yet

- The runcard's `ext_trigger` field (on instrument controllers) is deprecated; the Qblox cluster's external trigger is now enabled automatically when a QProgram uses `wait_trigger` or `if_trigger`.
    - Deprecated in an upcoming release (`#1112 <https://github.com/qilimanjaro-tech/qililab/pull/1112>`_)
    - No removal version set yet

- `QProgram.for_loop` is deprecated in favor of `qp.sweep(variable).from_range(start, stop, step)`. When `step` does not divide `stop - start`, `from_range` rounds the number of points to the nearest and steps by `step`, where `for_loop` rounds it down and spreads the points from `start` to `stop`.
    - Deprecated in an upcoming release (`#1273 <https://github.com/qilimanjaro-tech/qililab/pull/1273>`_)
    - No removal version set yet

- `QProgram.parallel` (with `ForLoop` / `Loop` descriptions) is deprecated in favor of combining sweeps with `|`: `qp.sweep(a).from_range(...) | qp.sweep(b).from_range(...)`.
    - Deprecated in an upcoming release (`#1273 <https://github.com/qilimanjaro-tech/qililab/pull/1273>`_)
    - No removal version set yet

- The runcard's `scope_acquire_trigger_mode`, `scope_hardware_averaging` and `scope_store_enabled` fields (on `QbloxADCSequencer`), and their `Parameter` members in `set_parameter` / `get_parameter`, are deprecated and ignored; the scope is now set from the QProgram with `qp.qblox.scope(bus, averaging, trigger_level)`.
    - Deprecated in an upcoming release (`#1273 <https://github.com/qilimanjaro-tech/qililab/pull/1273>`_)
    - No removal version set yet

Completed deprecation cycles
-----------------------------
- The `path` argument in `qililab.build_platform` was changed to `runcard`, since it not only accepts a path to the YAML file but also the dictionary directly.
    - Deprecated in v0.21
    - Removed in v0.22
