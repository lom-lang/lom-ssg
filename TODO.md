# lom-ssg TODO

> Maintenance ledger for this repository. Cross-workspace matters live in the
> workspace-local handbook (not in any public repo); this file tracks this
> repository's own items only. Current version: **v0.1.2**.

## Registered maintenance items (from the v0.1.1 review, 2026-10-29)

- ~~R1 assertion suite in-tree~~ — **done in v0.1.2** (tests/assert.py, 71
  assertions + golden fixtures; redeems the v0.1.0 claim that had never been
  committed). CI remains deliberately unbuilt (build depends on the Lom
  toolchain binary; revisit if a released binary distribution appears).
- R2 `collect_quote` / `collect_items` double traversal — mergeable into a
  single pass returning `(list, end)`.
- R3 `json_has_key` re-stringifies the key on every call.
- R4 template files are not CRLF-normalized (content files are).
- R5 non-string config values (`"name": 42`) and non-array `pages` fail at
  runtime with a type error; README does not state the type contract.
- R6 subdirectory pages depend on the output subdirectory existing; failure is
  silent.
- R7 front-matter values keep their original quotes — undocumented.
- R8 pathological single-line inputs recurse per character; no stack-depth
  bound documented.
- R9 link URLs containing `)` truncate early — not listed in README limits.

## Standing boundaries

- `pages` is an explicit list (no directory enumeration primitive in the
  language's file module) — registered as an honest boundary of the language
  surface; do not work around.
