# set_parameter kept as a shim delegating to BoundParameter

`Instrument.set_parameter(ParameterName, value, channel_id)` is preserved but made a thin dispatcher that resolves the correct BoundParameter and calls it. It is not dead code and should not be removed.

For multi-channel instruments the shim resolves the Channel identified by `channel_id`, then finds the matching BoundParameter on that Channel. For single-channel instruments (where BoundParameters live directly on the Instrument) `channel_id` is `None` and the BoundParameter is resolved directly. In both cases the write goes through the same BoundParameter validation path.

Platform internals call `set_parameter` during circuit and QProgram execution across all instrument types. Migrating all those call sites to the new BoundParameter API is a separate, larger change. The shim ensures Platform continues to work unchanged while also guaranteeing that all writes — whether from experimentalists using the new callable API or from Platform using `set_parameter` — are validated consistently.
