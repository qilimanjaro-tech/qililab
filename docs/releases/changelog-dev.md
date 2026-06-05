# Release dev (development release)

### New features since last release

### Improvements

- Migrated `QbloxCompiler` to the redesigned `qpysequence` API (version 1.0.0). The compiler now uses the new `Compiler` class (`qpysequence.compiler.Compiler`) to lower and compile Q1ASM programs, replacing the old `program.compile()` call. Program construction now uses `block.add()` throughout, programs have an explicit `setup` block followed by `main`, loop sweeps use the new `SweepSpec`-based `IterativeLoop` API with `ConversionInstruction` subclasses (`SetNormalisedOffs`, `SetNormalisedGain`, `SetFrequencyHz`, `SetPhaseRad`) for automatic physical-unit-to-integer scaling, and label references no longer require the `@` prefix. `Sequence.todict()` is replaced by `Sequence.to_dict()` throughout. Several responsibilities have shifted from `qililab` to `qpysequence`:
  - **`nop` insertion**: qililab no longer emits `nop` instructions manually; qpysequence's compiler handles read-after-write hazard guards automatically. Duplicate parameter instructions (e.g. double `set_awg_gain` or `set_freq`) that were previously emitted as a workaround are no longer needed.
  - **Physical-unit-to-integer conversion**: scaling of physical-unit values (normalised gain/offset, Hz frequency, radian phase) to Q1ASM integers is now fully owned by qpysequence via `ConversionInstruction.scale_factor`.
  - **Long-wait handling**: durations exceeding `INST_MAX_WAIT` are now managed by qpysequence's `LongWait` instruction rather than qililab.
  - **Adjacent wait merging**: consecutive `wait` instructions are now combined by qpysequence's compiler rather than by qililab.
  - The Q1ASM output is functionally equivalent but may differ structurally from previous versions; see the qpysequence changelog for a full description.
- Updated `QbloxDraw` to iterate over all program blocks (`setup` and `main`) to match the new multi-block program structure.
- `QbloxCompiler` now emits a warning and clamps to 4 ns when a `wait` duration or loop start value is below the Q1ASM minimum of 4 ns.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/1090)

### Breaking changes

### Deprecations / Removals

### Documentation

### Bug fixes

- Fixed incorrect Q1ASM emitted when a long wait (> `INST_MAX_WAIT`) follows a pending `upd_param`: the pending-instruction branch now uses `LongWait` consistently with the no-pending branch.
- Fixed numpy scalar passthrough in `QProgram` operations: `wait`, `wait_trigger`, `set_phase`, `set_frequency`, `set_gain`, `set_offset`, and `for_loop` parameters now call `_to_scalar()` to convert numpy integer/float types to native Python scalars before constructing operations, preventing type errors downstream.
  [#1090](https://github.com/qilimanjaro-tech/qpysequence/pull/71)
