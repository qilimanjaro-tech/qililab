# Two-layer parameter validation: Qililab pre-check before QCodes

BoundParameter enforces Active Limits before delegating to the underlying QCodes Parameter, rather than replacing QCodes' `vals` validator with a tighter one. This means every parameter write goes through two independent checks: Qililab's Active Limits first, then QCodes' hardware validator.

## Why not just override QCodes' vals?

Replacing QCodes' validator would collapse two distinct concerns into one. Qililab's limits are experiment-level policy (configurable per runcard, tightenable at runtime); QCodes' limits are hardware contracts (fixed by the driver). If the Qililab-layer limit is misconfigured wider than the hardware allows, the QCodes validator still catches it. With a single validator, that backstop disappears.

## Considered Options

- **Replace QCodes vals**: simpler, one code path, but loses hardware contract as backstop
- **Pre-check layer (chosen)**: two independent guards, defense in depth, each layer serves a distinct purpose

## Consequences

`set_parameter` shims must route through BoundParameter to ensure the Qililab pre-check is never bypassed — even when Platform is the caller.
