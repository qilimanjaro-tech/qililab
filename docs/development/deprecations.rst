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

Completed deprecation cycles
-----------------------------
- The `path` argument in `qililab.build_platform` was changed to `runcard`, since it not only accepts a path to the YAML file but also the dictionary directly.
    - Deprecated in v0.21
    - Removed in v0.22
