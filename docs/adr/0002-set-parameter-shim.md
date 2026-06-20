# set_parameter kept as a shim delegating to BoundParameter

`Instrument.set_parameter(ParameterName, value, channel_id)` is preserved but made a thin dispatcher that finds the matching Channel and calls its BoundParameter. It is not dead code and should not be removed.

Platform internals call `set_parameter` during circuit and QProgram execution. Migrating all those call sites to the new BoundParameter API is a separate, larger change. The shim ensures Platform continues to work unchanged while also guaranteeing that all writes — whether from experimentalists using `ch01.voltage(0.5)` or from Platform using `set_parameter` — go through the same BoundParameter validation path.
