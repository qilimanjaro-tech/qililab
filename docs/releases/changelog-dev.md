# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

- Added Yokogawa `GS200` instrument and associated istrument controller.
  [#619](https://github.com/qilimanjaro-tech/qililab/pull/619)

- Added QDevil `QDAC-II` instrument and associated istrument controller.
  [#634](https://github.com/qilimanjaro-tech/qililab/pull/634)

- `set_parameter()` can now be used without being connected to the instruments.
  [#647](https://github.com/qilimanjaro-tech/qililab/pull/647)

### Improvements

- `QuantumMachinesCluster` can be created by translating the runcard into the equivelant QUA config dictionary. `initial_setup`, `turn_on` and `turn_off` methods have been edited to properly instatiate and calibrate the instrument.
  [#620](https://github.com/qilimanjaro-tech/qililab/pull/620)

### Breaking changes

- `QuantumMachinesManager` has been renamed to `QuantumMachinesCluster` and `QMMController` to `QuantumMachinesClusterController`.
  [#620](https://github.com/qilimanjaro-tech/qililab/pull/620)

### Deprecations / Removals

### Documentation

### Bug fixes
