# Release dev (development release)

### New features since last release

### Improvements
- The driver of the VNA has been simplified: all files related to Agilent E5071B have been removed, only Keysight E5080B remains. The file structure has been refactored to align with the architecture used by other instruments in Qililab. The file 'driver_keysight_e5080b' is meant to be submitted to the public repo QCoDeS contrib drivers, conditional on their approval. The testing file for the driver 'test_driver_e50808b.py', alongside the file used to simulate the instrument 'Keysight_E5080B.yaml' will also be submitted. The data acquisition process now follows a status-check-based polling loop. The instrument is queried repeatedly using the command "STAT:OPER:COND?". Before each retrieval, a delay of 0.5 seconds is introduced to prevent overloading the instrument. The command returns an integer representing a bitmask indicating the status of the VNA's operation. A bitwise operation is performed to determine the readiness for data retrieval, this is done differently depending on whether the number of averages is 1 or greater:
    - For averages greater than 1: the data can be acquired when bit 8 is set (typically, bit 10 gets enabled after the first average, hence the command usually returns 1280 in decimal or 10100000000 in binary)
    - For averages equal to 1: the data can be acquired when bit 10 is set (bit 8 does not get set in this case, the expected response is 1024 in decimal or 10000000000 in binary)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes
