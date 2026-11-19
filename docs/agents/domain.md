# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.

If any of these files don't exist or are empty, **proceed silently**. Don't flag their absence. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates entries lazily when terms or decisions actually get resolved.

`docs/` is also the Sphinx source of the user documentation. `docs/adr/` and `docs/agents/` are agent files, not user docs.

## File structure

Single-context repo:

```
/
├── GLOSSARY.md
├── docs/adr/
└── src/qililab/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `GLOSSARY.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007, but worth reopening because…_
