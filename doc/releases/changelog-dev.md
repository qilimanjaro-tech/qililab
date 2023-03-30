# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added `Experiment.compile` method, which return the compiled experiment for debugging purposes.
  [#225](https://github.com/qilimanjaro-tech/qililab/pull/225)

  ```pycon
  >>> sequences = experiment.compile()
  ```

  This method returns a list of dictionaries (one dictionary per circuit executed in the experiment). Each dictionary
  contains the sequences uploaded for each bus:

  ```pycon
  >>> sequences[0]
  {'drive_line_bus': [qpysequence_1], 'feedline_input_output_bus': [qpysequence_2]}
  ```

  This experiment is only using one bus (`drive_line_bus`), which has a list of the uploaded sequences
  (in this case only 1).

  We can then obtain the program of such sequence:

  ```pycon
  >>> sequences[0]["drive_line_bus"][0]._program
  setup:
    move             1000, R0
    wait_sync        4
  average:
    reset_ph
    play             0, 1, 4
    long_wait_1:
        move             3, R1
        long_wait_1_loop:
            wait             65532
            loop             R1, @long_wait_1_loop
        wait             3400

    loop             R0, @average
  stop:
    stop
  ```

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
