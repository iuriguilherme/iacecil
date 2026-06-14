# Versioning Policy

ia.cecil follows [Semantic Versioning 2.0.0](https://semver.org).

## Format

Releases are tagged `vMAJOR.MINOR.PATCH` (note the leading `v`, matching the
current `v0.3.x` tags):

- **MAJOR** — incompatible / breaking changes.
- **MINOR** — backwards-compatible new functionality.
- **PATCH** — backwards-compatible fixes.

The project is pre-1.0. Per SemVer §4, anything may change at any time while
`MAJOR` is `0`; in practice a `MINOR` bump here may carry breaking changes and a
`PATCH` bump carries fixes. The single source of version truth is
`src/iacecil/_version.py` (`__version__`), read by `setup.cfg`.

## Tagging a release

1. Bump `__version__` in `src/iacecil/_version.py`.
2. Commit.
3. Tag the commit: `git tag -a vX.Y.Z -m "vX.Y.Z"` (annotated, not lightweight).
4. Push: `git push origin vX.Y.Z`.

## Label tags

A handful of tags are **channel labels, not releases**, and are exempt from
SemVer: `alpha`, `organic`, `stable`, `furhatgpt`, and the bare `0.2`. The first
four point at a single commit; they mark a channel, not a version, and are left
untouched.

## Historical tags (pre-SemVer)

Before this policy the project used an inconsistent 4-segment
`MAJOR.MINOR.PATCH.BUILD` scheme (`0.0.2.0`, `0.1.6.12`, `0.2.14.5`) interleaved
with some 3-segment tags. Those legacy tags are mapped onto SemVer in
[`tag-mapping.tsv`](./tag-mapping.tsv), which is the permanent record of the
old→new equivalence — consult it to find the SemVer name for any historical
version. The mapping is regenerated and validated by
[`scripts/versioning/gen_tag_mapping.py`](../../scripts/versioning/gen_tag_mapping.py).

### Mapping rules

- **4-segment `0.MINOR.B.C`** → `v0.MINOR.(B*100 + C)`. This keeps every legacy
  release below `0.3.0` (so the current latest tag stays latest), stays valid
  SemVer, and preserves a visible link to the original numbers. Patch numbers
  are intentionally inflated (`0.0.11.10` → `v0.0.1110`).
- **3-segment `0.MINOR.B`** → `v0.MINOR.(B*100)`.
- **Collision resolution.** In the `0.2` lineage a 3-segment release sometimes
  coexists with a `0.2.N.x` series (e.g. both `0.2.8` and `0.2.8.0` exist as
  distinct commits). The `.0` 4-segment variant keeps the base fold number; the
  later 3-segment release is placed immediately **after** its 4-segment
  siblings at `v0.2.(N*100 + maxC + 1)`, matching its chronological position.
  Resolved cases: `0.2.8`→`v0.2.804`, `0.2.9`→`v0.2.902`, `0.2.10`→`v0.2.1007`,
  `0.2.11`→`v0.2.1104`, `0.2.12`→`v0.2.1205`, `0.2.13`→`v0.2.1308`,
  `0.2.14`→`v0.2.1406`.
- **Already-SemVer** tags (`v0.3.0`, `v0.3.1`) are kept as-is.

### Applying the remap

New annotated SemVer tags are created at the original commits (additive, no
history rewrite) by
[`scripts/versioning/apply_tag_mapping.sh`](../../scripts/versioning/apply_tag_mapping.sh).
This step is safe and reversible — legacy tags are left in place and nothing is
pushed.

> **Rewriting published tags is a separate, irreversible step.** 190 of the
> legacy tags are already on the public remote. Deleting them and force-pushing
> the SemVer names breaks existing clones, forks, and GitHub release links. That
> step is intentionally **not** automated; it requires explicit maintainer
> action with full awareness of the breakage.
