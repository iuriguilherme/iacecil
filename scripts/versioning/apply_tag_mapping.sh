#!/bin/sh
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
# Create annotated SemVer tags at the legacy commits, from the reviewed
# mapping in docs/versioning/tag-mapping.tsv. ADDITIVE and REVERSIBLE: this
# script never deletes a legacy tag and never pushes. Legacy and new tags
# coexist locally afterwards; undo with `git tag -d <new>`.
#
# The destructive rewrite (delete legacy + force-push) is U6 in the plan and
# lives in a separate, gated script -- intentionally NOT here.
#
# Usage:
#   scripts/versioning/apply_tag_mapping.sh            # dry run (default)
#   scripts/versioning/apply_tag_mapping.sh --apply    # actually create tags
#   MAPPING=path scripts/versioning/apply_tag_mapping.sh --apply

set -eu

MAPPING="${MAPPING:-docs/versioning/tag-mapping.tsv}"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

if [ ! -f "$MAPPING" ]; then
    echo "error: mapping file not found: $MAPPING" >&2
    exit 1
fi

if [ "$APPLY" -eq 0 ]; then
    echo "DRY RUN (pass --apply to create tags). Mapping: $MAPPING"
else
    echo "APPLYING annotated tags from $MAPPING (additive, no push)"
fi

created=0
skipped=0
planned=0
mismatches=0

TAB=$(printf '\t')
CR=$(printf '\r')

# Read from the file (not a pipe) so the loop runs in this shell and the
# counters survive; skip the header with an initial read. Split fields by hand
# (IFS= read -r line) rather than letting read split on tabs: tab is IFS
# whitespace, so consecutive tabs would collapse and empty fields (e.g. the
# blank candidate on label rows) would shift every later column.
{
    read -r _header
    while IFS= read -r line || [ -n "$line" ]; do
        line=${line%"$CR"}          # tolerate CRLF line endings
        [ -z "$line" ] && continue
        legacy=${line%%"$TAB"*};    rest=${line#*"$TAB"}
        candidate=${rest%%"$TAB"*}; rest=${rest#*"$TAB"}
        commit=${rest%%"$TAB"*};    rest=${rest#*"$TAB"}
        date=${rest%%"$TAB"*}
        status=${rest##*"$TAB"}
        case "$status" in
            ok|already-semver) : ;;
            *) continue ;;
        esac
        [ -z "$candidate" ] && continue
        # Resolve the candidate as a TAG only (not any object of that name) to
        # its commit; skip when it already points where we want it.
        if existing="$(git rev-parse -q --verify "refs/tags/$candidate^{commit}" 2>/dev/null)"; then
            if [ "$existing" = "$commit" ]; then
                skipped=$((skipped + 1))
                continue
            fi
            echo "WARN: $candidate exists at $existing, want $commit -- skipping" >&2
            mismatches=$((mismatches + 1))
            continue
        fi
        planned=$((planned + 1))
        if [ "$APPLY" -eq 0 ]; then
            printf '  would tag %-12s -> %s\n' "$candidate" "$(echo "$commit" | cut -c1-12)"
        else
            # Pin tagger date to the legacy commit's date so creatordate stays sane.
            GIT_COMMITTER_DATE="$date" \
                git tag -a "$candidate" "$commit" \
                -m "SemVer retag of $legacy (see docs/versioning/tag-mapping.tsv)"
            created=$((created + 1))
            printf '  tagged %-12s -> %s\n' "$candidate" "$(echo "$commit" | cut -c1-12)"
        fi
    done
} < "$MAPPING"

if [ "$APPLY" -eq 0 ]; then
    echo "done (dry run). planned new=$planned, skipped existing=$skipped, mismatches=$mismatches"
else
    echo "done. created=$created, skipped existing=$skipped, mismatches=$mismatches"
fi

# A tag already at the WRONG commit is a mapping error, not an idempotent skip.
if [ "$mismatches" -gt 0 ]; then
    echo "error: $mismatches candidate tag(s) exist at a different commit than the mapping specifies" >&2
    exit 1
fi
