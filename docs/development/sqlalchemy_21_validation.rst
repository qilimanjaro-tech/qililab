SQLAlchemy 2.1 hardware validation
==================================

QHC-1644 keeps the PostgreSQL path on psycopg2 while adopting SQLAlchemy 2.1.
The implementation is in `Qililab PR 1278
<https://github.com/qilimanjaro-tech/qililab/pull/1278>`_.
Code review can proceed while the hardware result is pending. Hardware evidence
and independent human approval are still required before approval or merge.

Setup and planning inputs
-------------------------

Reserve the existing QHC Qblox instrument bench with a QRM-RF acquisition
channel, terminated input or a validated attenuated loopback fixture. Use an
approved readout-only runcard and a small binned integrated-I/Q acquisition.
No chip is required for the proposed persistence test. Do not change firmware,
QDAC biases or production configuration as part of this migration.

Before the run, record the actual asset and slot, receiving owner, instrument
modules/firmware, procedure and runcard/program hashes. Agree bins, shots,
integration time in ns, expected ``(2, bins)`` shape and an instrument-owner
approved absolute I/Q bound in integrated-I/Q arbitrary units. The bound checks
bench health. It does not permit any tolerance when comparing stored values
with the capture that was written.

``Platform.session()`` enables sources in its runcard. The receiving owner must
confirm that the selected runcard contains only approved test instruments,
without unintended outputs or a connected chip. Acquisition must finish and
cleanup must succeed before database writes begin.

For Monday 16 November 2026 planning, confirm the actual bench/slot, the supported
PostgreSQL version and the independent reviewer. These session inputs are not
established by the library ownership register.

Baseline and candidate
----------------------

Use two isolated environments on the same lab host and equipment:

* Baseline: Qililab 0.36.0 at
  ``e3c86ffc48c909292dd033bcad8dd6e86cb0e78f``, SQLAlchemy 2.0.54.
* Candidate: the reviewed full SHA of PR 1278, SQLAlchemy 2.1.8.
* Both: the same lab-supported Python 3.11, 3.12 or 3.13 patch version,
  QPySequence 0.12.0 and psycopg2-binary 2.9.13. Keep the rest of the package
  tuple fixed apart from removal of optional greenlet. Record install receipts,
  source/artifact identities and package lists privately.
* Hold hardware, firmware, wiring, acquisition limits, calibration and runcard
  fixed. Use the same deployment-supported PostgreSQL version for both.
  Existing local evidence covers PostgreSQL 18.6 only.

If the bench uses a different package tuple, agree it with the reviewer first.
Do not upgrade a working measurement environment in place or force unsupported
packages just to match this plan.

Provision two empty, dedicated databases per environment, named
``qhc1644_<unique>_measurements`` and ``qhc1644_<unique>_autocal``. Supply explicit
private INI files with the existing ``user``, ``passwd``, ``host``, ``port``,
``database`` and ``database_schema`` keys under ``[postgresql]``. No default home
INI or live measurement database is used. Keep credentials and addresses local.

Run sequence
------------

#. In baseline environment A, acquire the approved binned I/Q result. Require
   finite values, expected shape, the agreed instrument bound and successful
   session cleanup. Preserve the actual array and its hash.
#. Persist that capture through both ``measurements`` and ``autocal`` paths.
   Check exact values, dtype, shape, coordinates, metadata, calibration
   serialization, completion state, path meaning and HDF5 hash. Check fitting
   parameters and both row/DataFrame forms of ``head`` and ``tail``.
#. In candidate environment B, read A's unchanged database/file fixtures.
   Do not recreate tables or convert the stored data.
#. Run the same acquisition and persistence in B, with new output directories
   and fresh test databases. Independent acquisitions contain noise, so assess
   each against the same agreed bench bounds. Each persisted capture must match
   its own input exactly, without tolerance or dtype conversion.
#. For each schema/environment, reject an incomplete transaction, roll back,
   prove no partial row remains and run a successful query. Attempt a uniquely
   named nonexistent test database, observe a connection failure, then prove a
   fresh valid connection works. Induce no shared-server or instrument outage.
#. Reopen the unchanged A environment and read B's fixtures. Verify no schema or
   file-format conversion was introduced. This step needs no new acquisition.
#. Confirm the hardware is available for the normal procedure and sources are
   in their approved final state. Stop and preserve evidence on failure.

The notebook's fitting check stores deterministic I/Q summaries to exercise the
persistence seam. It makes no claim about a physical model fit.

Run package and evidence
------------------------

The guarded notebook, persistence helper and result template are prepared for
``QHC_hardware_tests/tests/qililab/qhc_1644_sqlalchemy/`` at test commit
``af3974a``. Publication requires a repository writer: the author's account has
read access and the private repository disables forking. The apply-ready patch
and unexecuted notebook are available from the QHC-1644 planning handoff. The
writer should publish the test PR and link it here and from QHC-1644 before the
instrument session. No hardware result is claimed by this preparation.

Attach the following to PR 1278 and its test record:

* Completed result template and sanitized executed notebook or HTML export.
* Operator, date/slot, actual asset/procedure, module/firmware versions,
  runcard/program/calibration hashes and pre-agreed acceptance bounds.
* Both full Qililab SHAs, wheel/source provenance, Python and package tuples,
  PostgreSQL version and deployment-matrix decision.
* Each schema's measurement identifier, array/dtype/shape/coordinate/metadata
  checks, fitting checks, capture/HDF5 hashes and cross-version readbacks.
* Failed-transaction and failed-connection recovery, acquisition/cleanup status,
  final safe state and all deviations or failed attempts.
* Human hardware sign-off and independent code/result review links.

Keep raw data in the approved private artifact location and link immutable
records. Do not commit populated INIs/runcards, credentials, instrument addresses
or full private paths. A passing synthetic harness is not a hardware result.
The operator/DB owner removes only these session databases after evidence review.

Review handoff
--------------

Albert runs the test and remains the implementation author. The
`Qililab maintenance entry
<https://app.notion.com/p/3fb7eec14c538127b780c522db925f5b>`_
nominates Flavie Le Bars as maintainer, with acceptance pending. Jordi Valls is
the checked-in results/database CODEOWNER. Route the library and DB review to
these contacts without treating a review request as accepted ongoing ownership.
Albert does not approve his own PR.

Follow the `QHC hardware-test workflow
<https://app.notion.com/p/4087eec14c5381ed904ffeb2672f3b20>`_.
A reviewer can comment that code review passed while hardware is pending.
Do not mark the migration Approved, replace the hardware-needed label with
``hardware-tested``, or merge until required evidence and independent approval
are complete. Applicable downstream consumer checks remain separately scoped.
