# Release dev (development release)

### New features since last release

### Improvements

- Removed unnecessary wait_syncs created by `qp.wait_trigger` when the instrument has only one sequencer. 
  Now for one sequencer it will behave like this:

    ```
        qp.set_frequency(bus="drive", frequency=1e6)
        qp.wait_trigger(bus="drive", duration=1_000, port=1)
      ---            
        set_freq         4000000
        set_freq         4000000
        upd_param        4
        wait_trigger     1, 4
        wait             992
    ```
  Whereas with two buses there will be an extra wait?sync in the Q1ASM (also compensated by duration):
    ```
        qp.set_frequency(bus="drive", frequency=1e6)
        qp.set_frequency(bus="readout", frequency=1e6)
        qp.wait_trigger(bus="drive", duration=1_000, port=1)
      ---
      drive sequencer:
        set_freq         4000000
        set_freq         4000000
        upd_param        4
        wait_trigger     1, 4
        wait             988
        wait_sync        4

      readout sequencer:
        set_freq         4000000        
        set_freq         4000000        
        wait_sync        4 
    ```
  [#1099](https://github.com/qilimanjaro-tech/qililab/pull/1099)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed a bug for `wait_trigger` where for large durations the waiting time was not correctly implemented. Now it uses `_handle_add_waits` like `wait`.
  These are some examples of uses:
  - Duration of 4 creates a simple Q1ASM with the wait trigger with the minimal wait duration, not defining a port defaults to port 15:
    ```
        qp.wait_trigger(bus="drive", duration=4)
      ---
        wait_trigger     15, 4
    ```
  - Duration of 70,000 (and any duration bigger than 8) will execute `_handle_add_waits` and create waits with duration minus 4 ns (from the wait trigger):
    ```
        qp.wait_trigger(bus="drive", duration=70_000, port=1)
      ---
        wait_trigger     1, 4
        wait             65532
        wait             4464
    ```
  - If the wait_trigger is set before any parameter update qprogram defines an `upd_param` of 4 ns (adding this value to the total time):
    ```
        qp.set_frequency(bus="readout", frequency=1e6)
        qp.wait_trigger(bus="drive", duration=1_000, port=1)
      ---
        upd_param        4
        wait_trigger     1, 4
        wait             992
    ```
  [#1099](https://github.com/qilimanjaro-tech/qililab/pull/1099)