# Release dev (development release)

### New features since last release

### Improvements
- The driver of the VNA has been simplified, all files related to Agilent E5071B have been removed, only Keysight E50808B is remaining. Refactored the file structure to align with the architecture used by other instruments in Qililab. The file 'driver_keysight_e5080b' is meant to be submitted to the public repo of qcode, conditional to their approval. For the wrapper, the code follows a new methodology to retrieve the data. It queries the device using "STAT:OPER:COND?" in a loop and only proceeds to acquire data once averaging is complete.

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
