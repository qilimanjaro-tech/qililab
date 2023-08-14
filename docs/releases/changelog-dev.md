# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Delete `Schema` class from `Platform` and `RuncardSchema` classes (and from the rest of qililab).

  Also `RuncardSchema` is now called simply `Runcard` (since its the class that maps our runcard files).

  This PR brings importants simplifications to the full qililab structure, now the runcard will have the following structure:

  ```yaml
  name: "str: name of platform"

  device_id: "in: device id of platform"

  gates_settings:   # Old `settings`` without name & device_id
    ...

  chip:
    ...

  buses:
    ...

  instruments:
    ...

  instrument_controllers:
    ...
  ```

  instead than the previous:

  ```yaml
  settings:
    name: "str: name of platform"
    device_id: "int: device id of platform "
    ...

  schema:   # Schema disappears from the platform.
    chip:
      ...

    buses:
      ...

    instruments:
      ...

    instrument_controllers:
      ...
  ```

  Notice also how `settings` (and his respective class `PlatformSettings`) has changed to `gates_settings` (and the class to `GatesSettings` having the runcard string and the class the same name now, before they didn't).

  [#475](https://github.com/qilimanjaro-tech/qililab/pull/475)
  [#505](https://github.com/qilimanjaro-tech/qililab/pull/505)

### Improvements

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
