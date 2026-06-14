#!/usr/bin/env python3
#
# ia.cecil
#
# Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

"""Generate a candidate legacy-tag -> SemVer mapping for ia.cecil.

This script is PURE READ. It never creates, deletes, or moves a tag; it only
inspects ``git`` and writes a TSV describing the proposed remap. See
``docs/versioning/SEMVER.md`` for the adopted policy and
``docs/plans/2026-06-14-001-chore-semver-tag-rewrite-plan.md`` (U2/U3) for the
rationale behind the heuristics here.

Output columns (tab-separated, with a header row):

    legacy   candidate   commit   creatordate   status

``status`` is one of:

    ok                       -- mechanical mapping, no ambiguity
    COLLISION-needs-review   -- distinct commits folded to the same SemVer key
    label-keep               -- non-version label tag, left untouched
    already-semver           -- already a valid v-prefixed SemVer tag, kept as-is

Two strategies are supported:

    fold (default)  -- 0.MINOR.B.C -> v0.MINOR.(B*100 + C); 3-seg 0.MINOR.B ->
                       v0.MINOR.(B*100). Keeps every legacy release below 0.3.0
                       and preserves a visible link to the old numbers. Can
                       collide when a 3-seg and 4-seg release share MINOR.B
                       (resolved by hand in U3).
    chronological   -- assign v0.0.N in creatordate order across all numeric
                       tags. Collision-free by construction; discards the shape
                       of the original numbers.
"""

import argparse
import os
import subprocess
import sys
from collections import defaultdict

# Tags that are channel labels, not releases. They must not be remapped to
# SemVer (see SEMVER.md "Label tags"). The bare "0.2" is included because it
# shares a commit with alpha/organic/stable and reads as a label, not a version.
LABEL_TAGS = {"alpha", "organic", "stable", "furhatgpt", "0.2"}


def git_tags():
    """Return [(tag, commit_sha, creatordate_iso)] sorted by creation date."""
    fmt = "%(refname:short)%09%(objectname)%09%(creatordate:iso-strict)"
    out = subprocess.run(
        ["git", "for-each-ref", "--sort=creatordate",
         "--format", fmt, "refs/tags"],
        check=True, capture_output=True, text=True,
    ).stdout
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        tag, sha, date = line.split("\t")
        # for-each-ref gives the tag object's sha for annotated tags; resolve
        # to the commit it points at so additive retags land on the real commit.
        commit = subprocess.run(
            ["git", "rev-list", "-n1", tag],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        rows.append((tag, commit, date))
    return rows


def classify(tag):
    """Return ('label'|'semver'|'numeric', parts) for a tag name."""
    if tag in LABEL_TAGS:
        return "label", None
    if tag.startswith("v"):
        body = tag[1:]
        parts = body.split(".")
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            return "semver", parts
        # v-prefixed but not clean 3-seg: treat conservatively as label-keep.
        return "label", None
    parts = tag.split(".")
    if all(p.isdigit() for p in parts) and len(parts) in (3, 4):
        return "numeric", parts
    # Anything else (2-seg numerics not in LABEL_TAGS, oddballs) -> label-keep.
    return "label", None


def fold_candidate(parts):
    """fold strategy: 0.MINOR.B[.C] -> v0.MINOR.(B*100 + C).

    The B*100 + C packing is only collision-free while C < 100 for every tag
    sharing a MINOR.B; the project's max C is 17, but assert it so a future tag
    that breaks the invariant fails loudly instead of silently colliding.
    """
    major, minor, b = parts[0], parts[1], int(parts[2])
    c = int(parts[3]) if len(parts) == 4 else 0
    assert c < 100, f"C={c} >= 100 in {parts}: fold packing would collide"
    return f"v{major}.{minor}.{b * 100 + c}"


def build_mapping(rows, strategy):
    """Return list of dicts: legacy, candidate, commit, date, kind."""
    mapping = []
    chrono_counter = 0
    for tag, commit, date in rows:
        kind, parts = classify(tag)
        if kind == "label":
            mapping.append(dict(legacy=tag, candidate="", commit=commit,
                                date=date, status="label-keep"))
        elif kind == "semver":
            mapping.append(dict(legacy=tag, candidate=tag, commit=commit,
                                date=date, status="already-semver"))
        else:  # numeric
            if strategy == "chronological":
                chrono_counter += 1
                candidate = f"v0.0.{chrono_counter}"
            else:
                candidate = fold_candidate(parts)
            mapping.append(dict(legacy=tag, candidate=candidate, commit=commit,
                                date=date, status="ok"))
    return mapping


def flag_collisions(mapping):
    """Mark rows whose candidate is claimed by more than one legacy tag.

    Two distinct legacy tags cannot both become one annotated SemVer tag, so the
    test is on distinct legacy *names*, not distinct commits: an alias pair that
    shares a commit (e.g. 0.2.11 / 0.2.11.0) still needs a human to pick which
    name keeps the base number. This keeps the generator's own output passing
    validate() instead of leaving a duplicate-target row marked ``ok``.
    """
    by_candidate = defaultdict(list)
    for row in mapping:
        if row["candidate"] and row["status"] == "ok":
            by_candidate[row["candidate"]].append(row)
    for candidate, group in by_candidate.items():
        if len({r["legacy"] for r in group}) > 1:
            for r in group:
                r["status"] = "COLLISION-needs-review"
    return mapping


def write_tsv(mapping, stream):
    stream.write("legacy\tcandidate\tcommit\tcreatordate\tstatus\n")
    for r in mapping:
        stream.write(f"{r['legacy']}\t{r['candidate']}\t{r['commit']}\t"
                     f"{r['date']}\t{r['status']}\n")


def validate(path):
    """Validate a reviewed mapping: no collisions, unique targets, full cover,
    and that each row's commit still matches the live legacy tag."""
    live = {t: c for t, c, _ in git_tags()}
    seen_legacy = set()
    targets = defaultdict(list)
    problems = []
    with open(path) as fh:
        # rstrip("\r\n") so a CRLF file does not leave "\r" on the status field,
        # which would let a COLLISION-needs-review row silently pass this gate.
        header = fh.readline().rstrip("\r\n")
        if header.split("\t")[:5] != \
                ["legacy", "candidate", "commit", "creatordate", "status"]:
            problems.append("bad or missing header row")
        for n, line in enumerate(fh, start=2):
            if not line.strip():
                continue
            cols = line.rstrip("\r\n").split("\t")
            if len(cols) != 5:
                problems.append(f"line {n}: expected 5 columns, got {len(cols)}")
                continue
            legacy, candidate, commit, _date, status = cols
            seen_legacy.add(legacy)
            if status == "COLLISION-needs-review":
                problems.append(f"line {n}: unresolved collision for {legacy}")
            if candidate and status in ("ok", "already-semver"):
                targets[candidate].append(legacy)
            # A hand-edited commit SHA that no longer matches the live legacy
            # tag would make apply_tag_mapping.sh tag the wrong commit.
            if legacy in live and live[legacy] != commit:
                problems.append(f"line {n}: {legacy} commit {commit[:12]} != "
                                f"live {live[legacy][:12]}")
    for candidate, legacies in targets.items():
        if len(legacies) > 1:
            problems.append(
                f"duplicate target {candidate} <- {', '.join(legacies)}")
    missing = set(live) - seen_legacy
    if missing:
        problems.append(f"missing {len(missing)} live tags: "
                        f"{', '.join(sorted(missing))}")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strategy", choices=["fold", "chronological"],
                        default="fold", help="mapping strategy (default: fold)")
    parser.add_argument("--out", default="-",
                        help="output TSV path, or - for stdout (default: -)")
    parser.add_argument("--validate", metavar="TSV",
                        help="validate a reviewed mapping file and exit")
    args = parser.parse_args(argv)

    if args.validate:
        if not os.path.exists(args.validate):
            print(f"error: file not found: {args.validate}", file=sys.stderr)
            return 1
        problems = validate(args.validate)
        if problems:
            print("INVALID mapping:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            return 1
        print("mapping OK: no collisions, unique targets, full coverage")
        return 0

    rows = git_tags()
    mapping = flag_collisions(build_mapping(rows, args.strategy))
    if args.out == "-":
        write_tsv(mapping, sys.stdout)
    else:
        with open(args.out, "w") as fh:
            write_tsv(mapping, fh)
        n_coll = sum(1 for r in mapping
                     if r["status"] == "COLLISION-needs-review")
        print(f"wrote {len(mapping)} rows to {args.out} "
              f"({n_coll} collision rows need review)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
