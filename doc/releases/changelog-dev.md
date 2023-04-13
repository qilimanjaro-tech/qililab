# Release dev (development release)

This document contains the changes of the current release.

### New features since last release

### Improvements

### Breaking changes

### Deprecations / Removals

The `Execution` class has been removed. Its functionality is now added to the `ExecutionManager` class. Please use `ExecutionManager`instead.

- Deprecated `Execution.platform` atribute in favor of `ExecutionManager.platform`.
- Removed all methods from `Execution` class. Methods with the same name are in the `ExecutionManager` class.
- Deprecated `Execution.turn_on_instruments()` function in favor of `ExecutionManager.turn_on_instruments()`.
- Deprecated `Execution.turn_off_instruments()` function in favor of `ExecutionManager.turn_off_instruments()`.

### Documentation

### Bug fixes
