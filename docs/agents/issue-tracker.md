# Issue Tracker

Work on qililab is tracked in **Linear, team QHC**. Issues are identified as `QHC-####`, branches derive from them (`qhc-####-<topic>`) and PR titles read `[QHC-####] Name`. See `AGENTS.md`, Branches and PRs.

The repository is public, so external users may also open GitHub issues on it, through the forms in `.github/ISSUE_TEMPLATE/`. GitHub Issues is an intake surface, not the work queue: a GitHub issue the team takes on gets a Linear issue in team QHC that links back to it.

## When a skill says "publish to the issue tracker"

Create the issue in Linear, team QHC, with the Linear tools available in the session. Show the human the title and body and wait for a yes before creating or editing an issue. Don't use `gh issue create` for qililab work.

## When a skill says "fetch the relevant ticket"

Read the Linear issue by its identifier (for example `QHC-1833`) with the Linear tools. For a GitHub issue from an external user, run `gh issue view <number> --comments`; it is read-only intake.

## PRs as a request surface

Off. External GitHub pull requests are not part of the triage queue. Flip this if the team starts triaging drive-by PRs.
