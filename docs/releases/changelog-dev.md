# Release dev (development release)

### New features since last release

### Improvements

- Compilation for pulses is now done at platform instead of being delegated to each bus pointing to an awg instrument. This allows easier
  communication between `pulse_bus_schedules` so that they can be handled at the same time in order to tackle more complex tasks which were
  not possible otherwise. It also decouples, to a great extent, the instruments and instrument controllers (hardware) from higher level processes
  more typical of quantum control, which are involved in the pulse compilation to assembly program steps.
  [#651](https://github.com/qilimanjaro-tech/qililab/pull/651)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
