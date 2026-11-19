SQLAlchemy 2.1 database validation
==================================

QHC-1644 keeps the PostgreSQL path on the shipped psycopg2 driver while adopting
SQLAlchemy 2.1. The implementation is in `Qililab PR 1278
<https://github.com/qilimanjaro-tech/qililab/pull/1278>`_. Database write/readback
checks validate this change without instruments or a chip. This replaces the
earlier hardware run plan, following the validation decision recorded on
17 November 2026 in the PR. The prepared instrument-only test package is
historical and is not a publication or merge dependency for this change.
Independent human review is still required.

Scope
-----

The runtime changes select ``postgresql+psycopg2`` in ``get_engine`` and keep
model and projected-row queries separately inferred in ``head`` and ``tail``.
The dependency range is ``sqlalchemy>=2.1.8,<2.2``. Public functions, database
INI fields, mapped models and stored file formats are unchanged.

The database layer is called by ``Platform.load_db_manager``, ``StreamArray``
and ``ExperimentResultsWriter``. Validate those software boundaries with
synthetic inputs and the existing consumer tests. Instrument acquisition,
firmware and calibration are outside this change's validation scope.

Disposable PostgreSQL setup
---------------------------

Use a dedicated local PostgreSQL server bound to loopback, with a
``qililab_test`` role (password ``test``) that can create databases. Set the
server's port explicitly to opt in:

.. code-block:: bash

   QILILAB_TEST_POSTGRES_PORT=55464 uv run pytest tests/result/test_database_postgresql.py

Each case creates and drops its own uniquely named database. Without the port,
these integration tests skip. The fixtures use explicit temporary INI files
with the existing ``user``, ``passwd``, ``host``, ``port``, ``database`` and
``database_schema`` keys under ``[postgresql]``. They do not use the default
home INI or an existing measurement database.

Run the driver and software consumer regressions as well:

.. code-block:: bash

   uv run pytest tests/result tests/platform/test_platform.py tests/qprogram/test_experiment_executor.py

Baseline and candidate checks
-----------------------------

Use isolated environments with SQLAlchemy 2.0.54 and 2.1.8. Record the full
Qililab source identity, local diff or artifact hash, Python patch version,
psycopg2-binary version, PostgreSQL version and remaining package versions.
Existing local evidence used QPySequence 0.12.0 and psycopg2-binary 2.9.13.
Keep the rest of each comparison's package tuple fixed apart from SQLAlchemy
and its optional greenlet dependency.

Check both ``measurements`` and ``autocal`` schemas:

* Write and reload deterministic values, dtype, shape, coordinates and metadata.
  Check calibration serialization, result paths, completion state and fitting
  parameters. Stored values must match their input exactly.
* For the measurements schema, exercise full-model and projected-row forms of
  ``head`` and ``tail``, including DataFrame output, filtering, ordering and limits.
  These methods are not available for the autocal schema.
* Reject an incomplete transaction, roll back and verify no partial row remains.
  Then prove the same session can complete a valid transaction.
* Attempt a uniquely named missing database, observe the connection failure,
  then prove a fresh valid connection works. Do not induce a shared-server outage.
* Preserve the same synthetic fixtures across a 2.0.54 write, 2.1.8 read/update
  and 2.0.54 read. Verify that no schema or file conversion is needed.

Keep raw artifacts and package receipts in the approved private evidence location.
Do not commit populated INIs, credentials, deployment addresses or operational
configuration. Remove only the disposable databases created for these checks.

Acceptance and review
---------------------

Local PostgreSQL evidence covers 18.6. Confirm the supported deployment
PostgreSQL versions with the maintainer and Platform, then provide evidence
for that agreed matrix. Separately scoped QiliTools, Seqtante, Seqtante-open
and SDK consumer compatibility remains required where applicable. Qililab's
software consumer tests alone do not establish downstream deployment readiness.

Albert retains implementation ownership and cannot approve his own PR. Route
database evidence to Ely and library review to Flavie, as recorded in PR 1278.
The database reviewer must accept the write/readback, transaction and parity
evidence, followed by fresh independent review of the revised code. Passing
software checks do not claim completed approval, release or deployment.
