# Release dev (development release)

### New features since last release

### Improvements
 - Now platform.get_parameter works for QM without the need of connecting to the machine.
 - Added the option to get the time of flight and smearing information from the QM cluster
[#751] https://github.com/qilimanjaro-tech/qililab/pull/751

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

get_parameter for QM did not work due to the lack of the variable bus_alias in self.system_control.get_parameter. The variable has been added to the function and now get parameter does not return a crash.
 - [#751] https://github.com/qilimanjaro-tech/qililab/pull/751